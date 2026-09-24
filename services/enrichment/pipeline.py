"""Pipeline coordinator for Idea Content Enrichment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.enrichment.researcher import synthesise_research
from services.enrichment.visuals import generate_visual_assets
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import (
    load_or_provision_idea,  # canonical location (TASK-021/022)
)

# load_or_provision_idea is re-exported here for backward compatibility.
# New callers should import directly from services.ingestion.provisioner.
__all__ = ["load_or_provision_idea", "enrich_idea"]


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
