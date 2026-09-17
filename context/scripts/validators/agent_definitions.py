#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml",
# ]
# ///
from __future__ import annotations

"""Validate agent definition structural integrity (context/agents/*.md).

Checks:
1. Valid YAML frontmatter with required 'name' and 'model' fields.
2. Referenced standards, rules, and skills exist on disk.
3. No hardcoded absolute paths or ./artefacts/ paths.
4. Presence of 'Required Standards' and 'Required Rules' sections.
5. Critical reminders include source attribution.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTEXT_DIR = REPO_ROOT / "context"
AGENTS_DIR = CONTEXT_DIR / "agents"

SKIPPED_FILES = {"TEMPLATE.md", "README.md", "MODEL-RECOMMENDATIONS.md", "orchestrator.md"}


def validate_agent_definition(
    file_path: Path,
    context_root: Path | None = None,
) -> list[str]:
    """Validate a single agent definition markdown file."""
    ctx = context_root or CONTEXT_DIR
    errors: list[str] = []

    try:
        content = file_path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        return [f"Unable to read file: {e}"]

    # Extract frontmatter
    if not content.startswith("---"):
        errors.append("Missing YAML frontmatter")
        return errors

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("Invalid YAML frontmatter structure")
        return errors

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors

    if not isinstance(frontmatter, dict):
        errors.append("YAML frontmatter must be a mapping")
        return errors

    # Check required frontmatter fields
    for field in ["name", "model"]:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate standards references
    if "standards" in frontmatter and isinstance(frontmatter["standards"], list):
        for standard in frontmatter["standards"]:
            standard_path = ctx / "standards" / standard
            if not standard_path.exists():
                errors.append(f"Referenced standard doesn't exist: {standard}")

    # Validate rules references
    if "rules" in frontmatter and isinstance(frontmatter["rules"], list):
        for rule in frontmatter["rules"]:
            rule_path = ctx / "rules" / rule
            if not rule_path.exists():
                errors.append(f"Referenced rule doesn't exist: {rule}")

    # Validate skills references
    if "skills" in frontmatter and isinstance(frontmatter["skills"], list):
        for skill in frontmatter["skills"]:
            skill_path = ctx / "skills" / skill
            if not skill_path.exists():
                errors.append(f"Referenced skill doesn't exist: {skill}")

    # Check for hardcoded absolute paths
    body = parts[2]
    if "/Users/" in body or "/home/" in body:
        errors.append("Contains hardcoded absolute paths")

    # Check for {project-root} usage instead of relative paths
    if "./artefacts/" in body:
        errors.append("Contains relative paths - use {project-root}/artefacts/ instead")

    # Check for Critical Reminders section and attribution
    if "Critical Reminders" in body:
        reminder_match = re.search(r"## Critical Reminders.*?(?=##|$)", body, re.DOTALL)
        if reminder_match:
            reminders = reminder_match.group(0)
            for line in reminders.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- ") and "(" not in stripped:
                    errors.append(f"Reminder missing attribution: {stripped}")

    # Check for Required Standards section
    if "Required Standards" not in body:
        errors.append("Missing 'Required Standards' section")

    # Check for Required Rules section
    if "Required Rules" not in body:
        errors.append("Missing 'Required Rules' section")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agent definition structural integrity (context/agents/*.md)"
    )
    parser.add_argument("files", nargs="*", help="Agent definition files to validate")
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file()]
    else:
        if not AGENTS_DIR.exists():
            print(f"❌ {AGENTS_DIR} directory not found", file=sys.stderr)
            return 1
        files = [
            f for f in AGENTS_DIR.glob("*.md")
            if f.name not in SKIPPED_FILES
        ]

    all_errors: dict[str, list[str]] = {}
    agent_count = 0

    for agent_file in sorted(files):
        if agent_file.name in SKIPPED_FILES:
            continue

        agent_count += 1
        errors = validate_agent_definition(agent_file)
        if errors:
            all_errors[agent_file.name] = errors

    if all_errors:
        print(f"❌ Validation failed for {len(all_errors)}/{agent_count} agents:\n", file=sys.stderr)
        for fname, errs in all_errors.items():
            print(f"{fname}:", file=sys.stderr)
            for err in errs:
                print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"✅ All {agent_count} agent definitions valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
