"""Typst compilation driver for single chapters and aggregated books."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.typesetting.translator import (
    markdown_to_volume_chapter_body,
    translate_chapter_to_typst,
)
from services.typesetting.volumes import VolumeConfig, load_volumes_config


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
    chapter_order: list[str] | None = None,
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

    if chapter_order:
        for seq_idx, idea_id in enumerate(chapter_order, start=1):
            idea_dir = ideas_root / idea_id
            if not idea_dir.is_dir():
                continue
            book_dir = idea_dir / "book"
            chapter_md = book_dir / "chapter.md"
            chapter_body = book_dir / "chapter-body.typ"
            standalone_typ = book_dir / "chapter.typ"
            if chapter_md.is_file():
                if not chapter_body.is_file() or force:
                    translate_chapter_to_typst(
                        chapter_md_path=chapter_md,
                        output_body_path=chapter_body,
                        output_standalone_path=standalone_typ,
                        idea_id=idea_dir.name,
                        title=idea_dir.name,
                    )
                found_chapters.append((seq_idx, idea_dir.name, chapter_body))
    else:
        candidates: list[tuple[int, str, Path]] = []
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
                candidates.append((num, idea_dir.name, chapter_body))

        # Sort chapters in ascending numerical order, then name
        candidates.sort(key=lambda x: (x[0], x[1]))
        found_chapters = [
            (idx, name, path) for idx, (_, name, path) in enumerate(candidates, start=1)
        ]

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


def compile_volume_pdf(
    volume: VolumeConfig,
    ideas_root: Path,
    repo_root: Path,
    output_pdf_override: Path | None = None,
    force: bool = False,
) -> tuple[Path, int]:
    """Compile a declarative multi-volume book specification to PDF via Typst.

    Handles TASK-017 / REQ-BOK-005 extended:
    Dynamically generates volume master Typst document and chapter fragments,
    rendering part divider pages, dynamic chapter numbering, running headers,
    and table of contents adhering to config/volumes.yaml.
    """
    if output_pdf_override:
        pdf_dest: Path = output_pdf_override.resolve()
    else:
        pdf_dest = (repo_root / volume.output_pdf).resolve()

    pdf_dest.parent.mkdir(parents=True, exist_ok=True)
    volume_typ: Path = pdf_dest.parent / f"{volume.id}.typ"
    intermediates_dir: Path = pdf_dest.parent / "_volumes" / volume.id
    intermediates_dir.mkdir(parents=True, exist_ok=True)

    # Validate all chapters exist before starting compilation
    for part in volume.parts:
        for chapter_ref in part.chapters:
            idea_dir = ideas_root / chapter_ref.idea_id
            chapter_md = idea_dir / "book" / "chapter.md"
            if not chapter_md.is_file():
                raise FileNotFoundError(
                    f"Chapter manuscript not found for '{chapter_ref.idea_id}' at {chapter_md}. "
                    f"Please draft the chapter before compiling volume '{volume.id}'."
                )

    brand_import = (
        f"/{volume.brand.lstrip('/')}" if not volume.brand.startswith("/") else volume.brand
    )
    clean_title = volume.title.replace('"', '\\"')
    clean_subtitle = volume.subtitle.replace('"', '\\"')

    lines: list[str] = [
        f'#import "{brand_import}": plandek-doc, plandek-contents, plandek-part-divider, plandek-endpiece, plandek-orange, plandek-light, plandek-dark, plandek-gray\n',
        "#show: plandek-doc.with(",
        f'  title: "{clean_title}",',
        f'  subtitle: "{clean_subtitle}",',
        '  date: "2026",',
        ")\n",
        "#plandek-contents(depth: 2)\n",
    ]

    seq = 1
    for part_idx, part in enumerate(volume.parts, start=1):
        if ":" in part.title:
            label, p_title = [s.strip() for s in part.title.split(":", 1)]
        else:
            label = f"Part {part_idx}"
            p_title = part.title

        clean_label = label.replace('"', '\\"')
        clean_p_title = p_title.replace('"', '\\"')

        lines.append(
            f'#plandek-part-divider(\n  label: "{clean_label}",\n  title: "{clean_p_title}",\n)\n'
        )

        if part.description:
            clean_desc = part.description.replace('"', '\\"')
            lines.append(
                f'#align(center)[\n  #block(width: 85%, inset: (y: 1.5em))[\n    #set text(size: 11pt, style: "italic", fill: plandek-gray)\n    {clean_desc}\n  ]\n]\n'
            )

        for chapter_ref in part.chapters:
            idea_dir = ideas_root / chapter_ref.idea_id
            chapter_md = idea_dir / "book" / "chapter.md"

            if chapter_ref.chapter_title_override:
                chapter_title = chapter_ref.chapter_title_override
            else:
                meta_file = idea_dir / "meta.yaml"
                chapter_title = ""
                if meta_file.is_file():
                    try:
                        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
                        if isinstance(meta_dict, dict):
                            chapter_title = str(meta_dict.get("title", "")).strip()
                    except Exception:
                        pass
                if not chapter_title:
                    chapter_title = chapter_ref.idea_id

            illus_file = idea_dir / "assets" / "illustration.png"
            if not illus_file.is_file():
                illus_file = idea_dir / "assets" / "illustration.webp"

            if illus_file.is_file():
                try:
                    rel_to_repo = illus_file.resolve().relative_to(repo_root.resolve())
                    illustration_root_path = f"/{rel_to_repo.as_posix()}"
                except ValueError:
                    illustration_root_path = illus_file.resolve().as_posix()
            else:
                illustration_root_path = None

            frag_name = f"chapter-{seq:03d}-{chapter_ref.idea_id}.typ"
            frag_path = intermediates_dir / frag_name

            if not frag_path.is_file() or force:
                md_text = chapter_md.read_text(encoding="utf-8")
                frag_content = markdown_to_volume_chapter_body(
                    markdown_content=md_text,
                    idea_id=chapter_ref.idea_id,
                    chapter_num=seq,
                    title=chapter_title,
                    volume_title=volume.title,
                    illustration_root_path=illustration_root_path,
                )
                temp_frag = intermediates_dir / f".{frag_name}.tmp"
                temp_frag.write_text(frag_content, encoding="utf-8")
                temp_frag.replace(frag_path)

            rel_include = f"_volumes/{volume.id}/{frag_name}"
            lines.append(f'#include "{rel_include}"\n')
            seq += 1

    lines.append('#plandek-endpiece(contact: "https://withineve.com")\n')

    temp_master = pdf_dest.parent / f".{volume_typ.name}.tmp"
    temp_master.write_text("\n".join(lines), encoding="utf-8")
    temp_master.replace(volume_typ)

    success, err = run_typst_compile(volume_typ, pdf_dest, repo_root)
    if not success:
        raise RuntimeError(f"Failed to compile volume '{volume.id}' PDF: {err}")

    return pdf_dest, seq - 1


def compile_all_volumes(
    config_path: Path,
    ideas_root: Path,
    repo_root: Path,
    force: bool = False,
) -> dict[str, tuple[Path, int]]:
    """Compile all volumes defined in declarative volumes configuration."""
    volumes = load_volumes_config(config_path)
    results: dict[str, tuple[Path, int]] = {}
    for vol_id, volume in volumes.items():
        pdf_path, total = compile_volume_pdf(
            volume=volume,
            ideas_root=ideas_root,
            repo_root=repo_root,
            force=force,
        )
        results[vol_id] = (pdf_path, total)
    return results
