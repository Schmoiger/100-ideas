"""High-level pipeline coordinator for Book Mode and Typst typesetting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.enrichment.pipeline import load_or_provision_idea
from services.ingestion.models import IdeaRecord
from services.typesetting.compiler import compile_aggregated_book, compile_chapter_pdf
from services.typesetting.drafter import draft_book_chapter


def process_book_chapter(
    idea_id_or_num: str | int,
    ideas_root: Path,
    repo_root: Path,
    catalog_path: Path,
    snapshot_path: Path,
    do_draft: bool = True,
    do_compile: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Execute end-to-end book drafting and typesetting for an idea.

    Handles REQ-BOK-001, REQ-BOK-002, REQ-BOK-003, REQ-BOK-004.
    """
    idea: IdeaRecord = load_or_provision_idea(
        idea_id_or_num=idea_id_or_num,
        ideas_root=ideas_root,
        catalog_path=catalog_path,
        snapshot_path=snapshot_path,
    )

    results: dict[str, Any] = {
        "idea_id": idea.id,
        "title": idea.title,
    }

    # 1. Draft chapter manuscript (REQ-BOK-001, REQ-BOK-002)
    if do_draft:
        chapter_md, draft_gen = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            force=force,
        )
        results["chapter_md"] = str(chapter_md)
        results["draft_generated"] = draft_gen

    # 2. Translate and compile PDF (REQ-BOK-003, REQ-BOK-004)
    if do_compile:
        chapter_pdf, pdf_gen = compile_chapter_pdf(
            idea=idea,
            ideas_root=ideas_root,
            repo_root=repo_root,
            force=force,
        )
        results["chapter_pdf"] = str(chapter_pdf)
        results["pdf_compiled"] = pdf_gen

    return results


def process_aggregated_book(
    ideas_root: Path,
    repo_root: Path,
    output_dir: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Compile aggregated multi-chapter book manuscript to single publication PDF.

    Handles REQ-BOK-005.
    """
    pdf_path, total = compile_aggregated_book(
        ideas_root=ideas_root,
        repo_root=repo_root,
        output_dir=output_dir,
        force=force,
    )
    return {
        "book_pdf": str(pdf_path),
        "total_chapters": total,
    }
