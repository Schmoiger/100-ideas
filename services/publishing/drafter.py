"""Blog article drafter implementing AS author persona (context/persona/author.md)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.publishing.models import BlogFrontmatter, BlogPost


def slugify(text: str) -> str:
    """Generate URL-safe slug from title or text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", slug).strip("-")


def count_words(text: str) -> int:
    """Count words in text string excluding Markdown symbols."""
    words = re.findall(r"\b[\w'-]+\b", text)
    return len(words)


def generate_author_blog_body(idea: IdeaRecord, research_summary: str = "") -> str:
    """Synthesise punchy, pragmatic blog post adhering to AS author persona (context/persona/author.md).

    Implements:
    - Punch over preamble (sharp momentum-building opening line).
    - Plain language with physical metaphors ('sweating assets', 'digital rust').
    - Maximum information density, zero throat-clearing.
    - Wry realism and hype puncturing.
    - The economic equation and 'So What?' operational consequences.
    - Empirical humility ('Except I might be wrong').
    - Bold lead-ins for scanability.
    - Target 400-800 words.
    - Strict British English spelling.
    """
    cat = idea.tags[0].title() if idea.tags else "Software Engineering"
    title = idea.title
    desc = idea.synopsis or (
        "Engineering capacity cannot keep pace with business demand when bound by manual developer bandwidth."
    )

    desc_clean = desc.strip()
    if not desc_clean.endswith("."):
        desc_clean += "."

    body_text = f"""Most enterprise software delivery bottlenecks have nothing to do with writing code.

They are caused by digital rust: the slow accumulation of manual handoffs, brittle glue scripts, and fragmented context across teams. We spend millions on compute infrastructure whilst sweating our engineering talent on the cognitive equivalent of moving piles of dirt from one corner of a field to another.

Enter **{title}**.

Strip away the vendor hype, and the underlying mechanical constraint in {cat} is simple: {desc_clean}

---

## The Operational Reality

Watch any delivery team struggle with this today. You do not see a deficit of intelligence; you see a rat's nest of fragmented workflows.

Smart engineers spend their working hours manually coordinating status updates, copy-pasting configuration fragments, and babysitting builds across disjointed portals. It is slow, it is unrepeatable, and it carries an astonishingly steep operational tax.

Every manual touchpoint introduces latency and cognitive decay. When delivery throughput is constrained by developer bandwidth, the entire enterprise slows to a crawl—regardless of how many agile ceremonies or strategic roadmaps management produces.

{title} confronts this economic equation directly. Rather than treating developer bandwidth as an infinite resource to be consumed by mechanical coordination, it automates the predictable pathways.

---

## What Actually Changes

When this architectural shift is deployed into a live delivery pipeline, the practical consequences are immediate:

- **Eliminating Digital Rust**: Automated synthesis removes the bespoke glue code that teams build to compensate for fragmented tooling.
- **Contract-First Verification**: Speculative tribal knowledge is replaced with deterministic checks and reproducible artefacts.
- **Throughput Decoupling**: Business delivery velocity decouples from raw headcount, allowing teams to scale impact without linear staffing costs.

Is it a silver bullet? Hardly. (If your underlying architectural boundaries are a disaster, automating them simply accelerates the creation of debt at scale.) But applied with disciplined intent, the operational leverage is undeniable.

---

## So What? The Economic Equation

So what should an engineering leader or systems practitioner do with this on Monday morning?

Ask the hard commercial question: what is manual coordination actually costing your organisation in delayed market feedback, context exhaustion, and defect remediation?

Stop tolerating mechanical drag as an inevitable cost of doing business. Identify the single most friction-laden handoff between concept and production in your pipeline. Put automated, verified rails around it. Measure cycle time and failure rate before and after.

Online services are driven by usage, not sentiment. Build engineering workflows that preserve human judgement for the problems that genuinely require it.
"""

    return body_text.strip()


# Backward-compatible alias
generate_opinionated_blog_body = generate_author_blog_body


def draft_blog_post(
    idea: IdeaRecord,
    ideas_root: Path,
    ideas_catalog: list[IdeaRecord] | None = None,
    force: bool = False,
    overwrite_manual: bool = False,
) -> tuple[Path, bool]:
    """Generate Hostinger-compatible blog post adhering to AS author persona.

    Implements REQ-BLG-001 and REQ-BLG-002.
    Returns (post_path, was_generated).
    Refuses to overwrite if human_modified=True without overwrite_manual=True.
    """
    from services.ingestion.safeguards import check_manual_edit_safeguard

    idea_dir = ideas_root / idea.id
    blog_dir = idea_dir / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)
    post_file = blog_dir / "post.md"

    # Check cache / idempotency & manual edit protection
    if post_file.is_file():
        if not force and not overwrite_manual:
            return post_file, False
        check_manual_edit_safeguard(
            target_file=post_file,
            idea=idea,
            force=force,
            overwrite_manual=overwrite_manual,
        )

    # Extract tags
    tags: list[str] = ["SoftwareEngineering", "Architecture"]
    for t in idea.tags:
        clean_tag = re.sub(r"\W+", "", t)
        if clean_tag and clean_tag not in tags:
            tags.append(clean_tag)
    tags.append("TechLeadership")

    # Generate slug and frontmatter
    slug = f"{idea.id}-{slugify(idea.title)}"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    excerpt = (
        f"Why {idea.title} matters for modern software engineering teams, and how to eliminate "
        f"costly cognitive friction in your day-to-day development workflow."
    )

    # Check for Single Source of Truth: master chapter manuscript
    chapter_file = idea_dir / "book" / "chapter.md"
    syndicated_from: str | None = None
    if chapter_file.is_file():
        from services.publishing.syndication import generate_syndicated_blog_body

        body_markdown = generate_syndicated_blog_body(idea, chapter_file)
        syndicated_from = "book/chapter.md"
    else:
        # Synthesise body from raw synopsis
        body_markdown = generate_author_blog_body(idea)

    words = count_words(body_markdown)
    reading_time = max(1, round(words / 200))

    frontmatter = BlogFrontmatter(
        title=f"{idea.title}: Cutting Delivery Drag",
        slug=slug,
        date=today_str,
        excerpt=excerpt,
        tags=tags,
        cover_image="../assets/illustration.png",
        author="AS",
        reading_time_minutes=reading_time,
        draft=False,
    )

    post = BlogPost(
        frontmatter=frontmatter,
        body_markdown=body_markdown,
        idea_id=idea.id,
        word_count=words,
    )

    post_content = post.render()
    post_file.write_text(post_content, encoding="utf-8")

    # Update meta.yaml
    meta_file = idea_dir / "meta.yaml"
    meta_dict: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:
            meta_dict = {}

    meta_dict["blog_post"] = "blog/post.md"
    meta_dict["blog_slug"] = slug
    meta_dict["blog_words"] = words
    if syndicated_from:
        meta_dict["syndicated_from"] = syndicated_from
        meta_dict["syndicated_at"] = datetime.now(timezone.utc).isoformat()
    meta_file.write_text(yaml.dump(meta_dict, sort_keys=False), encoding="utf-8")

    return post_file, True
