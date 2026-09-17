#!/usr/bin/env python3
from __future__ import annotations

"""Validate UI development invariants (context/rules/ui-dev.md).

Enforces:
1. NEVER use `!important` or specificity hacks in TSX, CSS, SCSS.
2. NEVER hardcode colour values (raw hex codes). Semantic tokens must be used.
3. Only single index.css under frontend/src; no component-scoped CSS/SCSS.
4. No Tailwind concrete colour classes for data-meaningful UI (use DaisyUI semantic).
5. Direct @heroicons/react import prohibition (use barrel).
6. Spacing scale constraints.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

# Forbidden !important
IMPORTANT_PATTERN = re.compile(r"!important\b", re.IGNORECASE)

# Forbidden raw hex colour codes (#fff, #123456, #12345678)
RAW_HEX_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")

# Allowed spacing tokens
ALLOWED_SPACING = {
    "gap-1",
    "gap-2",
    "gap-4",
    "p-2",
    "p-4",
    "px-4",
    "md:gap-6",
    "md:px-6",
}

# Disallowed concrete colour classes for data/state
CONCRETE_COLOUR_PATTERN = re.compile(
    r"(?:text|bg|border)-"
    r"(?:green|red|amber|yellow|blue|gray|slate|zinc|neutral|stone)-\d+"
    r"(?:/\d+)?"
    r"(?:\s+dark:[^\s]+)?"
)

# Direct Heroicons import (barrel is components/icons/HeroIcons.tsx)
HEROICONS_IMPORT_PATTERN = re.compile(r"from\s+['\"]@heroicons/react")

# Disallowed spacing pattern
DISALLOWED_SPACING_PATTERN = re.compile(
    r"\b(?:gap-(?:0|3|[5-9]|1[0-9]|\d{2,}|[0-9]\.[0-9]+)|"
    r"p-(?:0|1|3|[5-9]|1[0-9]|\d{2,}|[0-9]\.[0-9]+)|"
    r"px-(?:0|[1-3]|[5-9]|1[0-9]|\d{2,})|"
    r"py-[0-9]+|pt-[0-9]+|pb-[0-9]+|pl-[0-9]+|pr-[0-9]+)\b"
)


def check_important(path: Path, content: str) -> list[tuple[int, str]]:
    """Flag usage of !important."""
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(content.splitlines(), 1):
        if IMPORTANT_PATTERN.search(line):
            violations.append(
                (i, f"  Line {i}: '!important' is strictly forbidden (context/rules/ui-dev.md)")
            )
    return violations


def check_raw_hex(path: Path, content: str) -> list[tuple[int, str]]:
    """Flag raw hex colour values (semantic tokens required)."""
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(content.splitlines(), 1):
        # Skip comments or SVG path data
        line_clean = line.strip()
        if line_clean.startswith(("//", "/*", "*")):
            continue
        if "d=\"M" in line or "d='M" in line:
            continue
        for m in RAW_HEX_PATTERN.finditer(line):
            hex_val = m.group(0)
            violations.append(
                (i, f"  Line {i}: raw hex colour '{hex_val}' is forbidden — use DaisyUI semantic tokens (context/rules/ui-dev.md)")
            )
    return violations


def check_css_files(src_dir: Path | None = None) -> list[str]:
    """Only index.css under frontend/src; no component-scoped CSS/SCSS."""
    violations: list[str] = []
    target = src_dir or FRONTEND_SRC
    if not target.exists():
        return violations

    for ext in ("*.css", "*.scss"):
        for f in target.rglob(ext):
            if f.name != "index.css":
                violations.append(
                    f"  {f.relative_to(REPO_ROOT) if f.is_relative_to(REPO_ROOT) else f}: "
                    "component-scoped CSS/SCSS not allowed; use Tailwind/DaisyUI utilities (context/rules/ui-dev.md)"
                )
    return violations


def check_concrete_colours(path: Path, content: str) -> list[tuple[int, str]]:
    """Flag Tailwind concrete colour classes."""
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(content.splitlines(), 1):
        for m in CONCRETE_COLOUR_PATTERN.finditer(line):
            violations.append(
                (i, f"  Line {i}: concrete colour '{m.group(0).strip()}' — use DaisyUI semantic (e.g. text-success, text-error)")
            )
    return violations


def check_heroicons_import(path: Path, content: str) -> list[tuple[int, str]]:
    """No direct @heroicons/react; use barrel components/icons/HeroIcons.tsx."""
    if "icons/HeroIcons" in str(path) or "HeroIcons.tsx" in path.name:
        return []
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(content.splitlines(), 1):
        if HEROICONS_IMPORT_PATTERN.search(line):
            violations.append(
                (i, f"  Line {i}: import from '@heroicons/react' — use barrel from components/icons/HeroIcons.tsx")
            )
    return violations


def check_spacing(path: Path, content: str) -> list[tuple[int, str]]:
    """Spacing scale: only allowed tokens."""
    violations: list[tuple[int, str]] = []
    is_price_header = "PriceHeader" in path.name and "price-header" in str(path)
    for i, line in enumerate(content.splitlines(), 1):
        for m in DISALLOWED_SPACING_PATTERN.finditer(line):
            token = m.group(0)
            if token in ("md:gap-6", "md:px-6") and is_price_header:
                continue
            violations.append(
                (i, f"  Line {i}: spacing '{token}' — use only gap-1, gap-2, gap-4, p-2, p-4, px-4")
            )
    return violations


def is_test_or_spec(path: Path) -> bool:
    return "__tests__" in path.parts or ".test." in path.name or ".spec." in path.name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate UI development invariants (context/rules/ui-dev.md)"
    )
    parser.add_argument("files", nargs="*", help="Specific files to validate")
    args = parser.parse_args()

    all_violations: list[str] = []

    if args.files:
        files_to_check = [Path(f) for f in args.files if Path(f).is_file()]
        if any(f.suffix in [".css", ".scss"] for f in files_to_check):
            all_violations.extend(check_css_files())
    else:
        if not FRONTEND_SRC.exists():
            print("Frontend src not found; skipping ui-dev check.", file=sys.stderr)
            return 0
        all_violations.extend(check_css_files())
        files_to_check = []
        for ext in ("*.tsx", "*.jsx", "*.css", "*.scss"):
            files_to_check.extend(FRONTEND_SRC.rglob(ext))

    for path in files_to_check:
        if is_test_or_spec(path):
            continue
        try:
            content = path.read_text()
        except (OSError, UnicodeDecodeError) as e:
            all_violations.append(f"  {path}: read error — {e}")
            continue

        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path

        # Checks for all styling files
        for line_no, msg in check_important(path, content):
            all_violations.append(f"{rel}:{line_no}\n{msg}")

        # TSX/JSX checks
        if path.suffix in [".tsx", ".jsx"]:
            for line_no, msg in check_raw_hex(path, content):
                all_violations.append(f"{rel}:{line_no}\n{msg}")
            for line_no, msg in check_concrete_colours(path, content):
                all_violations.append(f"{rel}:{line_no}\n{msg}")
            for line_no, msg in check_heroicons_import(path, content):
                all_violations.append(f"{rel}:{line_no}\n{msg}")
            for line_no, msg in check_spacing(path, content):
                all_violations.append(f"{rel}:{line_no}\n{msg}")

    if all_violations:
        print("❌ UI development violations (context/rules/ui-dev.md):\n", file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        return 1

    print("✅ UI development invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
