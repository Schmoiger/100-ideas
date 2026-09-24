"""Safeguard enforcement protecting manual edits and locked ideas from automated overwriting."""

from __future__ import annotations

from pathlib import Path

from services.ingestion.models import IdeaRecord


class ManualEditProtectionError(PermissionError):
    """Raised when an operation attempts to overwrite human-edited files without --overwrite-manual."""

    pass


class IdeaLockedError(PermissionError):
    """Raised when an automated command targets an idea with locked=True."""

    pass


def check_manual_edit_safeguard(
    target_file: Path,
    idea: IdeaRecord,
    force: bool = False,
    overwrite_manual: bool = False,
) -> None:
    """Enforce manual edit protection and locked status invariants.

    Invariants:
    1. If idea.locked is True and neither force nor overwrite_manual is set, blocks execution.
    2. If target_file exists and idea.human_modified is True:
       - Refuses to overwrite unless overwrite_manual=True.
       - Standard force=True does NOT bypass human_modified protection.
    """
    if idea.locked and not overwrite_manual and not force:
        raise IdeaLockedError(
            f"Refusing to modify locked idea '{idea.id}'. Use --overwrite-manual or unlock in meta.yaml."
        )

    if target_file.is_file() and idea.human_modified and not overwrite_manual:
        raise ManualEditProtectionError(
            f"Refusing to overwrite manual edits in {target_file}. Use --overwrite-manual to override."
        )
