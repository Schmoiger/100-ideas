"""Smoke tests for Idea Ingestion and Selection Subsystem."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from services.ingestion.dedup import check_duplicate
from services.ingestion.models import IdeaRecord
from services.ingestion.parsers import parse_inbox_markdown, parse_markdown_table
from services.ingestion.provisioner import load_existing_provisioned_ideas, provision_idea
from services.ingestion.selector import select_ideas
from services.ingestion.sync import resolve_catalog_source


def test_parse_catalog_snapshot() -> None:
    """Verify parsing markdown table from snapshot extracts ideas with title and synopsis."""
    repo_root: Path = Path(__file__).resolve().parent.parent.parent.parent
    snapshot: Path = repo_root / "artefacts" / "product" / "100-ideas.snapshot.md"

    ideas: list[IdeaRecord] = parse_markdown_table(snapshot)
    assert len(ideas) >= 50, f"Expected at least 50 ideas parsed, got {len(ideas)}"
    for idea in ideas:
        assert idea.id.startswith("idea-")
        assert len(idea.title.strip()) > 0
        assert len(idea.synopsis.strip()) > 0


def test_selector_filtering() -> None:
    """Verify single-index, range, and batch selection."""
    ideas: list[IdeaRecord] = [
        IdeaRecord(
            id="idea-001", title="ADLC", synopsis="Agentic Dev Lifecycle", tags=["governance"]
        ),
        IdeaRecord(
            id="idea-002",
            title="HATL",
            synopsis="Humans Above The Loop",
            tags=["governance", "review"],
        ),
        IdeaRecord(
            id="idea-003",
            title="Everything As Code",
            synopsis="Operational assets",
            tags=["architecture"],
        ),
    ]

    single = select_ideas(ideas, idea_spec="1")
    assert len(single) == 1
    assert single[0].id == "idea-001"

    single_by_id = select_ideas(ideas, idea_spec="idea-002")
    assert len(single_by_id) == 1
    assert single_by_id[0].id == "idea-002"

    ranged = select_ideas(ideas, range_spec="1-2")
    assert len(ranged) == 2
    assert [r.id for r in ranged] == ["idea-001", "idea-002"]

    all_ideas = select_ideas(ideas, all_flag=True)
    assert len(all_ideas) == 3

    tagged = select_ideas(ideas, tag="review")
    assert len(tagged) == 1
    assert tagged[0].id == "idea-002"


def test_sandbox_symlink_fallback() -> None:
    """Verify that an inaccessible catalog path transparently falls back to snapshot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        broken_catalog = tmp_path / "non_existent_100-ideas.md"
        valid_snapshot = tmp_path / "100-ideas.snapshot.md"
        valid_snapshot.write_text(
            "# Snapshot\n\n| Idea Title | Synopsis | Reference |\n| --- | --- | --- |\n| Test | Synopsis | Ref |\n"
        )

        resolved = resolve_catalog_source(broken_catalog, valid_snapshot)
        assert resolved == valid_snapshot


def test_inbox_parsing_and_deduplication() -> None:
    """Verify incremental inbox parsing and duplicate detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        inbox_file = tmp_path / "inbox.md"
        inbox_file.write_text(
            "### Agentic Lifecycle\n"
            "- **Synopsis**: Supervised iteration and agentic pipelines.\n"
            "- **Tags/Domain**: Governance, ADLC\n"
            "- **Source/Reference**: Notes 2026\n"
        )

        inbox_records = parse_inbox_markdown(inbox_file, start_id=101)
        assert len(inbox_records) == 1
        record = inbox_records[0]
        assert record.id == "idea-101"
        assert record.title == "Agentic Lifecycle"
        assert "Governance" in record.tags

        # Duplicate check against existing
        existing = [
            IdeaRecord(id="idea-001", title="Agentic Lifecycle", synopsis="Different synopsis")
        ]
        is_dup, matched, reason = check_duplicate(record, existing)
        assert is_dup is True
        assert matched is not None
        assert matched.id == "idea-001"


def test_provisioning_structure() -> None:
    """Verify provisioning creates folders and valid meta.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        idea = IdeaRecord(
            id="idea-042",
            title="Theory of Constraints",
            synopsis="Elevate the binding constraint.",
            tags=["devx", "bottlenecks"],
            source_reference="Drafts line 50",
        )

        p_dir = provision_idea(idea, tmp_path)
        assert p_dir.is_dir()
        assert (p_dir / "research").is_dir()
        assert (p_dir / "assets").is_dir()
        assert (p_dir / "book").is_dir()
        assert (p_dir / "blog").is_dir()

        meta_file = p_dir / "meta.yaml"
        assert meta_file.is_file()

        loaded_meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert loaded_meta["id"] == "idea-042"
        assert loaded_meta["title"] == "Theory of Constraints"
        assert loaded_meta["status"] == "ingested"

        # Test loading provisioned ideas
        records = load_existing_provisioned_ideas(tmp_path)
        assert len(records) == 1
        assert records[0].id == "idea-042"


def test_cli_batch_resolution() -> None:
    """Verify resolve_ideas_to_process helper handles single and batch flags."""
    from services.ingestion.cli import resolve_ideas_to_process

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "idea-001").mkdir()
        (tmp_path / "idea-002").mkdir()
        (tmp_path / "other-dir").mkdir()

        # Single idea
        assert resolve_ideas_to_process("idea-001", False, tmp_path) == ["idea-001"]

        # All ideas
        all_ideas = resolve_ideas_to_process(None, True, tmp_path)
        assert all_ideas == ["idea-001", "idea-002"]

        # Empty
        assert resolve_ideas_to_process(None, False, tmp_path) == []


def test_cli_subparsers_and_pipeline() -> None:
    """Verify build_parser registers pipeline, enrich, and draft with batch options."""
    from services.ingestion.cli import build_parser

    parser = build_parser()
    # Test pipeline parsing
    args = parser.parse_args(["pipeline", "--idea", "idea-001", "--force"])
    assert args.subcommand == "pipeline"
    assert args.idea == "idea-001"
    assert args.force is True

    # Test batch pipeline parsing
    args_batch = parser.parse_args(["pipeline", "--all"])
    assert args_batch.subcommand == "pipeline"
    assert args_batch.all is True

    # Test batch enrich parsing
    args_enrich = parser.parse_args(["enrich", "--all"])
    assert args_enrich.subcommand == "enrich"
    assert args_enrich.all is True

    # Test batch draft parsing
    args_draft = parser.parse_args(["draft", "--all"])
    assert args_draft.subcommand == "draft"
    assert args_draft.all is True
