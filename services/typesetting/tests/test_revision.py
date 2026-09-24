"""Tests for Targeted Section Revision Subsystem and CLI integration (TASK-019)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from services.ingestion.cli import build_parser, handle_revise_command
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.typesetting.drafter import draft_book_chapter
from services.typesetting.revision import (
    parse_chapter_sections,
    reassemble_chapter_sections,
    resolve_canonical_section,
    revise_chapter_section,
)


def _create_sample_idea(idea_id: str = "idea-001") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Decouple Syntax from Architecture",
        synopsis="Software delivery is throttled by manual syntax typing rather than architectural intent.",
        tags=["Architecture", "PlatformEngineering"],
    )


def test_section_alias_resolution() -> None:
    """Verify section alias dictionary resolves aliases to canonical section names."""
    assert resolve_canonical_section("mechanics") == "mechanics"
    assert resolve_canonical_section("gears") == "mechanics"
    assert resolve_canonical_section("reality") == "lead_punch"
    assert resolve_canonical_section("lead") == "lead_punch"
    assert resolve_canonical_section("economics") == "economics"
    assert resolve_canonical_section("tradeoffs") == "economics"
    assert resolve_canonical_section("hype") == "hype"
    assert resolve_canonical_section("counterarguments") == "hype"
    assert resolve_canonical_section("takeaways") == "takeaways"
    assert resolve_canonical_section("actions") == "takeaways"
    assert resolve_canonical_section("citations") == "citations"


def test_parse_and_reassemble_roundtrip() -> None:
    """Verify parsing and reassembling a chapter manuscript preserves content faithfully."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea()
        provision_idea(idea, ideas_root)
        chapter_file, _ = draft_book_chapter(idea, ideas_root, force=True)
        original_text = chapter_file.read_text(encoding="utf-8")

        sections = parse_chapter_sections(original_text)
        assert "header" in sections
        assert "lead_punch" in sections
        assert "mechanics" in sections
        assert "economics" in sections
        assert "hype" in sections
        assert "takeaways" in sections

        reassembled = reassemble_chapter_sections(sections)
        assert reassembled.strip() == original_text.strip()


def test_revise_chapter_section_targeted() -> None:
    """Verify revise_chapter_section modifies ONLY the targeted section and updates meta.yaml."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea()
        provision_idea(idea, ideas_root)
        chapter_file, _ = draft_book_chapter(idea, ideas_root, force=True)
        orig_sections = parse_chapter_sections(chapter_file.read_text(encoding="utf-8"))

        new_mechanics = (
            "We replaced the mechanical gears with an asynchronous event broker.\n"
            "Cycle time dropped from 4 hours to 12 minutes."
        )

        chap_path, rev_info = revise_chapter_section(
            idea_dir=ideas_root / idea.id,
            section="mechanics",
            new_content=new_mechanics,
            reviewer="Avi",
            notes="Updated mechanics with event broker empirical observations.",
        )

        assert chap_path == chapter_file
        assert rev_info["section"] == "mechanics"

        # Read revised chapter
        rev_sections = parse_chapter_sections(chapter_file.read_text(encoding="utf-8"))
        assert rev_sections["mechanics"].strip() == new_mechanics.strip()

        # Other sections MUST remain untouched
        assert rev_sections["header"] == orig_sections["header"]
        assert rev_sections["lead_punch"] == orig_sections["lead_punch"]
        assert rev_sections["economics"] == orig_sections["economics"]
        assert rev_sections["hype"] == orig_sections["hype"]
        assert rev_sections["takeaways"] == orig_sections["takeaways"]

        # Check meta.yaml state
        meta_file = ideas_root / idea.id / "meta.yaml"
        meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_data.get("human_modified") is True
        assert meta_data.get("review_status") == "needs_revision"
        assert meta_data.get("stage") == "human_review"
        assert "revisions" in meta_data
        assert len(meta_data["revisions"]) >= 1
        last_rev = meta_data["revisions"][-1]
        assert last_rev["section"] == "mechanics"
        assert last_rev["reviewed_by"] == "Avi"
        assert "event broker" in last_rev["notes"]


def test_revise_chapter_section_append() -> None:
    """Verify append=True adds content to existing section rather than clobbering."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea()
        provision_idea(idea, ideas_root)
        chapter_file, _ = draft_book_chapter(idea, ideas_root, force=True)
        orig_sections = parse_chapter_sections(chapter_file.read_text(encoding="utf-8"))

        additional_note = "\n\n> [!TIP]\n> Always verify telemetry before promoting to production."
        revise_chapter_section(
            idea_dir=ideas_root / idea.id,
            section="gears",  # using alias
            new_content=additional_note,
            append=True,
        )

        rev_sections = parse_chapter_sections(chapter_file.read_text(encoding="utf-8"))
        assert orig_sections["mechanics"].strip() in rev_sections["mechanics"]
        assert "Always verify telemetry" in rev_sections["mechanics"]


def test_revise_unknown_section_raises_error() -> None:
    """Verify unknown section raises ValueError with helpful message."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea()
        provision_idea(idea, ideas_root)
        draft_book_chapter(idea, ideas_root, force=True)

        with pytest.raises(ValueError, match="Unknown section"):
            revise_chapter_section(
                idea_dir=ideas_root / idea.id,
                section="non_existent_section",
                new_content="something",
            )


def test_cli_revise_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify `ideas revise` CLI command updates section and executes downstream syndication."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea("idea-001")
        provision_idea(idea, ideas_root)
        chapter_file, _ = draft_book_chapter(idea, ideas_root, force=True)

        parser = build_parser()
        args = parser.parse_args(
            [
                "revise",
                "--idea",
                "idea-001",
                "--section",
                "takeaways",
                "--content",
                "- **Measure cycle time first**: Track lead time to changes.\n- **Verify contracts**: Enforce test fixtures.",
                "--notes",
                "Streamlined takeaways for clarity",
                "--reviewer",
                "Avi",
            ]
        )

        # Patch get_default_paths in both the legacy shim and the new command module
        import services.cli.commands.revise as revise_cmd
        from services.ingestion import cli

        orig_paths = cli.get_default_paths()

        def _paths():
            return (orig_paths[0], orig_paths[1], orig_paths[2], ideas_root)

        monkeypatch.setattr(cli, "get_default_paths", _paths)
        monkeypatch.setattr(revise_cmd, "get_default_paths", _paths)

        exit_code = handle_revise_command(args)
        assert exit_code == 0

        # Verify chapter was updated
        sections = parse_chapter_sections(chapter_file.read_text(encoding="utf-8"))
        assert "Measure cycle time first" in sections["takeaways"]

        # Verify meta.yaml updated
        meta_file = ideas_root / idea.id / "meta.yaml"
        meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_data.get("human_modified") is True
        assert meta_data.get("review_status") == "needs_revision"


def test_cli_revise_with_syndication(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify `ideas revise --syndicate` updates chapter and regenerates downstream blog and social."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea("idea-001")
        provision_idea(idea, ideas_root)
        draft_book_chapter(idea, ideas_root, force=True)

        parser = build_parser()
        args = parser.parse_args(
            [
                "revise",
                "--idea",
                "idea-001",
                "--section",
                "takeaways",
                "--content",
                "- **Measure cycle time first**: Track lead time to changes.\n- **Verify contracts**: Enforce test fixtures.",
                "--syndicate",
            ]
        )

        import services.cli.commands.revise as revise_cmd
        from services.ingestion import cli

        orig_paths = cli.get_default_paths()

        def _paths():
            return (orig_paths[0], orig_paths[1], orig_paths[2], ideas_root)

        monkeypatch.setattr(cli, "get_default_paths", _paths)
        monkeypatch.setattr(revise_cmd, "get_default_paths", _paths)

        exit_code = handle_revise_command(args)

        assert exit_code == 0

        # Verify blog and linkedin posts exist and contain the revised takeaway
        blog_file = ideas_root / idea.id / "blog" / "post.md"
        assert blog_file.is_file()
        blog_content = blog_file.read_text(encoding="utf-8")
        assert "Measure cycle time first" in blog_content

        linkedin_file = ideas_root / idea.id / "blog" / "linkedin.md"
        assert linkedin_file.is_file()
        linkedin_content = linkedin_file.read_text(encoding="utf-8")
        assert "Measure cycle time first" in linkedin_content
