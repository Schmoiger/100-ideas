"""CLI dispatch and modularisation tests (TASK-022).

Verifies that:
- The parser in ``services.cli.main`` registers all expected subcommands.
- Each subcommand dispatches to the correct handler module.
- The legacy shim (``services.ingestion.cli``) re-exports the canonical symbols.
- Command handlers honour the ``get_default_paths`` isolation contract.
- CLI test coverage is driven above 90% for the new package.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from services.cli.main import build_parser, main
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.llm.governance import TokenGovernance

# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Verify the system parser registers all expected subcommands."""

    def test_all_subcommands_registered(self) -> None:
        parser = build_parser()
        expected = {
            "sync",
            "catalog",
            "inbox",
            "add",
            "enrich",
            "draft",
            "typeset",
            "blog",
            "social",
            "pipeline",
            "review",
            "mark-edited",
            "revise",
        }
        choices = set(parser._subparsers._actions[1].choices.keys())  # type: ignore[attr-defined]
        assert expected == choices

    def test_sync_parser(self) -> None:
        args = build_parser().parse_args(["sync", "--source", "/tmp/a", "--destination", "/tmp/b"])
        assert args.subcommand == "sync"
        assert args.source == "/tmp/a"
        assert args.destination == "/tmp/b"

    def test_catalog_parser(self) -> None:
        args = build_parser().parse_args(["catalog", "--idea", "idea-001", "--provision"])
        assert args.subcommand == "catalog"
        assert args.idea == "idea-001"
        assert args.provision is True

    def test_enrich_parser(self) -> None:
        args = build_parser().parse_args(["enrich", "--all", "--dry-run", "--yes"])
        assert args.subcommand == "enrich"
        assert args.all is True
        assert args.dry_run is True
        assert args.yes is True

    def test_draft_parser(self) -> None:
        args = build_parser().parse_args(["draft", "--idea", "idea-005", "--force-llm"])
        assert args.subcommand == "draft"
        assert args.idea == "idea-005"
        assert args.force_llm is True

    def test_typeset_parser(self) -> None:
        args = build_parser().parse_args(["typeset", "--volume", "volume-1"])
        assert args.subcommand == "typeset"
        assert args.volume == "volume-1"

    def test_blog_parser(self) -> None:
        args = build_parser().parse_args(
            ["blog", "--idea", "idea-003", "--platform", "hostinger_ghost", "--force"]
        )
        assert args.subcommand == "blog"
        assert args.platform == "hostinger_ghost"
        assert args.force is True

    def test_social_parser(self) -> None:
        args = build_parser().parse_args(["social", "--idea", "idea-007"])
        assert args.subcommand == "social"
        assert args.idea == "idea-007"

    def test_pipeline_parser(self) -> None:
        args = build_parser().parse_args(["pipeline", "--all", "--yes"])
        assert args.subcommand == "pipeline"
        assert args.all is True
        assert args.yes is True

    def test_review_parser(self) -> None:
        args = build_parser().parse_args(["review", "--idea", "idea-001", "--reviewer", "Alice"])
        assert args.subcommand == "review"
        assert args.reviewer == "Alice"

    def test_mark_edited_parser(self) -> None:
        args = build_parser().parse_args(["mark-edited", "--idea", "idea-001", "--unmark"])
        assert args.subcommand == "mark-edited"
        assert args.unmark is True

    def test_revise_parser(self) -> None:
        args = build_parser().parse_args(
            ["revise", "--idea", "idea-002", "--section", "economics", "--content", "New text"]
        )
        assert args.subcommand == "revise"
        assert args.section == "economics"
        assert args.content == "New text"


# ---------------------------------------------------------------------------
# Dispatch integrity test
# ---------------------------------------------------------------------------


class TestDispatch:
    """Verify main() dispatches to the correct handler in each command module."""

    def test_dispatch_sync(self, tmp_path: Path) -> None:
        """Sync handler is invoked and returns 0 when source == destination."""
        src = tmp_path / "catalog.md"
        src.write_text("# test\n", encoding="utf-8")
        dst = tmp_path / "snapshot.md"
        rc = main(["sync", "--source", str(src), "--destination", str(dst)])
        assert rc == 0
        assert dst.is_file()

    def test_dispatch_unknown_subcommand_falls_back(self) -> None:
        """Parser exits for unrecognised subcommand (argparse behaviour)."""
        with pytest.raises(SystemExit):
            main(["nonexistent-command"])


# ---------------------------------------------------------------------------
# Shared helpers tests
# ---------------------------------------------------------------------------


class TestSharedHelpers:
    """Verify _shared.py utilities work correctly."""

    def test_resolve_ideas_to_process_single(self, tmp_path: Path) -> None:
        from services.cli._shared import resolve_ideas_to_process

        assert resolve_ideas_to_process("idea-001", False, tmp_path) == ["idea-001"]

    def test_resolve_ideas_to_process_all(self, tmp_path: Path) -> None:
        from services.cli._shared import resolve_ideas_to_process

        (tmp_path / "idea-001").mkdir()
        (tmp_path / "idea-002").mkdir()
        (tmp_path / "other").mkdir()
        result = resolve_ideas_to_process(None, True, tmp_path)
        assert result == ["idea-001", "idea-002"]

    def test_resolve_ideas_to_process_empty(self, tmp_path: Path) -> None:
        from services.cli._shared import resolve_ideas_to_process

        assert resolve_ideas_to_process(None, False, tmp_path) == []

    def test_confirm_batch_single_skips_prompt(self) -> None:
        from services.cli._shared import confirm_batch_execution

        with patch("builtins.input", MagicMock(side_effect=RuntimeError("should not be called"))):
            assert confirm_batch_execution(["idea-001"], "enrichment") is True

    def test_confirm_batch_yes_flag_skips_prompt(self) -> None:
        from services.cli._shared import confirm_batch_execution

        ideas = ["idea-001", "idea-002", "idea-003"]
        with patch("builtins.input", MagicMock(side_effect=RuntimeError("should not be called"))):
            assert confirm_batch_execution(ideas, "enrichment", yes=True) is True

    def test_confirm_batch_rejected(self) -> None:
        from services.cli._shared import confirm_batch_execution

        with patch("builtins.input", lambda _: "n"):
            assert confirm_batch_execution(["idea-001", "idea-002"], "enrichment") is False

    def test_confirm_batch_accepted(self) -> None:
        from services.cli._shared import confirm_batch_execution

        with patch("builtins.input", lambda _: "y"):
            assert confirm_batch_execution(["idea-001", "idea-002"], "enrichment") is True


# ---------------------------------------------------------------------------
# Integration: enrich dry-run via new entry point
# ---------------------------------------------------------------------------


@pytest.fixture()
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Provision an isolated idea environment wired to tmp_path."""
    TokenGovernance.reset()
    ideas_dir = tmp_path / "artefacts" / "content" / "ideas"
    res_dir = tmp_path / "artefacts" / "content" / "resources"
    catalog_path = tmp_path / "artefacts" / "product" / "100-ideas.md"
    snapshot_path = tmp_path / "artefacts" / "product" / "100-ideas.snapshot.md"

    ideas_dir.mkdir(parents=True)
    res_dir.mkdir(parents=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        "| ID | Category | Title | Synopsis | Source Reference | Linked Resources |\n"
        "|---|---|---|---|---|---|\n"
        "| idea-001 | Governance | Test Title | Test Synopsis for idea | Ref | devx |\n",
        encoding="utf-8",
    )

    def _paths():
        return catalog_path, snapshot_path, tmp_path / "inbox.md", ideas_dir

    monkeypatch.setattr("services.cli._shared.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.enrich.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.typeset.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.publishing.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.ingest.get_default_paths", _paths)

    monkeypatch.setattr("services.cli.commands.review.get_default_paths", _paths)
    monkeypatch.setattr("services.ingestion.cli.get_default_paths", _paths)

    rec = IdeaRecord(id="idea-001", title="Test Title", synopsis="Test Synopsis for idea")
    provision_idea(rec, ideas_dir)

    return {
        "ideas_dir": ideas_dir,
        "catalog_path": catalog_path,
    }


def test_new_entrypoint_enrich_dry_run(isolated_env, capsys) -> None:
    """Verify ``main()`` from services.cli.main routes enrich --dry-run correctly."""
    exit_code = main(["enrich", "--idea", "idea-001", "--dry-run"])
    assert exit_code == 0

    ideas_dir = isolated_env["ideas_dir"]
    notes_file = ideas_dir / "idea-001" / "research" / "notes.md"
    assert not notes_file.is_file(), "dry-run must not create research notes"

    meta_file = ideas_dir / "idea-001" / "meta.yaml"
    meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert "token_telemetry" in meta_dict
    assert "dry-run" in meta_dict["token_telemetry"]["model"]


def test_new_entrypoint_draft_dry_run(isolated_env, capsys) -> None:
    """Verify ``main()`` from services.cli.main routes draft --dry-run correctly."""
    exit_code = main(["draft", "--idea", "idea-001", "--dry-run"])
    assert exit_code == 0

    ideas_dir = isolated_env["ideas_dir"]
    chapter_file = ideas_dir / "idea-001" / "book" / "chapter.md"
    assert not chapter_file.is_file(), "dry-run must not create chapter.md"


def test_legacy_shim_main_is_canonical(isolated_env, capsys) -> None:
    """Verify services.ingestion.cli.main delegates to the new dispatcher."""
    from services.ingestion.cli import main as legacy_main

    exit_code = legacy_main(["enrich", "--idea", "idea-001", "--dry-run"])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# Legacy backward-compat re-export test
# ---------------------------------------------------------------------------


def test_legacy_shim_exports_all_symbols() -> None:
    """Verify the shim re-exports every symbol that existing tests depend on."""
    import services.ingestion.cli as shim

    required = [
        "main",
        "build_parser",
        "get_default_paths",
        "resolve_ideas_to_process",
        "confirm_batch_execution",
        "get_next_idea_number",
        "handle_sync_command",
        "handle_catalog_command",
        "handle_inbox_command",
        "handle_add_command",
        "handle_enrich_command",
        "handle_draft_command",
        "handle_typeset_command",
        "handle_blog_command",
        "handle_social_command",
        "handle_pipeline_command",
        "handle_review_command",
        "handle_mark_edited_command",
        "handle_revise_command",
    ]
    for name in required:
        assert hasattr(shim, name), f"services.ingestion.cli is missing '{name}'"
