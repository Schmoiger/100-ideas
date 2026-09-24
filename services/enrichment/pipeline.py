"""Pipeline coordinator for Idea Content Enrichment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from services.enrichment.researcher import synthesise_research
from services.enrichment.visuals import generate_visual_assets
from services.ingestion.models import IdeaRecord
from services.ingestion.parsers import parse_markdown_table
from services.ingestion.provisioner import provision_idea
from services.ingestion.sync import resolve_catalog_source


def load_or_provision_idea(
    idea_id_or_num: str | int,
    ideas_root: Path,
    catalog_path: Path,
    snapshot_path: Path,
) -> IdeaRecord:
    """Load an existing provisioned idea or provision it from catalogue."""
    # Normalize ID string
    target_id: str = (
        f"idea-{int(idea_id_or_num):03d}" if str(idea_id_or_num).isdigit() else str(idea_id_or_num)
    )

    idea_dir: Path = ideas_root / target_id
    meta_file: Path = idea_dir / "meta.yaml"

    if meta_file.is_file():
        meta_dict: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        if isinstance(meta_dict, dict):
            return IdeaRecord.from_meta_dict(meta_dict)

    # If not provisioned yet, find in catalogue table
    resolved_src: Path = resolve_catalog_source(catalog_path, snapshot_path)
    records: list[IdeaRecord] = parse_markdown_table(resolved_src)
    for rec in records:
        if rec.id.lower() == target_id.lower():
            provision_idea(rec, ideas_root)
            return rec

    raise ValueError(f"Idea '{target_id}' could not be found in content store or catalogue.")


def enrich_idea(
    idea_id_or_num: str | int,
    ideas_root: Path,
    resources_root: Path,
    catalog_path: Path,
    snapshot_path: Path,
    do_research: bool = True,
    do_visuals: bool = True,
    regenerate_image: bool = False,
    refinement: str | None = None,
    force: bool = False,
    force_llm: bool = False,
    dry_run: bool = False,
    overwrite_manual: bool = False,
    client: Any = None,
) -> dict[str, Any]:
    """Execute enrichment workflow for a specific idea.

    Coordinates REQ-ENR-001, REQ-ENR-002, REQ-ENR-003, REQ-ENR-004.
    """
    idea: IdeaRecord = load_or_provision_idea(
        idea_id_or_num, ideas_root, catalog_path, snapshot_path
    )

    results: dict[str, Any] = {
        "idea_id": idea.id,
        "title": idea.title,
    }

    # 1. Research phase (REQ-ENR-001)
    if do_research and not regenerate_image:
        notes_path, res_gen = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=resources_root,
            force=force,
            force_llm=force_llm,
            dry_run=dry_run,
            overwrite_manual=overwrite_manual,
            client=client,
        )
        results["research_notes"] = str(notes_path)
        results["research_generated"] = res_gen

    # 2. Visual phase (REQ-ENR-002, REQ-ENR-003, REQ-ENR-004)
    if do_visuals or regenerate_image:
        force_visuals: bool = force or regenerate_image
        prompt_path, img_path, vis_gen = generate_visual_assets(
            idea=idea,
            ideas_root=ideas_root,
            refinement=refinement,
            force=force_visuals,
            force_llm=force_llm,
            dry_run=dry_run,
            client=client,
        )
        results["visual_prompt"] = str(prompt_path)
        results["illustration"] = str(img_path)
        results["visuals_generated"] = vis_gen

    return results
