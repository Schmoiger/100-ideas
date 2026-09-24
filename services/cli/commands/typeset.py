"""Typeset commands: draft (book chapter) and typeset (Typst PDF compilation)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from services.cli._shared import (
    confirm_batch_execution,
    get_default_paths,
    get_repo_root,
    resolve_ideas_to_process,
)


def handle_draft_command(args: argparse.Namespace) -> int:
    """Handle ``draft`` subcommand: draft book chapter adhering to author persona."""
    from services.typesetting.pipeline import process_book_chapter

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    if not confirm_batch_execution(
        ideas_to_process,
        "drafting",
        model_name="gemini-2.5-pro",
        yes=getattr(args, "yes", False),
    ):
        print("Batch execution cancelled by user.")
        return 0

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        try:
            print(f"[{idx}/{total}] Drafting book chapter for idea {idea_target}...")
            results = process_book_chapter(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_draft=True,
                do_compile=False,
                force=args.force,
                force_llm=getattr(args, "force_llm", False),
                dry_run=getattr(args, "dry_run", False),
                overwrite_manual=getattr(args, "overwrite_manual", False),
            )
            status_str: str = "generated" if results.get("draft_generated") else "cached (skipped)"
            print(f"Drafting completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  Chapter Draft: {results['chapter_md']} [{status_str}]")
        except Exception as exc:
            print(f"Drafting error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_typeset_command(args: argparse.Namespace) -> int:
    """Handle ``typeset`` subcommand: compile single chapter, aggregated book, or volumes via Typst."""
    from services.typesetting.pipeline import (
        process_aggregated_book,
        process_all_volumes,
        process_book_chapter,
        process_volume_book,
    )
    from services.typesetting.volumes import get_default_volumes_path

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    book_output_dir: Path = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else repo_root / "artefacts" / "content" / "book"
    )
    volumes_config_path: Path = (
        Path(args.volumes_config).resolve()
        if getattr(args, "volumes_config", None)
        else get_default_volumes_path(repo_root)
    )

    volume_arg = getattr(args, "volume", None)
    all_volumes_arg = getattr(args, "all_volumes", False)

    if not args.idea and not args.all and not volume_arg and not all_volumes_arg:
        print(
            "Error: Specify either --idea <id>, --all, --volume <id>, or --all-volumes.",
            file=sys.stderr,
        )
        return 1

    try:
        if args.idea:
            results = process_book_chapter(
                idea_id_or_num=args.idea,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_draft=True,
                do_compile=True,
                force=args.force,
                force_llm=getattr(args, "force_llm", False),
                dry_run=getattr(args, "dry_run", False),
                overwrite_manual=getattr(args, "overwrite_manual", False),
            )
            status_str: str = "compiled" if results.get("pdf_compiled") else "cached (skipped)"
            print(f"Typesetting completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  Chapter PDF: {results['chapter_pdf']} [{status_str}]")

        if args.all:
            res_book = process_aggregated_book(
                ideas_root=ideas_dir,
                repo_root=repo_root,
                output_dir=book_output_dir,
                force=args.force,
            )
            print("Aggregated Book Compilation completed:")
            print(f"  Total Chapters Included: {res_book['total_chapters']}")
            print(f"  Publication PDF:         {res_book['book_pdf']}")

        if volume_arg:
            custom_out = (
                Path(args.output_dir).resolve() / f"{volume_arg}.pdf" if args.output_dir else None
            )
            res_vol = process_volume_book(
                volume_id=volume_arg,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                config_path=volumes_config_path,
                output_pdf_override=custom_out,
                force=args.force,
            )
            print(
                f"Volume Compilation completed for [{res_vol['volume_id']}] '{res_vol['title']}':"
            )
            print(f"  Total Chapters:  {res_vol['total_chapters']}")
            print(f"  Publication PDF: {res_vol['volume_pdf']}")

        if all_volumes_arg:
            res_vols = process_all_volumes(
                ideas_root=ideas_dir,
                repo_root=repo_root,
                config_path=volumes_config_path,
                force=args.force,
            )
            print(f"Multi-Volume Compilation completed ({len(res_vols)} volumes):")
            for vol_id, v_data in res_vols.items():
                print(
                    f"  [{vol_id}] {v_data['title']}: {v_data['total_chapters']} chapters -> {v_data['volume_pdf']}"
                )

        return 0
    except Exception as exc:
        print(f"Typesetting error: {exc}", file=sys.stderr)
        return 1
