"""Lifecycle state machine and transition rules for continuous publishing."""

from __future__ import annotations

from typing import Any

VALID_STAGES: tuple[str, ...] = (
    "raw",
    "research_ready",
    "draft_in_progress",
    "human_review",
    "approved",
    "published",
)

VALID_REVIEW_STATUSES: tuple[str, ...] = (
    "pending",
    "needs_revision",
    "approved",
)

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "raw": {"research_ready"},
    "research_ready": {"draft_in_progress", "human_review", "raw"},
    "draft_in_progress": {"human_review", "draft_in_progress", "research_ready"},
    "human_review": {"human_review", "approved", "draft_in_progress"},
    "approved": {"published", "human_review"},
    "published": {"approved", "human_review"},
}


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""

    pass


def validate_transition(
    current_stage: str,
    target_stage: str,
    editorial_quality: dict[str, Any] | None = None,
    force: bool = False,
) -> None:
    """Validate whether transitioning from current_stage to target_stage is allowed.

    Raises:
        InvalidStateTransitionError: If target_stage is invalid or transition disallowed.
    """
    if target_stage not in VALID_STAGES:
        raise InvalidStateTransitionError(
            f"Invalid target stage '{target_stage}'. Must be one of {VALID_STAGES}."
        )

    if current_stage not in VALID_STAGES:
        # If current stage unknown/legacy, allow transition to any valid stage if force=True or default
        if not force:
            raise InvalidStateTransitionError(f"Unknown current stage '{current_stage}'.")
        return

    if force:
        return

    allowed = ALLOWED_TRANSITIONS.get(current_stage, set())
    if target_stage not in allowed:
        raise InvalidStateTransitionError(
            f"Cannot transition idea from '{current_stage}' to '{target_stage}'. "
            f"Allowed target stages: {sorted(allowed)}."
        )

    # Extra invariant: Transitioning to 'approved' requires voice_fidelity in editorial_quality
    if target_stage == "approved":
        eq = editorial_quality or {}
        if not eq.get("voice_fidelity"):
            raise InvalidStateTransitionError(
                "Cannot transition to 'approved' without passed editorial quality gate (voice_fidelity=True)."
            )
