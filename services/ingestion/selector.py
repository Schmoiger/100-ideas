"""Idea selection and domain/tag filtering utilities."""

from __future__ import annotations

import re
from typing import Sequence

from services.ingestion.models import IdeaRecord


def parse_range(range_spec: str) -> tuple[int, int]:
    """Parse range specification such as '1-5' or 'idea-001-idea-005' into 1-based bounds."""
    # Match numeric range: "1-5" or "1..5"
    num_match = re.match(r"^(\d+)\s*(?:-|\.\.)\s*(\d+)$", range_spec.strip())
    if num_match:
        start: int = int(num_match.group(1))
        end: int = int(num_match.group(2))
        return (min(start, end), max(start, end))

    # Match idea-id range: "idea-001-idea-005"
    id_match = re.match(r"^idea-(\d+)\s*-\s*idea-(\d+)$", range_spec.strip(), re.IGNORECASE)
    if id_match:
        start_id: int = int(id_match.group(1))
        end_id: int = int(id_match.group(2))
        return (min(start_id, end_id), max(start_id, end_id))

    raise ValueError(
        f"Invalid range specification: '{range_spec}'. Expected format '1-5' or 'idea-001-idea-005'."
    )


def select_ideas(
    ideas: Sequence[IdeaRecord],
    idea_spec: str | int | None = None,
    range_spec: str | None = None,
    all_flag: bool = False,
    tag: str | None = None,
    domain: str | None = None,
    query: str | None = None,
) -> list[IdeaRecord]:
    """Filter and select ideas by index, range, batch flag, or taxonomy.

    Handles REQ-ING-002: Single index (--idea 1), index range (--ideas 1-5), batch (--all).
    Handles REQ-ING-007: Tag, thematic keyword, or domain filtering.
    """
    filtered: list[IdeaRecord] = list(ideas)

    # 1. Scope selection: single idea or range or all
    if idea_spec is not None:
        target: str = str(idea_spec).strip()
        matched: list[IdeaRecord] = []
        if target.isdigit():
            idx: int = int(target)
            if 1 <= idx <= len(filtered):
                matched = [filtered[idx - 1]]
        else:
            # Check exact ID match or case-insensitive match
            for rec in filtered:
                if rec.id.lower() == target.lower():
                    matched = [rec]
                    break
            if not matched:
                # Fall back to title substring match
                matched = [r for r in filtered if target.lower() in r.title.lower()]
        filtered = matched

    elif range_spec is not None:
        start_bound, end_bound = parse_range(range_spec)
        bounded: list[IdeaRecord] = []
        for idx, rec in enumerate(filtered, start=1):
            if start_bound <= idx <= end_bound:
                bounded.append(rec)
        filtered = bounded

    elif not all_flag and not tag and not domain and not query:
        # Default when no selection criteria provided
        return []

    # 2. Tag and Domain filtering (REQ-ING-007)
    if tag:
        tag_lower: str = tag.strip().lower()
        filtered = [
            r
            for r in filtered
            if any(tag_lower in t.lower() for t in r.tags)
            or tag_lower in r.title.lower()
            or tag_lower in r.synopsis.lower()
        ]

    if domain:
        domain_lower: str = domain.strip().lower()
        filtered = [
            r
            for r in filtered
            if any(domain_lower in t.lower() for t in r.tags)
            or domain_lower in r.title.lower()
            or domain_lower in r.synopsis.lower()
        ]

    if query:
        q_lower: str = query.strip().lower()
        filtered = [
            r for r in filtered if q_lower in r.title.lower() or q_lower in r.synopsis.lower()
        ]

    return filtered
