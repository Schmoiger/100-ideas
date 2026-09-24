"""Tests for Gemini 2.5 Pro chapter drafting, fingerprinting, and pre-flight estimation."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.llm.governance import TokenGovernance
from services.typesetting.drafter import ChapterManuscriptSchema, draft_book_chapter


def _create_mock_idea(idea_id: str = "idea-015") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Decoupled Agentic Publishing",
        synopsis="Decoupling content generation pipelines from monolithic publishing platforms.",
        tags=["publishing", "architecture"],
    )


def test_drafter_fingerprint_bypass_and_force_llm():
    """Verify that matching input fingerprint bypasses chapter drafting unless --force-llm is passed."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-015")
        provision_idea(idea, ideas_root)

        # First run: drafts chapter and records fingerprint
        chapter_path, gen1 = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            force=False,
        )
        assert gen1 is True
        assert chapter_path.is_file()

        meta_file = ideas_root / "idea-015" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert "token_telemetry" in meta_dict
        fingerprint = meta_dict["token_telemetry"]["fingerprint"]
        assert fingerprint.startswith("sha256:")

        # Second run with force=True, force_llm=False -> Fingerprint matches, zero-token bypass
        chapter_path, gen2 = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            force=True,
            force_llm=False,
        )
        assert gen2 is False

        # Third run with force_llm=True -> Bypasses fingerprint cache
        chapter_path, gen3 = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            force_llm=True,
        )
        assert gen3 is True


def test_drafter_dry_run_estimation():
    """Verify --dry-run calculates projected tokens and cost without writing final chapter.md."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-025")
        provision_idea(idea, ideas_root)

        chapter_path, gen = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            dry_run=True,
        )
        assert gen is False
        assert not chapter_path.is_file()

        meta_file = ideas_root / "idea-025" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert "token_telemetry" in meta_dict
        telemetry = meta_dict["token_telemetry"]
        assert "dry-run" in telemetry["model"]
        assert telemetry["total_tokens"] > 0
        assert telemetry["estimated_cost_usd"] > 0


def test_drafter_with_mocked_gemini_client():
    """Verify live Gemini 2.5 Pro dispatch, structured Pydantic schema, and token telemetry recording."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-035")
        provision_idea(idea, ideas_root)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed = ChapterManuscriptSchema(
            lead_punch="Monolithic publishing platforms have spent twenty years holding editorial teams hostage.",
            mechanics_section="Every publishing pipeline eventually accretes technical calcification. Digital rust builds behind the CMS.",
            economic_section="What does continuous syndication actually cost us in delivery velocity and cash? | Dimension | Old | New |",
            hype_section="Headless CMS vendors promise effortless nirvana. Except reality is messier.",
            takeaways=[
                "**Decouple authoring from delivery**: Separate markdown storage from presentation targets.",
                "**Enforce deterministic gates**: Never publish without automated verification.",
            ],
            citations=["`ref-pub-01`: Content Operations Whitepaper"],
        )
        mock_response.usage_metadata.prompt_token_count = 2100
        mock_response.usage_metadata.candidates_token_count = 1450
        mock_response.usage_metadata.cached_content_token_count = 0
        mock_client.models.generate_content.return_value = mock_response

        chapter_path, gen = draft_book_chapter(
            idea=idea,
            ideas_root=ideas_root,
            client=mock_client,
        )

        assert gen is True
        assert chapter_path.is_file()
        content = chapter_path.read_text(encoding="utf-8")
        assert "Monolithic publishing platforms" in content
        assert "Digital rust builds behind the CMS" in content

        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.5-pro"
        assert call_kwargs["config"].response_schema == ChapterManuscriptSchema

        meta_file = ideas_root / "idea-035" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        telemetry = meta_dict["token_telemetry"]
        assert telemetry["model"] == "gemini-2.5-pro"
        assert telemetry["prompt_tokens"] == 2100
        assert telemetry["completion_tokens"] == 1450
        assert telemetry["total_tokens"] == 3550
