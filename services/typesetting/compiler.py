"""Typst compilation driver for single chapters and aggregated books."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.typesetting.translator import translate_chapter_to_typst


def _extract_number(idea_id: str) -> int:
    """Extract integer number from idea ID (e.g. 'idea-042' -> 42)."""
    match = re.search(r"\d+", idea_id)
    return int(match.group()) if match else 1


def run_typst_compile(
    typst_src: Path,
    pdf_dest: Path,
    repo_root: Path,
) -> tuple[bool, str]:
    """Execute typst compile CLI command with project root isolation.

    Runs: typst compile --root {repo_root} {typst_src} {pdf_dest}
    """
    pdf_dest.parent.mkdir(parents=True, exist_ok=True)
    temp_pdf: Path = pdf_dest.parent / f".tmp.{pdf_dest.stem}.pdf"

    cmd: list[str] = [
        "typst",
        "compile",
        "--root",
        str(repo_root.resolve()),
        "--format",
        "pdf",
        str(typst_src.resolve()),
        str(temp_pdf.resolve()),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            if temp_pdf.is_file():
                temp_pdf.unlink()
            err_msg: str = proc.stderr.strip() or proc.stdout.strip() or "Unknown compilation error"
            return False, err_msg

        if not temp_pdf.is_file() or temp_pdf.stat().st_size == 0:
            return False, "Output PDF was not produced or is empty."

        temp_pdf.replace(pdf_dest)
        return True, ""
    except Exception as e:
        if temp_pdf.is_file():
            temp_pdf.unlink()
        return False, str(e)


def compile_chapter_pdf(
    idea: IdeaRecord,
    ideas_root: Path,
    repo_root: Path,
    force: bool = False,
) -> tuple[Path, bool]:
    """Ensure chapter.typ is translated and compile to book/chapter.pdf.

    Handles REQ-BOK-003 & REQ-BOK-004:
    Returns (pdf_path, was_compiled).
    """
    idea_dir: Path = ideas_root / idea.id
    book_dir: Path = idea_dir / "book"
    chapter_md: Path = book_dir / "chapter.md"
    chapter_body_typ: Path = book_dir / "chapter-body.typ"
    chapter_standalone_typ: Path = book_dir / "chapter.typ"
    chapter_pdf: Path = book_dir / "chapter.pdf"

    if not chapter_md.is_file():
        raise FileNotFoundError(f"Chapter manuscript not found: {chapter_md}")

    # Translate if typ files do not exist or force
    if not chapter_standalone_typ.is_file() or not chapter_body_typ.is_file() or force:
        translate_chapter_to_typst(
            chapter_md_path=chapter_md,
            output_body_path=chapter_body_typ,
            output_standalone_path=chapter_standalone_typ,
            idea_id=idea.id,
            title=idea.title,
        )

    # Compile if PDF missing or force
    if chapter_pdf.is_file() and not force:
        return chapter_pdf, False

    success, err = run_typst_compile(chapter_standalone_typ, chapter_pdf, repo_root)
    if not success:
        raise RuntimeError(f"Typst compilation failed for {idea.id}: {err}")

    # Update meta.yaml
    meta_file: Path = idea_dir / "meta.yaml"
    if meta_file.is_file():
        try:
            meta_data: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta_data, dict):
                meta_data["chapter_pdf"] = "book/chapter.pdf"
                temp_meta: Path = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True), encoding="utf-8"
                )
                temp_meta.replace(meta_file)
        except Exception:
            pass

    return chapter_pdf, True


def compile_aggregated_book(
    ideas_root: Path,
    repo_root: Path,
    output_dir: Path,
    book_title: str = "100 Ideas for Engineering Leaders",
    book_subtitle: str = "From Architecture to Autonomous Delivery",
    force: bool = False,
) -> tuple[Path, int]:
    """Compile aggregated multi-chapter book manuscript to PDF.

    Handles REQ-BOK-005:
    Collects all processed chapter bodies, synthesises master book.typ with TOC,
    and compiles to artefacts/content/book/100-ideas-book.pdf.
    Returns (book_pdf_path, total_chapters_included).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    master_typ: Path = output_dir / "100-ideas-book.typ"
    master_pdf: Path = output_dir / "100-ideas-book.pdf"

    # Find all idea directories with chapter.md or chapter-body.typ
    found_chapters: list[tuple[int, str, Path]] = []
    for idea_dir in ideas_root.iterdir():
        if not idea_dir.is_dir():
            continue
        book_dir = idea_dir / "book"
        chapter_md = book_dir / "chapter.md"
        chapter_body = book_dir / "chapter-body.typ"
        standalone_typ = book_dir / "chapter.typ"

        if chapter_md.is_file():
            num = _extract_number(idea_dir.name)
            # Ensure translation
            if not chapter_body.is_file() or force:
                translate_chapter_to_typst(
                    chapter_md_path=chapter_md,
                    output_body_path=chapter_body,
                    output_standalone_path=standalone_typ,
                    idea_id=idea_dir.name,
                    title=idea_dir.name,
                )
            found_chapters.append((num, idea_dir.name, chapter_body))

    # Sort chapters in ascending numerical order
    found_chapters.sort(key=lambda x: x[0])

    if not found_chapters:
        raise ValueError(f"No processed book chapters found in {ideas_root}")

    # Build master book.typ markup
    lines: list[str] = [
        '#import "/typst/brands/neutral.typ": plandek-doc, plandek-contents, plandek-endpiece, plandek-orange, plandek-light, plandek-dark\n',
        "#show: plandek-doc.with(",
        f'  title: "{book_title}",',
        f'  subtitle: "{book_subtitle}",',
        '  date: "2026",',
        ")\n",
        "= Introduction: The Industrialisation of Software Delivery\n",
        "Over the past twenty-five years, software engineering has evolved through successive waves ",
        "of methodology, tooling, and governance. Yet despite agile transformations, cloud-native infrastructure, ",
        "and modern DevOps pipelines, delivery velocity remains tightly bound by human developer bandwidth.\n\n",
        "This volume presents one hundred actionable architectural, organizational, and technological ideas ",
        "for navigating the generational transition to autonomous, agentic software delivery.\n\n",
        "#plandek-contents(depth: 2)\n",
    ]

    for num, idea_id, body_path in found_chapters:
        # Calculate relative path from output_dir to body_path
        # E.g. artefacts/content/book/ -> ../ideas/idea-001/book/chapter-body.typ
        rel_to_book: str = f"../ideas/{idea_id}/book/chapter-body.typ"
        lines.append(f'#include "{rel_to_book}"\n')

    lines.append('#plandek-endpiece(contact: "https://withineve.com")\n')

    # Atomic write of master typ
    temp_master: Path = output_dir / f".{master_typ.name}.tmp"
    temp_master.write_text("\n".join(lines), encoding="utf-8")
    temp_master.replace(master_typ)

    # Compile master PDF
    success, err = run_typst_compile(master_typ, master_pdf, repo_root)
    if not success:
        raise RuntimeError(f"Failed to compile aggregated book PDF: {err}")

    return master_pdf, len(found_chapters)
