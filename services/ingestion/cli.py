"""CLI interface for Idea Ingestion and Selection Subsystem."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from services.ingestion.dedup import check_duplicate
from services.ingestion.models import IdeaRecord
from services.ingestion.parsers import parse_inbox_markdown, parse_markdown_table
from services.ingestion.provisioner import (
    load_existing_provisioned_ideas,
    provision_idea,
)
from services.ingestion.selector import select_ideas
from services.ingestion.sync import resolve_catalog_source, sync_catalog_source


def get_default_paths() -> tuple[Path, Path, Path, Path]:
    """Return default project paths for catalog, snapshot, inbox, and ideas directory."""
    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    catalog_path: Path = repo_root / "artefacts" / "product" / "100-ideas.md"
    snapshot_path: Path = repo_root / "artefacts" / "product" / "100-ideas.snapshot.md"
    inbox_path: Path = repo_root / "artefacts" / "product" / "inbox.md"
    ideas_dir: Path = repo_root / "artefacts" / "content" / "ideas"
    return catalog_path, snapshot_path, inbox_path, ideas_dir


def handle_sync_command(args: argparse.Namespace) -> int:
    """Handle `sync` subcommand: copies authoritative source to snapshot."""
    catalog_path, snapshot_path, _, _ = get_default_paths()
    src: Path = Path(args.source) if args.source else catalog_path
    dst: Path = Path(args.destination) if args.destination else snapshot_path

    try:
        synced: Path = sync_catalog_source(src, dst)
        print(f"Successfully synchronised catalog to {synced}")
        return 0
    except Exception as exc:
        print(f"Sync error: {exc}", file=sys.stderr)
        return 1


def handle_catalog_command(args: argparse.Namespace) -> int:
    """Handle `catalog` subcommand: parse, filter, and optionally provision ideas."""
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    try:
        resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
    except FileNotFoundError as err:
        print(f"Catalogue resolution error: {err}", file=sys.stderr)
        return 1

    records: list[IdeaRecord] = parse_markdown_table(resolved_src)
    if not records:
        print("No valid ideas parsed from catalogue table.", file=sys.stderr)
        return 1

    # Apply selector
    selected: list[IdeaRecord] = select_ideas(
        ideas=records,
        idea_spec=args.idea,
        range_spec=args.ideas,
        all_flag=args.all,
        tag=args.tag,
        domain=args.domain,
        query=args.query,
    )

    if not selected:
        print("No ideas matched the selection criteria.")
        return 0

    print(f"Selected {len(selected)} idea(s) from {resolved_src.name}:")
    for r in selected:
        print(f"  [{r.id}] {r.title}")

    if args.provision:
        print(f"\nProvisioning {len(selected)} idea(s) into {ideas_dir}...")
        for r in selected:
            provision_dir: Path = provision_idea(r, ideas_dir, force=args.force)
            print(f"  Provisioned: {r.id} -> {provision_dir}")
        print("Provisioning completed successfully.")

    return 0


def handle_inbox_command(args: argparse.Namespace) -> int:
    """Handle `inbox` subcommand: parse inbox.md, check duplicates, and provision."""
    catalog_path, snapshot_path, inbox_path, ideas_dir = get_default_paths()

    # Load all existing ideas to avoid ID collisions and detect duplicates
    existing_provisioned: list[IdeaRecord] = load_existing_provisioned_ideas(ideas_dir)

    # Determine highest existing idea number
    max_id_num: int = 100
    try:
        resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
        cat_records: list[IdeaRecord] = parse_markdown_table(resolved_src)
        if cat_records:
            max_id_num = max(max_id_num, len(cat_records))
    except Exception:
        pass

    for r in existing_provisioned:
        if r.id.startswith("idea-") and r.id[5:].isdigit():
            max_id_num = max(max_id_num, int(r.id[5:]))

    inbox_ideas: list[IdeaRecord] = parse_inbox_markdown(inbox_path, start_id=max_id_num + 1)
    if not inbox_ideas:
        print(f"No pending idea entries found in {inbox_path}.")
        return 0

    print(f"Found {len(inbox_ideas)} entry/entries in inbox:")
    for idea in inbox_ideas:
        is_dup, matched_rec, reason = check_duplicate(idea, existing_provisioned)
        dup_warning: str = f" [WARNING DUPLICATE: {reason}]" if is_dup else ""
        print(f"  [{idea.id}] {idea.title}{dup_warning}")

    if args.provision:
        print(f"\nProvisioning inbox ideas into {ideas_dir}...")
        for idea in inbox_ideas:
            is_dup, matched_rec, reason = check_duplicate(idea, existing_provisioned)
            if is_dup and not args.force:
                print(f"  Skipping {idea.title} ({reason}). Use --force to provision anyway.")
                continue
            p_dir: Path = provision_idea(idea, ideas_dir, force=args.force)
            print(f"  Provisioned: {idea.id} -> {p_dir}")
        print("Inbox provisioning complete.")

    return 0


def handle_add_command(args: argparse.Namespace) -> int:
    """Handle `add` subcommand: directly add an idea through CLI/chat interface."""
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()

    title: str = args.title.strip()
    synopsis: str = args.synopsis.strip()
    if not title or not synopsis:
        print("Error: Both --title and --synopsis must be non-empty strings.", file=sys.stderr)
        return 1

    tags: list[str] = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    source: str = args.source.strip() if args.source else ""

    # Load existing provisioned ideas
    existing_provisioned: list[IdeaRecord] = load_existing_provisioned_ideas(ideas_dir)

    max_id_num: int = 100
    try:
        resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
        cat_records: list[IdeaRecord] = parse_markdown_table(resolved_src)
        if cat_records:
            max_id_num = max(max_id_num, len(cat_records))
    except Exception:
        pass

    for r in existing_provisioned:
        if r.id.startswith("idea-") and r.id[5:].isdigit():
            max_id_num = max(max_id_num, int(r.id[5:]))

    new_idea = IdeaRecord(
        id=f"idea-{max_id_num + 1:03d}",
        title=title,
        synopsis=synopsis,
        source_reference=source,
        tags=tags,
    )

    # Check duplicates per REQ-ING-006
    is_dup, matched_rec, reason = check_duplicate(new_idea, existing_provisioned)
    if is_dup:
        print(f"Warning: Potential duplicate detected: {reason}")
        if not args.force:
            print(
                "Aborting idea intake. Re-run with --force to override duplicate detection.",
                file=sys.stderr,
            )
            return 1

    # Provision intermediate structure per REQ-ING-005
    p_dir: Path = provision_idea(new_idea, ideas_dir, force=args.force)
    print(f"Successfully provisioned idea '{new_idea.title}' [{new_idea.id}] at {p_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="ideas",
        description="100-Ideas Ingestion and Selection Subsystem CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # sync
    sync_p = subparsers.add_parser(
        "sync", help="Synchronise authoritative catalog to local snapshot"
    )
    sync_p.add_argument("--source", "-s", help="Source catalog path")
    sync_p.add_argument("--destination", "-d", help="Destination snapshot path")

    # catalog
    cat_p = subparsers.add_parser("catalog", help="Select and provision ideas from catalog")
    cat_p.add_argument("--idea", help="Single idea index (1) or ID (idea-001) or title")
    cat_p.add_argument("--ideas", help="Idea range (e.g. 1-5 or idea-001-idea-005)")
    cat_p.add_argument("--all", "-a", action="store_true", help="Select all ideas")
    cat_p.add_argument("--tag", help="Filter by tag")
    cat_p.add_argument("--domain", help="Filter by domain")
    cat_p.add_argument("--query", "-q", help="Search by query term")
    cat_p.add_argument(
        "--provision", "-p", action="store_true", help="Provision selected ideas into content store"
    )
    cat_p.add_argument(
        "--force", "-f", action="store_true", help="Force overwrite existing provisioned ideas"
    )

    # inbox
    inbox_p = subparsers.add_parser("inbox", help="Ingest ideas from inbox.md")
    inbox_p.add_argument(
        "--provision",
        "-p",
        action="store_true",
        help="Provision new inbox ideas into content store",
    )
    inbox_p.add_argument(
        "--force", "-f", action="store_true", help="Force provision even if duplicate detected"
    )

    # add
    add_p = subparsers.add_parser("add", help="Directly submit a new idea via CLI/Chat")
    add_p.add_argument("--title", "-t", required=True, help="Idea title")
    add_p.add_argument("--synopsis", "-s", required=True, help="Idea synopsis")
    add_p.add_argument("--tags", help="Comma-separated tags or domain")
    add_p.add_argument("--source", help="Source or reference notes")
    add_p.add_argument(
        "--force", "-f", action="store_true", help="Force add even if duplicate detected"
    )

    # enrich
    enrich_p = subparsers.add_parser(
        "enrich", help="Enrich idea with empirical research synthesis and visual illustrations"
    )
    enrich_p.add_argument("--idea", "-i", help="Idea ID (e.g. idea-001) or 1-based index (e.g. 1)")
    enrich_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Enrich all provisioned ideas sequentially in batch",
    )
    enrich_p.add_argument(
        "--research", "-r", action="store_true", help="Run research synthesis phase only"
    )
    enrich_p.add_argument(
        "--visuals", "-v", action="store_true", help="Run visual asset generation phase only"
    )
    enrich_p.add_argument(
        "--regenerate-image",
        action="store_true",
        help="Regenerate visual asset without touching research notes",
    )
    enrich_p.add_argument(
        "--refinement", help="Optional stylistic or metaphorical refinement prompt for visual asset"
    )
    enrich_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-generation of existing research or visual assets",
    )

    # Subcommand: draft (Book mode drafting)
    draft_p = subparsers.add_parser(
        "draft",
        help="Draft publication-ready book chapter for an idea (REQ-BOK-001, REQ-BOK-002)",
    )
    draft_p.add_argument(
        "--idea",
        "-i",
        help="Idea ID (e.g. idea-001) or 1-based index (e.g. 1)",
    )
    draft_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Draft book chapters for all provisioned ideas sequentially in batch",
    )
    draft_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-drafting even if chapter.md already exists",
    )

    # Subcommand: typeset (Typst PDF compilation)
    typeset_p = subparsers.add_parser(
        "typeset",
        help="Compile chapter or aggregated book to publication-grade PDF via Typst (REQ-BOK-003, REQ-BOK-004, REQ-BOK-005)",
    )
    typeset_p.add_argument(
        "--idea",
        "-i",
        help="Idea ID (e.g. idea-001) or 1-based index to compile single chapter PDF",
    )
    typeset_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Compile aggregated multi-chapter book volume with TOC",
    )
    typeset_p.add_argument(
        "--output-dir",
        "-o",
        help="Custom output directory for compiled book (default: artefacts/content/book)",
    )
    typeset_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-compilation even if PDF already exists",
    )

    # Subcommand: blog (Hostinger blog post drafting)
    blog_p = subparsers.add_parser(
        "blog",
        help="Draft Hostinger-ready blog post for an idea (REQ-BLG-001, REQ-BLG-002, REQ-BLG-004)",
    )
    blog_p.add_argument(
        "--idea",
        "-i",
        help="Idea ID (e.g. idea-001) or 1-based index",
    )
    blog_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Generate blog posts for all provisioned ideas",
    )
    blog_p.add_argument(
        "--platform",
        "-p",
        choices=["hostinger_static", "hostinger_wordpress", "hostinger_ghost"],
        help="Target CMS publication platform adapter (default: hostinger_static)",
    )
    blog_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-generation even if blog post already exists",
    )

    # Subcommand: social (LinkedIn companion post generation)
    social_p = subparsers.add_parser(
        "social",
        help="Generate companion LinkedIn social post for an idea (REQ-BLG-003)",
    )
    social_p.add_argument(
        "--idea",
        "-i",
        help="Idea ID (e.g. idea-001) or 1-based index",
    )
    social_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Generate social posts for all provisioned ideas",
    )
    social_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-generation even if social post already exists",
    )

    # Subcommand: pipeline (End-to-end execution: enrich -> draft -> typeset -> blog -> social)
    pipeline_p = subparsers.add_parser(
        "pipeline",
        help="Run end-to-end publishing pipeline (enrich, draft, typeset, blog, social) for an idea or batch (REQ-ORC-001, REQ-ORC-004)",
    )
    pipeline_p.add_argument(
        "--idea",
        "-i",
        help="Idea ID (e.g. idea-001) or 1-based index",
    )
    pipeline_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run pipeline for all provisioned ideas sequentially in batch",
    )
    pipeline_p.add_argument(
        "--platform",
        "-p",
        choices=["hostinger_static", "hostinger_wordpress", "hostinger_ghost"],
        help="Target CMS publication platform adapter (default: hostinger_static)",
    )
    pipeline_p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-generation of all pipeline artefacts",
    )

    return parser


def resolve_ideas_to_process(idea_arg: str | None, all_arg: bool, ideas_dir: Path) -> list[str]:
    """Resolve target idea identifier(s) from either --idea or --all."""
    if idea_arg:
        return [idea_arg]
    if all_arg and ideas_dir.is_dir():
        ideas: list[str] = []
        for p in sorted(ideas_dir.iterdir()):
            if p.is_dir() and p.name.startswith("idea-"):
                ideas.append(p.name)
        return ideas
    return []


def handle_draft_command(args: argparse.Namespace) -> int:
    """Handle `draft` subcommand: draft book chapter adhering to author persona."""
    from services.typesetting.pipeline import process_book_chapter

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
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
            )
            status_str: str = "generated" if results.get("draft_generated") else "cached (skipped)"
            print(f"Drafting completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  Chapter Draft: {results['chapter_md']} [{status_str}]")
        except Exception as exc:
            print(f"Drafting error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_typeset_command(args: argparse.Namespace) -> int:
    """Handle `typeset` subcommand: compile single chapter or aggregated book via Typst."""
    from services.typesetting.pipeline import process_aggregated_book, process_book_chapter

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    book_output_dir: Path = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else repo_root / "artefacts" / "content" / "book"
    )

    if not args.idea and not args.all:
        print("Error: Specify either --idea <id> or --all.", file=sys.stderr)
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

        return 0
    except Exception as exc:
        print(f"Typesetting error: {exc}", file=sys.stderr)
        return 1


def handle_enrich_command(args: argparse.Namespace) -> int:
    """Handle `enrich` subcommand: run research synthesis and/or visual generation."""
    from services.enrichment.pipeline import enrich_idea

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    resources_dir: Path = repo_root / "artefacts" / "content" / "resources"

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    # Default to running both research and visuals if neither flag is explicitly set
    do_research: bool = True
    do_visuals: bool = True
    if args.research and not args.visuals:
        do_visuals = False
    elif args.visuals and not args.research:
        do_research = False

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        try:
            print(f"[{idx}/{total}] Processing idea {idea_target}...")
            results = enrich_idea(
                idea_id_or_num=idea_target,
                ideas_root=ideas_dir,
                resources_root=resources_dir,
                catalog_path=catalog_path,
                snapshot_path=snapshot_path,
                do_research=do_research,
                do_visuals=do_visuals,
                regenerate_image=args.regenerate_image,
                refinement=args.refinement,
                force=args.force,
            )
            print(f"Enrichment completed for [{results['idea_id']}] '{results['title']}':")
            if "research_notes" in results:
                status_str: str = (
                    "generated" if results.get("research_generated") else "cached (skipped)"
                )
                print(f"  Research Notes: {results['research_notes']} [{status_str}]")
            if "illustration" in results:
                status_str: str = (
                    "generated" if results.get("visuals_generated") else "cached (skipped)"
                )
                print(f"  Visual Prompt:  {results['visual_prompt']}")
                print(f"  Illustration:   {results['illustration']} [{status_str}]")
        except Exception as exc:
            print(f"Enrichment error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_blog_command(args: argparse.Namespace) -> int:
    """Handle `blog` subcommand: draft Hostinger-ready blog post with optional CMS adaptation."""
    from services.publishing.pipeline import process_blog_and_social

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
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
            )
            status_str: str = "generated" if results.get("blog_generated") else "cached (skipped)"
            print(f"Blog Post completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  Post Markdown: {results['blog_post']} [{status_str}]")
            if "cms_export" in results:
                exp = results["cms_export"]
                print(f"  CMS Adapter:   {exp['platform']} ({exp['format']})")
        except Exception as exc:
            print(f"Error processing blog for {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_social_command(args: argparse.Namespace) -> int:
    """Handle `social` subcommand: generate companion LinkedIn social post."""
    from services.publishing.pipeline import process_blog_and_social

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
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
            )
            status_str: str = "generated" if results.get("social_generated") else "cached (skipped)"
            print(f"Social Post completed for [{results['idea_id']}] '{results['title']}':")
            print(f"  LinkedIn Post: {results['linkedin_post']} [{status_str}]")
        except Exception as exc:
            print(f"Error processing social for {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def handle_pipeline_command(args: argparse.Namespace) -> int:
    """Handle `pipeline` subcommand: run end-to-end publishing pipeline."""
    from services.enrichment.pipeline import enrich_idea
    from services.publishing.pipeline import process_blog_and_social
    from services.typesetting.pipeline import process_book_chapter

    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    resources_dir: Path = repo_root / "artefacts" / "content" / "resources"

    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process: list[str] = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to process.", file=sys.stderr)
        return 1

    total: int = len(ideas_to_process)
    for idx, idea_target in enumerate(ideas_to_process, start=1):
        print("\n==========================================")
        print(f"[{idx}/{total}] Pipeline processing idea {idea_target}")
        print("==========================================")
        try:
            # 1. Enrich
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
            )
            # 2. Draft book chapter
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
            )
            # 3. Typeset single chapter PDF
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
            )
            # 4. Blog Post
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
            )
            # 5. Social Post
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
            )
            print(f"Completed pipeline for [{enrich_res['idea_id']}] '{enrich_res['title']}'.")
        except Exception as exc:
            print(f"Pipeline error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    if args.subcommand == "sync":
        return handle_sync_command(args)
    if args.subcommand == "catalog":
        return handle_catalog_command(args)
    if args.subcommand == "inbox":
        return handle_inbox_command(args)
    if args.subcommand == "add":
        return handle_add_command(args)
    if args.subcommand == "enrich":
        return handle_enrich_command(args)
    if args.subcommand == "draft":
        return handle_draft_command(args)
    if args.subcommand == "typeset":
        return handle_typeset_command(args)
    if args.subcommand == "blog":
        return handle_blog_command(args)
    if args.subcommand == "social":
        return handle_social_command(args)
    if args.subcommand == "pipeline":
        return handle_pipeline_command(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
