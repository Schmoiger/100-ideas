"""Unit tests for Editorial Quality Gate and Voice Fidelity Validator."""

from __future__ import annotations

from pathlib import Path

import yaml

from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.publishing.quality_gate import (
    evaluate_idea_quality_gate,
    validate_voice_fidelity,
)

SAMPLE_PASSING_MANUSCRIPT = """# Chapter 1: Decoupling Syntax from Intent

*Chapter 1 · 100 Ideas for Engineering Leaders*

---

## The Unvarnished Reality

Software engineering has spent decades mistaking typing speed for delivery capacity.
When delivery throughput is bottlenecked by manual developer bandwidth,
every initiative crawls under cognitive load.

---

## Where the Gears Bind

Every engineering organisation eventually accumulates digital rust.
Abstract architectures look pristine, but teams spend sixty percent of their time
sweating decaying assets and untangling dependencies.

---

## The Economic Equation & Trade-offs

What does this actually cost us in delivery velocity, cognitive load, and cash?
Silicon Valley marketing promises effortless acceleration, but the real equation
is about the maintenance tail. Who gets paged at 2 a.m. when an unverified divergence slips past?

| Operational Dimension | Conventional SDLC | Decoupled Model |
|---|---|---|
| **Binding Constraint** | Developer syntax bandwidth | Automated verification fidelity |
| **Failure Blast Radius** | Missed sprint commitments | Rapid divergence |

---

## Puncturing the Hype

Autonomous agents will not magically fix an enterprise organisation that cannot define boundaries.
If your domain model is a swamp of ambiguous terminology, accelerating code simply delivers a faster catastrophe.

---

## Actionable Takeaways

- **Map the binding constraint first**: Identify whether syntax production or validation latency throttles delivery.
- **Sweat architectural contracts**: Spend leadership bandwidth refining specifications rather than micromanaging PRs.
- **Budget for the maintenance tail**: Ensure operational telemetry scales alongside automated code generation.
"""

SAMPLE_FAILING_MANUSCRIPT = """# Chapter 1: AI Disruption

*Welcome to the future*

In this chapter, we will explore how AI revolutionizes development.
It is a testament to modern engineering that we can delve into code.
Furthermore, this seamless tool will optimize your workflow.

---

## Takeaways

- Just write more tests.
- Buy faster servers.
"""


def test_validate_voice_fidelity_passes_compliant_text() -> None:
    """Verify compliant text with British English and economic lens passes."""
    report = validate_voice_fidelity(SAMPLE_PASSING_MANUSCRIPT)
    assert report.passed is True
    assert report.voice_fidelity is True
    assert report.score == 1.0
    assert len(report.issues) == 0


def test_validate_voice_fidelity_catches_slop_and_americanisms() -> None:
    """Verify non-compliant text triggers specific actionable issues."""
    report = validate_voice_fidelity(SAMPLE_FAILING_MANUSCRIPT)
    assert report.passed is False
    assert report.voice_fidelity is False

    issues_str = " ".join(report.issues)
    # Catches preamble
    assert "preamble" in issues_str.lower()
    # Catches Americanism optimize
    assert "optimise" in issues_str.lower()
    # Catches AI slop delve, testament to, revolutionise/revolutionize
    assert "delve" in issues_str.lower()
    # Catches bold lead-ins
    assert "bold" in issues_str.lower()
    # Catches economic lens
    assert "economic" in issues_str.lower()


def test_evaluate_idea_quality_gate_promotes_stage(tmp_path: Path) -> None:
    """Verify quality gate promotes idea from human_review to approved on pass."""
    idea = IdeaRecord(
        id="idea-001",
        title="Decoupling Syntax",
        synopsis="Testing quality gate approval.",
        stage="human_review",
    )
    p_dir = provision_idea(idea, tmp_path)
    chapter_file = p_dir / "book" / "chapter.md"
    chapter_file.write_text(SAMPLE_PASSING_MANUSCRIPT, encoding="utf-8")

    report = evaluate_idea_quality_gate(p_dir, reviewer="Avi")
    assert report.passed is True

    # Check updated meta.yaml
    meta_file = p_dir / "meta.yaml"
    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["stage"] == "approved"
    assert meta["review_status"] == "approved"
    assert meta["editorial_quality"]["voice_fidelity"] is True
    assert meta["editorial_quality"]["reviewed_by"] == "Avi"


def test_evaluate_idea_quality_gate_rejects_and_marks_needs_revision(tmp_path: Path) -> None:
    """Verify quality gate sets needs_revision and does not approve failing draft."""
    idea = IdeaRecord(
        id="idea-002",
        title="Bad Draft",
        synopsis="Testing quality gate rejection.",
        stage="human_review",
    )
    p_dir = provision_idea(idea, tmp_path)
    chapter_file = p_dir / "book" / "chapter.md"
    chapter_file.write_text(SAMPLE_FAILING_MANUSCRIPT, encoding="utf-8")

    report = evaluate_idea_quality_gate(p_dir, reviewer="TechEditor")
    assert report.passed is False

    meta_file = p_dir / "meta.yaml"
    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["stage"] == "human_review"  # Not promoted
    assert meta["review_status"] == "needs_revision"
    assert meta["editorial_quality"]["voice_fidelity"] is False
    assert len(meta["editorial_quality"]["review_notes"]) > 0
