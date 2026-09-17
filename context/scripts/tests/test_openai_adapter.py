import json
from pathlib import Path

from context.scripts.generators.adapters.core.models import CanonicalAgent
from context.scripts.generators.adapters.openai.generator import (
    generate_runner_harness,
    generate_system_prompts,
    generate_tool_schemas,
)


def test_generate_system_prompts(tmp_path: Path):
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
    generate_system_prompts(context, tmp_path)
    
    prompt_path = tmp_path / ".openai" / "prompts" / "test-agent.txt"
    assert prompt_path.exists()
    content = prompt_path.read_text()
    
    assert "You are Test Agent." in content
    assert "Role: Test description" in content
    assert "STANDARDS:" in content
    assert "- Standard 1" in content
    assert "RULES:" in content
    assert "- Rule 1" in content


def test_generate_tool_schemas(tmp_path: Path):
    context = {}
    generate_tool_schemas(context, tmp_path)
    
    tools_path = tmp_path / ".openai" / "tools.json"
    assert tools_path.exists()
    content = json.loads(tools_path.read_text())
    
    assert len(content) == 1
    assert content[0]["type"] == "function"
    assert content[0]["function"]["name"] == "registry_lookup"


def test_generate_runner_harness(tmp_path: Path):
    generate_runner_harness(tmp_path)
    
    runner_path = tmp_path / ".openai" / "runner.py"
    assert runner_path.exists()
    content = runner_path.read_text()
    
    assert "import httpx" in content
    assert "def run_agent(" in content
    assert "https://api.openai.com/v1/chat/completions" in content
