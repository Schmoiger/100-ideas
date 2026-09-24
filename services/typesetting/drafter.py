"""Book chapter drafter adhering to author persona with live Gemini SDK integration and token governance."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import yaml
from google.genai import types
from pydantic import BaseModel, Field

from services.ingestion.models import IdeaRecord
from services.llm.caching import get_or_create_context_cache, should_create_cache
from services.llm.client import get_genai_client, is_live_genai_available
from services.llm.governance import (
    check_fingerprint_match,
    clamp_context,
    compute_input_fingerprint,
    estimate_cost,
    estimate_token_count,
    get_governance,
)
from services.llm.telemetry import TokenTelemetry, record_telemetry_in_meta
from services.typesetting.models import ChapterDraft


class ChapterManuscriptSchema(BaseModel):
    """Pydantic structured output schema for book chapter manuscript."""

    lead_punch: str = Field(
        description="Arresting opening paragraph with zero throat-clearing, arresting contrast, and momentum"
    )
    mechanics_section: str = Field(
        description="Core mechanism, physical metaphors (e.g. digital rust, plumbing valves), and empirical grounding"
    )
    economic_section: str = Field(
        description="Economic trade-offs, 2 a.m. pager realities, and markdown comparison table"
    )
    hype_section: str = Field(
        description="Puncturing industry hype, dry British realism, and empirical humility"
    )
    takeaways: list[str] = Field(
        description="Actionable takeaway bullets with bold lead-ins in British English"
    )
    citations: list[str] = Field(
        default_factory=list, description="Formal citations referencing verified resources"
    )


def _extract_number(idea_id: str) -> int:
    """Extract integer number from idea ID (e.g. 'idea-042' -> 42)."""
    match = re.search(r"\d+", idea_id)
    return int(match.group()) if match else 1


def parse_research_notes_sections(research_content: str) -> dict[str, list[str]]:
    """Extract structured findings from research dossier markdown."""
    sections: dict[str, list[str]] = {
        "empirical_evidence": [],
        "economic_tradeoffs": [],
        "counterarguments": [],
        "citations": [],
    }
    if not research_content:
        return sections

    current_section: str | None = None
    for line in research_content.splitlines():
        trimmed = line.strip()
        if "## Empirical Evidence" in trimmed:
            current_section = "empirical_evidence"
            continue
        if "## Economic Trade-offs" in trimmed:
            current_section = "economic_tradeoffs"
            continue
        if "## Counterarguments" in trimmed:
            current_section = "counterarguments"
            continue
        if "## Citations" in trimmed:
            current_section = "citations"
            continue
        if trimmed.startswith("## ") or trimmed == "---":
            current_section = None
            continue

        if current_section and trimmed.startswith("- "):
            item = trimmed[2:].strip()
            if item and not (item.startswith("*No ") and item.endswith("recorded.*")):
                sections[current_section].append(item)

    return sections


def load_author_persona(repo_root: Path | None = None) -> str:
    """Load authoritative author persona from context/persona/author.md."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
    author_file = repo_root / "context" / "persona" / "author.md"
    if author_file.is_file():
        return author_file.read_text(encoding="utf-8")
    return "You are AS, a seasoned technologist with 25+ years experience. Write with British English, punchy paragraphs, and wry realism."


def build_chapter_draft(
    idea: IdeaRecord,
    research_content: str,
    metaphor: str,
    illustration_rel_path: str = "../assets/illustration.png",
    chapter_num: int | None = None,
) -> ChapterDraft:
    """Compose substantive chapter manuscript adhering to author persona (deterministic fallback)."""
    num: int = chapter_num if chapter_num is not None else _extract_number(idea.id)
    res_sections = parse_research_notes_sections(research_content)

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
    if res_sections["empirical_evidence"]:
        ev_items = "\n".join(f"- {e}" for e in res_sections["empirical_evidence"])
        mechanics_section += f"\n\n**Empirical Grounding & Field Observations**:\n{ev_items}"

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
    if res_sections["economic_tradeoffs"]:
        to_items = "\n".join(f"- {t}" for t in res_sections["economic_tradeoffs"])
        economic_section += f"\n\n**Constraint Dynamics & Real-World Trade-offs**:\n{to_items}"

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
    if res_sections["counterarguments"]:
        ca_items = "\n".join(f"- {c}" for c in res_sections["counterarguments"])
        hype_section += f"\n\n**Counterarguments & Observed Anti-Patterns**:\n{ca_items}"

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
        citations=res_sections["citations"],
        illustration_path=illustration_rel_path,
    )


def draft_book_chapter(
    idea: IdeaRecord,
    ideas_root: Path,
    force: bool = False,
    force_llm: bool = False,
    dry_run: bool = False,
    overwrite_manual: bool = False,
    chapter_num: int | None = None,
    client: Any = None,
) -> tuple[Path, bool]:
    """Generate book chapter manuscript and write to artefacts/content/ideas/{id}/book/chapter.md.

    Handles REQ-BOK-001 and REQ-BOK-002 with live Gemini 2.5 Pro integration and token guard rails.
    """
    from services.ingestion.safeguards import check_manual_edit_safeguard

    idea_dir: Path = ideas_root / idea.id
    book_dir: Path = idea_dir / "book"
    book_dir.mkdir(parents=True, exist_ok=True)
    meta_file: Path = idea_dir / "meta.yaml"
    chapter_file: Path = book_dir / "chapter.md"

    if chapter_file.is_file():
        if not force and not overwrite_manual and not force_llm:
            return chapter_file, False
        check_manual_edit_safeguard(
            target_file=chapter_file,
            idea=idea,
            force=force or force_llm,
            overwrite_manual=overwrite_manual,
        )

    # 1. Read research notes if present
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
    num: int = chapter_num if chapter_num is not None else _extract_number(idea.id)

    # 2. Cryptographic input fingerprinting (Guard Rail 3)
    author_persona = load_author_persona()
    prompt_template = (
        f"Draft publication-grade book chapter for Idea #{num}: '{idea.title}'\n"
        f"Synopsis: {idea.synopsis}\n"
        f"Metaphor: {metaphor}\n"
    )
    fingerprint = compute_input_fingerprint(
        model_name="gemini-2.5-pro",
        prompt_template=prompt_template,
        input_documents=[research_content],
    )

    if chapter_file.is_file() and not force_llm:
        if check_fingerprint_match(meta_file, fingerprint):
            return chapter_file, False

    # 3. Context Clamping & Caching (Guard Rail 4)
    cache_name: str | None = None
    cached_tokens: int = 0
    live_available = is_live_genai_available() or client is not None

    if live_available and should_create_cache([author_persona, research_content]):
        active_client = client or get_genai_client()
        cache_name = get_or_create_context_cache(
            client=active_client,
            model="gemini-2.5-pro",
            contents=[author_persona, research_content],
        )
        if cache_name:
            cached_tokens = estimate_token_count(author_persona + research_content)

    clamped_research = clamp_context(research_content, max_tokens=10_000)

    # 4. Pre-flight check & circuit breaker (Guard Rails 1 & 2)
    gov = get_governance()
    prompt_tokens = estimate_token_count(f"{prompt_template}\n\n{clamped_research}")
    projected_completion_tokens = 2200

    projected_cost = gov.check_preflight(
        model="gemini-2.5-pro",
        projected_prompt_tokens=prompt_tokens,
        projected_completion_tokens=projected_completion_tokens,
        cached_tokens=cached_tokens,
        idea_id=idea.id,
    )

    if dry_run:
        telemetry = TokenTelemetry(
            model="gemini-2.5-pro (dry-run)",
            fingerprint=fingerprint,
            prompt_tokens=prompt_tokens,
            cached_tokens=cached_tokens,
            completion_tokens=projected_completion_tokens,
            total_tokens=prompt_tokens + cached_tokens + projected_completion_tokens,
            estimated_cost_usd=projected_cost,
        )
        record_telemetry_in_meta(meta_file, telemetry)
        return chapter_file, False

    # 5. Live generation or deterministic fallback
    draft: ChapterDraft | None = None
    actual_prompt_tokens = prompt_tokens
    actual_completion_tokens = projected_completion_tokens
    actual_cached_tokens = cached_tokens
    latency_ms = 0
    used_model = "offline-mock"

    if live_available:
        try:
            active_client = client or get_genai_client()
            t0 = time.perf_counter()

            if cache_name:
                config = types.GenerateContentConfig(
                    cached_content=cache_name,
                    response_mime_type="application/json",
                    response_schema=ChapterManuscriptSchema,
                    temperature=0.4,
                )
                full_contents = prompt_template
            else:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ChapterManuscriptSchema,
                    temperature=0.4,
                )
                full_contents = (
                    f"## Author Persona & Guidelines\n{author_persona}\n\n"
                    f"## Task Directive\n{prompt_template}\n\n"
                    f"## Research Notes\n{clamped_research}"
                )

            response = active_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=full_contents,
                config=config,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            used_model = "gemini-2.5-pro"

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                actual_prompt_tokens = getattr(
                    response.usage_metadata, "prompt_token_count", prompt_tokens
                )
                actual_completion_tokens = getattr(
                    response.usage_metadata, "candidates_token_count", projected_completion_tokens
                )
                actual_cached_tokens = (
                    getattr(response.usage_metadata, "cached_content_token_count", cached_tokens)
                    or 0
                )

            parsed: ChapterManuscriptSchema = response.parsed
            draft = ChapterDraft(
                idea_id=idea.id,
                chapter_num=num,
                title=idea.title,
                subtitle=f"Chapter {num} · 100 Ideas for Engineering Leaders",
                lead_punch=parsed.lead_punch,
                mechanics_section=parsed.mechanics_section,
                economic_section=parsed.economic_section,
                hype_section=parsed.hype_section,
                takeaways=parsed.takeaways,
                citations=parsed.citations,
                illustration_path=illustration_rel,
            )
        except Exception:
            draft = None

    if draft is None:
        draft = build_chapter_draft(
            idea=idea,
            research_content=research_content,
            metaphor=metaphor,
            illustration_rel_path=illustration_rel,
            chapter_num=chapter_num,
        )

    # Record spend in accumulator
    actual_cost = estimate_cost(
        model=used_model,
        prompt_tokens=actual_prompt_tokens,
        completion_tokens=actual_completion_tokens,
        cached_tokens=actual_cached_tokens,
    )
    gov.record_usage(
        prompt_tokens=actual_prompt_tokens,
        completion_tokens=actual_completion_tokens,
        cached_tokens=actual_cached_tokens,
        cost_usd=actual_cost,
    )

    # 6. Atomic write of chapter.md
    temp_file: Path = book_dir / ".chapter.md.tmp"
    temp_file.write_text(draft.to_markdown(), encoding="utf-8")
    temp_file.replace(chapter_file)

    # 7. Record Token Telemetry in meta.yaml
    telemetry = TokenTelemetry(
        model=used_model,
        fingerprint=fingerprint,
        prompt_tokens=actual_prompt_tokens,
        cached_tokens=actual_cached_tokens,
        completion_tokens=actual_completion_tokens,
        total_tokens=actual_prompt_tokens + actual_cached_tokens + actual_completion_tokens,
        estimated_cost_usd=actual_cost,
        latency_ms=latency_ms,
    )
    record_telemetry_in_meta(meta_file, telemetry)

    # Update meta.yaml stage
    if meta_file.is_file():
        try:
            meta_data: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta_data, dict):
                meta_data["chapter_draft"] = "book/chapter.md"
                if meta_data.get("stage") in ("raw", "research_ready", "draft_in_progress"):
                    meta_data["stage"] = "human_review"
                temp_meta: Path = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True), encoding="utf-8"
                )
                temp_meta.replace(meta_file)
        except Exception:
            pass

    return chapter_file, True
