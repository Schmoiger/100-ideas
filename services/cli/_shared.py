"""Shared path helpers and batch execution utilities for CLI commands.

These are extracted from ``services.ingestion.cli`` so that all command
modules can import them without depending on the ingestion domain package.
"""

from __future__ import annotations

from pathlib import Path


def get_default_paths() -> tuple[Path, Path, Path, Path]:
    """Return default project paths for catalog, snapshot, inbox, and ideas directory."""
    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    catalog_path: Path = repo_root / "artefacts" / "product" / "100-ideas.md"
    snapshot_path: Path = repo_root / "artefacts" / "product" / "100-ideas.snapshot.md"
    inbox_path: Path = repo_root / "artefacts" / "product" / "inbox.md"
    ideas_dir: Path = repo_root / "artefacts" / "content" / "ideas"
    return catalog_path, snapshot_path, inbox_path, ideas_dir


def get_repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parent.parent.parent


def get_inbox_archive_path() -> Path:
    """Return default project path for inbox archive."""
    return get_repo_root() / "artefacts" / "product" / "inbox-archive.md"


def resolve_ideas_to_process(idea_arg: str | None, all_arg: bool, ideas_dir: Path) -> list[str]:
    """Resolve target idea identifier(s) from either --idea or --all."""
    if idea_arg:
        return [idea_arg]
    if all_arg and ideas_dir.is_dir():
        ideas: list[str] = []
        for p in sorted(ideas_dir.iterdir()):
            if p.is_dir() and p.name.startswith("idea-"):
                ideas.append(p.name)
        return ideas
    return []


def confirm_batch_execution(
    ideas_to_process: list[str],
    operation_name: str,
    model_name: str = "gemini-2.5-flash",
    yes: bool = False,
) -> bool:
    """Prompt user before processing multiple ideas in batch unless --yes is passed.

    Enforces Guard Rail 6 (Interactive Batch Confirmation).
    """
    if len(ideas_to_process) <= 1 or yes:
        return True

    from services.llm.governance import estimate_cost

    tokens_per_idea = 4000 if "pipeline" in operation_name else 2500
    total_tokens = len(ideas_to_process) * tokens_per_idea
    est_cost = estimate_cost(
        model=model_name,
        prompt_tokens=total_tokens,
        completion_tokens=len(ideas_to_process) * 1000,
    )

    prompt_msg = (
        f"Ready to process {len(ideas_to_process)} ideas (~{total_tokens // 1000}k tokens, "
        f"est. ${est_cost:.2f} USD). Proceed? [y/N]: "
    )
    try:
        ans = input(prompt_msg).strip().lower()
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False
