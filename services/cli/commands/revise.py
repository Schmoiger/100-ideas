"""Revise command: targeted section refinement for chapter manuscript."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from services.cli._shared import get_default_paths, get_repo_root


def handle_revise_command(args: argparse.Namespace) -> int:
    """Handle ``revise`` subcommand: targeted refinement of specific document sections (TASK-019)."""
    from services.ingestion.provisioner import load_or_provision_idea
    from services.typesetting.revision import revise_chapter_section

    repo_root: Path = get_repo_root()
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    if not args.idea:
        print("Error: Specify --idea <id>", file=sys.stderr)
        return 1

    target_id: str = f"idea-{int(args.idea):03d}" if str(args.idea).isdigit() else str(args.idea)
    idea_dir: Path = ideas_dir / target_id

    content: str = args.content or ""
    if getattr(args, "from_file", None):
        from_path = Path(args.from_file)
        if not from_path.is_file():
            print(f"Error: Content file not found at {from_path}", file=sys.stderr)
            return 1
        content = from_path.read_text(encoding="utf-8")

    if not content:
        print("Error: Provide revision content via --content or --from-file", file=sys.stderr)
        return 1

    try:
        chapter_file, rev_info = revise_chapter_section(
            idea_dir=idea_dir,
            section=args.section,
            new_content=content,
            reviewer=getattr(args, "reviewer", "Avi"),
            notes=getattr(args, "notes", ""),
            append=getattr(args, "append", False),
        )
        print(
            f"[{target_id}] Successfully revised section '{rev_info['section']}' in {chapter_file.name}:"
        )
        print(f"  Reviewer: {rev_info['reviewed_by']}")
        print(f"  Notes:    {rev_info['notes']}")
        print("  Status:   human_modified=True, review_status=needs_revision")

        if getattr(args, "syndicate", False):
            from services.publishing.pipeline import process_blog_and_social

            print(f"Re-syndicating downstream blog and social channels for {target_id}...")
            process_blog_and_social(
                idea_id_or_num=target_id,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_blog=True,
                do_social=True,
                force=True,
                overwrite_manual=True,
            )
            print("  ✓ Syndication complete: blog/post.md and blog/linkedin.md updated.")

        if getattr(args, "typeset", False):
            from services.typesetting.compiler import compile_chapter_pdf

            idea = load_or_provision_idea(
                idea_id_or_num=target_id,
                ideas_root=ideas_dir,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
            )
            print(f"Compiling Typst PDF preview for {target_id}...")
            pdf_path, success, err = compile_chapter_pdf(
                idea=idea,
                ideas_root=ideas_dir,
                repo_root=repo_root,
                force=True,
            )
            if success:
                print(f"  ✓ PDF preview compiled: {pdf_path}")
            else:
                print(f"  ✗ PDF compilation failed: {err}", file=sys.stderr)

        return 0
    except Exception as exc:
        print(f"Error revising {target_id}: {exc}", file=sys.stderr)
        return 1
