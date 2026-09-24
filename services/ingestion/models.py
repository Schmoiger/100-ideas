"""Data models for Idea Ingestion and Selection Subsystem."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IdeaRecord:
    """Represents a structured idea record across ingestion pathways."""

    id: str
    title: str
    synopsis: str
    source_reference: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "ingested"
    linked_resources: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    model_tiers: dict[str, str] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialise default timestamps if absent."""
        now_iso: str = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now_iso
        if not self.updated_at:
            self.updated_at = now_iso

    def to_meta_dict(self) -> dict[str, Any]:
        """Convert record to metadata dictionary suitable for meta.yaml serialization."""
        return asdict(self)

    @classmethod
    def from_meta_dict(cls, data: dict[str, Any]) -> IdeaRecord:
        """Construct an IdeaRecord from a dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            synopsis=data.get("synopsis", ""),
            source_reference=data.get("source_reference", ""),
            tags=list(data.get("tags", [])),
            status=data.get("status", "ingested"),
            linked_resources=list(data.get("linked_resources", [])),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            model_tiers=dict(data.get("model_tiers", {})),
            token_usage=dict(data.get("token_usage", {})),
        )
