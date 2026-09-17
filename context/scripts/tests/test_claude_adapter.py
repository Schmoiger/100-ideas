from pathlib import Path

from context.scripts.generators.adapters.core.models import CanonicalAgent
from context.scripts.generators.adapters.claude.generator import (
    generate_claude_md,
    generate_subagent_prompts,
)


def test_generate_claude_md(tmp_path: Path):
    context = {}
    generate_claude_md(context, tmp_path)
    
    claude_md_path = tmp_path / "CLAUDE.md"
    assert claude_md_path.exists()
    content = claude_md_path.read_text()
    
    assert "# Claude System Instructions" in content
    assert "@AGENTS.md" in content
    assert "@.claude/prompts/" in content


def test_generate_subagent_prompts(tmp_path: Path):
    context = {
        "agents": {
            "test-agent": CanonicalAgent(
                name="test-agent",
                description="Test description",
                model="test-model",
                standards=["Standard 1"],
                rules=["Rule 1"]
            )
        }
    }
    generate_subagent_prompts(context, tmp_path)
    
    prompt_path = tmp_path / ".claude" / "prompts" / "test-agent.md"
    assert prompt_path.exists()
    content = prompt_path.read_text()
    
    assert "# Test Agent" in content
    assert "Test description" in content
    assert "@context/standards/Standard 1" in content
    assert "@context/rules/Rule 1" in content
