#!/usr/bin/env python3
from __future__ import annotations

"""Validate secrets invariants (context/rules/secrets.md).

Enforces:
1. NEVER create or stage .env files with credentials.
2. NEVER hardcode secrets, private keys, or API tokens in source code.
3. Secrets must live in /secrets/*.json or environment variables.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

RESTRICTED_PATTERNS = [
    (re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----"), "Private key block"),
    (re.compile(r"\b(?:AIza[0-9A-Za-z-_]{35})\b"), "Google API Key"),
    (re.compile(r"\b(?:ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})\b"), "GitHub Personal Access Token"),
    (re.compile(r"\b(?:sk-[a-zA-Z0-9]{32,})\b"), "OpenAI API signature"),
    (re.compile(r"\b(?:AKIA[0-9A-Z]{16})\b"), "AWS Access Key ID"),
    (re.compile(r"(?:api_key|secret_key|client_secret)\s*[:=]\s*['\"][0-9a-zA-Z_\-]{20,}['\"]", re.IGNORECASE), "Hardcoded API key assignment"),
    (re.compile(r"(?:password|passwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE), "Hardcoded password assignment"),
]

EXEMPT_DIRS = {"tests", "fixtures", "__tests__", ".git", ".venv", "venv", "node_modules"}
EXEMPT_MARKERS = ["# test-secret", "// test-secret", "dummy", "placeholder", "test-token"]


def is_exempt_path(path: Path) -> bool:
    """Check if file is in an exempt directory (tests/fixtures)."""
    parts = set(path.parts)
    return bool(parts & EXEMPT_DIRS)


def scan_file_for_secrets(file_path: Path) -> list[str]:
    """Scan a single file for exposed secrets."""
    violations: list[str] = []

    # Check for .env file containing credentials
    if file_path.name == ".env" or file_path.name.endswith(".env"):
        try:
            content = file_path.read_text()
            if any(pat.search(content) for pat, _ in RESTRICTED_PATTERNS) or "KEY=" in content or "SECRET=" in content:
                violations.append(
                    f"{file_path}: .env files with credentials are strictly forbidden (context/rules/secrets.md §2)"
                )
                return violations
        except (OSError, UnicodeDecodeError):
            pass

    if is_exempt_path(file_path):
        return []

    try:
        content = file_path.read_text()
    except (OSError, UnicodeDecodeError):
        return []

    for i, line in enumerate(content.splitlines(), 1):
        line_clean = line.strip()
        if any(marker in line_clean.lower() for marker in EXEMPT_MARKERS):
            continue

        for pattern, desc in RESTRICTED_PATTERNS:
            if pattern.search(line):
                violations.append(
                    f"{file_path}:{i}: Potential exposed secret detected ({desc}) — context/rules/secrets.md"
                )
                break

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate secrets invariants (context/rules/secrets.md)"
    )
    parser.add_argument("files", nargs="*", help="Files to scan for secrets")
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file()]
    else:
        files = []
        for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.json", "*.env*"):
            for p in REPO_ROOT.rglob(ext):
                if not is_exempt_path(p) and "node_modules" not in p.parts:
                    files.append(p)

    all_violations: list[str] = []
    for f in files:
        all_violations.extend(scan_file_for_secrets(f))

    if all_violations:
        print("❌ Secrets invariant violations detected (context/rules/secrets.md):", file=sys.stderr)
        for v in all_violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("✅ Secrets invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
