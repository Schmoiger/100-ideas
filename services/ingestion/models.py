"""Data models for Idea Ingestion and Selection Subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from services.ingestion.state import (
    VALID_STAGES,
    InvalidStateTransitionError,
    validate_transition,
)


@dataclass
class IdeaRecord:
    """Represents a structured idea record across ingestion and publishing pathways."""

    id: str
    title: str
    synopsis: str
    source_reference: str = ""
    tags: list[str] = field(default_factory=list)
    stage: str = "raw"
    human_modified: bool = False
    locked: bool = False
    review_status: str = "pending"
    editorial_quality: dict[str, Any] = field(default_factory=dict)
    assets: dict[str, Any] = field(default_factory=dict)
    token_telemetry: dict[str, Any] = field(default_factory=dict)
    linked_resources: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    model_tiers: dict[str, str] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)
    status: str = "ingested"
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialise default timestamps if absent and normalize status/stage."""
        now_iso: str = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now_iso
        if not self.updated_at:
            self.updated_at = now_iso
        if not self.editorial_quality:
            self.editorial_quality = {
                "voice_fidelity": False,
                "reviewed_by": None,
                "reviewed_at": None,
                "review_notes": "",
            }
        if not self.assets:
            self.assets = {
                "illustration": None,
                "prompt": None,
                "web_cover_url": None,
            }
        if not self.token_telemetry:
            self.token_telemetry = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cached_tokens": 0,
                "latency_ms": 0,
            }
        if self.stage not in VALID_STAGES:
            # Map legacy status
            legacy_map = {
                "ingested": "raw",
                "enriched": "research_ready",
                "drafted": "human_review",
                "typeset": "published",
            }
            self.stage = legacy_map.get(self.status, "raw")

    def touch(self) -> None:
        """Update updated_at timestamp to current UTC time."""
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def transition_to(self, target_stage: str, force: bool = False) -> None:
        """Transition idea to a new lifecycle stage, validating invariants."""
        validate_transition(
            current_stage=self.stage,
            target_stage=target_stage,
            editorial_quality=self.editorial_quality,
            force=force,
        )
        self.stage = target_stage
        self.touch()
        if target_stage == "approved":
            self.review_status = "approved"

    def can_transition_to(self, target_stage: str, force: bool = False) -> bool:
        """Check if transition to target_stage is valid."""
        try:
            validate_transition(
                current_stage=self.stage,
                target_stage=target_stage,
                editorial_quality=self.editorial_quality,
                force=force,
            )
            return True
        except InvalidStateTransitionError:
            return False

    def mark_human_modified(self, modified: bool = True, notes: str = "") -> None:
        """Flag manual author modifications, protecting files from automated overwrites."""
        self.human_modified = modified
        if modified and self.stage in ("draft_in_progress", "raw", "research_ready"):
            self.stage = "human_review"
        if notes:
            self.editorial_quality["review_notes"] = notes
        self.touch()

    def set_editorial_quality(
        self,
        voice_fidelity: bool,
        reviewed_by: str = "",
        review_notes: str = "",
    ) -> None:
        """Record editorial quality review outcomes."""
        now_iso: str = datetime.now(timezone.utc).isoformat()
        self.editorial_quality = {
            "voice_fidelity": voice_fidelity,
            "reviewed_by": reviewed_by,
            "reviewed_at": now_iso,
            "review_notes": review_notes,
        }
        if voice_fidelity:
            self.review_status = "approved"
        else:
            self.review_status = "needs_revision"
        self.touch()

    def to_meta_dict(self) -> dict[str, Any]:
        """Convert record to metadata dictionary suitable for meta.yaml serialization."""
        data: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "synopsis": self.synopsis,
            "source_reference": self.source_reference,
            "tags": list(self.tags),
            "stage": self.stage,
            "human_modified": self.human_modified,
            "locked": self.locked,
            "review_status": self.review_status,
            "editorial_quality": dict(self.editorial_quality),
            "assets": dict(self.assets),
            "token_telemetry": dict(self.token_telemetry),
            "linked_resources": list(self.linked_resources),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "model_tiers": dict(self.model_tiers),
            "token_usage": dict(self.token_usage),
            "status": self.status,
        }
        for k, v in self.extra_fields.items():
            if k not in data:
                data[k] = v
        return data

    @classmethod
    def from_meta_dict(cls, data: dict[str, Any]) -> IdeaRecord:
        """Construct an IdeaRecord from a dictionary."""
        known_keys = {
            "id",
            "title",
            "synopsis",
            "source_reference",
            "tags",
            "stage",
            "human_modified",
            "locked",
            "review_status",
            "editorial_quality",
            "assets",
            "token_telemetry",
            "linked_resources",
            "created_at",
            "updated_at",
            "model_tiers",
            "token_usage",
            "status",
        }
        extra = {k: v for k, v in data.items() if k not in known_keys}

        stage_val = data.get("stage")
        status_val = data.get("status", "ingested")
        if not stage_val:
            legacy_map = {
                "ingested": "raw",
                "enriched": "research_ready",
                "drafted": "human_review",
                "typeset": "published",
            }
            stage_val = legacy_map.get(status_val, "raw")

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            synopsis=data.get("synopsis", ""),
            source_reference=data.get("source_reference", ""),
            tags=list(data.get("tags", [])),
            stage=stage_val,
            human_modified=bool(data.get("human_modified", False)),
            locked=bool(data.get("locked", False)),
            review_status=data.get("review_status", "pending"),
            editorial_quality=dict(data.get("editorial_quality", {})),
            assets=dict(data.get("assets", {})),
            token_telemetry=dict(data.get("token_telemetry", {})),
            linked_resources=list(data.get("linked_resources", [])),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            model_tiers=dict(data.get("model_tiers", {})),
            token_usage=dict(data.get("token_usage", {})),
            status=status_val,
            extra_fields=extra,
        )
