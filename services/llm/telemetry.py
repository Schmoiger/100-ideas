"""Token telemetry models and persistence for idea metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class TokenTelemetry(BaseModel):
    """Execution telemetry tracking token consumption, caching, and financial spend."""

    model: str = Field(
        description="Target model identifier (e.g. gemini-2.5-flash, gemini-2.5-pro)"
    )
    fingerprint: str = Field(description="SHA-256 hash of inputs for idempotent bypass")
    prompt_tokens: int = Field(default=0, description="Number of input prompt tokens")
    cached_tokens: int = Field(default=0, description="Number of cached input tokens")
    completion_tokens: int = Field(default=0, description="Number of output completion tokens")
    total_tokens: int = Field(default=0, description="Total tokens processed in operation")
    estimated_cost_usd: float = Field(default=0.0, description="Projected financial cost in USD")
    latency_ms: int = Field(default=0, description="Operation round-trip latency in milliseconds")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of execution",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert telemetry to standard serializable dictionary."""
        return {
            "model": self.model,
            "fingerprint": self.fingerprint,
            "prompt_tokens": self.prompt_tokens,
            "cached_tokens": self.cached_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


def record_telemetry_in_meta(meta_path: Path, telemetry: TokenTelemetry) -> None:
    """Record token telemetry into idea's meta.yaml safely and atomically."""
    if not meta_path.is_file():
        return

    try:
        content = meta_path.read_text(encoding="utf-8")
        data: Any = yaml.safe_load(content)
        if not isinstance(data, dict):
            return

        # Store latest token telemetry
        data["token_telemetry"] = telemetry.to_dict()

        # Append to historical ledger
        history = data.setdefault("token_history", [])
        if isinstance(history, list):
            history.append(telemetry.to_dict())

        # Atomic write
        temp_meta = meta_path.parent / f".{meta_path.name}.tmp"
        temp_meta.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        temp_meta.replace(meta_path)
    except Exception:
        # Never corrupt metadata on telemetry logging failure
        pass
