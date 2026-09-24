"""Catalog synchronisation and sandbox-boundary resolution."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def is_readable_file(path: Path) -> bool:
    """Check if a file exists and can be opened for reading."""
    try:
        if not path.is_file():
            return False
        with path.open("rb") as handle:
            handle.read(1)
        return True
    except (OSError, PermissionError):
        return False


def resolve_catalog_source(catalog_path: Path, snapshot_path: Path) -> Path:
    """Resolve authoritative catalog source or fall back to local snapshot.

    Handles REQ-ING-003: If catalog_path is a symbolic link resolving outside
    the workspace boundary or encounters permission exceptions under sandbox constraints,
    falls back transparently to snapshot_path.
    """
    if is_readable_file(catalog_path):
        return catalog_path

    if is_readable_file(snapshot_path):
        return snapshot_path

    raise FileNotFoundError(
        f"Unable to read catalog at {catalog_path} (permission or link error) "
        f"and no snapshot found at {snapshot_path}."
    )


def sync_catalog_source(source_path: Path, snapshot_path: Path) -> Path:
    """Copy authoritative catalog source into workspace boundary snapshot.

    Handles REQ-ING-003: Ensures tools within the standard sandbox can read idea
    records without filesystem permission exceptions.
    """
    if not is_readable_file(source_path):
        raise PermissionError(
            f"Cannot sync from {source_path}: source file is inaccessible or permission denied."
        )

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    # Copy following symlinks
    shutil.copyfile(os.path.realpath(source_path), snapshot_path)
    return snapshot_path
