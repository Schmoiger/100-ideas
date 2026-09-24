"""Deduplication and semantic similarity checking for idea intake."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Sequence

from services.ingestion.models import IdeaRecord


def normalize_string(text: str) -> str:
    """Normalize string for fuzzy comparison by removing punctuation and extra spacing."""
    lowered: str = text.lower()
    cleaned: str = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(cleaned.split())


def token_similarity(str1: str, str2: str) -> float:
    """Calculate token-level Jaccard similarity between two strings."""
    tokens1: set[str] = set(normalize_string(str1).split())
    tokens2: set[str] = set(normalize_string(str2).split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection: set[str] = tokens1.intersection(tokens2)
    union: set[str] = tokens1.union(tokens2)
    return len(intersection) / len(union)


def string_similarity(str1: str, str2: str) -> float:
    """Calculate character-sequence similarity between two strings."""
    norm1: str = normalize_string(str1)
    norm2: str = normalize_string(str2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def check_duplicate(
    candidate: IdeaRecord,
    existing_records: Sequence[IdeaRecord],
    threshold: float = 0.75,
) -> tuple[bool, IdeaRecord | None, str]:
    """Check if an incoming candidate idea duplicates an existing record.

    Handles REQ-ING-006: Checks title and synopsis similarity against existing
    records before provisioning.
    """
    candidate_norm_title: str = normalize_string(candidate.title)
    candidate_norm_synopsis: str = normalize_string(candidate.synopsis)

    for record in existing_records:
        if record.id == candidate.id:
            continue

        existing_norm_title: str = normalize_string(record.title)

        # Exact normalized title match
        if candidate_norm_title == existing_norm_title:
            return (
                True,
                record,
                f"Identical title matches existing {record.id}: '{record.title}'",
            )

        # High title similarity
        title_sim: float = max(
            string_similarity(candidate.title, record.title),
            token_similarity(candidate.title, record.title),
        )
        if title_sim >= threshold:
            return (
                True,
                record,
                f"High title similarity ({title_sim:.2f}) with {record.id}: '{record.title}'",
            )

        # High synopsis similarity
        if candidate_norm_synopsis and record.synopsis:
            syn_sim: float = max(
                string_similarity(candidate.synopsis, record.synopsis),
                token_similarity(candidate.synopsis, record.synopsis),
            )
            if syn_sim >= threshold:
                return (
                    True,
                    record,
                    f"High synopsis similarity ({syn_sim:.2f}) with {record.id}: '{record.title}'",
                )

    return (False, None, "")
