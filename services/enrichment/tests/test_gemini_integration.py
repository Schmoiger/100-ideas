"""Tests for live Gemini SDK integration, fingerprint bypass, and dry-run in enrichment."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from services.enrichment.researcher import ResearchDossierSchema, synthesise_research
from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.llm.governance import TokenGovernance


def _create_mock_idea(idea_id: str = "idea-010") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Automated Quality Gates",
        synopsis="Using deterministic verification gates to stop unverified code from reaching production.",
        tags=["governance", "testing"],
    )


def test_research_fingerprint_bypass_and_force_llm():
    """Verify that matching input fingerprint bypasses re-generation unless --force-llm is passed."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-010")
        provision_idea(idea, ideas_root)

        # First run: generates notes and writes fingerprint
        notes_path, gen1 = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            force=False,
        )
        assert gen1 is True
        assert notes_path.is_file()

        meta_file = ideas_root / "idea-010" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert "token_telemetry" in meta_dict
        fingerprint = meta_dict["token_telemetry"]["fingerprint"]
        assert fingerprint.startswith("sha256:")

        # Second run with force=True, but force_llm=False -> Fingerprint matches, zero-token bypass
        notes_path, gen2 = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            force=True,
            force_llm=False,
        )
        assert gen2 is False

        # Third run with force_llm=True -> Bypasses fingerprint cache
        notes_path, gen3 = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            force_llm=True,
        )
        assert gen3 is True


def test_research_dry_run_estimation():
    """Verify --dry-run calculates projected tokens and cost without writing final output."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-020")
        provision_idea(idea, ideas_root)

        notes_path, gen = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            dry_run=True,
        )
        assert gen is False
        assert not notes_path.is_file()

        meta_file = ideas_root / "idea-020" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert "token_telemetry" in meta_dict
        telemetry = meta_dict["token_telemetry"]
        assert "dry-run" in telemetry["model"]
        assert telemetry["total_tokens"] > 0
        assert telemetry["estimated_cost_usd"] > 0


def test_research_with_mocked_gemini_client():
    """Verify live Gemini SDK dispatch, structured Pydantic output, and token telemetry recording."""
    TokenGovernance.reset()
    with tempfile.TemporaryDirectory() as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        res_root = Path(tmp_dir) / "resources"
        ideas_root.mkdir(parents=True)
        res_root.mkdir(parents=True)

        idea = _create_mock_idea("idea-030")
        provision_idea(idea, ideas_root)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed = ResearchDossierSchema(
            empirical_evidence=[
                "Field test: 45% reduction in production regressions across 12 teams."
            ],
            economic_tradeoffs=[
                "Upstream verification overhead shifts constraint away from production hotfixes."
            ],
            counterarguments=["Flaky test suites invalidate deterministic gates."],
            citations=["`ref-001`: Core Architecture Whitepaper"],
        )
        mock_response.usage_metadata.prompt_token_count = 1420
        mock_response.usage_metadata.candidates_token_count = 620
        mock_response.usage_metadata.cached_content_token_count = 0
        mock_client.models.generate_content.return_value = mock_response

        notes_path, gen = synthesise_research(
            idea=idea,
            ideas_root=ideas_root,
            resources_root=res_root,
            client=mock_client,
        )

        assert gen is True
        assert notes_path.is_file()
        content = notes_path.read_text(encoding="utf-8")
        assert "45% reduction in production regressions" in content
        assert "Upstream verification overhead" in content

        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.5-flash"
        assert call_kwargs["config"].response_schema == ResearchDossierSchema

        meta_file = ideas_root / "idea-030" / "meta.yaml"
        meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        telemetry = meta_dict["token_telemetry"]
        assert telemetry["model"] == "gemini-2.5-flash"
        assert telemetry["prompt_tokens"] == 1420
        assert telemetry["completion_tokens"] == 620
        assert telemetry["total_tokens"] == 2040
