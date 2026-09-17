"""
Static analysis tests for documentation format validation.

These tests run without LLM calls and are suitable for every PR.
"""

import re
from pathlib import Path

import pytest
import yaml


DOCS_ROOT = Path(__file__).parent.parent.parent / "context"
AGENTS_DIR = DOCS_ROOT / "agents"


class TestAgentFrontmatter:
    """Validate YAML frontmatter in agent definition files."""

    @pytest.fixture
    def agent_files(self) -> list[Path]:
        """Get all agent definition files (excluding README, CLAUDE.md, etc.)."""
        exclude = {"README.md", "CLAUDE.md", "MODEL-RECOMMENDATIONS.md"}
        return [
            f for f in AGENTS_DIR.glob("*.md")
            if f.name not in exclude
        ]

    def test_all_agents_have_frontmatter(self, agent_files: list[Path]):
        """Every agent file must have YAML frontmatter."""
        missing = []
        for path in agent_files:
            content = path.read_text()
            if not content.startswith("---"):
                missing.append(path.name)

        if missing:
            pytest.fail(f"Missing frontmatter in: {', '.join(missing)}")

    def test_frontmatter_is_valid_yaml(self, agent_files: list[Path]):
        """Frontmatter must be valid YAML."""
        invalid = []
        for path in agent_files:
            content = path.read_text()
            if not content.startswith("---"):
                continue

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                invalid.append((path.name, "Unclosed frontmatter"))
                continue

            try:
                yaml.safe_load(parts[1])
            except yaml.YAMLError as e:
                invalid.append((path.name, str(e)))

        if invalid:
            errors = "\n".join(f"  - {name}: {err}" for name, err in invalid)
            pytest.fail(f"Invalid YAML frontmatter:\n{errors}")

    def test_required_frontmatter_fields(self, agent_files: list[Path]):
        """Agent frontmatter must have required fields."""
        required_fields = {"name", "description"}
        missing = []

        for path in agent_files:
            content = path.read_text()
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                fm = yaml.safe_load(parts[1]) or {}
                missing_fields = required_fields - set(fm.keys())
                if missing_fields:
                    missing.append((path.name, missing_fields))
            except yaml.YAMLError:
                pass  # Already caught by test_frontmatter_is_valid_yaml

        if missing:
            errors = "\n".join(
                f"  - {name}: missing {', '.join(fields)}"
                for name, fields in missing
            )
            pytest.fail(f"Missing required frontmatter fields:\n{errors}")

    def test_name_matches_filename(self, agent_files: list[Path]):
        """Frontmatter 'name' must match the filename (without .md)."""
        mismatches = []

        for path in agent_files:
            content = path.read_text()
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                fm = yaml.safe_load(parts[1]) or {}
                name = fm.get("name", "")
                expected = path.stem  # filename without .md
                if name != expected:
                    mismatches.append((path.name, name, expected))
            except yaml.YAMLError:
                pass

        if mismatches:
            errors = "\n".join(
                f"  - {filename}: name='{name}' but expected '{expected}'"
                for filename, name, expected in mismatches
            )
            pytest.fail(f"Frontmatter name doesn't match filename:\n{errors}")


class TestAgentStructure:
    """Validate agent file structure and required sections."""

    @pytest.fixture
    def agent_files(self) -> list[Path]:
        """Get all agent definition files."""
        exclude = {"README.md", "CLAUDE.md", "MODEL-RECOMMENDATIONS.md"}
        return [
            f for f in AGENTS_DIR.glob("*.md")
            if f.name not in exclude
        ]

    def test_has_task_placeholder(self, agent_files: list[Path]):
        """Agent files should have {$ARGUMENTS} placeholder for task injection."""
        missing = []
        for path in agent_files:
            content = path.read_text()
            if "{$ARGUMENTS}" not in content:
                missing.append(path.name)

        if missing:
            pytest.fail(
                f"Missing {{$ARGUMENTS}} placeholder in: {', '.join(missing)}"
            )

    def test_has_constraints_section(self, agent_files: list[Path]):
        """Agent files should have a Constraints section."""
        missing = []
        for path in agent_files:
            content = path.read_text()
            if "## Constraints" not in content:
                missing.append(path.name)

        if missing:
            pytest.fail(f"Missing '## Constraints' section in: {', '.join(missing)}")


class TestStandardsFormat:
    """Validate standards documentation format."""

    @pytest.fixture
    def standards_files(self) -> list[Path]:
        """Get all standards files."""
        return list((DOCS_ROOT / "standards").glob("*.md"))

    def test_standards_have_introduction(self, standards_files: list[Path], capsys):
        """Standards files should have an Introduction section (warning only)."""
        missing = []
        for path in standards_files:
            content = path.read_text()
            if "## 1. Introduction" not in content and "# Introduction" not in content:
                # Allow either "## 1. Introduction" or "# Introduction"
                if "Introduction" not in content:
                    missing.append(path.name)

        if missing:
            # Print warning but don't fail - these are pre-existing docs
            print(f"\nWarning: Missing Introduction section in: {', '.join(missing)}")


class TestRulesFormat:
    """Validate rules file format (.mdc files)."""

    @pytest.fixture
    def rules_files(self) -> list[Path]:
        """Get all rules files."""
        return list((DOCS_ROOT / "rules").glob("*.mdc"))

    def test_rules_have_frontmatter(self, rules_files: list[Path], capsys):
        """Rules files should have YAML frontmatter (warning only)."""
        if not rules_files:
            pytest.skip("No rules files found")

        missing = []
        for path in rules_files:
            content = path.read_text()
            if not content.startswith("---"):
                missing.append(path.name)

        if missing:
            # Print warning but don't fail - frontmatter is optional for rules
            print(f"\nWarning: Missing frontmatter in rules: {', '.join(missing)}")


class TestMarkdownLinks:
    """Validate markdown link format (not target existence)."""

    @pytest.fixture
    def all_markdown_files(self) -> list[Path]:
        """Get all markdown files in docs."""
        return list(DOCS_ROOT.rglob("*.md"))

    def test_no_broken_link_syntax(self, all_markdown_files: list[Path]):
        """Check for malformed markdown links."""
        # Pattern for common malformed links
        malformed_patterns = [
            (r'\[([^\]]*)\]\s+\(', "Space between ] and ("),
            (r'\[([^\]]*)\]\([^)]*\s[^)]*\)', "Space in URL (might be intentional)"),
        ]

        issues = []
        for path in all_markdown_files:
            content = path.read_text()
            for pattern, desc in malformed_patterns[:1]:  # Only check first pattern
                if re.search(pattern, content):
                    issues.append((path.relative_to(DOCS_ROOT), desc))

        if issues:
            errors = "\n".join(f"  - {path}: {desc}" for path, desc in issues)
            pytest.fail(f"Malformed markdown links:\n{errors}")
