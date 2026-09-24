"""Intermediate folder and meta.yaml provisioning engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord


def provision_idea(
    idea: IdeaRecord,
    content_ideas_dir: Path,
    force: bool = False,
) -> Path:
    """Provision directory structure and meta.yaml for an idea.

    Handles REQ-ING-005, REQ-DRY-001, REQ-DRY-002:
    Creates artefacts/content/ideas/{idea-id}/ with research/, assets/, book/,
    blog/ and persists valid atomic meta.yaml.
    """
    idea_dir: Path = content_ideas_dir / idea.id
    idea_dir.mkdir(parents=True, exist_ok=True)

    # Provision standard subdirectories
    for subdir_name in ("research", "assets", "book", "blog"):
        (idea_dir / subdir_name).mkdir(exist_ok=True)

    meta_file: Path = idea_dir / "meta.yaml"
    if meta_file.is_file() and not force:
        # If already provisioned and not forcing, keep existing content but update timestamps
        try:
            existing_data: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(existing_data, dict):
                idea.linked_resources = list(existing_data.get("linked_resources", []))
                idea.status = existing_data.get("status", idea.status)
                idea.created_at = existing_data.get("created_at", idea.created_at)
        except Exception:
            pass

    meta_dict: dict[str, Any] = idea.to_meta_dict()
    temp_meta: Path = idea_dir / ".meta.yaml.tmp"
    temp_meta.write_text(
        yaml.safe_dump(meta_dict, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    temp_meta.replace(meta_file)

    return idea_dir


def load_existing_provisioned_ideas(content_ideas_dir: Path) -> list[IdeaRecord]:
    """Scan ideas directory and load all provisioned meta.yaml records."""
    if not content_ideas_dir.is_dir():
        return []

    records: list[IdeaRecord] = []
    for idea_subdir in sorted(content_ideas_dir.iterdir()):
        if not idea_subdir.is_dir():
            continue
        meta_path: Path = idea_subdir / "meta.yaml"
        if meta_path.is_file():
            try:
                data: Any = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    records.append(IdeaRecord.from_meta_dict(data))
            except Exception:
                continue

    return records
