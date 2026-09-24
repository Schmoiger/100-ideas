"""Review commands: editorial quality gate evaluation and mark-edited safeguard toggling."""

from __future__ import annotations

import argparse
import sys

import yaml

from services.cli._shared import get_default_paths, resolve_ideas_to_process
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import save_idea_meta


def handle_review_command(args: argparse.Namespace) -> int:
    """Handle ``review`` subcommand: validate voice fidelity against author persona."""
    from services.publishing.quality_gate import evaluate_idea_quality_gate

    _, _, _, ideas_dir = get_default_paths()
    if not args.idea and not args.all:
        print("Error: Specify --idea <id> or --all", file=sys.stderr)
        return 1

    ideas_to_process = resolve_ideas_to_process(args.idea, args.all, ideas_dir)
    if not ideas_to_process:
        print("No ideas found to review.", file=sys.stderr)
        return 1

    reviewer = getattr(args, "reviewer", "Avi") or "Avi"
    all_passed = True
    for idea_target in ideas_to_process:
        target_id = (
            f"idea-{int(idea_target):03d}" if str(idea_target).isdigit() else str(idea_target)
        )
        idea_dir = ideas_dir / target_id
        if not idea_dir.is_dir():
            print(f"Idea directory not found: {idea_dir}", file=sys.stderr)
            all_passed = False
            continue

        try:
            report = evaluate_idea_quality_gate(idea_dir, reviewer=reviewer)
            status_symbol = "✓ APPROVED" if report.passed else "✗ NEEDS REVISION"
            print(
                f"[{target_id}] Quality Gate: {status_symbol} (Fidelity Score: {report.score * 100:.0f}%)"
            )
            for metric, passed in report.metrics.items():
                m_icon = "✓" if passed else "✗"
                print(f"  {m_icon} {metric}")
            if report.issues:
                print("  Issues to address:")
                for issue in report.issues:
                    print(f"    - {issue}")
            if not report.passed:
                all_passed = False
        except Exception as exc:
            print(f"Error reviewing {target_id}: {exc}", file=sys.stderr)
            all_passed = False

    return 0 if all_passed else 1


def handle_mark_edited_command(args: argparse.Namespace) -> int:
    """Handle ``mark-edited`` subcommand: toggle human_modified safeguard on idea meta.yaml."""
    _, _, _, ideas_dir = get_default_paths()
    if not args.idea:
        print("Error: Specify --idea <id>", file=sys.stderr)
        return 1

    target_id = f"idea-{int(args.idea):03d}" if str(args.idea).isdigit() else str(args.idea)
    idea_dir = ideas_dir / target_id
    meta_file = idea_dir / "meta.yaml"
    if not meta_file.is_file():
        print(f"Error: meta.yaml not found at {meta_file}", file=sys.stderr)
        return 1

    unmark = getattr(args, "unmark", False)
    notes = getattr(args, "notes", "") or ("Manual author edit recorded" if not unmark else "")

    meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    record = IdeaRecord.from_meta_dict(meta_dict)
    record.mark_human_modified(not unmark, notes=notes)
    save_idea_meta(record, idea_dir)

    status_str = (
        "unmarked (automated overwrites permitted)"
        if unmark
        else "flagged human_modified (protected from automated overwrites)"
    )
    print(f"[{record.id}] '{record.title}': {status_str}")
    return 0
