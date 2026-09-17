#!/usr/bin/env python3
from __future__ import annotations

"""Validate TypeScript environment invariants (context/rules/typescript-environment.md).

Enforces:
1. No package-lock.json (must use yarn.lock).
2. tsconfig.json files must have strict: true, noImplicitAny: true, strictNullChecks: true.
3. TypeScript subprojects must be declared in root package.json workspaces array.
4. Banned npm/npx invocations in package.json scripts.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def check_package_lock(root_dir: Path) -> list[str]:
    """Flag presence of package-lock.json files."""
    violations: list[str] = []
    for p in root_dir.rglob("package-lock.json"):
        if "node_modules" in p.parts:
            continue
        violations.append(
            f"{p.relative_to(root_dir) if p.is_relative_to(root_dir) else p}: "
            "package-lock.json is strictly forbidden; project uses Yarn Berry (context/rules/typescript-environment.md §1)"
        )
    return violations


def _parse_json_with_comments(text: str) -> dict:
    """Parse JSON text that may contain comments and trailing commas (common in tsconfig.json)."""
    # Remove single line comments
    clean_lines = []
    for line in text.splitlines():
        line_no_comment = re.sub(r"//.*$", "", line)
        clean_lines.append(line_no_comment)
    clean_text = "\n".join(clean_lines)
    # Remove multiline comments
    clean_text = re.sub(r"/\*.*?\*/", "", clean_text, flags=re.DOTALL)
    # Remove trailing commas before } or ]
    clean_text = re.sub(r",\s*([}\]])", r"\1", clean_text)
    return json.loads(clean_text)


def check_tsconfig_strictness(tsconfig_path: Path) -> list[str]:
    """Verify strict compiler options in tsconfig.json."""
    violations: list[str] = []
    try:
        data = _parse_json_with_comments(tsconfig_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"{tsconfig_path}: unable to parse tsconfig JSON: {e}"]

    compiler_options = data.get("compilerOptions", {})

    required_flags = {
        "strict": True,
        "noImplicitAny": True,
        "strictNullChecks": True,
    }

    for flag, expected in required_flags.items():
        val = compiler_options.get(flag)
        if val is not expected:
            violations.append(
                f"{tsconfig_path}: compilerOptions.{flag} must be set to {expected} (found {val})"
            )

    return violations


def check_workspaces(root_dir: Path) -> list[str]:
    """Verify package.json subdirectories are listed in root package.json workspaces."""
    violations: list[str] = []
    root_pkg = root_dir / "package.json"
    if not root_pkg.is_file():
        return violations

    try:
        root_data = json.loads(root_pkg.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return violations

    workspaces = root_data.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])

    # Find all subproject package.json files
    for sub_pkg in root_dir.rglob("package.json"):
        if sub_pkg == root_pkg or "node_modules" in sub_pkg.parts:
            continue
        rel_dir = sub_pkg.parent.relative_to(root_dir).as_posix()
        # Check if rel_dir or a glob matches
        matched = False
        for ws in workspaces:
            if ws == rel_dir or ws == f"{rel_dir}/*":
                matched = True
                break
            if ws.endswith("/*"):
                parent_ws = ws[:-2]
                if rel_dir.startswith(parent_ws):
                    matched = True
                    break
        if not matched and workspaces:
            violations.append(
                f"{sub_pkg.relative_to(root_dir)}: subproject '{rel_dir}' must be listed in root package.json workspaces"
            )

    return violations


def check_banned_npm_in_scripts(package_json_path: Path) -> list[str]:
    """Check for banned npm/npx references in package.json scripts."""
    violations: list[str] = []
    try:
        data = json.loads(package_json_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return violations

    scripts = data.get("scripts", {})
    for name, cmd in scripts.items():
        if re.search(r"\b(npm|npx)\b", cmd):
            violations.append(
                f"{package_json_path}: script '{name}' uses banned command '{cmd}' (use yarn / yarn dlx)"
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate TypeScript environment invariants (context/rules/typescript-environment.md)"
    )
    parser.add_argument("files", nargs="*", help="Specific files to validate")
    args = parser.parse_args()

    violations: list[str] = []

    if args.files:
        for f in args.files:
            p = Path(f)
            if p.name == "package-lock.json":
                violations.append(f"{p}: package-lock.json is strictly forbidden (use yarn.lock)")
            elif "tsconfig" in p.name and p.suffix == ".json":
                violations.extend(check_tsconfig_strictness(p))
            elif p.name == "package.json":
                violations.extend(check_banned_npm_in_scripts(p))
    else:
        violations.extend(check_package_lock(REPO_ROOT))
        for tsconfig in REPO_ROOT.rglob("tsconfig*.json"):
            if "node_modules" in tsconfig.parts:
                continue
            violations.extend(check_tsconfig_strictness(tsconfig))
        for pkg in REPO_ROOT.rglob("package.json"):
            if "node_modules" in pkg.parts:
                continue
            violations.extend(check_banned_npm_in_scripts(pkg))
        violations.extend(check_workspaces(REPO_ROOT))

    if violations:
        print("❌ TypeScript environment violations (context/rules/typescript-environment.md):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("✅ TypeScript environment invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
