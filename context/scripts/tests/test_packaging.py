from __future__ import annotations

from pathlib import Path
from context.scripts.generators.generate_adapters import build_parser as build_generator_parser
from context.scripts.validators.adapter_drift import check_adapter_drift


def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and declares required entrypoints."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    pyproject_file = repo_root / "pyproject.toml"
    assert pyproject_file.is_file(), "pyproject.toml must exist at repo root"
    content = pyproject_file.read_text()
    assert "[project.scripts]" in content
    assert 'agent-harness = "context.scripts.generators.generate_adapters:main"' in content
    assert 'agent-drift = "context.scripts.validators.adapter_drift:main"' in content
    assert "hatchling" in content


def test_generator_entrypoint_parser():
    """Verify that agent-harness argument parser configures all options properly."""
    parser = build_generator_parser()
    assert parser.prog == "agent-harness"

    # Test default parsing
    args = parser.parse_args([])
    assert args.target is None
    assert args.dry_run is False
    assert args.all is False

    # Test custom flags
    args = parser.parse_args(["-d", "-t", "gemini", "--repo-root", "/tmp/fake"])
    assert args.dry_run is True
    assert args.target == "gemini"
    assert str(args.repo_root) == "/tmp/fake"


def test_drift_validator_callable():
    """Verify that check_adapter_drift runs without throwing exceptions on canonical context."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"

    is_synced, drift_issues = check_adapter_drift(
        repo_root=repo_root,
        context_dir=context_dir,
    )
    assert is_synced is True
    assert len(drift_issues) == 0
