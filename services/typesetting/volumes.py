"""Data models and configuration loader for multi-volume book compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class VolumeChapterRef:
    """Reference to an idea included in a book volume part."""

    idea_id: str
    chapter_title_override: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> VolumeChapterRef:
        """Construct a chapter reference from dict or string identifier."""
        if isinstance(data, str):
            return cls(idea_id=data.strip(), chapter_title_override=None)
        if isinstance(data, dict):
            idea_id = str(data.get("idea_id", "")).strip()
            if not idea_id:
                raise ValueError("Chapter reference missing required 'idea_id'")
            override = data.get("chapter_title_override")
            return cls(
                idea_id=idea_id,
                chapter_title_override=str(override).strip() if override else None,
            )
        raise TypeError(f"Expected dict or str for chapter reference, got {type(data).__name__}")


@dataclass
class VolumePart:
    """Thematic section grouping chapters within a volume."""

    title: str
    description: str = ""
    chapters: list[VolumeChapterRef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VolumePart:
        """Construct a VolumePart from parsed dictionary."""
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError("Volume part missing required 'title'")
        description = str(data.get("description", "")).strip()
        raw_chapters = data.get("chapters", [])
        if not isinstance(raw_chapters, list):
            raise TypeError(f"Part 'chapters' must be a list, got {type(raw_chapters).__name__}")
        chapters = [VolumeChapterRef.from_dict(c) for c in raw_chapters]
        return cls(title=title, description=description, chapters=chapters)


@dataclass
class VolumeConfig:
    """Declarative specification for an individual published volume."""

    id: str
    title: str
    subtitle: str = ""
    author: str = "AS"
    brand: str = "typst/brands/neutral.typ"
    output_pdf: str = ""
    parts: list[VolumePart] = field(default_factory=list)

    def all_chapter_refs(self) -> list[VolumeChapterRef]:
        """Return flattened list of all chapter references in presentation order."""
        refs: list[VolumeChapterRef] = []
        for part in self.parts:
            refs.extend(part.chapters)
        return refs

    def all_idea_ids(self) -> list[str]:
        """Return ordered list of unique idea IDs included in this volume."""
        seen: set[str] = set()
        ids: list[str] = []
        for ref in self.all_chapter_refs():
            if ref.idea_id not in seen:
                seen.add(ref.idea_id)
                ids.append(ref.idea_id)
        return ids

    def total_chapters(self) -> int:
        """Return total number of chapter entries across all parts."""
        return sum(len(part.chapters) for part in self.parts)

    def get_ordered_chapters(self) -> list[tuple[int, VolumePart, VolumeChapterRef]]:
        """Return sequential 1-based indexed chapter sequence across all parts."""
        ordered: list[tuple[int, VolumePart, VolumeChapterRef]] = []
        seq = 1
        for part in self.parts:
            for chapter_ref in part.chapters:
                ordered.append((seq, part, chapter_ref))
                seq += 1
        return ordered

    @classmethod
    def from_dict(cls, volume_id: str, data: dict[str, Any]) -> VolumeConfig:
        """Construct a VolumeConfig from parsed dictionary."""
        clean_id = str(volume_id).strip()
        if not clean_id:
            raise ValueError("Volume identifier cannot be empty")
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError(f"Volume '{clean_id}' missing required 'title'")
        subtitle = str(data.get("subtitle", "")).strip()
        author = str(data.get("author", "AS")).strip()
        brand = str(data.get("brand", "typst/brands/neutral.typ")).strip()
        output_pdf = str(data.get("output_pdf", f"artefacts/content/book/{clean_id}.pdf")).strip()

        raw_parts = data.get("parts", [])
        if not isinstance(raw_parts, list):
            raise TypeError(
                f"Volume '{clean_id}' parts must be a list, got {type(raw_parts).__name__}"
            )
        parts = [VolumePart.from_dict(p) for p in raw_parts]

        return cls(
            id=clean_id,
            title=title,
            subtitle=subtitle,
            author=author,
            brand=brand,
            output_pdf=output_pdf,
            parts=parts,
        )


@dataclass
class VolumesManifest:
    """Top-level multi-volume configuration manifest."""

    version: str
    volumes: dict[str, VolumeConfig] = field(default_factory=dict)


def load_volumes_config(config_path: Path) -> dict[str, VolumeConfig]:
    """Load and validate declarative volumes configuration from YAML.

    Raises:
        FileNotFoundError: If configuration file does not exist.
        ValueError: If configuration schema or structure is invalid.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"Volumes configuration file not found: {config_path}")

    try:
        raw_text = config_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(raw_text)
    except Exception as exc:
        raise ValueError(f"Malformed YAML in volumes configuration {config_path}: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Volumes configuration must be a mapping, got {type(parsed).__name__}")

    raw_volumes = parsed.get("volumes")
    if not isinstance(raw_volumes, dict):
        raise ValueError(
            f"Volumes configuration must contain a 'volumes' mapping, got {type(raw_volumes).__name__}"
        )

    volumes: dict[str, VolumeConfig] = {}
    for vol_id, vol_data in raw_volumes.items():
        if not isinstance(vol_data, dict):
            raise ValueError(
                f"Configuration for volume '{vol_id}' must be a mapping, got {type(vol_data).__name__}"
            )
        volumes[vol_id] = VolumeConfig.from_dict(vol_id, vol_data)

    return volumes


def get_default_volumes_path(repo_root: Path | None = None) -> Path:
    """Resolve default config/volumes.yaml path."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "config" / "volumes.yaml"
