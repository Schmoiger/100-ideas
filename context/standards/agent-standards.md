# Agent Interaction Standards

---

## 1. Introduction

This document outlines the standards for how AI agents shall interact with this software development project. Its purpose is to create a predictable and reliable environment where agents can act as effective and autonomous partners in development.

---

## 1.1. Standards Compliance

All agents shall follow the standards defined in `./context/standards/` and rules defined in `./context/rules/`. Agents are not required to explicitly reference individual standards; compliance is inherited by operating within this project.

### Rule Injection

Subagents do not auto-load rules. The orchestrator injects rules into each spawn prompt via Rule Resolution (see `context/agents/orchestrator.md`):

1. **Always-apply rules** are hardcoded in the orchestrator definition and included for every agent. When adding a new rule with `alwaysApply: true`, you must also add it to the orchestrator's always-apply list.
2. **Agent-specific rules** come from the agent's `rules:` frontmatter, filtered by glob match against the task's files.

This means a rule with `alwaysApply: true` in its `.mdc` frontmatter will NOT be injected unless it is also listed in the orchestrator's always-apply list.

### Canonical Asset Parsing

Markdown files in the `context/` directory (such as agents, personas, and rules) use YAML frontmatter separated by `---`. Any automated parsers or runtime adapters reading these files MUST extract this metadata by splitting on the `---` delimiters, keeping the parsed frontmatter separate from the markdown body.

---

## 1.2. Input Standards vs Output Artefacts

Agents read from input standards and write to output artefacts. For full directory layout see [doc-standards.md §2.1](doc-standards.md#21-directory-structure).

| Directory | Purpose | Lifecycle |
|----------|---------|-----------|
| `/context/` | Input standards and rules for agents to follow | Persistent; version controlled |
| `{service}/artefacts/` | Service-specific working outputs (bugs, tasks, test results) | Persistent; version controlled |
| `/artefacts/` | System-wide artefacts (architecture, requirements, API contracts) | Persistent; version controlled |

**Workflow**: Agents read standards from `/context/` and write outputs to `{service}/artefacts/` for service-specific work or `/artefacts/` for system-wide artefacts. All artefacts are version controlled and do not require promotion.

---

## 2. State Recovery After Compaction

When context is compacted or a new session begins mid-project, the agent shall re-orient using two steps:

1. **Glob `**/artefacts/README.md`** and read all matches. Each `artefacts/` directory (root and service-level) maintains a `README.md` describing current state — active tasks, recent decisions, blockers, and key file pointers. See [doc-standards.md §2.3](doc-standards.md#23-service-package-artefact-files) for the format.

2. **Run `git log --oneline -5`** to understand what has changed recently.

These two steps are sufficient for orientation. The agent shall not attempt to re-read all standards or reconstruct project state from scratch.

---

## 3. Agent Context Setup Workflow

*For procedural guidance on bootstrapping a new project or feature, refer to `context/skills/bootstrap-workflow.md`.*
---

## 4. Agent Behaviour

To operate autonomously but safely, agents shall adhere to the following behaviours:

### 4.1. Agent Planning and Execution

*   When an agent is assigned a multi-step task, it shall first create a plan and present it for approval.
*   If an agent is to perform a destructive action, then it shall seek confirmation before proceeding. A destructive action is one that is not easily reversible. This includes, but is not limited to, deleting untracked files or running commands that permanently alter a remote resource.
*   When an agent completes a task, it shall state what it did and why.
*   If an agent is in doubt about the project's state, then it shall ask for clarification or read the relevant documentation.

### 4.2. Agent Boundaries

*   The agent shall not perform work that is outside the scope of the currently assigned task.
*   The agent shall not perform any action that contradicts the standards defined in the project and common documentation.
*   The agent shall not modify files outside the directory of the current project.
*   The agent shall not proceed based on their own assumptions until the assumptions are validated with the user.

### 4.3. Tool Usage

*For procedural guidance on sandbox heuristics and tool selection policies, refer to `context/skills/agent-sandbox.md`.*
### 4.4. Version Control

Agents shall adhere strictly to the version control and commit strategies defined in `context/rules/workspace-conventions.md` and follow the procedural guidance in `context/skills/agent-workflows.md`.

### 4.5. Agent Handoffs

Agents shall communicate context and status through structured handoff documents to enable coordination.

#### 4.5.1. Handoff Types

**Intra-domain handoffs** (within same service/package):
- Location: `{service-directory}/HANDOFF.md`
- Purpose: Coordinate between agents working on the same context domain
- Example: functional-tester → python-coder → tech-lead

**Inter-domain handoffs** (between services):
- Location: `artefacts/shared/handoffs/{service}-api.md`
- Purpose: Coordinate between agents working on different context domains
- Example: bronze-service → vis-service, vis-service → frontend

*For handoff formatting, workflows, integration readiness checklists, and templates, refer to the `context/skills/multi-agent-workflows.md` skill.*

### 4.6. Interruptions Logging

*For interruption log formats and procedures, refer to `context/skills/multi-agent-workflows.md`.*
---

## 5. Build, Test, and Automation Artefacts

*   The agent shall store all tests in a `tests/` directory within the project.
*   The agent shall store all scripts used for automation in a `scripts/` directory.
*   The agent shall store all test results and build artefacts in the `{service}/artefacts/` directory within the project.

---

## 6. Git Strategy: Single Branch + Scoped Commits

All agents work on the **same branch**. The orchestrator prevents collisions by assigning each agent a **file scope** — the set of paths the agent may write to and commit. No worktrees, no branch merging, no integration step.

*For procedural details on File Scope Assignment, Parallel Agent Safety, Read-Only Agents, and Scope Violations, refer to `context/skills/multi-agent-workflows.md`.*

*For commit cadence guidance (RED/GREEN/REFACTOR checkpoints), refer to `context/skills/agent-workflows.md`.*
