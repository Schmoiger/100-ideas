"""Smoke tests for Content Enrichment Subsystem."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import yaml

from services.enrichment.pipeline import enrich_idea
from services.enrichment.researcher import synthesise_research
from services.enrichment.resource_library import resolve_resources_for_idea
from services.enrichment.visuals import create_editorial_png, generate_visual_assets
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea


def _create_mock_idea(idea_id: str = "idea-001") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Agentic Development Lifecycle (ADLC)",
        synopsis="Replacing SDLC with agentic collaboration, continuous iteration, and verification.",
        tags=["governance", "architecture", "devx"],
    )


def test_resource_library_loader() -> None:
    """Verify loading resources from library by matching tags or citations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        res_root = Path(tmp_dir) / "resources"
        res_root.mkdir(parents=True)

        manifest_file = res_root / "manifest.yaml"
        manifest_file.write_text(
            """resources:
  - id: devx-doc
    title: Modern DevX
    file: devx-doc.md
    tags: [devx, productivity]
""",
            encoding="utf-8",
        )

        res_file = res_root / "devx-doc.md"
        res_file.write_text(
            """## Content
Empirical data indicates a 30% reduction in cycle time.
""",
            encoding="utf-8",
        )

        idea = _create_mock_idea()
        matched = resolve_resources_for_idea(idea, res_root)
        assert len(matched) == 1
        res_meta, content = matched[0]
        assert res_meta["title"] == "Modern DevX"
        assert "30% reduction" in content


def test_research_synthesis_creates_dossier() -> None:
    """Verify synthesise_research generates research/notes.md with all required sections."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-042")
        provision_idea(idea, ideas_root)

        notes_path, generated = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            force=False,
        )

        assert generated is True
        assert notes_path.is_file()
        content = notes_path.read_text(encoding="utf-8")

        # REQ-ENR-001 mandatory sections
        assert "## Core Thesis" in content
        assert "## Empirical Evidence" in content
        assert "## Economic Trade-offs" in content
        assert "## Counterarguments" in content
        assert "## Citations" in content

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-042" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_dict.get("research_notes") == "research/notes.md"


def test_visual_generation_produces_valid_png() -> None:
    """Verify generate_visual_assets creates prompt.txt and a valid binary PNG."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-007")
        provision_idea(idea, ideas_root)

        prompt_path, img_path, generated = generate_visual_assets(
            idea=idea,
            ideas_root=ideas_root,
            force=False,
        )

        assert generated is True
        assert prompt_path.is_file()
        assert img_path.is_file()

        prompt_text = prompt_path.read_text(encoding="utf-8")
        assert "editorial book illustration" in prompt_text.lower()
        assert "**Style**:" in prompt_text
        assert "**Negative Prompt**:" in prompt_text

        # Verify valid PNG signature: \x89PNG\r\n\x1a\n
        img_bytes = img_path.read_bytes()
        assert len(img_bytes) > 64
        assert img_bytes.startswith(b"\x89PNG\r\n\x1a\n")

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-007" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_dict.get("illustration") == "assets/illustration.png"
        assert meta_dict.get("visual_prompt") == "assets/prompt.txt"


def test_pure_python_png_generator() -> None:
    """Verify pure-Python PNG generator generates valid header and chunks."""
    png_bytes = create_editorial_png("Test Idea", width=200, height=200)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"IHDR" in png_bytes
    assert b"IDAT" in png_bytes
    assert b"IEND" in png_bytes


def test_regenerate_image_isolation() -> None:
    """Verify REQ-ENR-004: --regenerate-image updates image/prompt without touching research notes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        catalog_path = Path(tmp_dir) / "catalog.md"
        snapshot_path = Path(tmp_dir) / "snapshot.md"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-010")
        provision_idea(idea, ideas_root)

        # First run: research and visuals
        res1 = enrich_idea(
            idea_id_or_num="idea-010",
            ideas_root=ideas_root,
            resources_root=res_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_research=True,
            do_visuals=True,
            force=False,
        )
        assert res1["research_generated"] is True
        assert res1["visuals_generated"] is True

        notes_file = ideas_root / "idea-010" / "research" / "notes.md"
        notes_mtime_before = notes_file.stat().st_mtime
        original_notes_content = notes_file.read_text(encoding="utf-8")

        # Sleep briefly to ensure mtime change detection if modified
        time.sleep(0.05)

        # Regenerate image with refinement
        res2 = enrich_idea(
            idea_id_or_num="idea-010",
            ideas_root=ideas_root,
            resources_root=res_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_research=True,
            do_visuals=False,
            regenerate_image=True,
            refinement="Use midnight blue and copper linework",
            force=False,
        )

        assert "research_generated" not in res2
        assert res2["visuals_generated"] is True

        # Verify research notes were untouched
        notes_mtime_after = notes_file.stat().st_mtime
        assert notes_mtime_before == notes_mtime_after
        assert notes_file.read_text(encoding="utf-8") == original_notes_content

        # Verify prompt received refinement
        prompt_file = ideas_root / "idea-010" / "assets" / "prompt.txt"
        prompt_text = prompt_file.read_text(encoding="utf-8")
        assert "midnight blue and copper linework" in prompt_text


def test_idempotency() -> None:
    """Verify REQ-ORC-005: Second run skips generation unless force=True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        catalog_path = Path(tmp_dir) / "catalog.md"
        snapshot_path = Path(tmp_dir) / "snapshot.md"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-020")
        provision_idea(idea, ideas_root)

        # Run 1: generated
        run1 = enrich_idea(
            idea_id_or_num="idea-020",
            ideas_root=ideas_root,
            resources_root=res_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            force=False,
        )
        assert run1["research_generated"] is True
        assert run1["visuals_generated"] is True

        # Run 2: skipped (cached)
        run2 = enrich_idea(
            idea_id_or_num="idea-020",
            ideas_root=ideas_root,
            resources_root=res_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            force=False,
        )
        assert run2["research_generated"] is False
        assert run2["visuals_generated"] is False

        # Run 3: forced
        run3 = enrich_idea(
            idea_id_or_num="idea-020",
            ideas_root=ideas_root,
            resources_root=res_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            force=True,
        )
        assert run3["research_generated"] is True
        assert run3["visuals_generated"] is True
