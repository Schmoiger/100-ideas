#!/usr/bin/env python3
"""Pre-commit hook: check framework docs when context/ files change.

Behaviour:
  - reference doc not staged → BLOCK (exit 1)
  - brief doc not staged     → WARN  (exit 0)
  - [docs-ok] in commit msg  → PASS  (exit 0), leaves audit trail

Only staged context/ files trigger the check. The two framework docs
themselves are excluded to avoid circular triggering. No other paths
are hardcoded — gitignored files never appear in staged output anyway.
"""

import subprocess
import sys
from pathlib import Path

REFERENCE_DOC = "context/docs/agentic-framework-reference.md"
BRIEF_DOC = "context/docs/agentic-framework.md"
FRAMEWORK_DOCS = {REFERENCE_DOC, BRIEF_DOC}
BYPASS_MARKER = "[docs-ok]"


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


def get_commit_message() -> str:
    msg_file = Path(".git/COMMIT_EDITMSG")
    if msg_file.exists():
        return msg_file.read_text()
    return ""


def is_context_change(path: str) -> bool:
    if not path.startswith("context/"):
        return False
    return path not in FRAMEWORK_DOCS


def main() -> None:
    staged = get_staged_files()

    context_changes = [f for f in staged if is_context_change(f)]
    if not context_changes:
        sys.exit(0)

    if BYPASS_MARKER in get_commit_message():
        print(f"✅ {BYPASS_MARKER} found in commit message — skipping framework docs check")
        sys.exit(0)

    staged_set = set(staged)
    ref_staged = REFERENCE_DOC in staged_set
    brief_staged = BRIEF_DOC in staged_set

    if ref_staged and brief_staged:
        print("✅ Framework docs updated alongside context/ changes")
        sys.exit(0)

    print("Staged context changes:")
    for f in sorted(context_changes):
        print(f"  {f}")
    print()

    exit_code = 0

    if not ref_staged:
        print(f"❌ {REFERENCE_DOC}")
        print("   Reference doc not updated — this blocks the commit.")
        print()
        exit_code = 1
    else:
        print(f"✓  {REFERENCE_DOC}")
        print()

    if not brief_staged:
        print(f"⚠  {BRIEF_DOC}")
        print("   Brief doc not updated — consider whether it needs a change.")
        print()
    else:
        print(f"✓  {BRIEF_DOC}")
        print()

    if exit_code != 0:
        print(f"To bypass: include {BYPASS_MARKER} in the commit message.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
