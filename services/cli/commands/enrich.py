"""Enrich command: empirical research synthesis and visual illustration generation."""

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


def handle_enrich_command(args: argparse.Namespace) -> int:
    """Handle ``enrich`` subcommand: run research synthesis and/or visual generation."""
    from services.enrichment.pipeline import enrich_idea

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
        "enrichment",
        model_name="gemini-2.5-flash",
        yes=getattr(args, "yes", False),
    ):
        print("Batch execution cancelled by user.")
        return 0

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
                force_llm=getattr(args, "force_llm", False),
                dry_run=getattr(args, "dry_run", False),
                overwrite_manual=getattr(args, "overwrite_manual", False),
            )
            print(f"Enrichment completed for [{results['idea_id']}] '{results['title']}':")
            if "research_notes" in results:
                status_str: str = (
                    "generated" if results.get("research_generated") else "cached (skipped)"
                )
                print(f"  Research Notes: {results['research_notes']} [{status_str}]")
            if "illustration" in results:
                status_str = "generated" if results.get("visuals_generated") else "cached (skipped)"
                print(f"  Visual Prompt:  {results['visual_prompt']}")
                print(f"  Illustration:   {results['illustration']} [{status_str}]")
        except Exception as exc:
            print(f"Enrichment error on {idea_target}: {exc}", file=sys.stderr)
            return 1

    return 0
