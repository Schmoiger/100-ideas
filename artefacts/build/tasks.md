# Tasks: 100-Ideas Agentic Publishing System

---

## Header

**Branch**: `feature/requirements`
**Status**: In Progress
**Scope**: Agentic content pipeline automating the transformation of 100 ideas into a typeset Typst book and publication-ready blog posts.
**Design**: [requirements.md](file:///Users/avi/Repos/100-ideas/artefacts/product/requirements.md)
**Created**: 2026-09-17
**Amended**: 2026-09-17 — Initial task breakdown and workflow/agent tracking setup

---

## Task Index

| ID | Pri | Status | Blocked By | Task |
|---|---|---|---|---|
| TASK-001 | critical | completed | - | Define product requirements in `artefacts/product/requirements.md` |
| TASK-002 | high | pending | TASK-001 | Audit existing agents/workflows vs new agent needs and document mapping |
| TASK-003 | high | pending | TASK-002 | Create or adapt workflow definition (e.g. `context/workflows/ideas-publishing.yaml`) |
| TASK-004 | high | pending | TASK-002 | Author new specialized agents if required (e.g. illustrator, typesetter) in `context/agents/` |
| TASK-005 | medium | pending | TASK-003, TASK-004 | Run `uv run agent-harness` to compile adapters and verify zero drift (`uv run agent-drift`) |
| TASK-006 | high | pending | TASK-001 | Resolve `100-ideas.md` symlink/sandbox ingestion and test batch catalog parsing |
| TASK-007 | medium | pending | TASK-006 | Implement incremental inbox ingestion parser (`artefacts/product/inbox.md`) |
| TASK-008 | high | pending | TASK-004 | Implement shared M:N resource library indexing and idea linking |
| TASK-009 | high | pending | TASK-004 | Implement Gemini visual prompt derivation and image generation agent integration |
| TASK-010 | high | pending | TASK-004 | Implement Book Mode drafting (author persona) and Typst typesetting pipeline |
| TASK-011 | high | pending | TASK-004 | Implement Blog Mode drafting (blogger persona), Hostinger frontmatter, and LinkedIn exports |
| TASK-012 | medium | pending | TASK-008 | Implement Markdown portability export bundling |

---

## Specifications

### TASK-001: Define Product Requirements
- **Status**: Completed
- **Acceptance Criteria**:
  - Structured EARS notation in `artefacts/product/requirements.md`.
  - Defined dual-path ingestion, M:N shared resource library, book & blog modes, and token governance.

### TASK-002: Audit Existing Agents and Workflows
- **Status**: Pending
- **Description**: Review existing agents (`product-expert`, `documentation`, `ui-designer`, `orchestrator`) and workflows (`context/workflows/content.yaml`) to determine which can be reused directly vs where new specialized definitions are required.
- **Acceptance Criteria**:
  - Mapping matrix produced comparing required pipeline roles to existing agents.
  - Decision documented on whether `content.yaml` should be extended or a new `ideas-publishing.yaml` created.

### TASK-003: Pipeline Workflow Definition
- **Status**: Pending
- **Description**: Define or update workflow YAML with phase dependencies, agent assignments, outputs, and quality gates for 100-ideas pipeline.
- **Acceptance Criteria**:
  - Valid YAML in `context/workflows/`.
  - Complies with `context/standards/workflow-standards.md`.

### TASK-004: Author New Specialized Agents
- **Status**: Pending
- **Description**: Author any newly required agents (e.g. `illustrator.md`, `typesetter.md`) in `context/agents/` according to `context/standards/agent-standards.md`.
- **Acceptance Criteria**:
  - Valid YAML frontmatter with model tier, standards, rules, and scoped permissions.

### TASK-005: Adapter Compilation & Drift Check
- **Status**: Pending
- **Description**: Run `uv run agent-harness` to project new context definitions into runtime adapters (`AGENTS.md`, `GEMINI.md`, etc.).
- **Acceptance Criteria**:
  - `uv run agent-drift` exits with code 0.
