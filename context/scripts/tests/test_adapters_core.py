import unittest
from pathlib import Path

from context.scripts.generators.adapters.core.budget import (
    DeliveryStrategy,
    TokenEstimator,
)
from context.scripts.generators.adapters.core.loader import load_canonical_context

# These imports will fail initially because the modules don't exist yet
from context.scripts.generators.adapters.core.models import (
    CanonicalAgent,
    CanonicalSkill,
    Phase,
    WorkflowDAG,
)
from context.scripts.generators.adapters.core.tools import CapabilityRegistry


class TestAdaptersCoreModels(unittest.TestCase):
    def test_canonical_agent_dataclass(self):
        agent = CanonicalAgent(
            name="test-agent",
            description="A test agent",
            model="sonnet",
            mcp_tools=["tool1"],
            standards=["std1.md"],
            rules=["rule1.md"],
        )
        self.assertEqual(agent.name, "test-agent")
        self.assertEqual(agent.model, "sonnet")
        self.assertIn("tool1", agent.mcp_tools)

    def test_canonical_skill_dataclass(self):
        skill = CanonicalSkill(
            name="test-skill",
            description="A test skill",
            globs=["**/*.py"],
            body="Skill instructions",
        )
        self.assertEqual(skill.name, "test-skill")
        self.assertEqual(skill.description, "A test skill")
        self.assertEqual(skill.globs, ["**/*.py"])
        self.assertEqual(skill.body, "Skill instructions")


import tempfile

import yaml


class TestAdaptersCoreLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.context_path = Path(self.temp_dir.name)

        # Create agents directory
        agents_dir = self.context_path / "agents"
        agents_dir.mkdir(parents=True)

        agent_content = """---
name: test-agent
description: A mock agent
model: sonnet
mcp_tools:
  - tool1
standards:
  - test-standard.md
rules:
  - test-rule.md
---

This is the body of the markdown.
"""
        (agents_dir / "test-agent.md").write_text(agent_content)

        # Create workflows directory
        workflows_dir = self.context_path / "workflows"
        workflows_dir.mkdir(parents=True)

        workflow_content = {
            "name": "test-build",
            "description": "Mock workflow",
            "phases": [
                {
                    "id": "phase-1",
                    "name": "First Phase",
                    "agents": ["test-agent"],
                    "validation": ["Check something"],
                }
            ],
        }
        (workflows_dir / "test-build.yaml").write_text(yaml.dump(workflow_content))

        # Create rules directory
        rules_dir = self.context_path / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test-rule.md").write_text(
            "---\nname: test-rule\nkey_points: some rule\n---"
        )

        # Create standards directory
        standards_dir = self.context_path / "standards"
        standards_dir.mkdir(parents=True)
        (standards_dir / "test-standard.md").write_text("# Test Standard")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_canonical_context(self):
        context_data = load_canonical_context(str(self.context_path))

        # Verify agents
        self.assertIn("agents", context_data)
        agent = context_data["agents"]["test-agent"]
        self.assertIsInstance(agent, CanonicalAgent)
        self.assertEqual(agent.name, "test-agent")
        self.assertEqual(agent.description, "A mock agent")
        self.assertEqual(agent.rules, ["test-rule.md"])

        # Verify workflows
        self.assertIn("workflows", context_data)
        workflow = context_data["workflows"]["test-build"]
        self.assertIsInstance(workflow, WorkflowDAG)
        self.assertEqual(workflow.name, "test-build")
        self.assertEqual(len(workflow.phases), 1)
        self.assertEqual(workflow.phases[0].id, "phase-1")
        self.assertIsInstance(workflow.phases[0], Phase)

    def test_missing_agent_validation(self):
        # Create a workflow that references a non-existent agent
        workflows_dir = self.context_path / "workflows"
        bad_workflow = {
            "name": "bad",
            "description": "bad",
            "phases": [{"id": "p1", "name": "p1", "agents": ["missing-agent"]}],
        }
        (workflows_dir / "bad.yaml").write_text(yaml.dump(bad_workflow))

        with self.assertRaises(ValueError) as context:
            load_canonical_context(str(self.context_path))
        self.assertIn("references unmapped agent", str(context.exception))


class TestAdaptersCoreTools(unittest.TestCase):
    def test_capability_registry_extensibility(self):
        registry = CapabilityRegistry()

        # Test default capability registration
        registry.register_capability(
            "FILE_WRITE",
            {"claude": "Write", "gemini": "write_to_file", "codex": "custom_write"},
        )

        mapping = registry.get_mapping("FILE_WRITE")
        self.assertEqual(mapping["claude"], "Write")
        self.assertEqual(mapping["gemini"], "write_to_file")


class TestAdaptersCoreBudget(unittest.TestCase):
    def test_token_estimator(self):
        estimator = TokenEstimator()
        # Using a simple chars/4 heuristic
        text = "a" * 400
        tokens = estimator.estimate_tokens(text)
        self.assertEqual(tokens, 100)

        strategy = estimator.recommend_strategy(tokens, budget=50)
        self.assertEqual(strategy, DeliveryStrategy.ON_DEMAND_LINK)

        strategy2 = estimator.recommend_strategy(tokens, budget=200)
        self.assertEqual(strategy2, DeliveryStrategy.INLINE_COMPREHENSIVE)


if __name__ == "__main__":
    unittest.main()
