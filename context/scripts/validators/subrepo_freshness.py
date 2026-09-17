#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
from __future__ import annotations

"""Pre-commit & CI validator: detects divergence between tracked subrepos and canonical upstream repositories.

Ensures that before local changes to a subrepo are merged to main, the subrepo's tracked commit
matches the latest commit on upstream remote HEAD, preventing desynchronisation and push rejections.
"""

import argparse
import configparser
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubrepoConfig:
    name: str
    subdir: Path
    gitrepo_file: Path
    remote: str
    branch: str
    commit: str
    parent: str | None = None


def find_subrepos(repo_root: Path) -> list[SubrepoConfig]:
    """Discovers all directories containing a .gitrepo tracking file."""
    subrepos: list[SubrepoConfig] = []
    for gitrepo in repo_root.glob("*/.gitrepo"):
        if not gitrepo.is_file():
            continue
        subdir = gitrepo.parent
        parser = configparser.ConfigParser(comment_prefixes=(";", "#"))
        try:
            parser.read_string(gitrepo.read_text(encoding="utf-8"))
            if not parser.has_section("subrepo"):
                continue
            remote = parser.get("subrepo", "remote")
            branch = parser.get("subrepo", "branch", fallback="main")
            commit = parser.get("subrepo", "commit")
            parent = parser.get("subrepo", "parent", fallback=None)
            subrepos.append(
                SubrepoConfig(
                    name=subdir.name,
                    subdir=subdir,
                    gitrepo_file=gitrepo,
                    remote=remote,
                    branch=branch,
                    commit=commit,
                    parent=parent,
                )
            )
        except (configparser.Error, OSError) as exc:
            print(f"Warning: Failed to parse {gitrepo}: {exc}", file=sys.stderr)
    return sorted(subrepos, key=lambda s: s.name)


def get_modified_files(repo_root: Path) -> set[str]:
    """Identifies modified files in current branch/working tree relative to base branch or HEAD."""
    modified: set[str] = set()

    # 1. Uncommitted / working tree changes
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            modified.update(res.stdout.strip().splitlines())
    except (subprocess.SubprocessError, OSError):
        pass

    # 2. Branch changes against base branch
    base_ref = os.environ.get("GITHUB_BASE_REF")
    candidates = []
    if base_ref:
        candidates.extend([f"origin/{base_ref}", base_ref])
    candidates.extend(["origin/main", "origin/master", "main", "master", "HEAD~1"])

    for candidate in candidates:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", f"{candidate}...HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                if res.stdout.strip():
                    modified.update(res.stdout.strip().splitlines())
                break
        except (subprocess.SubprocessError, OSError):
            continue

    return modified


def query_upstream_head(remote: str, branch: str, timeout_seconds: int = 15) -> str | None:
    """Queries upstream remote repository using git ls-remote to find HEAD SHA."""
    try:
        res = subprocess.run(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split()
            if parts:
                return parts[0]
        elif res.stderr.strip():
            print(f"Notice: git ls-remote failed for {remote}: {res.stderr.strip()}", file=sys.stderr)
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"Warning: Failed to reach remote {remote}: {exc}", file=sys.stderr)
    return None



def check_subrepo_freshness(
    repo_root: Path | None = None,
    check_all: bool = False,
    subrepo_names: list[str] | None = None,
    allow_offline: bool = False,
) -> tuple[bool, list[str]]:
    """Validates that tracked subrepos match upstream HEAD when local changes exist.

    Args:
        repo_root: Path to repository root.
        check_all: If True, check all subrepos regardless of whether local changes exist.
        subrepo_names: Optional specific list of subrepos to check.
        allow_offline: If True, skip network failures gracefully instead of erroring.

    Returns:
        (is_fresh: bool, issues: list[str])
    """
    if repo_root is None:
        repo_root = Path.cwd()

    subrepos = find_subrepos(repo_root)
    if not subrepos:
        return True, ["No tracked subrepos (.gitrepo) found in repository."]

    if subrepo_names:
        filter_set = set(subrepo_names)
        subrepos = [s for s in subrepos if s.name in filter_set]

    modified_files = get_modified_files(repo_root) if not check_all else set()
    issues: list[str] = []

    for subrepo in subrepos:
        prefix = f"{subrepo.name}/"
        has_changes = check_all or any(f.startswith(prefix) for f in modified_files)

        if not has_changes:
            continue

        remote_head = query_upstream_head(subrepo.remote, subrepo.branch)
        if remote_head is None:
            if allow_offline:
                print(
                    f"Notice: Could not contact remote for '{subrepo.name}'. Skipping due to allow-offline.",
                    file=sys.stderr,
                )
                continue
            issues.append(
                f"Subrepo '{subrepo.name}': Unable to reach upstream remote ({subrepo.remote})."
            )
            continue

        if remote_head != subrepo.commit:
            issues.append(
                f"Subrepo '{subrepo.name}' is out of sync with upstream!\n"
                f"  Remote:          {subrepo.remote} (branch: {subrepo.branch})\n"
                f"  Upstream HEAD:   {remote_head}\n"
                f"  Tracked Commit:  {subrepo.commit}\n"
                f"  Local changes:   Detected modifications in '{subrepo.name}/'\n"
                f"  Action Required: Pull upstream updates into your branch before merging:\n"
                f'                   PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull {subrepo.name}'
            )

    return len(issues) == 0, issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify subrepo tracking commits against canonical upstream repositories."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all subrepos unconditionally, even if not modified in current branch.",
    )
    parser.add_argument(
        "--subrepo",
        action="append",
        dest="subrepos",
        help="Specific subrepo name(s) to check (e.g. --subrepo context).",
    )
    parser.add_argument(
        "--allow-offline",
        action="store_true",
        help="Treat network reachability errors as warnings instead of failures.",
    )
    args = parser.parse_args()

    is_fresh, issues = check_subrepo_freshness(
        check_all=args.all,
        subrepo_names=args.subrepos,
        allow_offline=args.allow_offline,
    )

    if not is_fresh:
        print("❌ Subrepo Freshness Validation Failed:\n", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}\n", file=sys.stderr)
        return 1

    print("✅ Subrepo tracking references are fresh and in sync with upstream.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
