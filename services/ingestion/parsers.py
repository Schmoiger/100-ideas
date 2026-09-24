"""Parsers for catalogue markdown tables and incremental inbox documents."""

from __future__ import annotations

import re
from datetime import datetime, timezone
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
    altering 100-ideas.md. Supports optional explicit ID specifications.
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
    current_id: str | None = None

    def commit_current() -> None:
        nonlocal current_title, current_synopsis, current_tags, current_source, current_id
        if current_title and current_synopsis:
            if current_id:
                idea_id: str = current_id
            else:
                idea_num: int = start_id + len(records)
                idea_id = f"idea-{idea_num:03d}"
            records.append(
                IdeaRecord(
                    id=idea_id,
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
        current_id = None

    header_pattern: re.Pattern[str] = re.compile(r"^###\s+\[?([^\]\n]+)\]?")
    id_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*(?:Assigned\s+)?ID\*\*:\s*([^\n]+)", re.IGNORECASE
    )
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

        id_m = id_pattern.match(stripped)
        if id_m:
            current_id = id_m.group(1).strip()
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


def archive_inbox_entries(
    inbox_path: Path,
    archive_path: Path,
    provisioned_records: list[IdeaRecord],
) -> None:
    """Archive provisioned ideas from inbox into inbox-archive.md and prune inbox.md."""
    if not provisioned_records or not inbox_path.is_file():
        return

    content: str = inbox_path.read_text(encoding="utf-8")
    lines: list[str] = content.splitlines()

    provisioned_titles: set[str] = {r.title.strip().lower() for r in provisioned_records}

    header_pattern: re.Pattern[str] = re.compile(r"^###\s+\[?([^\]\n]+)\]?")

    prefix_lines: list[str] = []
    retained_entries: list[list[str]] = []
    current_entry: list[str] = []
    current_entry_title: str | None = None
    in_entries_section: bool = False

    has_marker: bool = "<!-- Add new entries below this line -->" in content
    has_pending: bool = "## Pending Ingestion" in content

    for line in lines:
        stripped: str = line.strip()
        if has_marker and stripped == "<!-- Add new entries below this line -->":
            prefix_lines.append(line)
            in_entries_section = True
            continue

        if not has_marker and has_pending and stripped.startswith("## Pending Ingestion"):
            prefix_lines.append(line)
            in_entries_section = True
            continue

        if not in_entries_section and (has_marker or has_pending):
            prefix_lines.append(line)
            continue

        # We are in the entries section (or no marker was present)
        h_match = header_pattern.match(stripped)
        if h_match:
            if current_entry and current_entry_title:
                if current_entry_title.lower() not in provisioned_titles:
                    retained_entries.append(current_entry)
            current_entry = [line]
            current_entry_title = h_match.group(1).strip()
        else:
            if current_entry:
                current_entry.append(line)
            elif not has_marker and not has_pending:
                prefix_lines.append(line)

    if current_entry and current_entry_title:
        if current_entry_title.lower() not in provisioned_titles:
            retained_entries.append(current_entry)

    # Reconstruct updated inbox.md
    new_inbox_lines: list[str] = list(prefix_lines)
    if new_inbox_lines and new_inbox_lines[-1] != "":
        new_inbox_lines.append("")

    for entry_block in retained_entries:
        new_inbox_lines.extend(entry_block)
        if entry_block and entry_block[-1] != "":
            new_inbox_lines.append("")

    updated_inbox_text = "\n".join(new_inbox_lines).rstrip() + "\n"
    inbox_path.write_text(updated_inbox_text, encoding="utf-8")

    # Append to archive_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not archive_path.is_file():
        archive_header = (
            "# Ideas Inbox Archive\n\n"
            "Historical archive of processed and provisioned ideas from `inbox.md`.\n\n"
            "---\n\n"
            "## Archived Entries\n\n"
        )
        archive_content = archive_header
    else:
        archive_content = archive_path.read_text(encoding="utf-8")
        if not archive_content.endswith("\n"):
            archive_content += "\n"
        if not archive_content.endswith("\n\n"):
            archive_content += "\n"

    new_archive_blocks: list[str] = []
    for r in provisioned_records:
        tags_str: str = ", ".join(r.tags) if r.tags else "None"
        source_str: str = r.source_reference if r.source_reference else "None"
        block = (
            f"### [{r.title}]\n"
            f"- **Assigned ID**: {r.id}\n"
            f"- **Status**: provisioned\n"
            f"- **Archived At**: {now_iso}\n"
            f"- **Synopsis**: {r.synopsis}\n"
            f"- **Tags/Domain**: {tags_str}\n"
            f"- **Source/Reference**: {source_str}\n"
        )
        new_archive_blocks.append(block)

    archive_content += "\n".join(new_archive_blocks) + "\n"
    archive_path.write_text(archive_content, encoding="utf-8")


def parse_inbox_archive(file_path: Path) -> list[IdeaRecord]:
    """Parse archived idea records from inbox-archive.md."""
    if not file_path.is_file():
        return []

    content: str = file_path.read_text(encoding="utf-8")
    lines: list[str] = content.splitlines()

    records: list[IdeaRecord] = []
    current_title: str | None = None
    current_id: str | None = None
    current_synopsis: str = ""
    current_tags: list[str] = []
    current_source: str = ""
    current_status: str = "provisioned"

    def commit_current() -> None:
        nonlocal \
            current_title, \
            current_id, \
            current_synopsis, \
            current_tags, \
            current_source, \
            current_status
        if current_title and current_id:
            records.append(
                IdeaRecord(
                    id=current_id,
                    title=current_title,
                    synopsis=current_synopsis,
                    source_reference=current_source,
                    tags=current_tags,
                    status=current_status,
                )
            )
        current_title = None
        current_id = None
        current_synopsis = ""
        current_tags = []
        current_source = ""
        current_status = "provisioned"

    header_pattern: re.Pattern[str] = re.compile(r"^###\s+\[?([^\]\n]+)\]?")
    id_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*Assigned\s+ID\*\*:\s*([^\n]+)", re.IGNORECASE
    )
    status_pattern: re.Pattern[str] = re.compile(r"^-\s+\*\*Status\*\*:\s*([^\n]+)", re.IGNORECASE)
    synopsis_pattern: re.Pattern[str] = re.compile(r"^-\s+\*\*Synopsis\*\*:\s*(.*)", re.IGNORECASE)
    tags_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*Tags(?:/Domain)?\*\*:\s*(.*)", re.IGNORECASE
    )
    source_pattern: re.Pattern[str] = re.compile(
        r"^-\s+\*\*Source(?:/Reference)?\*\*:\s*(.*)", re.IGNORECASE
    )

    for line in lines:
        stripped: str = line.strip()
        h_match = header_pattern.match(stripped)
        if h_match:
            commit_current()
            current_title = h_match.group(1).strip()
            continue

        if not current_title:
            continue

        id_m = id_pattern.match(stripped)
        if id_m:
            current_id = id_m.group(1).strip()
            continue

        status_m = status_pattern.match(stripped)
        if status_m:
            current_status = status_m.group(1).strip()
            continue

        s_match = synopsis_pattern.match(stripped)
        if s_match:
            current_synopsis = s_match.group(1).strip()
            continue

        t_match = tags_pattern.match(stripped)
        if t_match:
            raw_tags: str = t_match.group(1).strip()
            if raw_tags.lower() != "none":
                current_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            continue

        ref_match = source_pattern.match(stripped)
        if ref_match:
            raw_source: str = ref_match.group(1).strip()
            if raw_source.lower() != "none":
                current_source = raw_source
            continue

    commit_current()
    return records
