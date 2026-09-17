"""Tests for agent definition validator."""

import pytest
from pathlib import Path
import sys

from context.scripts.validators.agent_definitions import validate_agent_definition


class TestAgentValidator:
    """Tests for agent definition validator."""

    def test_valid_agent(self, valid_agent):
        """Test that valid agent definition passes."""
        errors = validate_agent_definition(valid_agent)
        # Note: May have errors if referenced standards don't exist in test environment
        # But should not have structural errors
        structural_errors = [e for e in errors if
                           "frontmatter" in e.lower() or
                           "missing required" in e.lower() or
                           "hardcoded" in e.lower()]
        assert len(structural_errors) == 0, f"Unexpected structural errors: {structural_errors}"

    def test_no_frontmatter(self, invalid_agent_no_frontmatter):
        """Test that agent without frontmatter fails."""
        errors = validate_agent_definition(invalid_agent_no_frontmatter)
        assert len(errors) > 0
        assert any("frontmatter" in e.lower() for e in errors)

    def test_hardcoded_paths(self, invalid_agent_hardcoded_paths):
        """Test that hardcoded paths are caught."""
        errors = validate_agent_definition(invalid_agent_hardcoded_paths)
        assert len(errors) > 0
        assert any("hardcoded" in e.lower() for e in errors)

    def test_missing_required_sections(self, invalid_agent_missing_sections):
        """Test that missing sections are caught."""
        errors = validate_agent_definition(invalid_agent_missing_sections)
        assert len(errors) > 0
        # Should catch missing "Required Standards" and "Required Rules" sections
        assert any("Required Standards" in e for e in errors)
        assert any("Required Rules" in e for e in errors)

    def test_invalid_yaml_frontmatter(self, tmp_path):
        """Test that invalid YAML frontmatter is caught."""
        bad_agent = tmp_path / "bad_agent.md"
        bad_agent.write_text("""---
name: test
invalid yaml: [unclosed
---

## Role
Test
""")
        errors = validate_agent_definition(bad_agent)
        assert len(errors) > 0
        assert any("YAML" in e for e in errors)

    def test_missing_required_fields(self, tmp_path):
        """Test that missing required frontmatter fields are caught."""
        incomplete_agent = tmp_path / "incomplete_agent.md"
        incomplete_agent.write_text("""---
name: test-agent
# Missing 'model'
---

## Role
Test agent

## Required Standards (Read First!)
None

## Required Rules (Must Follow!)
None
""")
        errors = validate_agent_definition(incomplete_agent)
        assert len(errors) > 0
        assert any("model" in e for e in errors)

    def test_relative_paths_flagged(self, tmp_path):
        """Test that relative paths to artefacts are flagged."""
        bad_agent = tmp_path / "bad_agent.md"
        bad_agent.write_text("""---
name: test-agent
model: sonnet
---

## Role
Test agent

## Required Standards (Read First!)
None

## Required Rules (Must Follow!)
None

## Workflow

1. Read from ./artefacts/requirements.md
2. Write to ./artefacts/output.md
""")
        errors = validate_agent_definition(bad_agent)
        assert len(errors) > 0
        assert any("relative paths" in e.lower() for e in errors)

    def test_reminders_without_attribution(self, tmp_path):
        """Test that reminders without attribution are caught."""
        bad_agent = tmp_path / "bad_agent.md"
        bad_agent.write_text("""---
name: test-agent
model: sonnet
---

## Role
Test agent

## Required Standards (Read First!)
None

## Required Rules (Must Follow!)
None

## Critical Reminders (from standards above)

- Use uv run for Python
- Write tests before code
""")
        errors = validate_agent_definition(bad_agent)
        assert len(errors) > 0
        # Should catch reminders without (file:line) attribution
        assert any("attribution" in e.lower() for e in errors)

    def test_proper_attribution_passes(self, tmp_path):
        """Test that properly attributed reminders pass."""
        good_agent = tmp_path / "good_agent.md"
        good_agent.write_text("""---
name: test-agent
model: sonnet
---

## Role
Test agent

## Required Standards (Read First!)
1. context/standards/tech-standards.md - Lines 1-50

## Required Rules (Must Follow!)
1. context/rules/conventional-commits.md

## Critical Reminders (from standards above)

- Use uv run for Python (tech-standards.md:34)
- Write tests before code (testing-standards.md:12)

## Workflow

Use {project-root}/artefacts/
""")
        errors = validate_agent_definition(good_agent)
        # May have errors for missing files, but not attribution errors
        attribution_errors = [e for e in errors if "attribution" in e.lower()]
        assert len(attribution_errors) == 0

    def test_project_root_placeholders_allowed(self, tmp_path):
        """Test that {project-root} placeholders are allowed."""
        good_agent = tmp_path / "good_agent.md"
        good_agent.write_text("""---
name: test-agent
model: sonnet
---

## Role
Test agent

## Required Standards (Read First!)
None

## Required Rules (Must Follow!)
None

## Workflow

1. Read from {project-root}/artefacts/requirements.md
2. Write to {project-root}/artefacts/output.md
""")
        errors = validate_agent_definition(good_agent)
        # Should not have path-related errors
        path_errors = [e for e in errors if
                      "hardcoded" in e.lower() or
                      "relative paths" in e.lower()]
        assert len(path_errors) == 0

    def test_nonexistent_standards_flagged(self, tmp_path):
        """Test that references to nonexistent standards are caught."""
        bad_agent = tmp_path / "bad_agent.md"
        bad_agent.write_text("""---
name: test-agent
model: sonnet
standards: [nonexistent-standard.md]
---

## Role
Test agent

## Required Standards (Read First!)
1. context/standards/nonexistent-standard.md

## Required Rules (Must Follow!)
None
""")
        errors = validate_agent_definition(bad_agent)
        assert len(errors) > 0
        assert any("doesn't exist" in e for e in errors)

    def test_nonexistent_rules_flagged(self, tmp_path):
        """Test that references to nonexistent rules are caught."""
        bad_agent = tmp_path / "bad_agent.md"
        bad_agent.write_text("""---
name: test-agent
model: sonnet
rules: [nonexistent-rule.md]
---

## Role
Test agent

## Required Standards (Read First!)
None

## Required Rules (Must Follow!)
1. context/rules/nonexistent-rule.md
""")
        errors = validate_agent_definition(bad_agent)
        assert len(errors) > 0
        assert any("doesn't exist" in e for e in errors)
