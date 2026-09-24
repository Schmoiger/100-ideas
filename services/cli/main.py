"""System CLI entry point for the 100-Ideas Agentic Publishing System.

This module owns the argument parser and top-level dispatcher.  Each
subcommand is delegated to a focused handler in ``services.cli.commands``,
inverting the historical coupling where ``services.ingestion.cli`` imported
all downstream domain packages.

Entry point (pyproject.toml)::

    [project.scripts]
    ideas = "services.cli.main:main"
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the system-wide ``ideas`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="ideas",
        description="100-Ideas Agentic Publishing System CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # ------------------------------------------------------------------
    # Ingest commands
    # ------------------------------------------------------------------

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
        "--id", help="Explicit canonical idea identifier (e.g. idea-105 or idea-devx-latency)"
    )
    add_p.add_argument(
        "--force", "-f", action="store_true", help="Force add even if duplicate detected"
    )

    # ------------------------------------------------------------------
    # Enrich command
    # ------------------------------------------------------------------

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
    enrich_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited assets even if marked human_modified (TASK-018)",
    )
    enrich_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate prompt token count and projected USD cost without firing live API requests (TASK-020)",
    )
    enrich_p.add_argument(
        "--force-llm",
        action="store_true",
        help="Bypass input fingerprint cache to force live LLM re-generation (TASK-020)",
    )
    enrich_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass interactive batch confirmation prompt (TASK-020)",
    )

    # ------------------------------------------------------------------
    # Typeset commands
    # ------------------------------------------------------------------

    # draft
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
    draft_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited chapter drafts even if marked human_modified (TASK-018)",
    )
    draft_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate prompt token count and projected USD cost without firing live API requests (TASK-020)",
    )
    draft_p.add_argument(
        "--force-llm",
        action="store_true",
        help="Bypass input fingerprint cache to force live LLM re-generation (TASK-020)",
    )
    draft_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass interactive batch confirmation prompt (TASK-020)",
    )

    # typeset
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
        "--volume",
        "-v",
        help="Volume ID from config/volumes.yaml (e.g. volume-1) to compile specific volume (TASK-017)",
    )
    typeset_p.add_argument(
        "--all-volumes",
        action="store_true",
        help="Compile all volumes defined in config/volumes.yaml (TASK-017)",
    )
    typeset_p.add_argument(
        "--volumes-config",
        help="Custom path to volumes configuration YAML (default: config/volumes.yaml)",
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
    typeset_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited assets during typesetting (TASK-018)",
    )
    typeset_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate prompt token count and projected USD cost without firing live API requests (TASK-020)",
    )
    typeset_p.add_argument(
        "--force-llm",
        action="store_true",
        help="Bypass input fingerprint cache to force live LLM re-generation (TASK-020)",
    )
    typeset_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass interactive batch confirmation prompt (TASK-020)",
    )

    # ------------------------------------------------------------------
    # Publishing commands
    # ------------------------------------------------------------------

    # blog
    blog_p = subparsers.add_parser(
        "blog",
        help="Draft Hostinger-ready blog post for an idea (REQ-BLG-001, REQ-BLG-002, REQ-BLG-004)",
    )
    blog_p.add_argument("--idea", "-i", help="Idea ID (e.g. idea-001) or 1-based index")
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
    blog_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited blog drafts even if marked human_modified (TASK-018)",
    )

    # social
    social_p = subparsers.add_parser(
        "social",
        help="Generate companion LinkedIn social post for an idea (REQ-BLG-003)",
    )
    social_p.add_argument("--idea", "-i", help="Idea ID (e.g. idea-001) or 1-based index")
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
    social_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited social drafts even if marked human_modified (TASK-018)",
    )

    # pipeline
    pipeline_p = subparsers.add_parser(
        "pipeline",
        help="Run end-to-end publishing pipeline (enrich, draft, typeset, blog, social) for an idea or batch (REQ-ORC-001, REQ-ORC-004)",
    )
    pipeline_p.add_argument("--idea", "-i", help="Idea ID (e.g. idea-001) or 1-based index")
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
    pipeline_p.add_argument(
        "--overwrite-manual",
        action="store_true",
        help="Force overwrite of human-edited assets throughout publishing pipeline (TASK-018)",
    )
    pipeline_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate prompt token count and projected USD cost without firing live API requests (TASK-020)",
    )
    pipeline_p.add_argument(
        "--force-llm",
        action="store_true",
        help="Bypass input fingerprint cache to force live LLM re-generation (TASK-020)",
    )
    pipeline_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass interactive batch confirmation prompt (TASK-020)",
    )

    # ------------------------------------------------------------------
    # Review commands
    # ------------------------------------------------------------------

    # review
    review_p = subparsers.add_parser(
        "review",
        help="Evaluate editorial quality gate and voice fidelity against author persona (TASK-018)",
    )
    review_p.add_argument("--idea", "-i", help="Idea ID (e.g. idea-001) or 1-based index")
    review_p.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Evaluate all provisioned ideas sequentially in batch",
    )
    review_p.add_argument(
        "--reviewer",
        default="Avi",
        help="Reviewer identifier to record in editorial_quality metadata (default: Avi)",
    )

    # mark-edited
    mark_p = subparsers.add_parser(
        "mark-edited",
        help="Set human_modified safeguard on an idea to prevent automated overwriting (TASK-018)",
    )
    mark_p.add_argument(
        "--idea",
        "-i",
        required=True,
        help="Idea ID (e.g. idea-001) or 1-based index",
    )
    mark_p.add_argument(
        "--notes",
        help="Optional editorial notes describing the human modifications",
    )
    mark_p.add_argument(
        "--unmark",
        action="store_true",
        help="Remove human_modified safeguard to re-enable automated overwriting",
    )

    # ------------------------------------------------------------------
    # Revise command
    # ------------------------------------------------------------------

    revise_p = subparsers.add_parser(
        "revise",
        help="Targeted section refinement for chapter manuscript (TASK-019)",
    )
    revise_p.add_argument(
        "--idea",
        "-i",
        required=True,
        help="Idea ID (e.g. idea-001) or 1-based index",
    )
    revise_p.add_argument(
        "--section",
        "-s",
        required=True,
        help="Target section name or alias (e.g. mechanics, economics, takeaways, hype, lead_punch)",
    )
    revise_p.add_argument(
        "--content",
        "-c",
        help="Replacement text for the targeted section",
    )
    revise_p.add_argument(
        "--from-file",
        help="Path to text or markdown file containing the new section content",
    )
    revise_p.add_argument(
        "--append",
        action="store_true",
        help="Append content to existing section rather than replacing it",
    )
    revise_p.add_argument(
        "--notes",
        "-m",
        default="",
        help="Editorial note explaining the revision rationale",
    )
    revise_p.add_argument(
        "--reviewer",
        "-r",
        default="Avi",
        help="Reviewer or author identifier (default: Avi)",
    )
    revise_p.add_argument(
        "--syndicate",
        action="store_true",
        help="Re-syndicate downstream blog and social channels after revision",
    )
    revise_p.add_argument(
        "--typeset",
        action="store_true",
        help="Trigger immediate single-chapter Typst PDF compilation for visual review",
    )

    return parser


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH: dict[str, str] = {
    "sync": "services.cli.commands.ingest:handle_sync_command",
    "catalog": "services.cli.commands.ingest:handle_catalog_command",
    "inbox": "services.cli.commands.ingest:handle_inbox_command",
    "add": "services.cli.commands.ingest:handle_add_command",
    "enrich": "services.cli.commands.enrich:handle_enrich_command",
    "draft": "services.cli.commands.typeset:handle_draft_command",
    "typeset": "services.cli.commands.typeset:handle_typeset_command",
    "blog": "services.cli.commands.publishing:handle_blog_command",
    "social": "services.cli.commands.publishing:handle_social_command",
    "pipeline": "services.cli.commands.publishing:handle_pipeline_command",
    "review": "services.cli.commands.review:handle_review_command",
    "mark-edited": "services.cli.commands.review:handle_mark_edited_command",
    "revise": "services.cli.commands.revise:handle_revise_command",
}


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the 100-Ideas system."""
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    handler_ref = _DISPATCH.get(args.subcommand)
    if handler_ref is None:
        parser.print_help()
        return 1

    module_path, func_name = handler_ref.split(":")
    import importlib

    module = importlib.import_module(module_path)
    handler = getattr(module, func_name)
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
