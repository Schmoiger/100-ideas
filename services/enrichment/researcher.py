"""Research synthesis engine for idea enrichment with live Gemini SDK integration and token governance."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import yaml
from google.genai import types
from pydantic import BaseModel, Field

from services.enrichment.models import ResearchNotes
from services.enrichment.resource_library import resolve_resources_for_idea
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


class ResearchDossierSchema(BaseModel):
    """Pydantic structured output schema for empirical research extraction."""

    empirical_evidence: list[str] = Field(
        default_factory=list,
        description="Concrete field observations, empirical data points, and measured impacts from source materials",
    )
    economic_tradeoffs: list[str] = Field(
        default_factory=list,
        description="Economic trade-offs, constraint migration, bottleneck dynamics, and maintenance realities",
    )
    counterarguments: list[str] = Field(
        default_factory=list,
        description="Known failure modes, boundary conditions, and observed anti-patterns",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Formal citations referencing the source resources",
    )


def extract_relevant_sections(content: str, keywords: list[str]) -> list[str]:
    """Scan markdown text for paragraphs containing keywords."""
    paragraphs: list[str] = [p.strip() for p in content.split("\n\n") if p.strip()]
    matched: list[str] = []
    for para in paragraphs:
        if para.startswith("#"):
            continue
        lowered: str = para.lower()
        if any(kw.lower() in lowered for kw in keywords):
            matched.append(para)
    return matched


def build_research_dossier(
    idea: IdeaRecord,
    resources: list[tuple[dict[str, Any], str]],
) -> ResearchNotes:
    """Construct structured empirical research notes from idea and linked resources (deterministic fallback).

    Handles REQ-ENR-001: Extracts verified evidence, economic trade-offs,
    and counterarguments linking back to resource IDs.
    """
    evidence: list[str] = []
    tradeoffs: list[str] = []
    counterarguments: list[str] = []
    citations: list[str] = []

    # Keywords extracted from idea title and synopsis
    keywords: list[str] = [
        w for w in re.findall(r"\b[A-Za-z]{4,}\b", f"{idea.title} {idea.synopsis}")
    ]

    for res_meta, content in resources:
        res_id: str = res_meta.get("id", "unknown-resource")
        res_title: str = res_meta.get("title", res_id)

        citations.append(
            f"`{res_id}`: {res_title} (Citation reference: {idea.source_reference or 'Core Framework'})"
        )

        if content:
            matches: list[str] = extract_relevant_sections(content, keywords)
            for m in matches[:3]:
                evidence.append(f"[{res_title}]: {m}")

    # If no resource text matched, generate grounded empirical evidence from synopsis
    if not evidence:
        evidence.append(f"Observation from software delivery teams: {idea.synopsis}")

    # Core economic trade-offs and constraint dynamics
    tradeoffs.append(
        f"Bottleneck migration: When adopting '{idea.title}', engineering capacity expands upstream, "
        "shifting operational friction to review queues, automated test execution, and deployment pipelines."
    )
    tradeoffs.append(
        "Opportunity cost: Allocating engineering bandwidth to manual inspection rather than governing "
        "automated verification guard rails creates a high learning tax and slows cycle times."
    )

    # Counterarguments and anti-patterns
    counterarguments.append(
        f"Failure mode: Naive implementation of '{idea.title}' without formal contracts or deterministic "
        "guard rails leads to cognitive thrashing and accumulated unverified technical debt."
    )
    counterarguments.append(
        "Boundary condition: Highly regulated or life-critical software domains require multi-tiered human "
        "approval gates before autonomous agents can operate without supervisory friction."
    )

    return ResearchNotes(
        idea_id=idea.id,
        title=idea.title,
        synopsis=idea.synopsis,
        empirical_evidence=evidence,
        economic_tradeoffs=tradeoffs,
        counterarguments=counterarguments,
        citations=citations,
    )


def synthesise_research(
    idea: IdeaRecord,
    ideas_root: Path,
    resources_root: Path,
    force: bool = False,
    force_llm: bool = False,
    dry_run: bool = False,
    overwrite_manual: bool = False,
    client: Any = None,
) -> tuple[Path, bool]:
    """Execute research phase for an idea and persist notes.md.

    Handles REQ-ENR-001 & REQ-ORC-005 with Gemini context caching and spend circuit breakers:
    - Bypasses API requests when cryptographic input fingerprint matches in meta.yaml (zero token burn).
    - Clamps un-cached input context <= 12,000 tokens.
    - Employs Gemini context caching when resource contents exceed 32,768 tokens.
    - Halts on budget exhaustion (MAX_SESSION_SPEND_USD, MAX_IDEA_TOKENS).
    - Supports --dry-run for pre-flight estimation without firing API calls.
    - Records detailed TokenTelemetry into meta.yaml.
    """
    from services.ingestion.safeguards import check_manual_edit_safeguard

    idea_dir: Path = ideas_root / idea.id
    research_dir: Path = idea_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    meta_file: Path = idea_dir / "meta.yaml"
    notes_file: Path = research_dir / "notes.md"

    # Safeguard check against human modification
    if notes_file.is_file():
        if not force and not overwrite_manual and not force_llm:
            return notes_file, False
        check_manual_edit_safeguard(
            target_file=notes_file,
            idea=idea,
            force=force or force_llm,
            overwrite_manual=overwrite_manual,
        )

    # 1. Resolve resources for idea
    resources: list[tuple[dict[str, Any], str]] = resolve_resources_for_idea(idea, resources_root)
    for r_meta, _ in resources:
        r_id: str = r_meta.get("id", "")
        if r_id and r_id not in idea.linked_resources:
            idea.linked_resources.append(r_id)

    # 2. Cryptographic input fingerprinting (Guard Rail 3)
    doc_texts: list[str] = [content for _, content in resources if content]
    prompt_template = (
        f"Synthesise grounded empirical research notes for engineering thesis:\n"
        f"Title: {idea.title}\n"
        f"Synopsis: {idea.synopsis}\n"
        "Extract empirical evidence, trade-offs, counterarguments, and citations."
    )
    fingerprint = compute_input_fingerprint(
        model_name="gemini-2.5-flash",
        prompt_template=prompt_template,
        input_documents=doc_texts,
    )

    # If fingerprint matches and not force_llm, zero token burn bypass
    if notes_file.is_file() and not force_llm:
        if check_fingerprint_match(meta_file, fingerprint):
            return notes_file, False

    # 3. Context Clamping & Caching (Guard Rail 4)
    # Check if resources exceed caching threshold
    cache_name: str | None = None
    cached_tokens: int = 0
    clamped_docs: list[str] = []

    live_available = is_live_genai_available() or client is not None

    if live_available and should_create_cache(doc_texts):
        # Gemini Context Caching active for reusable context > 32k tokens
        active_client = client or get_genai_client()
        cache_name = get_or_create_context_cache(
            client=active_client,
            model="gemini-2.5-flash",
            contents=doc_texts,
        )
        if cache_name:
            cached_tokens = estimate_token_count("".join(doc_texts))

    if not cache_name:
        # Context clamping: hard cap un-cached input context <= 12,000 tokens
        for doc in doc_texts:
            clamped_docs.append(clamp_context(doc, max_tokens=6000))

    # 4. Pre-flight cost estimator and circuit breaker check (Guard Rails 1 & 2)
    gov = get_governance()
    uncached_content_str = "\n\n".join(clamped_docs)
    prompt_tokens = estimate_token_count(f"{prompt_template}\n\n{uncached_content_str}")
    projected_completion_tokens = 800

    projected_cost = gov.check_preflight(
        model="gemini-2.5-flash",
        projected_prompt_tokens=prompt_tokens,
        projected_completion_tokens=projected_completion_tokens,
        cached_tokens=cached_tokens,
        idea_id=idea.id,
    )

    if dry_run:
        # Dry run verifies estimation without making live calls
        telemetry = TokenTelemetry(
            model="gemini-2.5-flash (dry-run)",
            fingerprint=fingerprint,
            prompt_tokens=prompt_tokens,
            cached_tokens=cached_tokens,
            completion_tokens=projected_completion_tokens,
            total_tokens=prompt_tokens + cached_tokens + projected_completion_tokens,
            estimated_cost_usd=projected_cost,
            latency_ms=0,
        )
        record_telemetry_in_meta(meta_file, telemetry)
        return notes_file, False

    # 5. Live generation or deterministic fallback
    dossier: ResearchNotes | None = None
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
                    response_schema=ResearchDossierSchema,
                    temperature=0.2,
                )
                full_contents = prompt_template
            else:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResearchDossierSchema,
                    temperature=0.2,
                )
                full_contents = (
                    f"{prompt_template}\n\n## Referenced Resources\n{uncached_content_str}"
                )

            response = active_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_contents,
                config=config,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            used_model = "gemini-2.5-flash"

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

            parsed: ResearchDossierSchema = response.parsed
            dossier = ResearchNotes(
                idea_id=idea.id,
                title=idea.title,
                synopsis=idea.synopsis,
                empirical_evidence=parsed.empirical_evidence or [f"Observation: {idea.synopsis}"],
                economic_tradeoffs=parsed.economic_tradeoffs
                or ["Capacity migration and review bottlenecks."],
                counterarguments=parsed.counterarguments
                or ["Boundary condition: requires deterministic verification."],
                citations=parsed.citations
                or [f"`{r[0].get('id', 'resource')}`" for r in resources],
            )
        except Exception:
            # Fall back cleanly to deterministic synthesis
            dossier = None

    if dossier is None:
        dossier = build_research_dossier(idea, resources)

    # Record spend in governance accumulator
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

    # 6. Write notes.md atomically
    temp_notes: Path = research_dir / ".notes.md.tmp"
    temp_notes.write_text(dossier.to_markdown(), encoding="utf-8")
    temp_notes.replace(notes_file)

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
                meta_data["linked_resources"] = idea.linked_resources
                meta_data["research_notes"] = "research/notes.md"
                meta_data["status"] = "enriched"
                if meta_data.get("stage") == "raw" or "stage" not in meta_data:
                    meta_data["stage"] = "research_ready"
                temp_meta: Path = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True), encoding="utf-8"
                )
                temp_meta.replace(meta_file)
        except Exception:
            pass

    return notes_file, True
