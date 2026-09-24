"""Tests for CLI Gemini integration, --dry-run, --force-llm, and interactive batch confirmation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from services.ingestion.cli import main
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.llm.governance import TokenGovernance


@pytest.fixture
def test_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up isolated project environment for CLI tests."""
    TokenGovernance.reset()
    ideas_dir = tmp_path / "artefacts" / "content" / "ideas"
    res_dir = tmp_path / "artefacts" / "content" / "resources"
    catalog_path = tmp_path / "artefacts" / "product" / "100-ideas.md"
    snapshot_path = tmp_path / "artefacts" / "product" / "100-ideas.snapshot.md"

    ideas_dir.mkdir(parents=True)
    res_dir.mkdir(parents=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)

    catalog_path.write_text(
        """| ID | Category | Title | Synopsis | Source Reference | Linked Resources |
|---|---|---|---|---|---|
| idea-001 | Governance | Test Title | Test Synopsis for idea | Ref | devx |
""",
        encoding="utf-8",
    )

    def _paths():
        return catalog_path, snapshot_path, tmp_path / "inbox.md", ideas_dir

    monkeypatch.setattr("services.cli._shared.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.enrich.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.typeset.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.publishing.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.ingest.get_default_paths", _paths)
    # Legacy shim compat (kept for any test that patches the old location)
    monkeypatch.setattr("services.ingestion.cli.get_default_paths", _paths)

    # Provision idea-001
    rec = IdeaRecord(id="idea-001", title="Test Title", synopsis="Test Synopsis for idea")
    provision_idea(rec, ideas_dir)

    return {
        "ideas_dir": ideas_dir,
        "res_dir": res_dir,
        "catalog_path": catalog_path,
    }


def test_cli_enrich_dry_run(test_env, capsys):
    """Verify ideas enrich --dry-run records estimation in meta.yaml without creating notes.md."""
    exit_code = main(["enrich", "--idea", "idea-001", "--dry-run"])
    assert exit_code == 0

    ideas_dir = test_env["ideas_dir"]
    notes_file = ideas_dir / "idea-001" / "research" / "notes.md"
    assert not notes_file.is_file()

    meta_file = ideas_dir / "idea-001" / "meta.yaml"
    meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert "token_telemetry" in meta_dict
    assert "dry-run" in meta_dict["token_telemetry"]["model"]


def test_cli_draft_dry_run(test_env, capsys):
    """Verify ideas draft --dry-run records estimation in meta.yaml without creating chapter.md."""
    exit_code = main(["draft", "--idea", "idea-001", "--dry-run"])
    assert exit_code == 0

    ideas_dir = test_env["ideas_dir"]
    chapter_file = ideas_dir / "idea-001" / "book" / "chapter.md"
    assert not chapter_file.is_file()

    meta_file = ideas_dir / "idea-001" / "meta.yaml"
    meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert "token_telemetry" in meta_dict
    assert "dry-run" in meta_dict["token_telemetry"]["model"]


def test_cli_batch_confirmation_prompt_reject(test_env, monkeypatch):
    """Verify running --all prompts user and aborts when rejected."""
    # Provision second idea
    ideas_dir = test_env["ideas_dir"]
    rec2 = IdeaRecord(id="idea-002", title="Second Title", synopsis="Synopsis two")
    provision_idea(rec2, ideas_dir)

    # Mock user input 'n'
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    exit_code = main(["enrich", "--all"])
    assert exit_code == 0

    # Ensure files were not created
    notes1 = ideas_dir / "idea-001" / "research" / "notes.md"
    notes2 = ideas_dir / "idea-002" / "research" / "notes.md"
    assert not notes1.is_file()
    assert not notes2.is_file()


def test_cli_batch_confirmation_with_yes_flag(test_env, monkeypatch):
    """Verify running --all --yes bypasses interactive prompt and executes."""
    ideas_dir = test_env["ideas_dir"]
    rec2 = IdeaRecord(id="idea-002", title="Second Title", synopsis="Synopsis two")
    provision_idea(rec2, ideas_dir)

    # If input is called, it should raise
    monkeypatch.setattr(
        "builtins.input", MagicMock(side_effect=RuntimeError("Prompt should not be called"))
    )

    exit_code = main(["enrich", "--all", "--yes"])
    assert exit_code == 0

    notes1 = ideas_dir / "idea-001" / "research" / "notes.md"
    notes2 = ideas_dir / "idea-002" / "research" / "notes.md"
    assert notes1.is_file()
    assert notes2.is_file()
