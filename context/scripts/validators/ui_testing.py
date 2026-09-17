#!/usr/bin/env python3
from __future__ import annotations

"""Validate UI testing invariants (context/rules/ui-testing.md).

Enforces:
1. Prohibits full 'puppeteer' dependency (project strictly uses 'puppeteer-core').
2. Prohibits 'playwright', '@playwright/test', and 'cypress'.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

BANNED_PACKAGES = {
    "puppeteer": "puppeteer is banned; strictly use puppeteer-core (context/rules/ui-testing.md §1)",
    "playwright": "playwright is banned; use puppeteer-core for lightweight automation (context/rules/ui-testing.md §1)",
    "@playwright/test": "@playwright/test is banned; use puppeteer-core (context/rules/ui-testing.md §1)",
    "cypress": "cypress is banned; use puppeteer-core (context/rules/ui-testing.md §1)",
}


def is_exempt_package(package_json_path: Path) -> bool:
    """Check if package.json is the documentation typesetting pipeline using mermaid-cli."""
    try:
        data = json.loads(package_json_path.read_text())
        dev_deps = data.get("devDependencies", {})
        if "@mermaid-js/mermaid-cli" in dev_deps and "frontend" not in package_json_path.parts:
            return True
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return False


def check_forbidden_ui_test_deps(package_json_path: Path) -> list[str]:
    """Scan package.json for banned UI testing packages."""
    if is_exempt_package(package_json_path):
        return []

    violations: list[str] = []
    try:
        data = json.loads(package_json_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"{package_json_path}: unable to read JSON: {e}"]

    dep_sections = ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]

    for sec in dep_sections:
        deps = data.get(sec, {})
        if not isinstance(deps, dict):
            continue
        for pkg_name in deps:
            if pkg_name in BANNED_PACKAGES:
                violations.append(
                    f"{package_json_path} [{sec}]: {BANNED_PACKAGES[pkg_name]}"
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate UI testing invariants (context/rules/ui-testing.md)"
    )
    parser.add_argument("files", nargs="*", help="package.json files to inspect")
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file()]
        if not files:
            print("✅ UI testing invariants verified (no files to check)")
            return 0
    else:
        files = []
        for p in REPO_ROOT.rglob("package.json"):
            if "node_modules" in p.parts:
                continue
            files.append(p)

    all_violations: list[str] = []
    for pkg in files:
        all_violations.extend(check_forbidden_ui_test_deps(pkg))

    if all_violations:
        print("❌ UI testing dependency violations (context/rules/ui-testing.md):", file=sys.stderr)
        for v in all_violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("✅ UI testing invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
