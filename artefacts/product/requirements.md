# Example Requirements: Agentic Orchestration Harness

THIS SECTION IS POPULATED AS AN EXAMPLE. THESE ARE THE PRODUCT REQUIREMENTS FOR THE AGENTIC HARNESS AND SHOULD BE REPLACED BY THE PRODUCT REQUIREMENTS FOR YOUR PROJECT.

---

## Overview

The Agentic Orchestration Harness is a vendor-neutral, portable framework designed to coordinate teams of specialised AI agents across heterogeneous development runtimes (Claude Code, GitHub Copilot, Codex/OpenAI, and Gemini/Antigravity). The system enforces a strict architectural separation between a portable, authoritative **Core Harness** (canonical agents, rules, standards, workflows, and templates) and **Runtime Adapters** (compilation targets projecting canonical assets into platform-specific instructions, skills, hooks, and tool schemas).

The framework answers five coordination questions: **who** does work (agents), **how** work should be done (standards and rules), **when** work happens (workflows), **what** gets produced (templates), and **how quality is maintained** (review gates, validators, and telemetry).

---

## Legend

| Symbol | Meaning |
| -------- | --------- |
| **M** | MVP (P0) — Must have for baseline cross-platform release |
| **P** | Post-MVP (P1) — Next iteration (enhanced automation and broad ecosystem) |
| **F** | Future (P2) — Backlog (autonomous adapter synthesis) |

---

## Functional Requirements

### 1. Context Layer (`context/`)

The Context Layer serves as the single source of truth (SSOT) for all agent specifications, operating rules, reference standards, workflow topologies, artefact templates, and writing personas.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-CTX-001 | M | THE core-harness SHALL maintain all authoritative agent definitions, rules, standards, workflow topologies, templates, and personas in a versioned `context/` directory. | Core definitions exist in git, formatted as Markdown with YAML frontmatter (`agents/`), MDC (`rules/`), Markdown (`standards/`, `templates/`, `persona/`), and YAML (`workflows/`). |
| REQ-CTX-002 | M | THE core-harness SHALL isolate concise, binary rules (`context/rules/*.mdc`) from detailed reference standards (`context/standards/*.md`). | Rules are independently injectable (<200 tokens each) with binary compliance criteria; standards contain rationale and in-depth guidance. |
| REQ-CTX-003 | M | WHEN an agent is spawned, THE core-harness SHALL dynamically resolve and inject only applicable rules by glob-matching the task file scope against rule headers. | Unrelated rules are excluded from agent context, keeping framework injection overhead under 2,500 tokens per spawn. |
| REQ-CTX-004 | M | THE core-harness SHALL provide standardised artefact templates (`context/templates/`) for all system deliverables. | Handoffs, requirements, architectures, task lists, reviews, commit messages, PR descriptions, agent definitions, and design documents conform to uniform templates across all runtimes. |
| REQ-CTX-005 | M | THE core-harness SHALL provide writing personas (`context/persona/`) for human-facing content workflows. | Personas define voice and style (technical writer, opinionated blogger, editor, expert reviewer) and are applied exclusively to external-facing prose, not technical artefacts. |
| REQ-CTX-006 | P | WHEN a new rule is created with `alwaysApply: true`, THE core-harness SHALL require that it is also added to the orchestrator's always-apply list. | Static validation halts if an always-apply rule exists in `context/rules/` but is absent from `context/agents/orchestrator.md`. |

### 2. Agent Coordination

The Agent Coordination subsystem defines how agents are structured, spawned, scoped, and governed during execution.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-AGT-001 | M | THE core-harness SHALL define specialised agent roles as Markdown files with YAML frontmatter declaring name, model tier, applicable rules, and required standards. | Each agent definition in `context/agents/*.md` contains parseable YAML frontmatter and an instruction body. |
| REQ-AGT-002 | M | THE core-harness SHALL enforce orchestrator governance where only the orchestrator commits to version control. | Specialised child agents produce code and artefacts within assigned file scopes but SHALL NOT execute git commits directly. |
| REQ-AGT-003 | M | WHEN spawning a subagent, THE orchestrator SHALL use the task prompt template (`context/templates/task-prompt-template.md`) to ensure consistent rule resolution, file scope assignment, and escalation instructions. | Every spawn prompt includes the agent definition file path, resolved rules, immediate context, file scope constraints, and escalation instructions. |
| REQ-AGT-004 | M | WHEN spawning multiple agents in a parallel hive phase, THE orchestrator SHALL assign disjoint file scopes to each agent. | No two concurrent agents are permitted write access to overlapping file paths, preventing merge collisions. |
| REQ-AGT-005 | M | WHEN proposing parallel agent execution, THE orchestrator SHALL present token cost, time, and coordination risk trade-offs to the human operator. | User is presented with explicit sequential vs parallel execution options prior to dispatching multi-agent tasks. |
| REQ-AGT-006 | M | IF an agent encounters unresolvable ambiguity or rule conflict, THE agent SHALL halt and record an escalation issue in `artefacts/product/open-questions.md`. | Agents avoid ungrounded assumptions by formally pausing execution and raising blocking questions to the human operator. |
| REQ-AGT-007 | P | THE core-harness SHALL support optional `mcp_tools` declarations in agent frontmatter to document runtime tool and MCP server expectations. | Frontmatter tool declarations serve as deployment alignment guidance; runtime configuration is managed separately per platform. |

### 3. Workflow Engine

The Workflow Engine defines phase-based execution DAGs that govern the sequencing, dependencies, quality gates, and state recovery of all development activities.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-WF-001 | M | THE core-harness SHALL define multi-phase execution DAGs with strict dependencies and quality gates in declarative YAML files (`context/workflows/*.yaml`). | Workflows support phase chaining, dependencies, agent assignments, parallel/sequential execution, outputs, validation criteria, and review gate verdicts. |
| REQ-WF-002 | M | THE orchestration-engine SHALL enforce Test-Driven Development (TDD) as three non-combinable, sequential phases: RED (write failing tests), GREEN (implement to pass), and BLUE (refactor). | The orchestrator prohibits combining RED test authoring with GREEN implementation or BLUE refactoring within the same agent spawn. |
| REQ-WF-003 | M | WHILE a quality gate is unapproved, THE orchestration-engine SHALL prevent progression to downstream workflow phases. | Quality reviewers (tech-lead, code-reviewer, security-tester) must record formal approval in `artefacts/build/` before subsequent phases unlock. |
| REQ-WF-004 | M | THE core-harness SHALL provide workflow variants for distinct development activities: primary TDD build, design, prototype, deployment, bugfix, full regression, content authoring, continuous improvement, and retrospective. | Nine workflow YAML files exist in `context/workflows/`, each encoding appropriate rigour for its purpose. |
| REQ-WF-005 | M | THE prototype workflow SHALL trade rigour for speed by providing minimal agents, no quality gates, and no coverage requirements. | `prototype.yaml` enables fast iteration for POCs and experiments; code produced SHALL NOT be promoted to production without rewriting via the build workflow. |
| REQ-WF-006 | M | THE content workflow SHALL support a phased pipeline (research → draft → editorial review → technical review → finalise) using writing personas for human-facing content. | `content.yaml` enables blogs, papers, and guides with persona-driven voice and anti-slop enforcement. |
| REQ-WF-007 | M | THE continuous-improvement workflow SHALL support both reactive incident diagnosis and proactive retrospective analysis of framework performance. | Causal incident logs (`artefacts/build/agent-incidents.md`) trace failures to specific missing rules, ambiguous standards, or template defects; retrospective mode mines git telemetry for recurring patterns. |

### 4. State Durability and Recovery

The State Durability subsystem ensures that all execution state, task lists, and handoffs are persisted directly to disk, enabling flawless recovery after context compaction without relying on conversational history.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-DUR-001 | M | WHILE executing a workflow, THE core-harness SHALL persist all execution state, task lists, and handoffs directly to disk in `artefacts/`. | Session state is fully recoverable from disk artefacts after context compaction without relying on conversational history. |
| REQ-DUR-002 | M | THE orchestrator SHALL write the active workflow phase to `HANDOFF.md` before spawning subagents, not after they report back. | Phase state survives compaction events that occur during subagent execution. |
| REQ-DUR-003 | M | WHEN a context compaction occurs, THE orchestrator SHALL recover its position by reading `HANDOFF.md`, `artefacts/build/tasks.md`, and the workflow YAML's `state_recovery` section. | State recovery completes within one turn without re-reading entire codebases or duplicating completed work. |
| REQ-DUR-004 | M | THE core-harness SHALL treat context (documentation, tasks, handoffs) as first-class deliverables with equal priority to code. | Every agent spawn produces durable context updates alongside code changes. |

### 5. Enforcement, Automation, and Telemetry

The Enforcement subsystem ensures that rules are mechanically checkable at commit time, derived files remain synchronised with authoritative sources, and agent execution telemetry is recorded in the version history.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-ENF-001 | M | THE verification-system SHALL validate all requirements files (`**/requirements.md`) for strict EARS syntax adherence via pre-commit hooks. | `ears_notation.py` executes on staged requirements and blocks non-compliant commits. |
| REQ-ENF-002 | M | THE verification-system SHALL validate documentation and commit messages for British English spelling and formatting conventions. | `british_english.py` verifies standard spelling (`colour`, `behaviour`, `artefacts`, `licence`) across Markdown and code. |
| REQ-ENF-003 | M | THE verification-system SHALL validate commit messages against conventional commit format with agent session metadata. | `conventional_commits.py` checks `type(scope): description` format, imperative mood, and `Agent-Session:` trailer structure. |
| REQ-ENF-004 | M | THE verification-system SHALL validate agent definitions for structural integrity, including frontmatter fields and rule/standard file references. | `validate_agent_definitions.py` halts if an agent references a non-existent rule or standard. |
| REQ-ENF-005 | M | THE generator-system SHALL produce derived runtime configuration files (`AGENTS.md`, `CLAUDE.md`) from canonical assets without requiring manual edits in target files. | Derived files include auto-generation headers; the generator surfaces mismatches between agent definitions and workflow YAML at generation time. |
| REQ-ENF-006 | M | WHEN canonical assets in `context/` are updated, THE verification-system SHALL require that framework documentation is updated in the same commit. | `framework_docs_staleness.py` blocks commits that stage `context/` changes without also staging the framework reference document; `[docs-ok]` bypass is auditable. |
| REQ-ENF-007 | M | THE telemetry-system SHALL record agent session metadata (model, agents, token usage, duration, dispatch mode, interaction count) as structured trailers within git commit messages. | `prepare-commit-msg` hook reads Claude Code session JSONL, computes token deltas via a watermark file, and appends `tokens=` to the `Agent-Session:` trailer. |
| REQ-ENF-008 | P | THE verification-system SHALL require visual regression and screenshot evidence in `artefacts/test-results/` for all UI modifications. | UI testing workflows fail quality review if automated browser screenshots are missing from test results. |

### 6. Runtime Adapters and Portability

Runtime Adapters compile or project the canonical core harness into target platforms, preserving vendor neutrality without sacrificing platform-specific capabilities. The framework is designed to survive changes in agent runtime or orchestration platform.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-ADP-001 | M | THE adapter-system SHALL generate derived runtime configuration files from canonical assets without requiring manual edits in target files. | Derived files (`AGENTS.md`, `CLAUDE.md`, Copilot instructions, Gemini skills) include auto-generation headers and warning notices against direct edits. |
| REQ-ADP-002 | M | WHEN canonical assets in `context/` are updated, THE adapter-system SHALL regenerate all target runtime configuration files deterministically. | Running generator scripts updates all target configs to reflect current rules, agents, and workflows. |
| REQ-ADP-003 | M | IF a generated runtime configuration drifts from the canonical source, THE adapter-system SHALL fail verification during pre-commit and CI validation. | Drift detector reports desynchronised files and halts commit until regenerated. |
| REQ-ADP-004 | M | THE adapter-system SHALL map abstract canonical tool capabilities to runtime-specific tool implementations. | Canonical requests for file operations map to `Write`/`Edit` in Claude, `replace_file_content`/`write_to_file` in Gemini, and JSON function calling in Codex. |
| REQ-ADP-005 | M | THE claude-adapter SHALL project canonical workflows and agent registries into `CLAUDE.md` and `AGENTS.md` optimised for Claude Code CLI and subagent Task tool invocations. | Generates valid `CLAUDE.md`/`AGENTS.md` with phase transitions, agent spawn templates, and token telemetry hook bindings. |
| REQ-ADP-006 | M | THE claude-adapter SHALL reconcile the framework's orchestration model with Claude Code's native multi-agent orchestration capabilities, expressing canonical workflow phases, quality gates, and spawn discipline within Claude's built-in subagent and task primitives. | The adapter produces runtime configurations that leverage Claude's native delegation without losing framework governance (rule injection, file scope, gate enforcement). |
| REQ-ADP-007 | M | THE gemini-adapter SHALL project canonical agents, rules, and workflows into Google Antigravity-compatible skills (`.agents/skills/`), `GEMINI.md`, and MCP configurations. | Generates structured Antigravity skill folders with `SKILL.md` frontmatter and maps large-context standard ingestion. |
| REQ-ADP-008 | P | THE github-adapter SHALL project canonical instructions into `.github/copilot-instructions.md`, custom prompts (`.github/prompts/`), and workspace rule configurations. | Produces valid GitHub Copilot workspace instructions and prompt files aligned with canonical rules and EARS notation. |
| REQ-ADP-009 | P | THE codex-adapter SHALL project canonical agent definitions and workflows into OpenAI-compatible system prompts and JSON schema tool definitions. | Generates structured prompt bundles and tool declarations compatible with OpenAI Assistants API and execution harnesses. |
| REQ-ADP-010 | M | THE claude-adapter SHALL inject session token telemetry into git commit trailers via a `prepare-commit-msg` hook. | Every commit created by the orchestrator records Agent-Session, model, and token metrics. |
| REQ-ADP-011 | P | THE adapter-system SHALL adapt context delivery depth based on runtime context window capacities. | Runtimes with >1M context (Gemini) receive preloaded reference standards; runtimes with compact budgets (Claude/Codex) receive on-demand reference links. |

### 7. Framework Distribution

The Distribution subsystem enables downstream projects to adopt the framework and receive upstream improvements without manual copying or merge conflicts.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
| ---- | ----- | ------------------- | --------------------- |
| REQ-DST-001 | P | THE distribution-system SHALL package generator scripts as a versioned internal Python library installable via standard package management. | Downstream projects install the generator engine via `pip install` (or equivalent) and invoke adapter compilation from the library. |
| REQ-DST-002 | P | THE distribution-system SHALL manage the `context/` directory boilerplate via a stateful templating tool (e.g. `cruft`) enabling automated 3-way git merges for upstream updates. | Downstream repositories receive upstream improvements while preserving project-specific rule overrides. |
| REQ-DST-003 | F | THE distribution-system SHALL support automated adapter synthesis, generating adapter plugins for new runtimes from canonical asset schemas without manual plugin authorship. | New runtime targets can be onboarded by describing their configuration format rather than writing a bespoke generator. |

---

## Non-Functional Requirements

The three foundational quality axes for the framework are **autonomy** (maximising uninterrupted agent execution), **token efficiency** (minimising context overhead per spawn), and **intent preservation** (ensuring the human operator's design intent survives delegation to agents and persists across context compaction).

| ID | Category | Requirement | Target |
| ---- | ---------- | ------------- | -------- |
| NFR-001 | Autonomy | Proportion of agent spawns that complete without human intervention (approval-free commits with `dispatch=orchestrator` and zero interactions) | Increasing trend per retrospective cycle |
| NFR-002 | Autonomy | Time for an orchestrator to resume workflow execution from disk artefacts after context compaction | < 1 turn / 10 seconds |
| NFR-003 | Token Efficiency | Overhead of framework rules and agent frontmatter injected into a single agent spawn prompt | < 2,500 tokens |
| NFR-004 | Token Efficiency | Additional token cost of parallel (hive) execution vs sequential for the same work | < 20% overhead |
| NFR-005 | Intent Preservation | Canonical core files (`context/agents/`, `rules/`, `standards/`, `workflows/`) containing zero vendor-specific tool names or proprietary prompt syntax | 100% vendor-agnostic |
| NFR-006 | Intent Preservation | Repeated runs of adapter generators on unchanged canonical files produce identical byte-for-byte outputs | 100% deterministic |
| NFR-007 | Intent Preservation | Prevention of credentials or API secrets committing to git or leaking into agent prompt payloads | Zero committed secrets; strict rule enforcement |
| NFR-008 | Token Efficiency | Execution time to regenerate all runtime adapter projections from canonical sources | < 2.0 seconds |

---

## Out of Scope

- Implementing end-user domain application features (the harness is strictly an agent coordination and governance engine).
- Autonomous unconstrained swarm exploration without orchestrator oversight (the framework implements centralised Hive and Chain patterns; swarm is a future exploration documented in vision materials).
- Graphical drag-and-drop workflow visualiser editor (workflows are authored and reviewed directly as YAML code).
- Hosting proprietary model endpoints or custom LLM weights (the harness coordinates external runtimes via their native interfaces).
- Real-time enforcement of agent rule compliance during execution (compliance is enforced post-hoc via validators and review gates; runtime interception is not currently possible).

---

## Revision History

| Date | Author | Changes |
|------|--------|---------| 
| 09/09/2026 | Product Owner (@product-owner) | Initial product requirements specification for Core Harness and Framework Adapters |
| 09/09/2026 | Retrospective rebuild | Comprehensive rewrite: restructured into seven categories (Context Layer, Agent Coordination, Workflow Engine, State Durability, Enforcement, Runtime Adapters, Distribution); added NFRs along autonomy/token-efficiency/intent-preservation axes; documented Claude native orchestration reconciliation; added content workflow, persona, and state durability requirements |
