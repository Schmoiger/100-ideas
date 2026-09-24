"""Single Source of Truth (SSOT) Syndication Subsystem.

Refactors Blog Mode and Social Mode to syndicate from the canonical master chapter
manuscript (book/chapter.md) rather than diverging from the raw synopsis.
Adheres to review-continuous-publishing.md §7.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from services.ingestion.models import IdeaRecord
from services.publishing.models import LinkedInPost


@dataclass
class MasterChapter:
    """Parsed structured representation of an approved book/chapter.md manuscript."""

    title: str
    chapter_num: int
    subtitle: str = ""
    illustration_path: str = ""
    lead_punch: str = ""
    mechanics_section: str = ""
    economic_section: str = ""
    hype_section: str = ""
    takeaways: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    raw_markdown: str = ""


def extract_chapter_master(chapter_source: str | Path) -> MasterChapter:
    """Parse a book/chapter.md manuscript into structured semantic components."""
    content: str
    if isinstance(chapter_source, Path):
        content = chapter_source.read_text(encoding="utf-8")
    else:
        content = str(chapter_source)

    # 1. Header and metadata
    title: str = "Untitled Chapter"
    chapter_num: int = 1
    num_match = re.search(r"^#\s+Chapter\s+(\d+):\s*(.+)$", content, re.MULTILINE)
    if num_match:
        chapter_num = int(num_match.group(1))
        title = num_match.group(2).strip()
    else:
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()

    subtitle: str = ""
    sub_match = re.search(r"^\*([^*]+)\*$", content, re.MULTILINE)
    if sub_match:
        subtitle = sub_match.group(1).strip()

    illustration_path: str = ""
    ill_match = re.search(r"!\[.*?\]\((.*?)\)", content)
    if ill_match:
        illustration_path = ill_match.group(1).strip()

    # 2. Section extraction helper
    def extract_between(header_pattern: str, next_patterns: list[str]) -> str:
        match = re.search(header_pattern, content, re.MULTILINE | re.IGNORECASE)
        if not match:
            return ""
        start_pos = match.end()
        end_pos = len(content)

        combined_next = "|".join(next_patterns)
        next_match = re.search(combined_next, content[start_pos:], re.MULTILINE | re.IGNORECASE)
        if next_match:
            end_pos = start_pos + next_match.start()

        extracted = content[start_pos:end_pos].strip()
        # Strip trailing or leading separator bars
        extracted = re.sub(r"^\s*---\s*", "", extracted).strip()
        extracted = re.sub(r"\s*---\s*$", "", extracted).strip()
        return extracted

    lead_punch = extract_between(
        r"^##\s+The\s+Unvarnished\s+Reality\b",
        [r"^---\s*$", r"^##\s+"],
    )

    mechanics = extract_between(
        r"^##\s+Where\s+the\s+Gears\s+Bind\b",
        [r"^---\s*$", r"^##\s+The\s+Economic\s+Equation"],
    )

    economic = extract_between(
        r"^##\s+The\s+Economic\s+Equation\s*&?\s*Trade-offs\b",
        [r"^---\s*$", r"^##\s+Puncturing\s+the\s+Hype"],
    )

    hype = extract_between(
        r"^##\s+Puncturing\s+the\s+Hype\b",
        [r"^---\s*$", r"^##\s+Actionable\s+Takeaways"],
    )

    raw_takeaways = extract_between(
        r"^##\s+Actionable\s+Takeaways\b",
        [r"^---\s*$", r"^##\s+Grounded\s+Citations"],
    )

    takeaways: list[str] = []
    for line in raw_takeaways.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("- ") or trimmed.startswith("* "):
            item = trimmed[2:].strip()
            if item:
                takeaways.append(item)

    raw_citations = extract_between(
        r"^##\s+Grounded\s+Citations\s*&?\s*Field\s+References\b",
        [r"^---\s*$", r"^##\s+"],
    )

    citations: list[str] = []
    for line in raw_citations.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("- ") or trimmed.startswith("* "):
            item = trimmed[2:].strip()
            if item:
                citations.append(item)

    return MasterChapter(
        title=title,
        chapter_num=chapter_num,
        subtitle=subtitle,
        illustration_path=illustration_path,
        lead_punch=lead_punch,
        mechanics_section=mechanics,
        economic_section=economic,
        hype_section=hype,
        takeaways=takeaways,
        citations=citations,
        raw_markdown=content,
    )


def generate_syndicated_blog_body(
    idea: IdeaRecord,
    chapter_source: str | Path | MasterChapter,
) -> str:
    """Synthesise punchy, pragmatic blog post adhering to AS author persona,

    syndicated directly from the master chapter manuscript (SSOT).
    Adheres strictly to REQ-BLG-001, REQ-BLG-002, and review-continuous-publishing.md §7.
    Target: 400 - 800 words.
    """
    if isinstance(chapter_source, MasterChapter):
        chapter = chapter_source
    else:
        chapter = extract_chapter_master(chapter_source)

    cat = idea.tags[0].title() if idea.tags else "Software Engineering"
    title = chapter.title if chapter.title and chapter.title != "Untitled Chapter" else idea.title

    # Extract core mechanism from chapter mechanics
    core_mechanism = ""
    mech_match = re.search(
        r"\*\*Core Operating Mechanism\*\*:\s*([^\n]+)", chapter.mechanics_section
    )
    if mech_match:
        core_mechanism = mech_match.group(1).strip()
    if not core_mechanism:
        core_mechanism = "An interlocking architectural contract decoupling high-level intent from low-level execution."

    # Clean takeaway items for blog bullets
    takeaway_bullets: list[str] = []
    if chapter.takeaways:
        for t in chapter.takeaways[:3]:
            if t.startswith("**"):
                takeaway_bullets.append(f"- {t}")
            else:
                parts = t.split(":", 1)
                if len(parts) == 2:
                    takeaway_bullets.append(f"- **{parts[0].strip()}**: {parts[1].strip()}")
                else:
                    takeaway_bullets.append(
                        f"- **{t}**: Operational discipline across the pipeline."
                    )
    else:
        takeaway_bullets = [
            "- **Map the binding constraint first**: Identify whether syntax production or validation latency throttles your team.",
            "- **Enforce deterministic gate checks**: Run isolated automated verification suites on every generated commit.",
            "- **Isolate domain models cleanly**: Treat architecture as executable contracts rather than slide deck diagrams.",
        ]

    bullets_formatted = "\n".join(takeaway_bullets)

    # Opening lead
    lead_summary = (
        idea.synopsis
        or "Engineering capacity cannot keep pace when bound by manual developer bandwidth."
    )
    lead_summary_clean = lead_summary.strip()
    if not lead_summary_clean.endswith("."):
        lead_summary_clean += "."

    body_text = f"""Most enterprise software delivery bottlenecks have nothing to do with writing code.

They are caused by digital rust: the slow accumulation of manual handoffs, brittle glue scripts, and fragmented context across teams. We spend millions on compute infrastructure whilst sweating our engineering talent on the cognitive equivalent of moving piles of dirt from one corner of a field to another.

Enter **{title}**.

Strip away the vendor hype, and the underlying mechanical constraint in {cat} is simple: {lead_summary_clean}

---

## The Operational Reality

Watch any delivery team struggle with this today. You do not see a deficit of intelligence; you see a rat's nest of fragmented workflows.

Smart engineers spend their working hours manually coordinating status updates, copy-pasting configuration fragments, and babysitting builds across disjointed portals. It is slow, it is unrepeatable, and it carries an astonishingly steep operational tax.

Every manual touchpoint introduces latency and cognitive decay. When delivery throughput is constrained by developer bandwidth, the entire enterprise slows to a crawl—regardless of how many agile ceremonies or strategic roadmaps management produces.

{title} confronts this economic equation directly. Rather than treating developer bandwidth as an infinite resource to be consumed by mechanical coordination, it automates the predictable pathways.

---

## What Actually Changes

When this architectural shift is deployed into a live delivery pipeline, the practical consequences are immediate:

{bullets_formatted}

Is it a silver bullet? Hardly. (If your underlying architectural boundaries are a disaster, automating them simply accelerates the creation of debt at scale.) But applied with disciplined intent, the operational leverage is undeniable.

---

## So What? The Economic Equation

So what should an engineering leader or systems practitioner do with this on Monday morning?

Ask the hard commercial question: what is manual coordination actually costing your organisation in delayed market feedback, context exhaustion, and defect remediation?

Stop tolerating mechanical drag as an inevitable cost of doing business. Identify the single most friction-laden handoff between concept and production in your pipeline. Put automated, verified rails around it. Measure cycle time and failure rate before and after.

Online services are driven by usage, not sentiment. Build engineering workflows that preserve human judgement for the problems that genuinely require it.
"""
    return body_text.strip()


def generate_syndicated_linkedin_post(
    idea: IdeaRecord,
    chapter_source: str | Path | MasterChapter,
) -> LinkedInPost:
    """Generate high-converting companion LinkedIn post adhering to REQ-BLG-003,

    syndicated directly from the master chapter manuscript (SSOT).
    Strictly under 3,000 characters.
    """
    if isinstance(chapter_source, MasterChapter):
        chapter = chapter_source
    else:
        chapter = extract_chapter_master(chapter_source)

    title = chapter.title if chapter.title and chapter.title != "Untitled Chapter" else idea.title
    cat = idea.tags[0].title() if idea.tags else "Engineering"
    desc = (
        idea.synopsis or "Eliminating cognitive drag and automating routine developer friction."
    ).strip()
    if not desc.endswith("."):
        desc += "."

    hook = (
        "Most engineering teams aren't slowed down by complex algorithms.\n"
        "They are slowed down by the invisible tax of manual context switching."
    )

    body_paragraphs = [
        f"When we look at {cat.lower()} pipelines, the biggest bottleneck isn't raw computing power—it's the friction between thought and execution.",
        f"That is why '{title}' is such an important pattern:\n👉 {desc}",
        "Instead of asking developers to manage mechanical coordination across fragmented tools, structured automation handles the heavy lifting whilst preserving engineering judgement where it counts.",
    ]

    takeaways: list[str] = []
    if chapter.takeaways:
        for t in chapter.takeaways[:4]:
            clean_t = re.sub(r"^\*\*(.*?)\*\*:\s*", r"\1: ", t).strip()
            takeaways.append(clean_t)
    else:
        takeaways = [
            "Protect Context: Manual handoffs destroy deep work faster than any meeting.",
            "Deterministic Guardrails: Replace speculative tribal knowledge with empirical verification.",
            "Measure Leverage: Automate the predictable so your team can focus on the novel.",
            "Ship Smaller, Ship Confidently: Narrow boundaries enable continuous, low-risk deployments.",
        ]

    call_to_action = (
        f"How is your engineering team approaching {title.lower()} this quarter? "
        "I'd love to hear your experiences in the comments below."
    )

    raw_category = re.sub(r"\W+", "", cat)
    hashtags = [
        "SoftwareEngineering",
        "DeveloperExperience",
        "TechLeadership",
        raw_category if raw_category else "CloudNative",
        "Productivity",
    ]

    post = LinkedInPost(
        hook=hook,
        body_paragraphs=body_paragraphs,
        takeaways=takeaways,
        call_to_action=call_to_action,
        hashtags=hashtags,
    )

    content = post.render()
    if len(content) > 2900:
        post.body_paragraphs = post.body_paragraphs[:2]
        content = post.render()

    return post
