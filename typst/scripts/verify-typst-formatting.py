#!/usr/bin/env python3
"""
Verify and enforce Typst-friendly Markdown formatting rules.

Rules enforced:
1. Double line spacing (at least 2 blank lines) following mermaid diagrams / diagram blocks.
2. Horizontal rule ('---') preceding major section headings (level 2 headings '## '),
   ensuring consistent section separation for Typst document generation.

Usage:
    uv run python typst/scripts/verify-typst-formatting.py [files...]
    uv run python typst/scripts/verify-typst-formatting.py --fix [files...]
    uv run python typst/scripts/verify-typst-formatting.py --staged
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def get_staged_markdown_files(repo_root: Path) -> list[Path]:
    """Return list of staged markdown files in docs/drafts/."""
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)
    files: list[Path] = []
    for line in res.stdout.splitlines():
        p = repo_root / line.strip()
        if p.suffix == ".md" and p.exists() and "docs/drafts/" in str(p):
            files.append(p)
    return files


def check_and_fix_file(path: Path, fix: bool = False) -> list[str]:
    """
    Check a markdown file for Typst formatting requirements.

    Returns a list of error descriptions (if any).
    If fix is True, writes updated content when violations can be auto-remediated.
    """
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        # Skip broken symlinks or files with restricted access
        return errors
    lines = content.splitlines()

    new_lines: list[str] = []
    modified = False

    in_mermaid = False
    i = 0
    total_lines = len(lines)

    # Track if we are inside frontmatter or typst-skip blocks
    in_typst_skip = False

    while i < total_lines:
        line = lines[i]
        stripped = line.strip()

        if stripped == "<!-- typst-skip-start -->":
            in_typst_skip = True
        elif stripped == "<!-- typst-skip-end -->":
            in_typst_skip = False

        # Detect mermaid fence start/end
        if stripped == "```mermaid":
            in_mermaid = True
            new_lines.append(line)
            i += 1
            continue

        if in_mermaid and stripped == "```":
            in_mermaid = False
            new_lines.append(line)

            # Count following blank lines
            blank_count = 0
            peek = i + 1
            while peek < total_lines and not lines[peek].strip():
                blank_count += 1
                peek += 1

            if peek < total_lines and blank_count < 2:
                errors.append(
                    f"{path}:{i + 1} Mermaid diagram fence must be followed by at least 2 blank lines (found {blank_count})"
                )
                if fix:
                    new_lines.extend(["", ""])
                    modified = True
                    i = peek  # skip original blanks and resume at next content
                    continue
            i += 1
            continue

        # Check section separation for level 2 headings '## '
        # (Exclude '# Title', '## Table of Contents', and headings inside typst-skip)
        if stripped.startswith("## ") and not in_typst_skip and not in_mermaid:
            heading_title = stripped[3:].strip()
            if heading_title.lower() != "table of contents":
                # Check previous non-blank line in new_lines
                prev_idx = len(new_lines) - 1
                while prev_idx >= 0 and not new_lines[prev_idx].strip():
                    prev_idx -= 1

                prev_content = new_lines[prev_idx].strip() if prev_idx >= 0 else ""
                if prev_content != "---":
                    errors.append(
                        f"{path}:{i + 1} Section heading '## {heading_title}' must be preceded by '---' horizontal rule"
                    )
                    if fix:
                        # Ensure there is a blank line before '---' unless at start
                        if prev_idx >= 0 and new_lines and new_lines[-1].strip():
                            new_lines.append("")
                        new_lines.append("---")
                        new_lines.append("")
                        modified = True

        new_lines.append(line)
        i += 1

    if fix and modified:
        # Preserve trailing newline
        new_content = "\n".join(new_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"
        path.write_text(new_content, encoding="utf-8")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Typst-specific Markdown formatting rules.")
    parser.add_argument("files", nargs="*", type=Path, help="Markdown files to check")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations where possible")
    parser.add_argument("--staged", action="store_true", help="Check git staged markdown files")

    args = parser.parse_args()
    
    repo_root = Path.cwd().resolve()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            repo_root = Path(res.stdout.strip()).resolve()
    except Exception:
        pass
    if not (repo_root / "docs").exists():
        for parent in Path(__file__).resolve().parents:
            if (parent / "docs").exists():
                repo_root = parent
                break

    target_files: list[Path] = []
    if args.staged:
        target_files = get_staged_markdown_files(repo_root)
        if not target_files:
            return 0
    elif args.files:
        target_files = [f.resolve() for f in args.files]
    else:
        # Default: check drafts and published docs
        drafts_dir = repo_root / "docs" / "drafts"
        if drafts_dir.exists():
            target_files = sorted(drafts_dir.glob("*.md"))

    all_errors: list[str] = []
    for file_path in target_files:
        if not file_path.exists() or file_path.suffix != ".md":
            continue
        errs = check_and_fix_file(file_path, fix=args.fix)
        all_errors.extend(errs)

    if all_errors and not args.fix:
        print("Typst formatting check failed:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        print("\nRun with '--fix' to automatically remediate formatting issues.", file=sys.stderr)
        return 1

    if args.fix and all_errors:
        print(f"Fixed {len(all_errors)} Typst formatting violation(s).")
    else:
        print(f"Typst formatting check passed ({len(target_files)} file(s) checked).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
