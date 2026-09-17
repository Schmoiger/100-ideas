from pathlib import Path
from typing import Any

import yaml

from context.scripts.generators.adapters.core.models import (
    CanonicalAgent,
    CanonicalSkill,
    Phase,
    WorkflowDAG,
)


def extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}, parts[2]
    return {}, content


def load_canonical_context(context_dir_path: str) -> dict[str, Any]:
    """
    Scans the context directory and parses the canonical representation
    of agents, rules, standards, and workflows.
    """
    context_path = Path(context_dir_path)
    if not context_path.exists():
        raise FileNotFoundError(f"Context directory not found: {context_dir_path}")

    agents: dict[str, CanonicalAgent] = {}
    workflows: dict[str, WorkflowDAG] = {}
    skills: dict[str, CanonicalSkill] = {}

    # Parse agents
    agents_dir = context_path / "agents"
    if agents_dir.exists():
        for file_path in agents_dir.glob("*.md"):
            content = file_path.read_text()
            frontmatter, _ = extract_frontmatter(content)
            if "name" in frontmatter:
                agents[frontmatter["name"]] = CanonicalAgent(
                    name=frontmatter["name"],
                    description=frontmatter.get("description", ""),
                    model=frontmatter.get("model", ""),
                    mcp_tools=frontmatter.get("mcp_tools", []),
                    standards=frontmatter.get("standards", []),
                    rules=frontmatter.get("rules", []),
                    skills=frontmatter.get("skills", []),
                )

    # Parse skills
    skills_dir = context_path / "skills"
    if skills_dir.exists():
        for file_path in sorted(skills_dir.glob("*.md")):
            content = file_path.read_text()
            frontmatter, body = extract_frontmatter(content)
            if "name" in frontmatter:
                skills[frontmatter["name"]] = CanonicalSkill(
                    name=frontmatter["name"],
                    description=frontmatter.get("description", ""),
                    globs=frontmatter.get("globs", []),
                    body=body.strip(),
                )

    # Parse workflows
    workflows_dir = context_path / "workflows"
    if workflows_dir.exists():
        for file_path in workflows_dir.glob("*.yaml"):
            data = yaml.safe_load(file_path.read_text()) or {}
            if "name" in data:
                phases = []
                for p_data in data.get("phases", []):
                    phase_agents = p_data.get("agents", [])
                    # Validate cross-references
                    for agent_name in phase_agents:
                        if agent_name not in agents:
                            raise ValueError(
                                f"Workflow '{data['name']}' references unmapped agent: '{agent_name}'"
                            )
                    phases.append(
                        Phase(
                            id=p_data.get("id", ""),
                            name=p_data.get("name", ""),
                            agents=phase_agents,
                            validation=p_data.get("validation", []),
                        )
                    )
                workflows[data["name"]] = WorkflowDAG(
                    name=data["name"],
                    description=data.get("description", ""),
                    phases=phases,
                )

    return {"agents": agents, "workflows": workflows, "skills": skills}
