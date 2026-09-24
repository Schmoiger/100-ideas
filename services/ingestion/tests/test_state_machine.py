"""Tests for IdeaRecord state machine, transitions, and meta.yaml safeguards."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea, update_idea_meta
from services.ingestion.state import (
    InvalidStateTransitionError,
)


def test_default_stage_and_safeguard_fields() -> None:
    """Verify newly initialized IdeaRecord starts at 'raw' stage with safeguards enabled."""
    idea = IdeaRecord(
        id="idea-099",
        title="Decoupled Architecture",
        synopsis="Testing state machine defaults.",
    )
    assert idea.stage == "raw"
    assert idea.human_modified is False
    assert idea.locked is False
    assert idea.review_status == "pending"
    assert idea.editorial_quality["voice_fidelity"] is False
    assert idea.editorial_quality["reviewed_by"] is None
    assert idea.assets["illustration"] is None
    assert idea.token_telemetry["prompt_tokens"] == 0


def test_state_machine_valid_transitions() -> None:
    """Verify valid transitions across idea lifecycle stages."""
    idea = IdeaRecord(
        id="idea-100",
        title="Lifecycle Progression",
        synopsis="Verifying sequential stage transitions.",
    )
    # raw -> research_ready
    assert idea.can_transition_to("research_ready")
    idea.transition_to("research_ready")
    assert idea.stage == "research_ready"

    # research_ready -> draft_in_progress
    assert idea.can_transition_to("draft_in_progress")
    idea.transition_to("draft_in_progress")
    assert idea.stage == "draft_in_progress"

    # draft_in_progress -> human_review
    assert idea.can_transition_to("human_review")
    idea.transition_to("human_review")
    assert idea.stage == "human_review"

    # human_review -> approved requires editorial quality voice_fidelity
    assert not idea.can_transition_to("approved")
    with pytest.raises(InvalidStateTransitionError):
        idea.transition_to("approved")

    # Set editorial quality pass
    idea.set_editorial_quality(
        voice_fidelity=True,
        reviewed_by="Avi",
        review_notes="Meets British English and voice standards.",
    )
    assert idea.can_transition_to("approved")
    idea.transition_to("approved")
    assert idea.stage == "approved"
    assert idea.review_status == "approved"

    # approved -> published
    assert idea.can_transition_to("published")
    idea.transition_to("published")
    assert idea.stage == "published"


def test_state_machine_invalid_transitions() -> None:
    """Verify illegal transitions are rejected."""
    idea = IdeaRecord(
        id="idea-101",
        title="Illegal Transitions",
        synopsis="Verifying invalid jumps are blocked.",
    )
    # raw cannot jump directly to approved or published
    with pytest.raises(InvalidStateTransitionError):
        idea.transition_to("approved")
    with pytest.raises(InvalidStateTransitionError):
        idea.transition_to("published")


def test_mark_human_modified_promotes_stage() -> None:
    """Verify marking human_modified flags draft and promotes to human_review."""
    idea = IdeaRecord(
        id="idea-102",
        title="Human Polish",
        synopsis="Verifying human modification tracking.",
        stage="draft_in_progress",
    )
    idea.mark_human_modified(True, notes="Author polished Section 3.")
    assert idea.human_modified is True
    assert idea.stage == "human_review"
    assert idea.editorial_quality["review_notes"] == "Author polished Section 3."


def test_meta_yaml_round_trip_preserves_safeguards(tmp_path: Path) -> None:
    """Verify meta.yaml serialization and deserialization preserves all state machine fields."""
    idea = IdeaRecord(
        id="idea-103",
        title="Round Trip Test",
        synopsis="Checking YAML serialization fidelity.",
        stage="human_review",
        human_modified=True,
        locked=False,
        review_status="needs_revision",
        editorial_quality={
            "voice_fidelity": False,
            "reviewed_by": "Senior Editor",
            "reviewed_at": "2026-09-24T18:00:00Z",
            "review_notes": "Reduce passive voice in opening.",
        },
        assets={
            "illustration": "assets/illustration.png",
            "prompt": "assets/prompt.txt",
            "web_cover_url": "https://example.com/cover.png",
        },
        token_telemetry={
            "prompt_tokens": 1200,
            "completion_tokens": 450,
            "cached_tokens": 8000,
            "latency_ms": 120,
        },
    )

    provision_idea(idea, tmp_path)
    meta_path = tmp_path / "idea-103" / "meta.yaml"
    assert meta_path.is_file()

    # Load back
    loaded_data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    loaded_idea = IdeaRecord.from_meta_dict(loaded_data)

    assert loaded_idea.id == "idea-103"
    assert loaded_idea.stage == "human_review"
    assert loaded_idea.human_modified is True
    assert loaded_idea.locked is False
    assert loaded_idea.review_status == "needs_revision"
    assert loaded_idea.editorial_quality["reviewed_by"] == "Senior Editor"
    assert loaded_idea.assets["web_cover_url"] == "https://example.com/cover.png"
    assert loaded_idea.token_telemetry["cached_tokens"] == 8000


def test_atomic_update_meta(tmp_path: Path) -> None:
    """Verify update_idea_meta performs atomic in-place key updates."""
    idea = IdeaRecord(
        id="idea-104",
        title="Atomic Updates",
        synopsis="Testing atomic update helper.",
    )
    p_dir = provision_idea(idea, tmp_path)
    updated = update_idea_meta(p_dir, {"stage": "research_ready", "custom_key": 42})
    assert updated["stage"] == "research_ready"
    assert updated["custom_key"] == 42

    meta_file = p_dir / "meta.yaml"
    disk_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert disk_data["stage"] == "research_ready"
    assert disk_data["custom_key"] == 42
    assert disk_data["title"] == "Atomic Updates"
