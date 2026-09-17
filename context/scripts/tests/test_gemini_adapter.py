import os
import shutil
import tempfile
import unittest
from pathlib import Path

from context.scripts.generators.adapters.core.models import CanonicalAgent
from context.scripts.generators.adapters.gemini.generator import (
    generate_gemini_md,
    generate_skills,
)


class TestGeminiAdapter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.context = {
            "agents": {
                "test-agent": CanonicalAgent(
                    name="test-agent",
                    description="A test agent",
                    model="gemini-test",
                    mcp_tools=["test-tool"],
                    standards=["test-standard"],
                    rules=["test-rule"],
                )
            },
            "workflows": {},
        }
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_generate_skills(self):
        generate_skills(self.context, self.output_dir)

        skill_dir = self.output_dir / ".agents" / "skills" / "test-agent"
        self.assertTrue(skill_dir.exists())

        skill_file = skill_dir / "SKILL.md"
        self.assertTrue(skill_file.exists())

        content = skill_file.read_text()
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name: test-agent", content)
        self.assertIn("description: A test agent", content)
        self.assertIn("Auto-generated", content)

    def test_generate_gemini_md(self):
        generate_gemini_md(self.context, self.output_dir)
    
        gemini_md_path = self.output_dir / "GEMINI.md"
        self.assertTrue(gemini_md_path.exists())
    
        content = gemini_md_path.read_text()
        self.assertIn("Auto-generated", content)
        self.assertIn("@AGENTS.md", content)
        self.assertIn("replace_file_content", content)

if __name__ == "__main__":
    unittest.main()
