"""Tests for continuous ingestion lifecycle, inbox archiving, and decoupled IDs (TASK-016)."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

from services.ingestion.cli import (
    get_next_idea_number,
    handle_add_command,
    handle_inbox_command,
)
from services.ingestion.models import IdeaRecord
from services.ingestion.parsers import (
    archive_inbox_entries,
    parse_inbox_archive,
    parse_inbox_markdown,
)
from services.typesetting.drafter import build_chapter_draft


def test_inbox_provision_prunes_inbox_and_populates_archive() -> None:
    """Verify inbox provisioning prunes inbox.md and populates inbox-archive.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        inbox_file = tmp_path / "inbox.md"
        archive_file = tmp_path / "inbox-archive.md"
        ideas_dir = tmp_path / "ideas"
        ideas_dir.mkdir()

        inbox_content = (
            "# Ideas Inbox\n\n"
            "Drop new idea stubs here.\n\n"
            "---\n\n"
            "## Format Guidelines\n\n"
            "Guideline text.\n\n"
            "---\n\n"
            "## Pending Ingestion\n\n"
            "<!-- Add new entries below this line -->\n\n"
            "### [Developer Latency]\n"
            "- **Synopsis**: Measuring turnaround time on verification.\n"
            "- **Tags/Domain**: Tooling, DevX\n"
            "- **Source/Reference**: Internal memo 2026\n\n"
            "### [Autonomous Verification Gate]\n"
            "- **Synopsis**: Continuous automated policy enforcement.\n"
            "- **Tags/Domain**: Architecture, Governance\n"
            "- **Source/Reference**: Whitepaper draft\n"
        )
        inbox_file.write_text(inbox_content, encoding="utf-8")

        # 1. Parse inbox
        records = parse_inbox_markdown(inbox_file, start_id=1)
        assert len(records) == 2
        assert records[0].id == "idea-001"
        assert records[0].title == "Developer Latency"
        assert records[1].id == "idea-002"
        assert records[1].title == "Autonomous Verification Gate"

        # 2. Archive provisioned entries
        archive_inbox_entries(
            inbox_path=inbox_file,
            archive_path=archive_file,
            provisioned_records=records,
        )

        # 3. Assert inbox.md has been pruned
        updated_inbox = inbox_file.read_text(encoding="utf-8")
        assert "Developer Latency" not in updated_inbox
        assert "Autonomous Verification Gate" not in updated_inbox
        assert "## Pending Ingestion" in updated_inbox
        assert "<!-- Add new entries below this line -->" in updated_inbox

        # 4. Assert inbox-archive.md is populated
        assert archive_file.is_file()
        archived_records = parse_inbox_archive(archive_file)
        assert len(archived_records) == 2
        assert archived_records[0].id == "idea-001"
        assert archived_records[0].title == "Developer Latency"
        assert archived_records[0].status == "provisioned"
        assert archived_records[1].id == "idea-002"
        assert archived_records[1].title == "Autonomous Verification Gate"

        # 5. Subsequent parse of inbox returns 0 pending records
        subsequent_records = parse_inbox_markdown(inbox_file, start_id=3)
        assert len(subsequent_records) == 0


def test_cli_handle_inbox_end_to_end() -> None:
    """Verify handle_inbox_command provisions ideas and drains queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        catalog_file = tmp_path / "100-ideas.md"
        snapshot_file = tmp_path / "100-ideas.snapshot.md"
        inbox_file = tmp_path / "inbox.md"
        archive_file = tmp_path / "inbox-archive.md"
        ideas_dir = tmp_path / "ideas"
        ideas_dir.mkdir()

        snapshot_file.write_text(
            "| Idea Title | Synopsis | Source Reference |\n"
            "| --- | --- | --- |\n"
            "| Base Concept | Initial idea | Ref 1 |\n",
            encoding="utf-8",
        )

        inbox_file.write_text(
            "# Ideas Inbox\n\n"
            "## Pending Ingestion\n\n"
            "<!-- Add new entries below this line -->\n\n"
            "### [Continuous Publication]\n"
            "- **Synopsis**: Decoupling intake from volume compilation.\n"
            "- **Tags/Domain**: Architecture\n",
            encoding="utf-8",
        )

        args = argparse.Namespace(provision=True, force=False)
        with (
            patch(
                "services.ingestion.cli.get_default_paths",
                return_value=(catalog_file, snapshot_file, inbox_file, ideas_dir),
            ),
            patch(
                "services.cli.commands.ingest.get_default_paths",
                return_value=(catalog_file, snapshot_file, inbox_file, ideas_dir),
            ),
            patch("services.ingestion.cli.get_inbox_archive_path", return_value=archive_file),
            patch("services.cli.commands.ingest.get_inbox_archive_path", return_value=archive_file),
        ):
            ret = handle_inbox_command(args)
            assert ret == 0

        # Assert provisioned into ideas_dir
        provisioned_dirs = [d.name for d in ideas_dir.iterdir() if d.is_dir()]
        assert "idea-002" in provisioned_dirs

        # Assert inbox drained
        updated_inbox = inbox_file.read_text(encoding="utf-8")
        assert "Continuous Publication" not in updated_inbox

        # Assert archive created
        assert archive_file.is_file()
        archived = parse_inbox_archive(archive_file)
        assert len(archived) == 1
        assert archived[0].title == "Continuous Publication"
        assert archived[0].id == "idea-002"


def test_get_next_idea_number_decoupled_from_100() -> None:
    """Verify dynamic index calculation has no arbitrary 100 limit."""
    # 0 existing
    assert get_next_idea_number([]) == 1

    # 5 existing
    records_5 = [
        IdeaRecord(id=f"idea-{i:03d}", title=f"Idea {i}", synopsis="Test") for i in range(1, 6)
    ]
    assert get_next_idea_number(records_5) == 6

    # 120 existing
    records_120 = [
        IdeaRecord(id=f"idea-{i:03d}", title=f"Idea {i}", synopsis="Test") for i in range(1, 121)
    ]
    assert get_next_idea_number(records_120) == 121

    # Non-numeric semantic slug does not break calculation
    records_slug = [
        IdeaRecord(id="idea-devx-friction", title="DevX Friction", synopsis="Test"),
        IdeaRecord(id="idea-003", title="Third Idea", synopsis="Test"),
    ]
    assert get_next_idea_number(records_slug) == 4


def test_cli_add_with_custom_semantic_id() -> None:
    """Verify ideas add supports --id with arbitrary identifier."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        catalog_file = tmp_path / "100-ideas.md"
        snapshot_file = tmp_path / "100-ideas.snapshot.md"
        inbox_file = tmp_path / "inbox.md"
        archive_file = tmp_path / "inbox-archive.md"
        ideas_dir = tmp_path / "ideas"
        ideas_dir.mkdir()

        snapshot_file.write_text(
            "| Idea Title | Synopsis | Source Reference |\n| --- | --- | --- |\n",
            encoding="utf-8",
        )

        args = argparse.Namespace(
            title="Semantic Decoupling",
            synopsis="Decouple identifiers from publishing order.",
            tags="architecture,governance",
            source="Architecture Review",
            id="idea-semantic-decoupling",
            force=False,
        )

        with (
            patch(
                "services.ingestion.cli.get_default_paths",
                return_value=(catalog_file, snapshot_file, inbox_file, ideas_dir),
            ),
            patch(
                "services.cli.commands.ingest.get_default_paths",
                return_value=(catalog_file, snapshot_file, inbox_file, ideas_dir),
            ),
            patch("services.ingestion.cli.get_inbox_archive_path", return_value=archive_file),
            patch("services.cli.commands.ingest.get_inbox_archive_path", return_value=archive_file),
        ):
            ret = handle_add_command(args)
            assert ret == 0

        target_dir = ideas_dir / "idea-semantic-decoupling"
        assert target_dir.is_dir()
        assert (target_dir / "meta.yaml").is_file()


def test_decoupled_chapter_number_in_drafter() -> None:
    """Verify chapter draft honours decoupled chapter numbering."""
    idea = IdeaRecord(
        id="idea-semantic-decoupling",
        title="Decoupled Chapter Order",
        synopsis="Chapter number assigned at book assembly time.",
    )

    draft = build_chapter_draft(
        idea=idea,
        research_content="",
        metaphor="Interlocking mechanical gears",
        chapter_num=42,
    )

    assert draft.chapter_num == 42
    assert "Chapter 42" in draft.subtitle
    assert draft.idea_id == "idea-semantic-decoupling"
