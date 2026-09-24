"""Ingest commands: sync, catalog, inbox, add.

These commands belong exclusively to the ``services.ingestion`` domain and
are the only CLI modules that are permitted to import from it directly.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from services.cli._shared import (
    get_default_paths,
    get_inbox_archive_path,
)
from services.ingestion.dedup import check_duplicate
from services.ingestion.models import IdeaRecord
from services.ingestion.parsers import (
    archive_inbox_entries,
    parse_inbox_archive,
    parse_inbox_markdown,
    parse_markdown_table,
)
from services.ingestion.provisioner import (
    load_existing_provisioned_ideas,
    provision_idea,
)
from services.ingestion.selector import select_ideas
from services.ingestion.sync import resolve_catalog_source, sync_catalog_source


def get_next_idea_number(
    existing_provisioned: list[IdeaRecord],
    catalog_records: list[IdeaRecord] | None = None,
    archive_records: list[IdeaRecord] | None = None,
) -> int:
    """Determine highest existing numeric idea index and return next integer.

    Decoupled from hardcoded 100 ceiling or floor to support continuous publishing.
    """
    max_num: int = 0
    all_records: list[IdeaRecord] = list(existing_provisioned)
    if catalog_records:
        all_records.extend(catalog_records)
    if archive_records:
        all_records.extend(archive_records)

    for r in all_records:
        match = re.search(r"\d+", r.id)
        if match:
            max_num = max(max_num, int(match.group()))

    return max_num + 1


def handle_sync_command(args: argparse.Namespace) -> int:
    """Handle ``sync`` subcommand: copies authoritative source to snapshot."""
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
    """Handle ``catalog`` subcommand: parse, filter, and optionally provision ideas."""
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
    """Handle ``inbox`` subcommand: parse inbox.md, check duplicates, provision, and archive."""
    catalog_path, snapshot_path, inbox_path, ideas_dir = get_default_paths()
    archive_path: Path = get_inbox_archive_path()

    existing_provisioned: list[IdeaRecord] = load_existing_provisioned_ideas(ideas_dir)
    archived_ideas: list[IdeaRecord] = parse_inbox_archive(archive_path)

    cat_records: list[IdeaRecord] = []
    try:
        resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
        cat_records = parse_markdown_table(resolved_src)
    except Exception:
        pass

    next_id_num: int = get_next_idea_number(
        existing_provisioned=existing_provisioned,
        catalog_records=cat_records,
        archive_records=archived_ideas,
    )

    inbox_ideas: list[IdeaRecord] = parse_inbox_markdown(inbox_path, start_id=next_id_num)
    if not inbox_ideas:
        print(f"No pending idea entries found in {inbox_path}.")
        return 0

    all_known_records: list[IdeaRecord] = existing_provisioned + cat_records + archived_ideas

    print(f"Found {len(inbox_ideas)} entry/entries in inbox:")
    for idea in inbox_ideas:
        is_dup, matched_rec, reason = check_duplicate(idea, all_known_records)
        dup_warning: str = f" [WARNING DUPLICATE: {reason}]" if is_dup else ""
        print(f"  [{idea.id}] {idea.title}{dup_warning}")

    if args.provision:
        print(f"\nProvisioning inbox ideas into {ideas_dir}...")
        provisioned: list[IdeaRecord] = []
        for idea in inbox_ideas:
            is_dup, matched_rec, reason = check_duplicate(idea, existing_provisioned)
            if is_dup and not args.force:
                print(f"  Skipping {idea.title} ({reason}). Use --force to provision anyway.")
                continue
            p_dir: Path = provision_idea(idea, ideas_dir, force=args.force)
            print(f"  Provisioned: {idea.id} -> {p_dir}")
            provisioned.append(idea)

        if provisioned:
            archive_inbox_entries(
                inbox_path=inbox_path,
                archive_path=archive_path,
                provisioned_records=provisioned,
            )
            print(f"Archived {len(provisioned)} entry/entries to {archive_path.name}.")
        print("Inbox provisioning complete.")

    return 0


def handle_add_command(args: argparse.Namespace) -> int:
    """Handle ``add`` subcommand: directly add an idea through CLI/chat interface."""
    catalog_path, snapshot_path, _, ideas_dir = get_default_paths()
    archive_path: Path = get_inbox_archive_path()

    title: str = args.title.strip()
    synopsis: str = args.synopsis.strip()
    if not title or not synopsis:
        print("Error: Both --title and --synopsis must be non-empty strings.", file=sys.stderr)
        return 1

    tags: list[str] = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    source: str = args.source.strip() if args.source else ""

    existing_provisioned: list[IdeaRecord] = load_existing_provisioned_ideas(ideas_dir)
    archived_ideas: list[IdeaRecord] = parse_inbox_archive(archive_path)

    cat_records: list[IdeaRecord] = []
    try:
        resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
        cat_records = parse_markdown_table(resolved_src)
    except Exception:
        pass

    if args.id:
        target_id: str = args.id.strip()
        if not target_id.startswith("idea-"):
            target_id = f"idea-{target_id}"
    else:
        next_num: int = get_next_idea_number(
            existing_provisioned=existing_provisioned,
            catalog_records=cat_records,
            archive_records=archived_ideas,
        )
        target_id = f"idea-{next_num:03d}"

    new_idea = IdeaRecord(
        id=target_id,
        title=title,
        synopsis=synopsis,
        source_reference=source,
        tags=tags,
    )

    all_known_records: list[IdeaRecord] = existing_provisioned + cat_records + archived_ideas
    is_dup, matched_rec, reason = check_duplicate(new_idea, all_known_records)
    if is_dup:
        print(f"Warning: Potential duplicate detected: {reason}")
        if not args.force:
            print(
                "Aborting idea intake. Re-run with --force to override duplicate detection.",
                file=sys.stderr,
            )
            return 1

    p_dir: Path = provision_idea(new_idea, ideas_dir, force=args.force)
    print(f"Successfully provisioned idea '{new_idea.title}' [{new_idea.id}] at {p_dir}")
    return 0
