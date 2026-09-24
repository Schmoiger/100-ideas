"""Smoke tests for Book Mode and Typst Typesetting Subsystem."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from services.enrichment.visuals import create_editorial_png
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.typesetting.compiler import compile_aggregated_book, compile_chapter_pdf
from services.typesetting.drafter import draft_book_chapter
from services.typesetting.pipeline import process_book_chapter
from services.typesetting.translator import markdown_to_typst_body

HAS_TYPST = shutil.which("typst") is not None


def _create_test_idea(idea_id: str = "idea-001") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Software Development as the Binding Enterprise Growth Constraint",
        synopsis="Engineering capacity cannot keep pace with business demand when bound by manual developer bandwidth.",
        tags=["adlc", "devx", "theory-of-constraints"],
    )


def test_author_persona_drafter() -> None:
    """Verify chapter drafter produces manuscript adhering to author persona."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-001")
        provision_idea(idea, ideas_root)

        chapter_path, generated = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            force=False,
        )

        assert generated is True
        assert chapter_path.is_file()
        content = chapter_path.read_text(encoding="utf-8")

        # Verify persona structural requirements
        assert "# Chapter 1:" in content
        assert "## The Unvarnished Reality" in content
        assert "## Where the Gears Bind" in content
        assert "> [!NOTE]" in content
        assert "## The Economic Equation & Trade-offs" in content
        assert "| Operational Dimension |" in content
        assert "## Puncturing the Hype" in content
        assert "## Actionable Takeaways" in content
        assert "- **" in content

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-001" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_dict.get("chapter_draft") == "book/chapter.md"


def test_markdown_to_typst_translator() -> None:
    """Verify translation of markdown chapter into Typst markup."""
    sample_md = """# Chapter 1: The Binding Constraint

*Chapter 1 · 100 Ideas*

![Editorial illustration](../assets/illustration.png)

## The Unvarnished Reality

The cold reality is simple.

> [!NOTE]
> **Core Principle**: Flow over syntax.

| Column A | Column B |
|---|---|
| Val 1 | Val 2 |

- **First action**: Do this.
"""
    typst_body = markdown_to_typst_body(sample_md, idea_id="idea-001")

    assert "= Chapter 1: The Binding Constraint" in typst_body
    assert "_Chapter 1 · 100 Ideas_" in typst_body
    assert 'image("../assets/illustration.png"' in typst_body
    assert "== The Unvarnished Reality" in typst_body
    assert "#block(" in typst_body
    assert 'fill: rgb("#f1f5f9")' in typst_body
    assert "#table(" in typst_body
    assert "[Val 1], [Val 2]" in typst_body
    assert "- *First action*: Do this." in typst_body


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI binary not available in PATH")
def test_typst_chapter_compilation() -> None:
    """Verify compiling a single chapter into publication PDF via Typst CLI."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-002")
        provision_idea(idea, ideas_root)

        # Place a mock illustration
        assets_dir = ideas_root / "idea-002" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        img_bytes = create_editorial_png("test:idea-002", width=400, height=225)
        (assets_dir / "illustration.png").write_bytes(img_bytes)

        # Draft chapter
        draft_book_chapter(idea, ideas_root, force=True)

        # Compile PDF
        pdf_path, compiled = compile_chapter_pdf(
            idea=idea,
            ideas_root=ideas_root,
            repo_root=repo_root,
            force=True,
        )

        assert compiled is True
        assert pdf_path.is_file()
        pdf_bytes = pdf_path.read_bytes()
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 1000

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-002" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_dict.get("chapter_pdf") == "book/chapter.pdf"


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI binary not available in PATH")
def test_aggregated_book_compilation() -> None:
    """Verify aggregating multiple chapters into unified book volume with TOC."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        book_output_dir = Path(tmp_dir) / "book"
        ideas_root.mkdir(parents=True)

        # Create two ideas
        for i in [1, 2]:
            idea_id = f"idea-{i:03d}"
            idea = _create_test_idea(idea_id)
            provision_idea(idea, ideas_root)
            assets_dir = ideas_root / idea_id / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (assets_dir / "illustration.png").write_bytes(
                create_editorial_png(f"test:{idea_id}", width=200, height=100)
            )
            draft_book_chapter(idea, ideas_root, force=True)

        # Compile aggregated book
        book_pdf, total_chapters = compile_aggregated_book(
            ideas_root=ideas_root,
            repo_root=repo_root,
            output_dir=book_output_dir,
            force=True,
        )

        assert total_chapters == 2
        assert book_pdf.is_file()
        pdf_bytes = book_pdf.read_bytes()
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 2000


def test_pipeline_idempotency() -> None:
    """Verify running chapter processing twice skips generation unless force=True."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        catalog_path = Path(tmp_dir) / "cat.md"
        snapshot_path = Path(tmp_dir) / "snap.md"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-005")
        provision_idea(idea, ideas_root)

        # Run 1: generated & compiled (if typst available)
        run1 = process_book_chapter(
            idea_id_or_num="idea-005",
            ideas_root=ideas_root,
            repo_root=repo_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_draft=True,
            do_compile=HAS_TYPST,
            force=False,
        )
        assert run1["draft_generated"] is True
        assert run1["pdf_compiled"] is HAS_TYPST

        # Run 2: cached / skipped
        run2 = process_book_chapter(
            idea_id_or_num="idea-005",
            ideas_root=ideas_root,
            repo_root=repo_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_draft=True,
            do_compile=HAS_TYPST,
            force=False,
        )
        assert run2["draft_generated"] is False
        assert run2["pdf_compiled"] is False


@pytest.mark.skipif(not HAS_TYPST, reason="Typst binary not installed in test environment")
def test_typst_compilation_latency() -> None:
    """Verify Typst PDF chapter compilation time meets NFR-TOK-003 (< 2.0s per chapter)."""
    import time

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-001")
        provision_idea(idea, ideas_root)
        draft_book_chapter(idea, ideas_root, force=True)

        start_time = time.perf_counter()
        pdf_path, compiled = compile_chapter_pdf(
            idea=idea,
            ideas_root=ideas_root,
            repo_root=repo_root,
            force=True,
        )
        elapsed = time.perf_counter() - start_time

        assert compiled is True
        assert pdf_path.is_file()
        assert elapsed < 2.0, f"Compilation took {elapsed:.2f}s, exceeding 2.0s limit (NFR-TOK-003)"
