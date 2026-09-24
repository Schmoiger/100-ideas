"""Parsers for catalogue markdown tables and incremental inbox documents."""

from __future__ import annotations

import re
from pathlib import Path

from services.ingestion.models import IdeaRecord


def parse_markdown_table(file_path: Path) -> list[IdeaRecord]:
    """Parse Markdown table into structured IdeaRecord instances.

    Handles REQ-ING-001: Extracts Idea Title, Synopsis, and Source Reference.
    Validates non-empty title and synopsis strings.
    """
    content: str = file_path.read_text(encoding="utf-8")
    lines: list[str] = [line.strip() for line in content.splitlines()]

    records: list[IdeaRecord] = []
    header_indices: dict[str, int] = {}
    table_started: bool = False

    for line in lines:
        if not line.startswith("|") or not line.endswith("|"):
            continue

        raw_cells: list[str] = [c.strip() for c in line.split("|")[1:-1]]

        # Detect separator row (e.g., | --- | --- | --- |)
        if all(re.match(r"^:?-+:?$", cell) for cell in raw_cells):
            table_started = True
            continue

        if not table_started:
            # Header row
            lowered: list[str] = [c.lower() for c in raw_cells]
            for idx, col in enumerate(lowered):
                if "title" in col:
                    header_indices["title"] = idx
                elif "synopsis" in col:
                    header_indices["synopsis"] = idx
                elif "ref" in col or "source" in col:
                    header_indices["reference"] = idx
            continue

        # Data row
        title_idx: int = header_indices.get("title", 0)
        synopsis_idx: int = header_indices.get("synopsis", 1)
        ref_idx: int = header_indices.get("reference", 2)

        if len(raw_cells) <= max(title_idx, synopsis_idx):
            continue

        title: str = raw_cells[title_idx].strip()
        synopsis: str = raw_cells[synopsis_idx].strip()
        reference: str = raw_cells[ref_idx].strip() if len(raw_cells) > ref_idx else ""

        # Validate non-empty title and synopsis per REQ-ING-001 acceptance criteria
        if not title or not synopsis:
            continue

        row_num: int = len(records) + 1
        idea_id: str = f"idea-{row_num:03d}"

        records.append(
            IdeaRecord(
                id=idea_id,
                title=title,
                synopsis=synopsis,
                source_reference=reference,
                tags=[],
            )
        )

    return records


def parse_inbox_markdown(file_path: Path, start_id: int = 1) -> list[IdeaRecord]:
    """Parse incremental idea entries from inbox markdown file.

    Handles REQ-ING-004: Reads entries added under format guidelines without
    altering 100-ideas.md.
    """
    if not file_path.is_file():
        return []

    content: str = file_path.read_text(encoding="utf-8")
    lines: list[str] = content.splitlines()

    records: list[IdeaRecord] = []
    current_title: str | None = None
    current_synopsis: str = ""
    current_tags: list[str] = []
    current_source: str = ""

    def commit_current() -> None:
        nonlocal current_title, current_synopsis, current_tags, current_source
        if current_title and current_synopsis:
            idea_num: int = start_id + len(records)
            records.append(
                IdeaRecord(
                    id=f"idea-{idea_num:03d}",
                    title=current_title,
                    synopsis=current_synopsis,
                    source_reference=current_source,
                    tags=current_tags,
                )
            )
        current_title = None
        current_synopsis = ""
        current_tags = []
        current_source = ""

    header_pattern: re.Pattern[str] = re.compile(r"^###\s+\[?([^\]\n]+)\]?")
    synopsis_pattern: re.Pattern[str] = re.compile(r"^-\s+\*\*Synopsis\*\*:\s*(.*)", re.IGNORECASE)
    tags_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*Tags(?:/Domain)?\*\*:\s*(.*)", re.IGNORECASE
    )
    source_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*Source(?:/Reference)?\*\*:\s*(.*)", re.IGNORECASE
    )

    in_code_block: bool = False
    in_pending_section: bool = False

    for line in lines:
        stripped: str = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Look for ## Pending Ingestion section if present
        if stripped.startswith("## Pending Ingestion"):
            in_pending_section = True
            continue

        # If a pending section exists in document, only parse below it
        if "## Pending Ingestion" in content and not in_pending_section:
            continue

        # Ignore markdown comments
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue

        h_match = header_pattern.match(stripped)
        if h_match:
            commit_current()
            current_title = h_match.group(1).strip()
            continue

        if not current_title:
            continue

        s_match = synopsis_pattern.match(stripped)
        if s_match:
            current_synopsis = s_match.group(1).strip()
            continue

        t_match = tags_pattern.match(stripped)
        if t_match:
            raw_tags: str = t_match.group(1).strip()
            current_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            continue

        ref_match = source_pattern.match(stripped)
        if ref_match:
            current_source = ref_match.group(1).strip()
            continue

    commit_current()
    return records
