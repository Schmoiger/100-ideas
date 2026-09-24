"""Interface to centralised M:N Shared Resource Library."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord


def load_resource_manifest(resources_dir: Path) -> list[dict[str, Any]]:
    """Load resource manifest from artefacts/content/resources/manifest.yaml."""
    manifest_path: Path = resources_dir / "manifest.yaml"
    if not manifest_path.is_file():
        return []

    try:
        data: Any = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "resources" in data and isinstance(data["resources"], list):
            return [r for r in data["resources"] if isinstance(r, dict)]
    except Exception:
        pass
    return []


def resolve_resources_for_idea(
    idea: IdeaRecord,
    resources_dir: Path,
) -> list[tuple[dict[str, Any], str]]:
    """Match an idea to linked or relevant resources and return (resource_meta, content) pairs.

    Matches by:
    1. Explicit idea.linked_resources IDs.
    2. Mentions in idea.source_reference (e.g. 'New DevX Vision').
    3. Tag overlap with resource tags.
    """
    manifest: list[dict[str, Any]] = load_resource_manifest(resources_dir)
    matched: list[tuple[dict[str, Any], str]] = []

    for res in manifest:
        res_id: str = res.get("id", "")
        res_title: str = res.get("title", "")
        res_file: str = res.get("file", "")
        res_tags: list[str] = [t.lower() for t in res.get("tags", [])]

        is_match: bool = False

        # 1. Explicit link
        if res_id in idea.linked_resources:
            is_match = True

        # 2. Source reference match
        ref_lower: str = idea.source_reference.lower()
        if res_title.lower() in ref_lower or res_id.lower() in ref_lower:
            is_match = True

        # 3. Tag overlap
        idea_tags_lower: list[str] = [t.lower() for t in idea.tags]
        if any(t in res_tags for t in idea_tags_lower):
            is_match = True

        # Default fallback: if idea cites "New DevX Vision" or reference is from vision
        if not is_match and "vision" in ref_lower and res_id == "new-devx-vision":
            is_match = True

        if is_match:
            content_path: Path = resources_dir / res_file
            content: str = ""
            if content_path.is_file():
                content = content_path.read_text(encoding="utf-8")
            matched.append((res, content))

    return matched
