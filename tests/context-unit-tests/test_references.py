"""
Static cross-reference validation tests.

Validates that file references in documentation point to existing files.
Runs without LLM calls.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pytest
import yaml


BASE_DIR = Path(__file__).parent.parent.parent
DOCS_ROOT = BASE_DIR / "context"
AGENTS_DIR = DOCS_ROOT / "agents"


def extract_file_references(content: str) -> list[str]:
    """Extract file path references from markdown content."""
    refs = []

    # Match ./path/to/file patterns
    refs.extend(re.findall(r'`(\./[^`\s]+)`', content))

    # Match paths in backticks that look like relative file paths (not bare filenames)
    # Must have at least one directory separator
    refs.extend(re.findall(r'`([a-zA-Z0-9_-]+/[a-zA-Z0-9_/-]+\.(md|py|sh|json|yaml|yml|mdc))`', content))

    # Match markdown links to local files
    refs.extend(re.findall(r'\]\((\./[^)]+)\)', content))

    # Flatten any tuples from regex groups
    flat_refs = []
    for ref in refs:
        if isinstance(ref, tuple):
            flat_refs.append(ref[0])
        else:
            flat_refs.append(ref)

    return list(set(flat_refs))


def resolve_path(ref: str, source_file: Path) -> Optional[Path]:
    """Resolve a file reference relative to source file or docs root."""
    # Handle ./artifacts/ paths - these are runtime working directories
    if ref.startswith("./artifacts/"):
        return None  # Skip artifact paths - they're created at runtime

    # Handle relative paths from the file's location
    if ref.startswith("./"):
        # Try from docs root first (most common)
        candidate = DOCS_ROOT / ref[2:]
        if candidate.exists():
            return candidate

        # Try from source file's directory
        candidate = source_file.parent / ref[2:]
        if candidate.exists():
            return candidate

        # Try from base dir
        candidate = BASE_DIR / ref[2:]
        if candidate.exists():
            return candidate

        return None

    # Handle paths like docs/standards/file.md
    if not ref.startswith("/"):
        candidate = BASE_DIR / ref
        if candidate.exists():
            return candidate

        candidate = DOCS_ROOT / ref
        if candidate.exists():
            return candidate

    return None


class TestAgentReferences:
    """Validate file references in agent definitions."""

    @pytest.fixture
    def agent_files(self) -> list[Path]:
        """Get all agent definition files."""
        exclude = {"README.md", "CLAUDE.md", "MODEL-RECOMMENDATIONS.md"}
        return [
            f for f in AGENTS_DIR.glob("*.md")
            if f.name not in exclude
        ]

    def test_context_path_references(self, agent_files: list[Path]):
        """Context paths should reference valid patterns or known artifact dirs."""
        # These are known runtime directories that won't exist statically
        known_artifact_patterns = {
            "./artifacts/",
            "./context/",
        }

        issues = []
        for path in agent_files:
            content = path.read_text()

            # Find Context Paths section
            if "## Context Paths" not in content:
                continue

            # Extract the section
            match = re.search(
                r'## Context Paths\n(.*?)(?=\n##|\Z)',
                content,
                re.DOTALL
            )
            if not match:
                continue

            section = match.group(1)
            refs = extract_file_references(section)

            for ref in refs:
                # Skip known artifact patterns
                if any(ref.startswith(pat) for pat in known_artifact_patterns):
                    continue

                # Check if it's a context reference that should exist
                if ref.startswith("./context/"):
                    resolved = resolve_path(ref, path)
                    if resolved is None:
                        issues.append((path.name, ref))

        if issues:
            errors = "\n".join(f"  - {name}: {ref}" for name, ref in issues)
            pytest.fail(f"Broken doc references in agent files:\n{errors}")


class TestStandardsReferences:
    """Validate file references in standards documents."""

    @pytest.fixture
    def standards_files(self) -> list[Path]:
        """Get all standards files."""
        return list((DOCS_ROOT / "standards").glob("*.md"))

    def test_doc_references_exist(self, standards_files: list[Path], capsys):
        """File references in standards should point to existing files (warning only)."""
        # Skip these patterns - they're templates/examples
        skip_patterns = {
            "/project-a/",
            "/project-b/",
            "(monorepo root)",
            "(project root)",
        }

        issues = []
        for path in standards_files:
            content = path.read_text()
            refs = extract_file_references(content)

            for ref in refs:
                # Skip example/template paths
                if any(pat in ref for pat in skip_patterns):
                    continue

                # Skip artifact paths
                if "./artifacts/" in ref:
                    continue

                resolved = resolve_path(ref, path)
                if resolved is None and ref.startswith("./context/"):
                    issues.append((path.name, ref))

        if issues:
            # Print warning for pre-existing docs
            errors = "\n".join(f"  - {name}: {ref}" for name, ref in issues)
            print(f"\nWarning: Broken references in standards:\n{errors}")


class TestAgentDomainConsistency:
    """Check that agents referenced in standards exist as files."""

    def test_all_domain_agents_exist(self):
        """Agents listed in agent-standards.md domains should have definition files."""
        standards_path = DOCS_ROOT / "standards" / "agent-standards.md"
        if not standards_path.exists():
            pytest.skip("agent-standards.md not found")

        content = standards_path.read_text()

        # Extract agent names from the domain table
        # Pattern matches: | **domain** | agent1, agent2 |
        agent_pattern = r'\|\s*\*\*\w+\*\*\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(agent_pattern, content)

        # Parse agent names from matches
        agents_in_standards = set()
        for match in matches:
            # Clean up and split by comma
            agents = [a.strip() for a in match.split(",")]
            for agent in agents:
                # Remove parenthetical notes like "(Python)"
                agent = re.sub(r'\s*\([^)]+\)', '', agent).strip()
                if agent and not agent.startswith("All"):
                    agents_in_standards.add(agent)

        # Check each agent has a definition file
        missing = []
        for agent in agents_in_standards:
            agent_file = AGENTS_DIR / f"{agent}.md"
            if not agent_file.exists():
                missing.append(agent)

        if missing:
            pytest.fail(
                f"Agents in agent-standards.md without definition files: "
                f"{', '.join(sorted(missing))}"
            )


class TestReadmeLinks:
    """Validate that README files have working internal links."""

    def test_docs_readme_links(self):
        """Links in context/README.md should point to existing files."""
        readme = DOCS_ROOT / "README.md"
        if not readme.exists():
            pytest.skip("context/README.md not found")

        content = readme.read_text()

        # Extract markdown links
        links = re.findall(r'\]\(([^)]+)\)', content)

        broken = []
        for link in links:
            # Skip external links
            if link.startswith("http://") or link.startswith("https://"):
                continue

            # Skip anchors
            if link.startswith("#"):
                continue

            # Resolve relative to README location
            if link.startswith("./"):
                target = DOCS_ROOT / link[2:]
            else:
                target = DOCS_ROOT / link

            # Handle anchor in link
            if "#" in str(target):
                target = Path(str(target).split("#")[0])

            if not target.exists():
                broken.append(link)

        if broken:
            pytest.fail(f"Broken links in context/README.md: {', '.join(broken)}")
