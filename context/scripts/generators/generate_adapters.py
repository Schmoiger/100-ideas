# /// script
# dependencies = [
#   "pyyaml",
# ]
# ///
#!/usr/bin/env python3
from __future__ import annotations

"""Unified CLI dispatcher for runtime adapter projections.

Generates runtime-specific projections (Antigravity/Gemini, Claude Code,
GitHub Copilot, OpenAI/Codex) from canonical context/ definitions.

By default, only new or modified files are updated to preserve filesystem
timestamps and prevent unnecessary watcher/git noise.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from context.scripts.generators.adapters.claude.generator import (
    generate_claude_md,
    generate_subagent_prompts,
)
from context.scripts.generators.adapters.core.agents_md import generate_agents_md
from context.scripts.generators.adapters.core.loader import load_canonical_context
from context.scripts.generators.adapters.gemini.generator import (
    generate_gemini_md,
    generate_skills,
)
from context.scripts.generators.adapters.github.generator import (
    generate_copilot_instructions,
    generate_prompts,
    generate_scoped_instructions,
    generate_workflows,
)
from context.scripts.generators.adapters.openai.generator import (
    generate_runner_harness,
    generate_system_prompts,
    generate_tool_schemas,
)

SUPPORTED_TARGETS = {"all", "gemini", "claude", "github", "copilot", "codex", "openai"}

TARGET_ALIASES = {
    "all": "all",
    "gemini": "gemini",
    "g": "gemini",
    "claude": "claude",
    "c": "claude",
    "github": "github",
    "gh": "github",
    "copilot": "github",
    "p": "github",
    "codex": "openai",
    "openai": "openai",
    "o": "openai",
}

IGNORED_BLOCK = """
# Programmatically generated agent projections
.agents/skills/
.claude/prompts/
.github/instructions/
.github/prompts/
.github/copilot-instructions.md
.openai/prompts/
CLAUDE.md
GEMINI.md
AGENTS.md
"""


def ensure_root_gitignore(
    repo_root: Path,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> bool:
    """Ensure repo_root / .gitignore contains the generated agent projection ignore block.

    Returns True if .gitignore was created or updated, False otherwise.
    """
    gitignore_path = repo_root / ".gitignore"
    required_entries = [
        line.strip()
        for line in IGNORED_BLOCK.strip().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        missing = [entry for entry in required_entries if entry not in content]
        if not missing:
            return False

        if not dry_run:
            delimiter = "\n" if content.endswith("\n") else "\n\n"
            gitignore_path.write_text(content + delimiter + IGNORED_BLOCK.strip() + "\n")
        if verbose and not quiet:
            print("  * [UPDATE]  .gitignore (added agent projection ignores)")
        return True
    else:
        if not dry_run:
            gitignore_path.write_text(IGNORED_BLOCK.strip() + "\n")
        if verbose and not quiet:
            print("  + [NEW]     .gitignore")
        return True


def normalize_target(target: str) -> str:
    """Normalize target string to canonical target name."""
    cleaned = target.strip().lower()
    if cleaned in TARGET_ALIASES:
        return TARGET_ALIASES[cleaned]
    valid_keys = ", ".join(sorted(set(TARGET_ALIASES.keys())))
    raise ValueError(f"Unknown target '{target}'. Valid targets: {valid_keys}")


def load_configured_targets(repo_root: Path) -> set[str] | None:
    """Load active targets from .agent-targets file if present.

    Returns a set of normalized target names, or None if file does not exist
    or specifies 'all'.
    """
    targets_file = repo_root / ".agent-targets"
    if not targets_file.is_file():
        return None

    raw = targets_file.read_text()
    targets = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for item in line.split(","):
            cleaned = item.strip().lower()
            if cleaned:
                targets.add(normalize_target(cleaned))

    if "all" in targets or not targets:
        return None
    return targets


def get_adapter_projections(
    context: dict[str, Any],
    repo_root: Path,
    targets: set[str] | None = None,
) -> dict[Path, str]:
    """Generates expected file projections in-memory without writing to disk.

    Args:
        context: Canonical context dictionary.
        repo_root: Repository root path.
        targets: Set of normalized target names ('all', 'gemini', 'claude', 'github', 'openai').

    Returns:
        Mapping of target Path -> generated string content.
    """
    if targets is None or "all" in targets:
        active_targets = {"core", "gemini", "claude", "github", "openai"}
    else:
        active_targets = set(targets)
        # Gemini and Claude reference @AGENTS.md, so include core if either is targeted
        if "gemini" in active_targets or "claude" in active_targets:
            active_targets.add("core")

    projections: dict[Path, str] = {}

    if "core" in active_targets:
        projections.update(generate_agents_md(context, repo_root, dry_run=True))

    if "gemini" in active_targets:
        projections.update(generate_skills(context, repo_root, dry_run=True))
        projections.update(generate_gemini_md(context, repo_root, dry_run=True))

    if "claude" in active_targets:
        projections.update(generate_claude_md(context, repo_root, dry_run=True))
        projections.update(generate_subagent_prompts(context, repo_root, dry_run=True))

    if "github" in active_targets:
        projections.update(generate_copilot_instructions(context, repo_root, dry_run=True))
        projections.update(generate_prompts(context, repo_root, dry_run=True))
        projections.update(generate_scoped_instructions(repo_root, dry_run=True))
        projections.update(generate_workflows(repo_root, dry_run=True))

    if "openai" in active_targets:
        projections.update(generate_system_prompts(context, repo_root, dry_run=True))
        projections.update(generate_tool_schemas(context, repo_root, dry_run=True))
        projections.update(generate_runner_harness(repo_root, dry_run=True))

    return projections


def run_generation(
    repo_root: Path | None = None,
    context_dir: Path | None = None,
    targets: set[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> dict[str, Any]:
    """Execute projection generation with change detection and write policies.

    Args:
        repo_root: Repository root path (default: auto-detected).
        context_dir: Path to context directory (default: <repo_root>/context).
        targets: Target runtimes to generate.
        force: If True, overwrite all files even if unchanged.
        dry_run: If True, preview changes without writing to disk.
        verbose: If True, print details for each file.
        quiet: If True, suppress informational output.

    Returns:
        Dictionary containing execution summary and lists of affected paths.
    """
    if repo_root is None:
        if (Path.cwd() / "context").is_dir():
            repo_root = Path.cwd()
        else:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
    if context_dir is None:
        context_dir = repo_root / "context"

    context = load_canonical_context(str(context_dir))
    projections = get_adapter_projections(context, repo_root, targets)

    created: list[Path] = []
    updated: list[Path] = []
    unchanged: list[Path] = []

    for path, content in projections.items():
        rel_path = path.relative_to(repo_root) if path.is_relative_to(repo_root) else path

        if not path.exists():
            created.append(path)
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            if verbose and not quiet:
                print(f"  + [NEW]     {rel_path}")
        else:
            existing_content = path.read_text()
            if existing_content != content or force:
                updated.append(path)
                if not dry_run:
                    path.write_text(content)
                if verbose and not quiet:
                    action = "[FORCE]" if (existing_content == content and force) else "[UPDATE]"
                    print(f"  * {action}  {rel_path}")
            else:
                unchanged.append(path)
                if verbose and not quiet:
                    print(f"  . [SKIP]    {rel_path} (unchanged)")

    # Ensure root .gitignore ignores generated projections
    ensure_root_gitignore(repo_root, dry_run=dry_run, verbose=verbose, quiet=quiet)

    if not quiet:
        mode_str = " (dry run)" if dry_run else ""
        print(
            f"Projections summary{mode_str}: "
            f"{len(created)} created, {len(updated)} updated, {len(unchanged)} unchanged."
        )

    return {
        "projections": projections,
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "dry_run": dry_run,
        "force": force,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser with comprehensive help."""
    parser = argparse.ArgumentParser(
        prog="agent-harness",
        description="Regenerate runtime adapter projections from canonical context/ definitions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python generate_adapters.py                      # Smart update: write only changed/new files (default)
  python generate_adapters.py -a                   # Force-regenerate all files across all runtimes
  python generate_adapters.py -d                   # Dry-run: preview files that would be changed
  python generate_adapters.py -t claude            # Smart update Claude Code projections only
  python generate_adapters.py -t COPILOT -a        # Force-regenerate GitHub Copilot projections
  python generate_adapters.py -g -d                # Dry-run preview for Gemini / Antigravity
  python generate_adapters.py -c -v                # Verbose update for Claude Code projections
""",
    )

    # Target selection
    target_group = parser.add_argument_group("target selection")
    target_group.add_argument(
        "-t",
        "--target",
        metavar="TARGET",
        help=(
            "Target runtime to project: 'all', 'gemini' (or 'g'), 'claude' (or 'c'), "
            "'github'/'copilot' (or 'gh'/'p'), 'codex'/'openai' (or 'o'). Case-insensitive. "
            "(default: all)"
        ),
    )
    target_group.add_argument(
        "-g",
        "--gemini",
        action="store_true",
        help="Convenience flag: project Gemini / Antigravity runtime",
    )
    target_group.add_argument(
        "-c",
        "--claude",
        action="store_true",
        help="Convenience flag: project Claude Code runtime",
    )
    target_group.add_argument(
        "-p",
        "--copilot",
        action="store_true",
        help="Convenience flag: project GitHub Copilot runtime",
    )
    target_group.add_argument(
        "-o",
        "--codex",
        "--openai",
        action="store_true",
        dest="codex",
        help="Convenience flag: project OpenAI / Codex runtime",
    )

    # Generation mode (mutually exclusive)
    mode_group = parser.add_argument_group("generation modes")
    mode_mutex = mode_group.add_mutually_exclusive_group()
    mode_mutex.add_argument(
        "-n",
        "--new",
        action="store_true",
        help=(
            "Update only new or changed files, preserving timestamps for unchanged files. "
            "(default behaviour)"
        ),
    )
    mode_mutex.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Force full regeneration of all files across selected targets, overwriting even if unchanged.",
    )

    # Operational modifiers
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Preview actions without writing any changes to disk.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-file status details during generation.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress summary output messages.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repository root path (default: auto-detected).",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="Override context directory path (default: <repo-root>/context).",
    )

    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Resolve selected targets from options and flags
    selected_targets: set[str] = set()
    if args.target:
        selected_targets.add(normalize_target(args.target))
    if args.gemini:
        selected_targets.add("gemini")
    if args.claude:
        selected_targets.add("claude")
    if args.copilot:
        selected_targets.add("github")
    if args.codex:
        selected_targets.add("openai")

    if not selected_targets:
        repo_root = args.repo_root or (Path.cwd() if (Path.cwd() / "context").is_dir() else _REPO_ROOT)
        configured = load_configured_targets(repo_root)
        selected_targets = configured if configured else {"all"}

    force = bool(args.all)

    run_generation(
        repo_root=args.repo_root,
        context_dir=args.context_dir,
        targets=selected_targets,
        force=force,
        dry_run=args.dry_run,
        verbose=args.verbose,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
