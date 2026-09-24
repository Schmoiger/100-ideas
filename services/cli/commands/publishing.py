"""Publishing commands: blog and social post generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from services.cli._shared import (
    get_default_paths,
    get_repo_root,
    resolve_ideas_to_process,
)


def handle_blog_command(args: argparse.Namespace) -> int:
    """Handle ``blog`` subcommand: draft Hostinger-ready blog post with optional CMS adaptation."""
    from services.publishing.pipeline import process_blog_and_social

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        try:
            print(f"[{idx}/{total}] Generating blog post for idea {idea_target}...")
            results = process_blog_and_social(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_blog=True,
                do_social=False,
                cms_platform=args.platform,
                force=args.force,
                overwrite_manual=getattr(args, "overwrite_manual", False),
            )
            status_str: str = "generated" if results.get("blog_generated") else "cached (skipped)"
            print(f"Blog Post completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  Post Markdown: {results['blog_post']} [{status_str}]")

            # TASK-021: Emit explicit warning when falling back to synopsis
            syndicated_from = results.get("syndicated_from", "")
            if syndicated_from == "synopsis_fallback":
                print(
                    f"  Warning: Idea {idea_target} has not drafted book/chapter.md. "
                    "Generating blog post from raw synopsis fallback.",
                    file=sys.stderr,
                )

            if "cms_export" in results:
                exp = results["cms_export"]
                print(f"  CMS Adapter:   {exp['platform']} ({exp['format']})")
        except Exception as exc:
            print(f"Error processing blog for {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_social_command(args: argparse.Namespace) -> int:
    """Handle ``social`` subcommand: generate companion LinkedIn social post."""
    from services.publishing.pipeline import process_blog_and_social

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        try:
            print(f"[{idx}/{total}] Generating social companion post for idea {idea_target}...")
            results = process_blog_and_social(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_blog=False,
                do_social=True,
                force=args.force,
                overwrite_manual=getattr(args, "overwrite_manual", False),
            )
            status_str: str = "generated" if results.get("social_generated") else "cached (skipped)"
            print(f"Social Post completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  LinkedIn Post: {results['linkedin_post']} [{status_str}]")

            # TASK-021: Emit explicit warning when falling back to synopsis
            syndicated_from = results.get("syndicated_from", "")
            if syndicated_from == "synopsis_fallback":
                print(
                    f"  Warning: Idea {idea_target} has not drafted book/chapter.md. "
                    "Generating social post from raw synopsis fallback.",
                    file=sys.stderr,
                )
        except Exception as exc:
            print(f"Error processing social for {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_pipeline_command(args: argparse.Namespace) -> int:
    """Handle ``pipeline`` subcommand: run end-to-end publishing pipeline."""
    from services.cli._shared import confirm_batch_execution
    from services.enrichment.pipeline import enrich_idea
    from services.publishing.pipeline import process_blog_and_social
    from services.typesetting.pipeline import process_book_chapter

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    resources_dir: Path = repo_root / "artefacts" / "content" / "resources"

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    if not confirm_batch_execution(
        ideas_to_process,
        "pipeline",
        model_name="gemini-2.5-pro",
        yes=getattr(args, "yes", False),
    ):
        print("Batch execution cancelled by user.")
        return 0

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        print("\n==========================================")
        print(f"[{idx}/{total}] Pipeline processing idea {idea_target}")
        print("==========================================")
        try:
            ow_manual = getattr(args, "overwrite_manual", False)
            f_llm = getattr(args, "force_llm", False)
            d_run = getattr(args, "dry_run", False)

            print("  Phase 1/5: Research and Visual Enrichment...")
            enrich_res = enrich_idea(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                resources_root=resources_dir,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_research=True,
                do_visuals=True,
                force=args.force,
                force_llm=f_llm,
                dry_run=d_run,
                overwrite_manual=ow_manual,
            )

            print("  Phase 2/5: Drafting Book Chapter...")
            process_book_chapter(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_draft=True,
                do_compile=False,
                force=args.force,
                force_llm=f_llm,
                dry_run=d_run,
                overwrite_manual=ow_manual,
            )

            print("  Phase 3/5: Compiling Typst Chapter PDF...")
            process_book_chapter(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_draft=False,
                do_compile=True,
                force=args.force,
                overwrite_manual=ow_manual,
            )

            print("  Phase 4/5: Generating Blog Post...")
            process_blog_and_social(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_blog=True,
                do_social=False,
                cms_platform=args.platform,
                force=args.force,
                overwrite_manual=ow_manual,
            )

            print("  Phase 5/5: Generating Social Companion Post...")
            process_blog_and_social(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_blog=False,
                do_social=True,
                force=args.force,
                overwrite_manual=ow_manual,
            )

            print(f"Completed pipeline for [{enrich_res['idea_id']}] '{enrich_res['title']}'.")
        except Exception as exc:
            print(f"Pipeline error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0
