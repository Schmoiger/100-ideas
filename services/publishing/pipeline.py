"""Pipeline coordinator for Blog & Social Publishing Subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.enrichment.pipeline import load_or_provision_idea
from services.ingestion.models import IdeaRecord
from services.publishing.adapters import export_for_platform
from services.publishing.drafter import draft_blog_post
from services.publishing.social import generate_linkedin_post


def process_blog_and_social(
    idea_id_or_num: str | int,
    ideas_root: Path,
    repo_root: Path,
    catalog_path: Path,
    snapshot_path: Path,
    do_blog: bool = True,
    do_social: bool = True,
    cms_platform: str | None = None,
    config_path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Coordinate blog drafting, LinkedIn social generation, and CMS export.

    Implements REQ-BLG-001, REQ-BLG-002, REQ-BLG-003, and REQ-BLG-004.
    """
    idea: IdeaRecord = load_or_provision_idea(
        idea_id_or_num=idea_id_or_num,
        ideas_root=ideas_root,
        catalog_path=catalog_path,
        snapshot_path=snapshot_path,
    )

    results: dict[str, Any] = {
        "idea_id": idea.id,
        "title": idea.title,
        "blog_generated": False,
        "social_generated": False,
    }

    # 1. Draft Hostinger-compatible blog post (REQ-BLG-001, REQ-BLG-002)
    post_path: Path | None = None
    if do_blog:
        post_path, blog_gen = draft_blog_post(
            idea=idea,
            ideas_root=ideas_root,
            force=force,
        )
        results["blog_post"] = str(post_path)
        results["blog_generated"] = blog_gen

    # 2. Generate companion LinkedIn social post (REQ-BLG-003)
    if do_social:
        linkedin_path, social_gen = generate_linkedin_post(
            idea=idea,
            ideas_root=ideas_root,
            force=force,
        )
        results["linkedin_post"] = str(linkedin_path)
        results["social_generated"] = social_gen

    # 3. CMS publication adapter export (REQ-BLG-004)
    if cms_platform and post_path and post_path.is_file():
        cfg_file = config_path or (repo_root / "config" / "publishing.yaml")
        cms_export = export_for_platform(
            post_path=post_path,
            platform_id=cms_platform,
            config_path=cfg_file,
        )
        results["cms_export"] = cms_export

    return results
