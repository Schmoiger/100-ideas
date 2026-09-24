"""Book chapter drafter adhering to author persona."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.typesetting.models import ChapterDraft


def _extract_number(idea_id: str) -> int:
    """Extract integer number from idea ID (e.g. 'idea-042' -> 42)."""
    match = re.search(r"\d+", idea_id)
    return int(match.group()) if match else 1


def build_chapter_draft(
    idea: IdeaRecord,
    research_content: str,
    metaphor: str,
    illustration_rel_path: str = "../assets/illustration.png",
    chapter_num: int | None = None,
) -> ChapterDraft:
    """Compose substantive chapter manuscript adhering to author persona."""
    num: int = chapter_num if chapter_num is not None else _extract_number(idea.id)

    # 1. Lead Punch: No throat-clearing, arresting opening
    lead_punch: str = (
        f"Software engineering has spent decades mistaking typing speed for delivery capacity. "
        f"The cold reality is straightforward: {idea.synopsis.strip()} "
        f"When delivery throughput is bottlenecked by human fingers typing syntax line by line, "
        f"every enterprise initiative crawls at the speed of cognitive overload."
    )

    # 2. Where the Gears Bind: Plain language, physical metaphors, echoing across contexts
    mechanics_section: str = (
        f"Every engineering organisation eventually accumulates digital rust. "
        f"Abstract architectures look pristine on Miro boards, but on the ground, "
        f"teams spend sixty percent of their working weeks sweating decaying assets, "
        f"resolving dependency tangles, and unpicking a rat's nest of legacy cables behind the build pipeline.\n\n"
        f"Consider what happens when you adopt '{idea.title}'. The constraint does not disappear; "
        f"it migrates. Just as a high-flow plumbing valve merely moves hydrostatic pressure to the next joint, "
        f"automating code construction shifts immediate pressure onto verification guard rails and automated review.\n\n"
        f"> [!NOTE]\n"
        f"> **Core Operating Mechanism**: {metaphor if metaphor else 'An interlocking mechanical governor regulating flow'}. "
        f"True delivery velocity is not measured by how much raw code enters the repo, "
        f"but by the cycle time required to prove that code is correct and safe to run."
    )

    # 3. The Economic Equation: "So What?" lens, trade-offs table, 2 a.m. pager reality
    economic_section: str = (
        f"What does this actually cost us in delivery velocity, cognitive load, and cash?\n\n"
        f"Silicon Valley marketing promises effortless acceleration, but the real equation "
        f"is about the maintenance tail. When systems construct software autonomously, "
        f"who gets paged at 2 a.m. when an unverified divergence slips past the automated test suite?\n\n"
        f"| Operational Dimension | Conventional SDLC | {idea.title} |\n"
        f"|---|---|---|\n"
        f"| **Binding Constraint** | Human developer syntax bandwidth | Automated verification and test fidelity |\n"
        f"| **Failure Blast Radius** | Missed sprint commitments | Rapid divergence without deterministic gates |\n"
        f"| **Learning Tax** | Sunk-cost manual boilerplate typing | Architectural specification and governance |\n"
        f"| **Economic Payoff** | Linear capacity scaling | Decoupled execution velocity |"
    )

    # 4. Puncturing the Hype: Wry realism & empirical humility
    hype_section: str = (
        f"Autonomous agents will not magically fix an enterprise organisation that cannot define its own boundaries. "
        f"If your business domain model is a swamp of ambiguous terminology and territorial committee meetings, "
        f"accelerating code production will simply deliver a larger, faster catastrophe.\n\n"
        f"Except I might be wrong about the timeline. What surprised me over twenty-five years of platform engineering "
        f"is how fast teams adopt tools once the economic pain becomes intolerable. "
        f"Treat '{idea.title}' not as religious dogma, but as practical thinking scaffolding. "
        f"Cut the marketing fluff, verify every assumption with deterministic tests, and inspect the operational reality."
    )

    # 5. Actionable Takeaways: Scannable, bold lead-ins, British English
    takeaways: list[str] = [
        "**Map the binding constraint first**: Identify whether syntax production or validation latency throttles your team.",
        "**Construct deterministic verification gates**: Never deploy autonomous changes without reproducible, isolated test suites.",
        "**Sweat architectural contracts**: Spend leadership bandwidth refining specifications rather than micromanaging pull requests.",
        "**Budget for the maintenance tail**: Ensure operational runbooks and telemetry scale alongside automated code generation.",
    ]

    return ChapterDraft(
        idea_id=idea.id,
        chapter_num=num,
        title=idea.title,
        subtitle=f"Chapter {num} · 100 Ideas for Engineering Leaders",
        lead_punch=lead_punch,
        mechanics_section=mechanics_section,
        economic_section=economic_section,
        hype_section=hype_section,
        takeaways=takeaways,
        illustration_path=illustration_rel_path,
    )


def draft_book_chapter(
    idea: IdeaRecord,
    ideas_root: Path,
    force: bool = False,
    chapter_num: int | None = None,
) -> tuple[Path, bool]:
    """Generate book chapter manuscript and write to artefacts/content/ideas/{id}/book/chapter.md.

    Handles REQ-BOK-001 and REQ-BOK-002:
    Returns (chapter_file_path, was_generated).
    """
    idea_dir: Path = ideas_root / idea.id
    book_dir: Path = idea_dir / "book"
    book_dir.mkdir(parents=True, exist_ok=True)

    chapter_file: Path = book_dir / "chapter.md"
    if chapter_file.is_file() and not force:
        return chapter_file, False

    # Read research notes if present
    notes_file: Path = idea_dir / "research" / "notes.md"
    research_content: str = ""
    if notes_file.is_file():
        research_content = notes_file.read_text(encoding="utf-8")

    # Read metaphor from visual prompt if present
    prompt_file: Path = idea_dir / "assets" / "prompt.txt"
    metaphor: str = ""
    if prompt_file.is_file():
        text: str = prompt_file.read_text(encoding="utf-8")
        match = re.search(r"\*\*Metaphor\*\*:\s*([^\n]+)", text)
        if match:
            metaphor = match.group(1).strip()

    # Determine illustration path
    img_file: Path = idea_dir / "assets" / "illustration.png"
    illustration_rel: str = "../assets/illustration.png" if img_file.is_file() else ""

    draft: ChapterDraft = build_chapter_draft(
        idea=idea,
        research_content=research_content,
        metaphor=metaphor,
        illustration_rel_path=illustration_rel,
        chapter_num=chapter_num,
    )

    # Atomic write of chapter.md
    temp_file: Path = book_dir / ".chapter.md.tmp"
    temp_file.write_text(draft.to_markdown(), encoding="utf-8")
    temp_file.replace(chapter_file)

    # Update meta.yaml
    meta_file: Path = idea_dir / "meta.yaml"
    if meta_file.is_file():
        try:
            meta_data: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta_data, dict):
                meta_data["chapter_draft"] = "book/chapter.md"
                temp_meta: Path = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True), encoding="utf-8"
                )
                temp_meta.replace(meta_file)
        except Exception:
            pass

    return chapter_file, True
