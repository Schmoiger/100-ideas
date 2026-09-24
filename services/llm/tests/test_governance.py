"""Unit tests for token governance, fingerprinting, and spend circuit breakers."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from services.llm.caching import should_create_cache
from services.llm.client import get_genai_client, is_live_genai_available
from services.llm.governance import (
    BudgetExhaustedError,
    TokenGovernance,
    check_fingerprint_match,
    clamp_context,
    compute_input_fingerprint,
    estimate_cost,
    estimate_token_count,
    get_governance,
)
from services.llm.telemetry import TokenTelemetry, record_telemetry_in_meta


def test_client_resolution_without_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Verify that absent API key cleanly flags live unavailable and raises ValueError on client init."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Point to empty tmp directory so .env is not loaded from repo
    assert not is_live_genai_available(repo_root=tmp_path)
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        get_genai_client(repo_root=tmp_path)


def test_cost_estimation():
    """Verify pricing calculations for tiered models."""
    # gemini-2.5-flash: $0.075 / 1M prompt, $0.30 / 1M completion, $0.01875 / 1M cached
    flash_cost = estimate_cost(
        model="gemini-2.5-flash",
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
        cached_tokens=1_000_000,
    )
    assert pytest.approx(flash_cost, rel=1e-3) == (0.075 + 0.30 + 0.01875)

    # gemini-2.5-pro: $1.25 / 1M prompt, $5.00 / 1M completion, $0.3125 / 1M cached
    pro_cost = estimate_cost(
        model="gemini-2.5-pro",
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
        cached_tokens=1_000_000,
    )
    assert pytest.approx(pro_cost, rel=1e-3) == (1.25 + 5.00 + 0.3125)

    # imagen-3.0-generate-002: $0.03 per image
    img_cost = estimate_cost(model="imagen-3.0-generate-002", prompt_tokens=0, num_images=2)
    assert pytest.approx(img_cost, rel=1e-3) == 0.06


def test_context_clamping():
    """Verify that un-cached context is strictly clamped to the maximum token ceiling."""
    short_text = "This is a short input within boundaries."
    assert clamp_context(short_text, max_tokens=100) == short_text

    # Create oversized text (~20,000 words = ~80,000 chars = ~20,000 tokens)
    huge_text = "Detailed paragraph explaining software delivery bottlenecks. " * 1500
    clamped = clamp_context(huge_text, max_tokens=1000)

    assert len(clamped) < len(huge_text)
    assert "[... Context clamped" in clamped
    # Verify clamped length adheres to token estimate
    assert estimate_token_count(clamped) <= 1050


def test_cryptographic_fingerprinting():
    """Verify SHA-256 fingerprint generation and meta.yaml matching."""
    fp1 = compute_input_fingerprint(
        model_name="gemini-2.5-pro",
        prompt_template="Write chapter on testing",
        input_documents=["Document A content", "Document B content"],
    )
    assert fp1.startswith("sha256:")

    # Identical inputs yield identical hash
    fp2 = compute_input_fingerprint(
        model_name="gemini-2.5-pro",
        prompt_template="Write chapter on testing",
        input_documents=["Document A content", "Document B content"],
    )
    assert fp1 == fp2

    # Different prompt yields different hash
    fp3 = compute_input_fingerprint(
        model_name="gemini-2.5-pro",
        prompt_template="Write chapter on deployment",
        input_documents=["Document A content", "Document B content"],
    )
    assert fp1 != fp3


def test_fingerprint_matching_with_meta(tmp_path: Path):
    """Verify check_fingerprint_match against saved meta.yaml."""
    meta_file = tmp_path / "meta.yaml"
    fp = "sha256:abcd1234ef5678"

    meta_file.write_text(yaml.safe_dump({"id": "idea-001", "token_telemetry": {"fingerprint": fp}}))
    assert check_fingerprint_match(meta_file, fp)
    assert not check_fingerprint_match(meta_file, "sha256:different")


def test_circuit_breaker_idea_token_limit(monkeypatch: pytest.MonkeyPatch):
    """Verify BudgetExhaustedError when projected tokens exceed idea threshold."""
    monkeypatch.setenv("MAX_IDEA_TOKENS", "10000")
    TokenGovernance.reset()
    gov = get_governance()

    with pytest.raises(BudgetExhaustedError, match="exceeds maximum allowed idea token ceiling"):
        gov.check_preflight(
            model="gemini-2.5-pro",
            projected_prompt_tokens=15_000,
            projected_completion_tokens=1_000,
            idea_id="idea-001",
        )


def test_circuit_breaker_session_spend_limit(monkeypatch: pytest.MonkeyPatch):
    """Verify BudgetExhaustedError when session financial cap is breached."""
    monkeypatch.setenv("MAX_SESSION_SPEND_USD", "0.50")
    TokenGovernance.reset()
    gov = get_governance()

    # Pre-flight for request that fits within budget
    cost1 = gov.check_preflight(
        model="gemini-2.5-pro",
        projected_prompt_tokens=10_000,
        projected_completion_tokens=1_000,
    )
    assert cost1 < 0.50
    gov.record_usage(prompt_tokens=10_000, completion_tokens=1_000, cost_usd=cost1)

    # Next request breaches session budget
    gov.max_idea_tokens = 500_000
    with pytest.raises(BudgetExhaustedError, match="exceeding MAX_SESSION_SPEND_USD limit"):
        gov.check_preflight(
            model="gemini-2.5-pro",
            projected_prompt_tokens=400_000,  # 400k * $1.25/1M = $0.50 + prior spend > $0.50
            projected_completion_tokens=20_000,
        )


def test_context_caching_threshold():
    """Verify 32,768 token threshold for Gemini context caching."""
    small_doc = ["Paragraph of text. " * 50]
    assert not should_create_cache(small_doc)

    # ~35,000 tokens (> 140,000 characters)
    large_doc = ["Substantive architecture chapter with empirical evidence. " * 3000]
    assert should_create_cache(large_doc)


def test_telemetry_recording(tmp_path: Path):
    """Verify telemetry serialization and recording in meta.yaml."""
    meta_path = tmp_path / "meta.yaml"
    meta_path.write_text(yaml.safe_dump({"id": "idea-042", "status": "raw"}))

    telemetry = TokenTelemetry(
        model="gemini-2.5-pro",
        fingerprint="sha256:11223344",
        prompt_tokens=3200,
        cached_tokens=35000,
        completion_tokens=1500,
        total_tokens=39700,
        estimated_cost_usd=0.0125,
        latency_ms=980,
    )

    record_telemetry_in_meta(meta_path, telemetry)

    saved = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    assert "token_telemetry" in saved
    assert saved["token_telemetry"]["model"] == "gemini-2.5-pro"
    assert saved["token_telemetry"]["total_tokens"] == 39700
    assert saved["token_telemetry"]["cached_tokens"] == 35000
    assert len(saved["token_history"]) == 1
