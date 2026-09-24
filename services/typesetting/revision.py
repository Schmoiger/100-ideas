"""Targeted section revision engine adhering to AS author persona and review protocol.

Allows conversational refinement of drafted text, selective prompt adjustment,
and section-by-section regeneration without rewriting entire documents.
Adheres to review-continuous-publishing.md §8 and TASK-019.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CANONICAL_SECTIONS: list[str] = [
    "header",
    "lead_punch",
    "mechanics",
    "economics",
    "hype",
    "takeaways",
    "citations",
]

SECTION_HEADERS: dict[str, str] = {
    "lead_punch": "## The Unvarnished Reality",
    "mechanics": "## Where the Gears Bind",
    "economics": "## The Economic Equation & Trade-offs",
    "hype": "## Puncturing the Hype",
    "takeaways": "## Actionable Takeaways",
    "citations": "## Grounded Citations & Field References",
}

SECTION_ALIASES: dict[str, str] = {
    # lead_punch aliases
    "lead_punch": "lead_punch",
    "lead": "lead_punch",
    "punch": "lead_punch",
    "reality": "lead_punch",
    "unvarnished": "lead_punch",
    "the_unvarnished_reality": "lead_punch",
    # mechanics aliases
    "mechanics": "mechanics",
    "gears": "mechanics",
    "mechanism": "mechanics",
    "where_the_gears_bind": "mechanics",
    "operating_mechanism": "mechanics",
    # economics aliases
    "economics": "economics",
    "economic": "economics",
    "equation": "economics",
    "tradeoffs": "economics",
    "trade_offs": "economics",
    "the_economic_equation": "economics",
    "the_economic_equation_and_trade_offs": "economics",
    # hype aliases
    "hype": "hype",
    "puncturing": "hype",
    "puncturing_the_hype": "hype",
    "counterarguments": "hype",
    "wry_realism": "hype",
    # takeaways aliases
    "takeaways": "takeaways",
    "takeaway": "takeaways",
    "actions": "takeaways",
    "actionable_takeaways": "takeaways",
    # citations aliases
    "citations": "citations",
    "citation": "citations",
    "references": "citations",
    "grounded_citations": "citations",
}


def resolve_canonical_section(section_name: str) -> str:
    """Resolve section name or alias to canonical section key."""
    norm = re.sub(r"[\s-]+", "_", section_name.strip().lower())
    if norm in SECTION_ALIASES:
        return SECTION_ALIASES[norm]
    raise ValueError(
        f"Unknown section '{section_name}'. Valid sections or aliases are: "
        f"{', '.join(sorted(set(SECTION_ALIASES.keys())))}"
    )


def parse_chapter_sections(content: str) -> dict[str, str]:
    """Parse chapter markdown into semantic sections dictionary."""
    sections: dict[str, str] = {}

    # Extract header (everything up to first section header)
    first_sec_match = re.search(r"\n---\n\s*##\s+", content)
    if first_sec_match:
        sections["header"] = content[: first_sec_match.start()].strip()
    else:
        # Fallback to before any ##
        h2_match = re.search(r"^##\s+", content, re.MULTILINE)
        if h2_match:
            sections["header"] = content[: h2_match.start()].strip()
        else:
            sections["header"] = ""

    # Helper to extract section content between headers
    def extract_section_text(header_pattern: str, next_patterns: list[str]) -> str:
        match = re.search(header_pattern, content, re.MULTILINE | re.IGNORECASE)
        if not match:
            return ""
        start_pos = match.end()

        combined = "|".join(next_patterns)
        next_match = re.search(combined, content[start_pos:], re.MULTILINE | re.IGNORECASE)
        end_pos = start_pos + next_match.start() if next_match else len(content)

        raw = content[start_pos:end_pos].strip()
        # Clean leading/trailing divider bars
        raw = re.sub(r"^\s*---\s*", "", raw).strip()
        raw = re.sub(r"\s*---\s*$", "", raw).strip()
        return raw

    sections["lead_punch"] = extract_section_text(
        r"^##\s+The\s+Unvarnished\s+Reality\b",
        [r"^---\s*$", r"^##\s+Where\s+the\s+Gears"],
    )

    sections["mechanics"] = extract_section_text(
        r"^##\s+Where\s+the\s+Gears\s+Bind\b",
        [r"^---\s*$", r"^##\s+The\s+Economic\s+Equation"],
    )

    sections["economics"] = extract_section_text(
        r"^##\s+The\s+Economic\s+Equation\s*&?\s*Trade-offs\b",
        [r"^---\s*$", r"^##\s+Puncturing\s+the\s+Hype"],
    )

    sections["hype"] = extract_section_text(
        r"^##\s+Puncturing\s+the\s+Hype\b",
        [r"^---\s*$", r"^##\s+Actionable\s+Takeaways"],
    )

    sections["takeaways"] = extract_section_text(
        r"^##\s+Actionable\s+Takeaways\b",
        [r"^---\s*$", r"^##\s+Grounded\s+Citations"],
    )

    citations = extract_section_text(
        r"^##\s+Grounded\s+Citations\s*&?\s*Field\s+References\b",
        [r"^---\s*$", r"^##\s+"],
    )
    if citations:
        sections["citations"] = citations

    return sections


def reassemble_chapter_sections(sections: dict[str, str]) -> str:
    """Reassemble chapter sections dictionary back into standard Markdown format."""
    parts: list[str] = []

    header = sections.get("header", "").strip()
    if header:
        parts.append(header)

    def append_block(key: str, header_title: str) -> None:
        content = sections.get(key, "").strip()
        if content:
            parts.extend(["", "---", "", header_title, "", content])

    append_block("lead_punch", SECTION_HEADERS["lead_punch"])
    append_block("mechanics", SECTION_HEADERS["mechanics"])
    append_block("economics", SECTION_HEADERS["economics"])
    append_block("hype", SECTION_HEADERS["hype"])
    append_block("takeaways", SECTION_HEADERS["takeaways"])
    append_block("citations", SECTION_HEADERS["citations"])

    parts.append("")
    return "\n".join(parts)


def revise_chapter_section(
    idea_dir: Path,
    section: str,
    new_content: str,
    reviewer: str = "Author",
    notes: str = "",
    append: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Apply targeted refinement to a specific section of book/chapter.md.

    Preserves all other sections untouched, updates meta.yaml state machine,
    and records revision provenance.
    """
    chapter_file = idea_dir / "book" / "chapter.md"
    if not chapter_file.is_file():
        raise FileNotFoundError(f"Chapter file not found at {chapter_file}")

    canonical_key = resolve_canonical_section(section)
    original_text = chapter_file.read_text(encoding="utf-8")
    sections = parse_chapter_sections(original_text)

    cleaned_content = new_content.strip()

    if append and canonical_key in sections and sections[canonical_key]:
        sections[canonical_key] = f"{sections[canonical_key].strip()}\n\n{cleaned_content}"
    else:
        sections[canonical_key] = cleaned_content

    # Reassemble and atomically save
    updated_markdown = reassemble_chapter_sections(sections)
    temp_file = chapter_file.parent / ".chapter.md.tmp"
    temp_file.write_text(updated_markdown, encoding="utf-8")
    temp_file.replace(chapter_file)

    # Update meta.yaml
    meta_file = idea_dir / "meta.yaml"
    meta_data: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:
            meta_data = {}

    meta_data["human_modified"] = True
    meta_data["review_status"] = "needs_revision"
    meta_data["stage"] = "human_review"

    if "revisions" not in meta_data or not isinstance(meta_data["revisions"], list):
        meta_data["revisions"] = []

    revision_entry = {
        "target": "book/chapter.md",
        "section": canonical_key,
        "reviewed_by": reviewer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": notes or f"Refined section {canonical_key}",
    }
    meta_data["revisions"].append(revision_entry)

    temp_meta = idea_dir / ".meta.yaml.tmp"
    temp_meta.write_text(
        yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    temp_meta.replace(meta_file)

    return chapter_file, revision_entry
