import shutil
from pathlib import Path
import pytest

from context.scripts.generators.generate_adapters import (
    run_generation,
    get_adapter_projections,
)
from context.scripts.validators.adapter_drift import check_adapter_drift
from context.scripts.generators.adapters.core.loader import load_canonical_context


def test_e2e_full_compilation_all_targets(tmp_path: Path):
    """Validate end-to-end compilation of all 4 runtime adapters in an isolated environment."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"

    # Copy context/ into sandbox tmp_path
    shutil.copytree(
        context_dir, tmp_path / "context", symlinks=True, ignore_dangling_symlinks=True
    )

    # Run full compilation across all targets
    result = run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"all"},
        force=True,
    )

    created_files = result["created"] + result["updated"]
    assert len(created_files) >= 80

    # 1. Core verification
    assert (tmp_path / "AGENTS.md").is_file()
    agents_content = (tmp_path / "AGENTS.md").read_text()
    assert "# AGENTS.md" in agents_content
    assert "## Workflows" in agents_content
    assert "## Agents" in agents_content

    # 2. Gemini / Antigravity verification
    assert (tmp_path / "GEMINI.md").is_file()
    gemini_content = (tmp_path / "GEMINI.md").read_text()
    assert "@AGENTS.md" in gemini_content
    skills_dir = tmp_path / ".agents" / "skills"
    assert skills_dir.is_dir()
    skill_files = list(skills_dir.glob("*/SKILL.md"))
    assert len(skill_files) >= 18

    # 3. Claude Code verification
    assert (tmp_path / "CLAUDE.md").is_file()
    claude_content = (tmp_path / "CLAUDE.md").read_text()
    assert "@AGENTS.md" in claude_content
    claude_prompts_dir = tmp_path / ".claude" / "prompts"
    assert claude_prompts_dir.is_dir()
    claude_prompts = list(claude_prompts_dir.glob("*.md"))
    assert len(claude_prompts) >= 18

    # 4. GitHub Copilot verification
    assert (tmp_path / ".github" / "copilot-instructions.md").is_file()
    gh_prompts_dir = tmp_path / ".github" / "prompts"
    assert gh_prompts_dir.is_dir()
    gh_prompts = list(gh_prompts_dir.glob("*.prompt.md"))
    assert len(gh_prompts) >= 18
    gh_instructions_dir = tmp_path / ".github" / "instructions"
    assert gh_instructions_dir.is_dir()
    assert len(list(gh_instructions_dir.glob("*.instructions.md"))) >= 3

    # 5. OpenAI / Codex verification
    openai_prompts_dir = tmp_path / ".openai" / "prompts"
    assert openai_prompts_dir.is_dir()
    openai_prompts = list(openai_prompts_dir.glob("*.txt"))
    assert len(openai_prompts) >= 18
    assert (tmp_path / ".openai" / "tools.json").is_file()
    assert (tmp_path / ".openai" / "runner.py").is_file()

    # 6. Verify zero drift against validator
    is_synced, drift_issues = check_adapter_drift(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"all"},
    )
    assert is_synced, f"Generated projections drifted: {drift_issues}"


def test_e2e_deterministic_reproducibility(tmp_path: Path):
    """Verify that repeated compilation produces byte-for-byte identical output."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    context_dir = repo_root / "context"
    shutil.copytree(
        context_dir, tmp_path / "context", symlinks=True, ignore_dangling_symlinks=True
    )

    # Run 1
    run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"all"},
        force=True,
    )

    first_run_hashes: dict[str, str] = {}
    for f in tmp_path.rglob("*"):
        if f.is_file() and not str(f).startswith(str(tmp_path / "context")):
            first_run_hashes[str(f.relative_to(tmp_path))] = f.read_text()

    # Run 2 (forced full regeneration)
    run_generation(
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
        targets={"all"},
        force=True,
    )

    second_run_hashes: dict[str, str] = {}
    for f in tmp_path.rglob("*"):
        if f.is_file() and not str(f).startswith(str(tmp_path / "context")):
            second_run_hashes[str(f.relative_to(tmp_path))] = f.read_text()

    assert first_run_hashes.keys() == second_run_hashes.keys()
    for rel_path, content1 in first_run_hashes.items():
        content2 = second_run_hashes[rel_path]
        assert content1 == content2, (
            f"File {rel_path} differed between compilation runs"
        )


def test_e2e_synthetic_context_compilation(tmp_path: Path):
    """Verify compilation with a minimal synthetic context directory."""
    synth_context = tmp_path / "context"
    agents_dir = synth_context / "agents"
    workflows_dir = synth_context / "workflows"
    rules_dir = synth_context / "rules"
    standards_dir = synth_context / "standards"

    agents_dir.mkdir(parents=True)
    workflows_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    standards_dir.mkdir(parents=True)

    # 1 synthetic agent
    (agents_dir / "custom-bot.md").write_text(
        "---\n"
        "name: custom-bot\n"
        "description: Performs automated custom tasks.\n"
        "standards:\n"
        "  - custom-standards.md\n"
        "rules:\n"
        "  - custom-rule.md\n"
        "---\n\n"
        "# Custom Bot\n\nCustom bot body.\n"
    )

    # 1 synthetic workflow
    (workflows_dir / "sample-flow.yaml").write_text(
        "name: sample-flow\n"
        "description: Sample automated workflow.\n"
        "steps:\n"
        "  - name: step-1\n"
        "    agent: custom-bot\n"
    )

    # 1 synthetic standard with applyTo
    (standards_dir / "custom-standards.md").write_text(
        "# Custom Standards\n\n"
        "## Deployment Safety\n"
        '<!-- applyTo: "custom/**/*.py" -->\n\n'
        "Safety instructions.\n"
    )

    # 1 synthetic rule
    (rules_dir / "custom-rule.md").write_text("# Custom Rule\n\nRule details.\n")

    # Run compilation on synthetic context
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = run_generation(
        repo_root=output_dir,
        context_dir=synth_context,
        targets={"all"},
        force=True,
    )

    assert len(result["created"]) > 0
    assert (output_dir / "AGENTS.md").is_file()
    assert (output_dir / "GEMINI.md").is_file()
    assert (output_dir / "CLAUDE.md").is_file()
    assert (output_dir / ".agents" / "skills" / "custom-bot" / "SKILL.md").is_file()
    assert (output_dir / ".claude" / "prompts" / "custom-bot.md").is_file()
    assert (output_dir / ".github" / "prompts" / "custom-bot.prompt.md").is_file()
    assert (output_dir / ".openai" / "prompts" / "custom-bot.txt").is_file()
