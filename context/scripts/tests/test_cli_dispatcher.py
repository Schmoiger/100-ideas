import time
import shutil
from pathlib import Path
import pytest

from context.scripts.generators.generate_adapters import (
    build_parser,
    normalize_target,
    run_generation,
    get_adapter_projections,
)
from context.scripts.generators.adapters.core.loader import load_canonical_context


def test_target_normalization():
    """Verify alias normalization across supported targets."""
    assert normalize_target("all") == "all"
    assert normalize_target("gemini") == "gemini"
    assert normalize_target("g") == "gemini"
    assert normalize_target("claude") == "claude"
    assert normalize_target("c") == "claude"
    assert normalize_target("github") == "github"
    assert normalize_target("gh") == "github"
    assert normalize_target("copilot") == "github"
    assert normalize_target("p") == "github"
    assert normalize_target("codex") == "openai"
    assert normalize_target("openai") == "openai"
    assert normalize_target("o") == "openai"
    assert normalize_target("CLAUDE") == "claude"
    assert normalize_target("COPILOT") == "github"

    with pytest.raises(ValueError, match="Unknown target"):
        normalize_target("nonexistent")


def test_cli_parser_flags():
    """Verify command line parser parses target shortcuts and mode flags."""
    parser = build_parser()

    args = parser.parse_args(["-t", "claude", "-d"])
    assert args.target == "claude"
    assert args.dry_run is True
    assert args.all is False

    args_g = parser.parse_args(["-g", "-a"])
    assert args_g.gemini is True
    assert args_g.all is True

    args_p = parser.parse_args(["-p"])
    assert args_p.copilot is True

    args_c = parser.parse_args(["-c"])
    assert args_c.claude is True

    args_o = parser.parse_args(["-o"])
    assert args_o.codex is True


def test_dry_run_leaves_disk_untouched(tmp_path: Path):
    """Verify that --dry-run produces no files on disk."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"
    shutil.copytree(
        context_dir, tmp_path / "context", symlinks=True, ignore_dangling_symlinks=True
    )

    result = run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"claude"},
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert len(result["created"]) > 0
    # Files should not exist on disk
    assert not (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / ".claude").exists()


def test_smart_update_preserves_unchanged_files(tmp_path: Path):
    """Verify default smart update preserves mtime of unchanged files."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"
    shutil.copytree(
        context_dir, tmp_path / "context", symlinks=True, ignore_dangling_symlinks=True
    )

    # Initial generation
    result1 = run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"claude"},
        force=False,
    )
    assert len(result1["created"]) > 0

    claude_md = tmp_path / "CLAUDE.md"
    initial_mtime = claude_md.stat().st_mtime_ns

    # Small pause to ensure mtime difference would register if written
    time.sleep(0.01)

    # Second run without force
    result2 = run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"claude"},
        force=False,
    )

    assert len(result2["created"]) == 0
    assert len(result2["updated"]) == 0
    assert len(result2["unchanged"]) > 0
    assert claude_md.stat().st_mtime_ns == initial_mtime

    # Third run with force=True
    result3 = run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"claude"},
        force=True,
    )
    assert len(result3["updated"]) > 0


def test_generation_execution_speed_benchmark():
    """Verify that full in-memory projection generation executes in well under 2.0s."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"

    start = time.perf_counter()
    context = load_canonical_context(str(context_dir))
    projections = get_adapter_projections(context, repo_root, targets=None)
    duration = time.perf_counter() - start

    assert len(projections) > 50
    assert duration < 2.0, f"Generation took {duration:.3f}s, exceeding 2.0s threshold"


def test_ensure_root_gitignore(tmp_path: Path):
    """Verify that ensure_root_gitignore creates or updates .gitignore appropriately."""
    from context.scripts.generators.generate_adapters import (
        ensure_root_gitignore,
        IGNORED_BLOCK,
    )

    # Case 1: dry_run leaves disk untouched
    assert ensure_root_gitignore(tmp_path, dry_run=True) is True
    assert not (tmp_path / ".gitignore").exists()

    # Case 2: creates .gitignore if it doesn't exist
    assert ensure_root_gitignore(tmp_path, dry_run=False) is True
    assert (tmp_path / ".gitignore").exists()
    content = (tmp_path / ".gitignore").read_text()
    assert "AGENTS.md" in content
    assert ".agents/skills/" in content

    # Case 3: no-op if already present
    assert ensure_root_gitignore(tmp_path, dry_run=False) is False

    # Case 4: appends if partially missing
    (tmp_path / ".gitignore").write_text("existing_rule/\n")
    assert ensure_root_gitignore(tmp_path, dry_run=False) is True
    content_updated = (tmp_path / ".gitignore").read_text()
    assert "existing_rule/" in content_updated
    assert "AGENTS.md" in content_updated


def test_load_configured_targets(tmp_path: Path):
    """Verify loading active targets from .agent-targets file."""
    from context.scripts.generators.generate_adapters import load_configured_targets

    # Non-existent file returns None
    assert load_configured_targets(tmp_path) is None

    # File with comments and targets
    (tmp_path / ".agent-targets").write_text("# Target runtimes\nclaude, gemini\n# other\n")
    assert load_configured_targets(tmp_path) == {"claude", "gemini"}

    # File with 'all' returns None (meaning all targets)
    (tmp_path / ".agent-targets").write_text("all\n")
    assert load_configured_targets(tmp_path) is None
