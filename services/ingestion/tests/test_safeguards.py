"""Unit and integration tests for human_modified manual edit safeguards and CLI flags."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from services.ingestion.cli import handle_mark_edited_command
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.ingestion.safeguards import (
    IdeaLockedError,
    ManualEditProtectionError,
    check_manual_edit_safeguard,
)
from services.publishing.drafter import draft_blog_post
from services.typesetting.drafter import draft_book_chapter


def test_check_manual_edit_safeguard_locked(tmp_path: Path) -> None:
    """Verify locked idea raises IdeaLockedError."""
    idea = IdeaRecord(
        id="idea-001",
        title="Locked Idea",
        synopsis="Testing lock enforcement.",
        locked=True,
    )
    target = tmp_path / "notes.md"
    with pytest.raises(IdeaLockedError):
        check_manual_edit_safeguard(target, idea)


def test_check_manual_edit_safeguard_human_modified(tmp_path: Path) -> None:
    """Verify human_modified file raises ManualEditProtectionError on existing file without overwrite_manual."""
    idea = IdeaRecord(
        id="idea-002",
        title="Human Polished Idea",
        synopsis="Testing manual edit protection.",
        human_modified=True,
    )
    target = tmp_path / "chapter.md"
    target.write_text("# Human Edits Here", encoding="utf-8")

    # Regular force must NOT bypass human_modified protection
    with pytest.raises(ManualEditProtectionError) as exc_info:
        check_manual_edit_safeguard(target, idea, force=True, overwrite_manual=False)
    assert "Refusing to overwrite manual edits" in str(exc_info.value)
    assert "--overwrite-manual" in str(exc_info.value)

    # With overwrite_manual=True, it succeeds without error
    check_manual_edit_safeguard(target, idea, force=True, overwrite_manual=True)


def test_drafter_refuses_to_overwrite_human_modified_chapter(tmp_path: Path) -> None:
    """Verify draft_book_chapter aborts when chapter.md was manually edited (DEF-005)."""
    idea = IdeaRecord(
        id="idea-003",
        title="Manual Manuscript",
        synopsis="Testing drafter protection.",
        human_modified=True,
    )
    p_dir = provision_idea(idea, tmp_path)
    chapter_file = p_dir / "book" / "chapter.md"
    chapter_file.write_text("# Curated Human Prose", encoding="utf-8")

    # Calling with force=True must abort with ManualEditProtectionError
    with pytest.raises(ManualEditProtectionError):
        draft_book_chapter(
            idea=idea,
            ideas_root=tmp_path,
            force=True,
            overwrite_manual=False,
        )

    # Content unchanged
    assert chapter_file.read_text(encoding="utf-8") == "# Curated Human Prose"

    # Calling with overwrite_manual=True succeeds
    _, was_gen = draft_book_chapter(
        idea=idea,
        ideas_root=tmp_path,
        force=True,
        overwrite_manual=True,
    )
    assert was_gen is True
    assert "Curated Human Prose" not in chapter_file.read_text(encoding="utf-8")


def test_blog_drafter_refuses_to_overwrite_human_modified_post(tmp_path: Path) -> None:
    """Verify draft_blog_post aborts when post.md was manually edited."""
    idea = IdeaRecord(
        id="idea-004",
        title="Manual Blog Post",
        synopsis="Testing blog drafter protection.",
        human_modified=True,
    )
    p_dir = provision_idea(idea, tmp_path)
    post_file = p_dir / "blog" / "post.md"
    post_file.write_text("# Curated Blog Article", encoding="utf-8")

    # Refuses overwrite
    with pytest.raises(ManualEditProtectionError):
        draft_blog_post(
            idea=idea,
            ideas_root=tmp_path,
            force=True,
            overwrite_manual=False,
        )

    # Overwrite manual allowed
    draft_blog_post(
        idea=idea,
        ideas_root=tmp_path,
        force=True,
        overwrite_manual=True,
    )


def test_cli_mark_edited_and_unmark(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify mark-edited command updates meta.yaml human_modified and review_notes."""
    idea = IdeaRecord(
        id="idea-005",
        title="CLI Safeguard Test",
        synopsis="Testing CLI mark-edited.",
    )
    p_dir = provision_idea(idea, tmp_path)
    meta_file = p_dir / "meta.yaml"

    # Monkeypatch get_default_paths to point to tmp_path
    def _paths():
        return (
            tmp_path / "100-ideas.md",
            tmp_path / "snapshot.md",
            tmp_path / "inbox.md",
            tmp_path,
        )

    monkeypatch.setattr("services.ingestion.cli.get_default_paths", _paths)
    monkeypatch.setattr("services.cli.commands.review.get_default_paths", _paths)

    # Mark as edited
    args = argparse.Namespace(idea="idea-005", notes="Polished intro section", unmark=False)
    rc = handle_mark_edited_command(args)
    assert rc == 0

    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["human_modified"] is True
    assert meta["editorial_quality"]["review_notes"] == "Polished intro section"

    # Unmark
    args_unmark = argparse.Namespace(idea="idea-005", notes="", unmark=True)
    rc_unmark = handle_mark_edited_command(args_unmark)
    assert rc_unmark == 0

    meta_after = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta_after["human_modified"] is False
