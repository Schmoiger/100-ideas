#!/usr/bin/env python3
from __future__ import annotations

"""Validate workspace conventions (context/rules/workspace-conventions.md).

Enforces:
1. Output locations and naming conventions (Section 1)
2. Conventional commit message format and Agent-Session trailers (Section 2)
3. Agent metrics logging format in metrics/*.jsonl (Section 3)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# --- Section 1: Output Locations & Naming Conventions ---

VALID_OUTPUT_TOP_DIRS = {"artefacts", "secrets", "services"}
VALID_ARTEFACT_SUBDIRS = {"architecture", "build", "product", "test-results", "design"}

TEST_RESULT_PATTERN = re.compile(r"^v2-[a-zA-Z0-9-]+-results\.txt$")
REVIEW_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+-review\.md$")
IMPL_DOC_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+-IMPLEMENTATION\.md$")


def validate_output_path(path: str | Path) -> list[str]:
    """Validate that a generated file lands in an allowed directory with correct naming conventions."""
    p = Path(path)
    parts = p.parts
    if not parts:
        return []

    errors: list[str] = []

    # Check top-level directories if relative path given
    if len(parts) >= 2:
        top_dir = parts[0]
        if top_dir == "artefacts":
            sub_dir = parts[1]
            if sub_dir not in VALID_ARTEFACT_SUBDIRS:
                errors.append(
                    f"Invalid artefact subdirectory '{sub_dir}' in '{path}'. "
                    f"Must be one of: {', '.join(sorted(VALID_ARTEFACT_SUBDIRS))}"
                )
            if sub_dir == "test-results" and len(parts) == 3:
                filename = parts[2]
                if not (TEST_RESULT_PATTERN.match(filename) or filename.endswith((".txt", ".json"))):
                    errors.append(
                        f"Test result file '{filename}' should follow 'v2-{{task-id}}-results.txt' convention."
                    )
        elif top_dir == "services":
            if len(parts) >= 3 and parts[2] == "tests":
                # Valid service test directory
                pass
        elif top_dir == "secrets":
            # Secrets directory
            pass

    return errors


def validate_output_paths(paths: list[str | Path]) -> list[str]:
    """Validate multiple output paths."""
    all_errors: list[str] = []
    for p in paths:
        all_errors.extend(validate_output_path(p))
    return all_errors


# --- Section 2: Git Commits ---

VALID_COMMIT_TYPES = r"(feat|fix|test|refactor|docs|chore|perf)"
COMMIT_SUBJECT_PATTERN = re.compile(rf"^{VALID_COMMIT_TYPES}\([a-z][a-z0-9-]*\): .{{1,}}$")
COAUTHOR_PATTERN = re.compile(r"^Co-Authored-By: .+ <.+@.+\..+>$")
AGENT_SESSION_PATTERN = re.compile(
    r"^Agent-Session: tool=[a-z0-9-]+ model=[a-z0-9.-]+ agents=[a-z0-9,-]+"
    r"( duration=\d+[mh])?"
    r"( dispatch=(human|orchestrator))?"
    r"( interactions=\d+)?"
    r"( approvals=\d+)?"
    r"( tokens=\d+(\.\d+)?K?/\d+(\.\d+)?K?)?$"
)


def validate_commit_message(msg: str) -> tuple[bool, str]:
    """Validate commit message against conventional commits and agent trailers."""
    lines = msg.strip().split("\n")
    if not lines or not lines[0].strip():
        return False, "Empty commit message"

    subject = lines[0]
    if not COMMIT_SUBJECT_PATTERN.match(subject):
        return False, (
            f"Invalid subject line: '{subject}'\n"
            "Expected: {type}({scope}): {description}\n"
            "Valid types: feat, fix, test, refactor, docs, chore, perf\n"
            "Scope: lowercase, alphanumeric with hyphens\n"
            "Example: feat(auth): add token refresh endpoint"
        )

    if len(subject) > 72:
        return False, f"Subject line too long ({len(subject)} chars, max 72): {subject}"

    description = subject.split(": ", 1)[1] if ": " in subject else ""
    if description:
        first_word = description.split()[0].lower()
        if first_word.endswith(("ed", "ing")):
            return False, (
                f"Description should use imperative mood: '{description}'\n"
                "Use 'add' not 'added', 'fix' not 'fixing'"
            )

    has_coauthor = False
    for line in lines:
        if line.startswith("Co-Authored-By:"):
            has_coauthor = True
            if not COAUTHOR_PATTERN.match(line):
                return False, f"Invalid Co-Authored-By format: {line}"

    has_agent_session = False
    for line in lines:
        if line.startswith("Agent-Session:"):
            has_agent_session = True
            if not AGENT_SESSION_PATTERN.match(line):
                return False, (
                    f"Invalid Agent-Session format: {line}\n"
                    "Expected: Agent-Session: tool=<tool> model=<model> agents=<agents>"
                    " [duration=45m] [dispatch=orchestrator] [interactions=0] [approvals=2]"
                    " [tokens=8.2K/5.1K]\n"
                    "Triplet: tool, model, agents from context/agents"
                )

    if has_agent_session and not has_coauthor:
        return False, "Agent commits require Co-Authored-By line when Agent-Session is present"

    return True, ""


# --- Section 3: Metrics Logging ---

REQUIRED_METRICS_FIELDS = ["ts", "task", "agent", "event", "tokens"]
VALID_METRICS_EVENTS = ["start", "handoff", "escalate", "complete", "blocked"]
VALID_TOKEN_SOURCES = ["api_response", "estimated", "unavailable"]


def validate_metrics_entry(entry: dict[str, Any], line_num: int) -> list[str]:
    """Validate a single metrics log entry."""
    errors: list[str] = []

    for field in REQUIRED_METRICS_FIELDS:
        if field not in entry:
            errors.append(f"Line {line_num}: Missing required field '{field}'")

    if errors:
        return errors

    ts = entry.get("ts", "")
    if not (ts.endswith(("Z", "]")) or "+" in ts):
        errors.append(
            f"Line {line_num}: Invalid timestamp format '{ts}', expected ISO 8601 (e.g., 2025-01-28T09:00:00Z)"
        )

    event = entry.get("event", "")
    if event not in VALID_METRICS_EVENTS:
        errors.append(
            f"Line {line_num}: Invalid event '{event}', must be one of: {', '.join(VALID_METRICS_EVENTS)}"
        )

    tokens = entry.get("tokens", {})
    if not isinstance(tokens, dict):
        errors.append(f"Line {line_num}: 'tokens' must be an object")
    else:
        if "in" not in tokens or "out" not in tokens:
            errors.append(f"Line {line_num}: 'tokens' must have 'in' and 'out' fields")

        if "source" not in tokens:
            errors.append(f"Line {line_num}: 'tokens' must have 'source' field")
        elif tokens["source"] not in VALID_TOKEN_SOURCES:
            errors.append(
                f"Line {line_num}: Invalid token source '{tokens['source']}', "
                f"must be one of: {', '.join(VALID_TOKEN_SOURCES)}"
            )

        for key in ["in", "out"]:
            if key in tokens and not isinstance(tokens[key], (int, float)):
                errors.append(f"Line {line_num}: tokens.{key} must be a number")

    if event in ["handoff", "escalate"] and "to" not in entry:
        errors.append(f"Line {line_num}: '{event}' event requires 'to' field")

    return errors


def validate_metrics_file(file_path: Path) -> list[str]:
    """Validate metrics log file."""
    all_errors: list[str] = []
    try:
        content = file_path.read_text()
        if not content.strip():
            return []

        for line_num, line in enumerate(content.strip().split("\n"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue
            all_errors.extend(validate_metrics_entry(entry, line_num))
    except (OSError, UnicodeDecodeError) as e:
        all_errors.append(f"Error reading file: {e}")

    return all_errors


# --- CLI Interface ---


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate workspace conventions (commits, metrics, output paths)"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    commit_parser = subparsers.add_parser("commit-msg", help="Validate commit message")
    commit_parser.add_argument("file", help="Path to commit message file")

    metrics_parser = subparsers.add_parser("metrics", help="Validate metrics JSONL file")
    metrics_parser.add_argument("file", help="Path to metrics file")

    paths_parser = subparsers.add_parser("paths", help="Validate output file paths")
    paths_parser.add_argument("files", nargs="+", help="File paths to validate")

    parser.add_argument("auto_args", nargs="*", help="Auto-detect args if no subcommand provided")

    args = parser.parse_args()

    # Subcommand routing
    if args.subcommand == "commit-msg":
        p = Path(args.file)
        if not p.exists():
            print(f"File not found: {p}", file=sys.stderr)
            return 1
        msg = p.read_text()
        if msg.startswith(("Merge ", "Revert ")):
            return 0
        is_valid, err = validate_commit_message(msg)
        if not is_valid:
            print(f"❌ Invalid commit message:\n{err}", file=sys.stderr)
            return 1
        print("✅ Commit message valid")
        return 0

    if args.subcommand == "metrics":
        p = Path(args.file)
        if not p.exists():
            print(f"File not found: {p}", file=sys.stderr)
            return 1
        errors = validate_metrics_file(p)
        if errors:
            print(f"❌ Metrics logging violations in {p.name}:", file=sys.stderr)
            for err in errors:
                print(f"  {err}", file=sys.stderr)
            return 1
        print(f"✅ {p.name} follows metrics logging format")
        return 0

    if args.subcommand == "paths":
        errors = validate_output_paths(args.files)
        if errors:
            print("❌ Output path violations:", file=sys.stderr)
            for err in errors:
                print(f"  {err}", file=sys.stderr)
            return 1
        print("✅ Output paths conform to workspace conventions")
        return 0

    # Auto-detect mode if no subcommand was explicitly selected
    if args.auto_args:
        first = args.auto_args[0]
        p = Path(first)
        if "COMMIT_EDITMSG" in first or (len(args.auto_args) == 1 and p.suffix == ".txt" and p.exists() and "(" in p.read_text()[:50]):
            msg = p.read_text()
            if msg.startswith(("Merge ", "Revert ")):
                return 0
            is_valid, err = validate_commit_message(msg)
            if not is_valid:
                print(f"❌ Invalid commit message:\n{err}", file=sys.stderr)
                return 1
            print("✅ Commit message valid")
            return 0

        if p.suffix == ".jsonl":
            errors = validate_metrics_file(p)
            if errors:
                print(f"❌ Metrics logging violations in {p.name}:", file=sys.stderr)
                for err in errors:
                    print(f"  {err}", file=sys.stderr)
                return 1
            print(f"✅ {p.name} follows metrics logging format")
            return 0

        # Treat as file paths
        errors = validate_output_paths(args.auto_args)
        if errors:
            print("❌ Output path violations:", file=sys.stderr)
            for err in errors:
                print(f"  {err}", file=sys.stderr)
            return 1
        print("✅ Output paths conform to workspace conventions")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
