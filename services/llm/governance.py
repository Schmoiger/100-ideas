"""Token governance, cryptographic fingerprinting, and spend circuit breakers."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import yaml


class BudgetExhaustedError(RuntimeError):
    """Raised when token or financial spend limits are breached."""


# Pricing per 1,000,000 tokens (USD)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {
        "prompt": 0.075,
        "cached": 0.01875,
        "completion": 0.30,
    },
    "gemini-2.5-pro": {
        "prompt": 1.25,
        "cached": 0.3125,
        "completion": 5.00,
    },
    "imagen-3.0-generate-002": {
        "per_image": 0.03,
    },
}

DEFAULT_MAX_SESSION_SPEND_USD = 2.00
DEFAULT_MAX_IDEA_TOKENS = 50_000
DEFAULT_MAX_UNCACHED_CONTEXT_TOKENS = 12_000


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int = 0,
    cached_tokens: int = 0,
    num_images: int = 0,
) -> float:
    """Calculate projected cost in USD for a given model and token counts."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-2.5-flash"])

    if "per_image" in pricing:
        return pricing["per_image"] * max(1, num_images)

    prompt_cost = (prompt_tokens / 1_000_000.0) * pricing.get("prompt", 0.075)
    cached_cost = (cached_tokens / 1_000_000.0) * pricing.get("cached", 0.01875)
    completion_cost = (completion_tokens / 1_000_000.0) * pricing.get("completion", 0.30)

    return prompt_cost + cached_cost + completion_cost


def estimate_token_count(text: str) -> int:
    """Estimate token count heuristically (roughly 4 characters per token for English text)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def clamp_context(
    text: str,
    max_tokens: int = DEFAULT_MAX_UNCACHED_CONTEXT_TOKENS,
    truncation_indicator: str = "\n\n[... Context clamped to prevent token budget overload ...]\n",
) -> str:
    """Clamp un-cached input context strictly to an upper token limit (approx 4 chars/token)."""
    estimated = estimate_token_count(text)
    if estimated <= max_tokens:
        return text

    # Truncate by character budget
    char_budget = max_tokens * 4
    if len(text) <= char_budget:
        return text

    return text[: char_budget - len(truncation_indicator)] + truncation_indicator


def compute_input_fingerprint(
    model_name: str,
    prompt_template: str,
    input_documents: list[str] | None = None,
) -> str:
    """Compute SHA-256 fingerprint over tuple (model_name, prompt_template_hash, input_documents_hash)."""
    hasher = hashlib.sha256()
    hasher.update(model_name.strip().encode("utf-8"))
    hasher.update(b":")

    prompt_hash = hashlib.sha256(prompt_template.encode("utf-8")).hexdigest()
    hasher.update(prompt_hash.encode("utf-8"))
    hasher.update(b":")

    if input_documents:
        for doc in input_documents:
            doc_hash = hashlib.sha256(doc.encode("utf-8")).hexdigest()
            hasher.update(doc_hash.encode("utf-8"))
            hasher.update(b":")
    else:
        hasher.update(b"none")

    return f"sha256:{hasher.hexdigest()}"


def check_fingerprint_match(meta_path: Path, fingerprint: str) -> bool:
    """Return True if meta.yaml already records an identical input fingerprint."""
    if not meta_path.is_file():
        return False

    try:
        data: Any = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        telemetry = data.get("token_telemetry")
        if isinstance(telemetry, dict) and telemetry.get("fingerprint") == fingerprint:
            return True
    except Exception:
        pass

    return False


class TokenGovernance:
    """Central singleton accumulator managing session spend and enforcing circuit breakers."""

    _instance: TokenGovernance | None = None

    def __init__(self) -> None:
        self.max_session_spend_usd: float = float(
            os.environ.get("MAX_SESSION_SPEND_USD", DEFAULT_MAX_SESSION_SPEND_USD)
        )
        self.max_idea_tokens: int = int(os.environ.get("MAX_IDEA_TOKENS", DEFAULT_MAX_IDEA_TOKENS))
        self.max_uncached_context_tokens: int = int(
            os.environ.get("MAX_UNCACHED_CONTEXT_TOKENS", DEFAULT_MAX_UNCACHED_CONTEXT_TOKENS)
        )

        self.session_prompt_tokens: int = 0
        self.session_cached_tokens: int = 0
        self.session_completion_tokens: int = 0
        self.session_total_tokens: int = 0
        self.session_spend_usd: float = 0.0

    @classmethod
    def get_instance(cls) -> TokenGovernance:
        """Get or initialize singleton instance."""
        if cls._instance is None:
            cls._instance = TokenGovernance()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (useful for test isolation)."""
        cls._instance = None

    def check_preflight(
        self,
        model: str,
        projected_prompt_tokens: int,
        projected_completion_tokens: int = 1000,
        cached_tokens: int = 0,
        idea_id: str | None = None,
    ) -> float:
        """Verify projected execution will not breach idea token cap or session spend ceiling.

        Returns projected cost in USD. Raises BudgetExhaustedError if limits are breached.
        """
        projected_tokens = projected_prompt_tokens + projected_completion_tokens + cached_tokens
        if projected_tokens > self.max_idea_tokens:
            raise BudgetExhaustedError(
                f"Projected tokens ({projected_tokens:,}) for idea {idea_id or 'unknown'} "
                f"exceeds maximum allowed idea token ceiling ({self.max_idea_tokens:,}). "
                "Halting execution to prevent runaway token spend."
            )

        projected_cost = estimate_cost(
            model=model,
            prompt_tokens=projected_prompt_tokens,
            completion_tokens=projected_completion_tokens,
            cached_tokens=cached_tokens,
        )

        new_total_spend = self.session_spend_usd + projected_cost
        if new_total_spend > self.max_session_spend_usd:
            raise BudgetExhaustedError(
                f"Operation would increase session spend to ${new_total_spend:.4f}, "
                f"exceeding MAX_SESSION_SPEND_USD limit (${self.max_session_spend_usd:.2f}). "
                "Circuit breaker tripped: execution halted immediately."
            )

        return projected_cost

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record completed token usage in central telemetry accumulator."""
        self.session_prompt_tokens += prompt_tokens
        self.session_cached_tokens += cached_tokens
        self.session_completion_tokens += completion_tokens
        self.session_total_tokens += prompt_tokens + completion_tokens + cached_tokens
        self.session_spend_usd += cost_usd


def get_governance() -> TokenGovernance:
    """Convenience accessor for TokenGovernance singleton."""
    return TokenGovernance.get_instance()
