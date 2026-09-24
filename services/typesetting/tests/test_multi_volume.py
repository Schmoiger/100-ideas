"""Unit and integration tests for multi-volume book mapping and compilation."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from services.enrichment.visuals import create_editorial_png
from services.ingestion.cli import handle_typeset_command
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.typesetting.compiler import compile_volume_pdf
from services.typesetting.drafter import draft_book_chapter
from services.typesetting.pipeline import process_volume_book
from services.typesetting.translator import markdown_to_volume_chapter_body
from services.typesetting.volumes import (
    VolumeChapterRef,
    VolumeConfig,
    VolumePart,
    load_volumes_config,
)

HAS_TYPST = shutil.which("typst") is not None


def _create_test_idea(idea_id: str, title: str) -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title=title,
        synopsis=f"Synopsis for {title}.",
        tags=["sdlc", "devx"],
    )


def test_load_volumes_config_valid() -> None:
    """Verify loading valid declarative volumes configuration from YAML."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    config_file = repo_root / "config" / "volumes.yaml"

    volumes = load_volumes_config(config_file)
    assert "volume-1" in volumes
    assert "volume-2" in volumes

    vol1 = volumes["volume-1"]
    assert vol1.id == "volume-1"
    assert "Volume 1" in vol1.title
    assert vol1.author == "AS"
    assert len(vol1.parts) >= 2
    assert vol1.total_chapters() >= 3

    # Check parts structure
    part1 = vol1.parts[0]
    assert "Part I" in part1.title
    assert len(part1.chapters) >= 2
    assert part1.chapters[0].idea_id == "idea-001"


def test_load_volumes_config_errors() -> None:
    """Verify error handling for invalid or missing volumes YAML configurations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Missing file
        with pytest.raises(FileNotFoundError, match="not found"):
            load_volumes_config(tmp_path / "nonexistent.yaml")

        # 2. Malformed YAML
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("volumes: [unterminated", encoding="utf-8")
        with pytest.raises(ValueError, match="Malformed YAML"):
            load_volumes_config(bad_yaml)

        # 3. Not a dictionary
        scalar_yaml = tmp_path / "scalar.yaml"
        scalar_yaml.write_text("string_root", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            load_volumes_config(scalar_yaml)

        # 4. Missing volumes key
        missing_vols = tmp_path / "missing_vols.yaml"
        missing_vols.write_text("version: '1.0'", encoding="utf-8")
        with pytest.raises(ValueError, match="must contain a 'volumes' mapping"):
            load_volumes_config(missing_vols)

        # 5. Volume missing title
        missing_title = tmp_path / "no_title.yaml"
        missing_title.write_text(
            yaml.dump({"version": "1.0", "volumes": {"vol-1": {"parts": []}}}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="missing required 'title'"):
            load_volumes_config(missing_title)

        # 6. Part missing title
        missing_part_title = tmp_path / "no_part_title.yaml"
        missing_part_title.write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "volumes": {
                        "vol-1": {
                            "title": "Vol 1",
                            "parts": [{"chapters": []}],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="missing required 'title'"):
            load_volumes_config(missing_part_title)

        # 7. Chapter missing idea_id
        missing_idea_id = tmp_path / "no_idea_id.yaml"
        missing_idea_id.write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "volumes": {
                        "vol-1": {
                            "title": "Vol 1",
                            "parts": [
                                {
                                    "title": "Part 1",
                                    "chapters": [{"chapter_title_override": "Custom"}],
                                }
                            ],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="missing required 'idea_id'"):
            load_volumes_config(missing_idea_id)


def test_volume_config_methods() -> None:
    """Verify helper methods on VolumeConfig for ordering and chapter extraction."""
    part1 = VolumePart(
        title="Part I: Velocity",
        description="Velocity overview",
        chapters=[
            VolumeChapterRef(idea_id="idea-001"),
            VolumeChapterRef(idea_id="idea-002", chapter_title_override="Overridden Title"),
        ],
    )
    part2 = VolumePart(
        title="Part II: Governance",
        chapters=[
            VolumeChapterRef(idea_id="idea-003"),
        ],
    )
    volume = VolumeConfig(
        id="vol-test",
        title="Test Volume",
        parts=[part1, part2],
    )

    assert volume.total_chapters() == 3
    assert volume.all_idea_ids() == ["idea-001", "idea-002", "idea-003"]

    ordered = volume.get_ordered_chapters()
    assert len(ordered) == 3

    seq1, p1, ref1 = ordered[0]
    assert seq1 == 1
    assert p1.title == "Part I: Velocity"
    assert ref1.idea_id == "idea-001"
    assert ref1.chapter_title_override is None

    seq2, p2, ref2 = ordered[1]
    assert seq2 == 2
    assert ref2.idea_id == "idea-002"
    assert ref2.chapter_title_override == "Overridden Title"

    seq3, p3, ref3 = ordered[2]
    assert seq3 == 3
    assert p3.title == "Part II: Governance"
    assert ref3.idea_id == "idea-003"


def test_markdown_to_volume_chapter_body() -> None:
    """Verify dynamic chapter numbering, title override, and root-relative image generation."""
    source_md = """# Chapter 14: Original Chapter Title

*Chapter 14 · Original Book Title*

![Editorial illustration: Original Title](../assets/illustration.png)

---

## The Unvarnished Reality

Delivery friction is the primary constraint.

---

## Where the Gears Bind

Bottlenecks arise in review cycles.
"""
    typst_body = markdown_to_volume_chapter_body(
        markdown_content=source_md,
        idea_id="idea-014",
        chapter_num=2,
        title="Decoupled Continuous Ingestion",
        volume_title="100 Ideas: Volume 1",
        illustration_root_path="/artefacts/content/ideas/idea-014/assets/illustration.png",
    )

    # Dynamic chapter heading
    assert "= Chapter 2: Decoupled Continuous Ingestion" in typst_body
    assert "_Chapter 2 · 100 Ideas: Volume 1_" in typst_body
    assert "Original Chapter Title" not in typst_body

    # Root-relative image path
    assert 'image("/artefacts/content/ideas/idea-014/assets/illustration.png"' in typst_body

    # Substantive sections preserved
    assert "== The Unvarnished Reality" in typst_body
    assert "Delivery friction is the primary constraint." in typst_body
    assert "== Where the Gears Bind" in typst_body


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI binary not available in PATH")
def test_compile_volume_pdf_end_to_end() -> None:
    """Verify end-to-end multi-volume compilation with part dividers and table of contents."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        tmp_path = Path(tmp_dir)
        ideas_root = tmp_path / "ideas"
        ideas_root.mkdir(parents=True)
        book_dir = tmp_path / "book"
        book_dir.mkdir(parents=True)

        # Create two test ideas
        idea1 = _create_test_idea("idea-001", "Constraint Theory in Software")
        idea2 = _create_test_idea("idea-002", "Agentic Flow vs Manual Syntax")
        for idea in [idea1, idea2]:
            provision_idea(idea, ideas_root)
            assets_dir = ideas_root / idea.id / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (assets_dir / "illustration.png").write_bytes(
                create_editorial_png(f"test:{idea.id}", width=200, height=100)
            )
            draft_book_chapter(idea, ideas_root, force=True)

        vol = VolumeConfig(
            id="volume-test",
            title="100 Ideas: Volume Test — SDLC & Flow",
            subtitle="Architectural Principles for Autonomous Delivery",
            author="AS",
            brand="typst/brands/neutral.typ",
            output_pdf=f"{book_dir.name}/volume-test.pdf",
            parts=[
                VolumePart(
                    title="Part I: Flow Foundations",
                    description="Core principles of continuous flow and cognitive latency.",
                    chapters=[
                        VolumeChapterRef(idea_id="idea-001"),
                    ],
                ),
                VolumePart(
                    title="Part II: Agentic Engineering",
                    description="Autonomous agents and contract verification.",
                    chapters=[
                        VolumeChapterRef(
                            idea_id="idea-002",
                            chapter_title_override="Autonomous Agents in the Critical Path",
                        ),
                    ],
                ),
            ],
        )

        out_pdf = book_dir / "volume-test.pdf"
        pdf_path, total = compile_volume_pdf(
            volume=vol,
            ideas_root=ideas_root,
            repo_root=repo_root,
            output_pdf_override=out_pdf,
            force=True,
        )

        assert total == 2
        assert pdf_path.is_file()
        pdf_bytes = pdf_path.read_bytes()
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 2000

        # Verify intermediate fragment files generated
        frag1 = book_dir / "_volumes" / "volume-test" / "chapter-001-idea-001.typ"
        frag2 = book_dir / "_volumes" / "volume-test" / "chapter-002-idea-002.typ"
        assert frag1.is_file()
        assert frag2.is_file()

        frag2_text = frag2.read_text(encoding="utf-8")
        assert "= Chapter 2: Autonomous Agents in the Critical Path" in frag2_text


def test_compile_volume_missing_chapter_error() -> None:
    """Verify compile_volume_pdf raises FileNotFoundError when a chapter is missing."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ideas_root = tmp_path / "ideas"
        ideas_root.mkdir(parents=True)

        vol = VolumeConfig(
            id="vol-missing",
            title="Missing Chapter Vol",
            parts=[
                VolumePart(
                    title="Part I",
                    chapters=[VolumeChapterRef(idea_id="idea-999")],
                )
            ],
        )

        with pytest.raises(FileNotFoundError, match="Chapter manuscript not found"):
            compile_volume_pdf(
                volume=vol,
                ideas_root=ideas_root,
                repo_root=repo_root,
                output_pdf_override=tmp_path / "out.pdf",
            )


def test_pipeline_process_volume_book_not_found() -> None:
    """Verify process_volume_book raises ValueError for unknown volume ID."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cfg_file = tmp_path / "volumes.yaml"
        cfg_file.write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "volumes": {
                        "vol-1": {"title": "V1", "parts": []},
                    },
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="not found"):
            process_volume_book(
                volume_id="vol-nonexistent",
                ideas_root=tmp_path,
                repo_root=repo_root,
                config_path=cfg_file,
            )


def test_cli_typeset_volume_command_validation() -> None:
    """Verify CLI typeset validation handles volume flags correctly."""
    # Unknown volume argument
    args = argparse.Namespace(
        subcommand="typeset",
        idea=None,
        all=False,
        volume="unknown-vol-999",
        all_volumes=False,
        volumes_config=None,
        output_dir=None,
        force=False,
    )
    res = handle_typeset_command(args)
    assert res == 1
