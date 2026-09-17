"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def valid_commit(fixtures_dir):
    """Return path to valid commit fixture."""
    return fixtures_dir / 'valid_commit.txt'


@pytest.fixture
def invalid_commit_no_scope(fixtures_dir):
    """Return path to invalid commit (no scope) fixture."""
    return fixtures_dir / 'invalid_commit_no_scope.txt'


@pytest.fixture
def invalid_commit_too_long(fixtures_dir):
    """Return path to invalid commit (too long) fixture."""
    return fixtures_dir / 'invalid_commit_too_long.txt'


@pytest.fixture
def invalid_commit_past_tense(fixtures_dir):
    """Return path to invalid commit (past tense) fixture."""
    return fixtures_dir / 'invalid_commit_past_tense.txt'


@pytest.fixture
def valid_commit_with_agent_session(fixtures_dir):
    """Return path to valid commit with agent session fixture."""
    return fixtures_dir / 'valid_commit_with_agent_session.txt'


@pytest.fixture
def merge_commit(fixtures_dir):
    """Return path to merge commit fixture."""
    return fixtures_dir / 'merge_commit.txt'


@pytest.fixture
def valid_requirements(fixtures_dir):
    """Return path to valid requirements fixture."""
    return fixtures_dir / 'valid_requirements.md'


@pytest.fixture
def invalid_requirements(fixtures_dir):
    """Return path to invalid requirements fixture."""
    return fixtures_dir / 'invalid_requirements.md'


@pytest.fixture
def valid_british_english(fixtures_dir):
    """Return path to valid British English fixture."""
    return fixtures_dir / 'valid_british_english.md'


@pytest.fixture
def invalid_british_english(fixtures_dir):
    """Return path to invalid British English fixture."""
    return fixtures_dir / 'invalid_british_english.md'


@pytest.fixture
def valid_metrics(fixtures_dir):
    """Return path to valid metrics fixture."""
    return fixtures_dir / 'valid_metrics.jsonl'


@pytest.fixture
def invalid_metrics(fixtures_dir):
    """Return path to invalid metrics fixture."""
    return fixtures_dir / 'invalid_metrics.jsonl'


@pytest.fixture
def test_workflow(fixtures_dir):
    """Return path to test workflow fixture."""
    return fixtures_dir / 'test_workflow.yaml'


@pytest.fixture
def valid_agent(fixtures_dir):
    """Return path to valid agent fixture."""
    return fixtures_dir / 'valid_agent.md'


@pytest.fixture
def invalid_agent_no_frontmatter(fixtures_dir):
    """Return path to invalid agent (no frontmatter) fixture."""
    return fixtures_dir / 'invalid_agent_no_frontmatter.md'


@pytest.fixture
def invalid_agent_hardcoded_paths(fixtures_dir):
    """Return path to invalid agent (hardcoded paths) fixture."""
    return fixtures_dir / 'invalid_agent_hardcoded_paths.md'


@pytest.fixture
def invalid_agent_missing_sections(fixtures_dir):
    """Return path to invalid agent (missing sections) fixture."""
    return fixtures_dir / 'invalid_agent_missing_sections.md'
