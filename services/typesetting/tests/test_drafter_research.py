"""Tests verifying chapter drafting consumes research notes and citations."""

from __future__ import annotations

from services.ingestion.models import IdeaRecord
from services.typesetting.drafter import build_chapter_draft, parse_research_notes_sections


def test_parse_research_notes_sections() -> None:
    """Verify parsing extracts sections correctly from research dossier markdown."""
    markdown = """# Research Dossier: Test Idea

**Idea ID**: `idea-001`

---

## Empirical Evidence & Real-World Observations

- Field study across 40 enterprises showed 65% delivery drag.
- Context switching incurred 23 minutes per interruption.

---

## Economic Trade-offs & Constraint Dynamics

- Upfront specification investment increases by 30%.
- Long-term maintenance tail decreases by 80%.

---

## Counterarguments, Tensions & Anti-Patterns

- Premature automation before interface stabilization.

---

## Citations & Verified Resource Links

- New DevX Vision (Volume 1, Section 3, Line 45)
- DORA State of DevOps Report 2024
"""
    sections = parse_research_notes_sections(markdown)
    assert len(sections["empirical_evidence"]) == 2
    assert "65% delivery drag" in sections["empirical_evidence"][0]
    assert len(sections["economic_tradeoffs"]) == 2
    assert "30%" in sections["economic_tradeoffs"][0]
    assert len(sections["counterarguments"]) == 1
    assert "Premature automation" in sections["counterarguments"][0]
    assert len(sections["citations"]) == 2
    assert "New DevX Vision" in sections["citations"][0]


def test_build_chapter_draft_consumes_research_notes() -> None:
    """Verify build_chapter_draft interpolates research notes into the manuscript (DEF-003)."""
    idea = IdeaRecord(
        id="idea-001",
        title="Decouple Architecture",
        synopsis="Testing research consumption.",
    )
    research_markdown = """
## Empirical Evidence & Real-World Observations
- Enterprise teams spend 60% of time in manual coordination.

## Economic Trade-offs & Constraint Dynamics
- High initial governance costs offset by quadratic velocity gains.

## Counterarguments, Tensions & Anti-Patterns
- Unchecked divergence when feedback loops exceed 24 hours.

## Citations & Verified Resource Links
- Architecture Manifesto 2026, p. 112
"""
    draft = build_chapter_draft(
        idea=idea,
        research_content=research_markdown,
        metaphor="Interlocking mechanical governors",
        chapter_num=1,
    )

    # Check mechanics section includes empirical evidence
    assert "Empirical Grounding & Field Observations" in draft.mechanics_section
    assert "60% of time in manual coordination" in draft.mechanics_section

    # Check economic section includes trade-offs
    assert "Constraint Dynamics & Real-World Trade-offs" in draft.economic_section
    assert "quadratic velocity gains" in draft.economic_section

    # Check hype section includes counterarguments
    assert "Counterarguments & Observed Anti-Patterns" in draft.hype_section
    assert "Unchecked divergence" in draft.hype_section

    # Check citations populated
    assert len(draft.citations) == 1
    assert "Architecture Manifesto 2026" in draft.citations[0]

    # Check markdown rendering
    md = draft.to_markdown()
    assert "## Grounded Citations & Field References" in md
    assert "Architecture Manifesto 2026, p. 112" in md


def test_build_chapter_draft_empty_research() -> None:
    """Verify build_chapter_draft works gracefully without research notes."""
    idea = IdeaRecord(
        id="idea-002",
        title="Zero Research Baseline",
        synopsis="Baseline test.",
    )
    draft = build_chapter_draft(
        idea=idea,
        research_content="",
        metaphor="",
        chapter_num=2,
    )
    assert "Empirical Grounding & Field Observations" not in draft.mechanics_section
    assert draft.citations == []
    md = draft.to_markdown()
    assert "## Grounded Citations & Field References" not in md
