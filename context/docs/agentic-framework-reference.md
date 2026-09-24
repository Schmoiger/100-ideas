# Hive Mind: Framework Reference

**Document Status**: Draft  
**Version**: 0.7.0  
**Last Updated**: 24 September 2026  
**Word Count**: ~8,500 words  
**Reading Time**: ~35 minutes

**Companion**: *Hive Mind: Designing an Orchestration Framework for Multi-Agent Software Delivery* (`context/docs/agentic-framework.md`)

---

## Table of Contents

1. [How To Use This Reference](#how-to-use-this-reference)
2. [Framework Topology](#framework-topology)
3. [Source of Truth Hierarchy](#source-of-truth-hierarchy)
4. [Root-Level Framework Files](#root-level-framework-files)
5. [Standards](#standards)
6. [Rules](#rules)
7. [Skills](#skills)
8. [Agents](#agents)
   - [Tool and MCP surfaces (runtime vs frontmatter)](#tool-and-mcp-surfaces-runtime-vs-frontmatter)
   - [Writing Personas](#writing-personas)
9. [Workflows](#workflows)
   - [Design (`design.yaml`)](#design-designyaml)
   - [Build (`build.yaml`)](#build-buildyaml)
   - [Prototype (`prototype.yaml`)](#prototype-prototypeyaml)
   - [Deploy (`deploy.yaml`)](#deploy-deployyaml)
   - [Bugfix (`bugfix.yaml`)](#bugfix-bugfixyaml)
   - [Full-test (`full-test.yaml`)](#full-test-full-testyaml)
   - [Content (`content.yaml`)](#content-contentyaml)
   - [Continuous improvement (`continuous-improvement.yaml`)](#continuous-improvement-continuous-improvementyaml)
   - [Retrospective (`retrospective.yaml`)](#retrospective-retrospectiveyaml)
10. [Orchestration Patterns](#orchestration-patterns)
11. [Templates](#templates)
12. [Scripts and Automation](#scripts-and-automation)
13. [Portability and Framework Adapters](#portability-and-framework-adapters)
14. [How the Parts Connect](#how-the-parts-connect)
15. [Reading Paths](#reading-paths)
16. [Revision History](#revision-history)

---

## How To Use This Reference

The companion technical paper explains why the framework exists and the design principles behind it. This reference explains what the framework contains and how each part works. It is structured so that either document can be read first, or independently.

Use this document when you need to answer questions such as:

- What is this directory for?
- How does rule injection work at spawn time?
- What does the default workflow look like phase by phase?
- How would I port an agent definition to a different orchestration system?
- How do I measure whether the framework is working?

Each section covers one structural area of the framework: what it contains, how it operates, and where to make changes.

The companion paper develops the *why* and the trade-offs behind those choices. As you read the catalogue below, the same posture shows up repeatedly: explicitness (written phases, gates, paths, recovery—not tacit convention); durability (artefacts and handoffs—not chat memory); reuse (templates, shared agents, generated registries—not one-off prose); portability (Markdown and YAML at the core—not a single vendor runtime); and verification (validators, tests, reviews, gates, telemetry—not unevidenced claims). For the full argument, see `context/docs/agentic-framework.md`.

This reference summarises the tree on disk. If anything here disagrees with an authoritative file (a workflow YAML, an agent definition, a rule, or a generator script), trust the file and treat the mismatch as documentation drift to fix.

---

## Framework Topology

The framework is organised as a layered directory structure inside `context/`. The layers are ordered below by how frequently each is accessed during execution. Layers that touch every agent spawn sit at the top; layers consulted once per task or occasionally sit at the bottom.

| Layer | Location | Responsibility | Access Frequency |
|-------|----------|---------------|-----------------|
| Rules | `context/rules/` | State *what must happen*: short, binary, injectable constraints | Every agent spawn |
| Agents | `context/agents/` | Define *who*: specialised roles with frontmatter linking rules and standards | Every agent spawn |
| Templates | `context/templates/` | Define *what shape*: standardised formats for reviews, tasks, handoffs, design docs | Every output |
| Standards | `context/standards/` | Explain *why* and *how*: engineering rationale for coding, testing, security, documentation | On demand |
| Skills | `context/skills/` | Provide *procedural guidance*: step-by-step instructions for specific workflows or unusual tech boundaries | On demand |
| Scripts | `context/scripts/` | Enforce *everything above*: validators, generators, git hooks | Every commit |
| Workflows | `context/workflows/` | Define *when*: phase order, dependencies, gates, outputs, recovery | Once per task |
| Docs | `context/docs/` | Provide *further reading*: design rationale, strategic context, orchestration patterns, workflow guides | Human reference |
| Personas | `context/persona/` | Provide *voice*: writing style for human-facing content only | Content workflows only |

The layering determines where changes should be made. To change what agents do, edit a workflow. To change how they do it, edit a standard or rule. To change who does it, edit an agent definition. To change what the output looks like, edit a template. To add procedural steps for complex tools, add a skill. Nothing bleeds across boundaries unless explicitly designed to.

The design pattern is consistent throughout:

- define the role or rule
- explain how to use it
- standardise the output
- validate the result

---

## Source of Truth Hierarchy

Not all framework files carry equal authority. Some define behaviour; others project or summarise it.

| Tier | Examples | Role |
|------|----------|------|
| Authoritative source | `context/agents/*.md`, `context/workflows/*.yaml`, `context/rules/*.mdc`, `context/standards/*.md`, `context/skills/*.md`, `context/templates/*.md`, `context/persona/*.md`, `context/models.yaml` | These define how the framework behaves. Edit these to change it. |
| Derived projection | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/skills/`, `.github/prompts/`, `.openai/` | These surface framework information in runtime-friendly form. Never hand-edit; regenerate from source. |
| Operator guidance | `context/docs/*.md`, `README.md` | These explain how to use, extend, or evaluate the framework. |
| Enforcement | `context/scripts/validators/*`, `context/scripts/prepare-commit-msg.*` | These keep the repository aligned with the design. |

The principle: change the authoritative source, let derived projections follow. Contributors should be able to look at any file and know whether it is the right place to make a change or whether the real change needs to happen upstream.

### Antipattern: Personal Agent Settings and Memories

The source of truth hierarchy above governs files inside the repository. But agent runtimes introduce a precedence layer the repository cannot control: user-level configuration and accumulated memories that load *before* project-level files, silently overriding framework authority.

**How it works.** Claude Code reads `~/.claude/CLAUDE.md` and accumulated session memories before it reads the project's `CLAUDE.md` or `AGENTS.md`. Cursor reads user-scoped rules (in `~/.cursor/rules/`) and user settings before workspace-level rules. Other runtimes follow similar patterns. The result is a shadow configuration layer that sits above the framework's authoritative sources in the effective precedence order:

| Precedence | Source | Controlled by |
|------------|--------|---------------|
| 1 (highest) | User memories (auto-accumulated) | Runtime |
| 2 | User-level config (`~/.claude/CLAUDE.md`, `~/.cursor/rules/`) | Individual contributor |
| 3 | Project-level derived files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`) | Framework (generated) |
| 4 | Authoritative sources (`context/`) | Framework (versioned) |

Anything at precedence 1 or 2 that contradicts precedence 3 or 4 wins — and the framework has no mechanism to detect or prevent it.

**Why this breaks the framework.** The framework's design assumes that `context/` is the authoritative operating model and that derived projections (`AGENTS.md`, `CLAUDE.md`) faithfully represent it at runtime. Personal settings and memories violate that assumption. A contributor whose agent runtime has memorised "always use `pip install`" will have that memory override the framework's `python-environment.md` rule requiring `uv add`. A user-level `CLAUDE.md` that says "keep responses concise" can override the framework's handoff requirements. These overrides are invisible to other contributors, to review agents, and to the framework's validators — the pre-commit hooks check committed files, not what was in the agent's context window.

**Symptoms.** Inconsistent agent behaviour across contributors working on the same repository. Rules that are correctly defined and injected but not followed. Agents that produce output in a style or format that does not match any framework standard. Validators passing at commit time on rules that were violated during execution (because the violation was in approach, not in the committed artefact). Debugging these failures is difficult because the cause lives outside the repository.

**Mitigations.**

- **Disable agent memories** for repositories governed by this framework. In Claude Code: do not use `/memory` and clear any existing memories that overlap with framework concerns. The framework's durable context (handoffs, task files, standards) replaces what memories are meant to provide, with the advantage of being versioned, shared, and inspectable.
- **Avoid user-level configuration that overlaps with framework concerns.** If `context/rules/python-environment.md` governs Python tooling, do not also set Python tooling preferences in `~/.claude/CLAUDE.md` or `~/.cursor/rules/`. User-level configuration should be limited to genuinely personal, project-independent preferences (editor keybindings, display settings) that do not intersect with anything the framework manages.
- **Audit when behaviour diverges.** If an agent ignores a correctly injected rule, check user-level configuration and memories before assuming the rule is broken or the model is non-compliant. The most common cause is a higher-precedence instruction contradicting the rule.
- **Document the requirement.** Onboarding instructions for contributors should explicitly state that personal agent configuration must not overlap with framework-managed concerns, and that agent memories should be disabled or cleared.

The framework cannot enforce this boundary — it sits below the precedence layer it needs to control. This is a governance and onboarding discipline, not an automated check.

---

## Root-Level Framework Files

### `AGENTS.md`

Auto-generated registry of workflows and agents. It acts as the root-level entry point for agent runtimes and humans. The generator script (`context/scripts/generators/generate_agents_md.py`) reads every workflow YAML and every agent definition, then produces `AGENTS.md` as a single derived file containing the phase sequence, agent dispatch rules, spawn patterns, and state recovery procedures. If an agent definition references a rule that does not exist, or a workflow references an agent with no definition, the mismatch surfaces at generation time rather than at runtime.

Editing `AGENTS.md` by hand is always wrong. Edit the sources and regenerate.

### `CLAUDE.md`

Root agent guidance surfaced to the runtime. In this repository it points to `AGENTS.md`, making the generated registry the durable entry point instead of duplicating framework detail in multiple places.

### `README.md`

Repository-level onboarding and setup document. It complements `context/README.md`: the root README explains the repository; `context/README.md` explains the framework. This split keeps newcomer setup instructions close to the repository root whilst leaving framework theory in the portable context package.

---

## Standards

Standards are detailed reference material stored in `context/standards/`. They are intentionally longer and more explanatory than rules. An agent consults a standard when it needs deeper guidance than a rule provides: the reasoning behind a technology choice, the criteria for a good handoff, the philosophy behind the testing approach.

### How Standards Are Used

Each agent definition lists the standards it depends on in its frontmatter. When the orchestrator spawns an agent, it includes the standard references in the spawn prompt. The agent reads the relevant standards before starting work. Standards are loaded on demand rather than injected wholesale, because a single standard can run to 2,000-5,000 tokens and loading all of them would overwhelm the context window.

### The Rules, Standards, and Skills Split

The separation is enforced by **verification mechanism** and **runtime projection** — not by length or topic.

**Rules** are deterministic invariants. Binary: followed or not. Verified at **zero token cost** by code (pre-commit hooks, linters, AST parsers). *If it requires an LLM to verify, it is not a rule.*

- `alwaysApply: true`: injected into every spawn. Must be aggressively succinct. Currently ~1,300 tokens total — less than 1% of a 128k–200k context window, under 0.1% on 1M+ models. Only the most critical global invariants belong here.
- `alwaysApply: false`: injected JIT by glob match. Still succinct; domain-specific.
- **Content**: pure constraints. No tutorials, no explanations.

**Skills** are procedural runbooks. "How to accomplish X." Verified by **LLM-as-a-judge**: an agent executes the skill; a reviewer agent checks the outcome. Injected JIT when an agent matches globs or needs to navigate a specific complex boundary. **Content**: step-by-step instructions, tool commands, code snippets.

**Standards** are the reference canon and benchmark rubrics. "What good looks like and why." Used as the **evaluation rubric** against which LLM judges assess skill execution. Loaded JIT by any agent that needs them — design and dev agents when they need deep context on a decision, reviewer agents (`@tech-lead`, `@code-reviewer`) when evaluating output. **Content**: architectural patterns, design philosophy, trade-offs, and detailed rationale.

An agent executing a simple Python task needs the 15-token rule that says "run tests with `uv run pytest`." A reviewer evaluating test sufficiency needs the full testing standard. A coder navigating a `uv` PEP 723 inline script needs the `python-scripting` skill. The framework serves all three without forcing any to carry the others' weight.

### Standards Catalogue

`context/standards/README.md` is the lightweight index for humans navigating the folder. The tables below describe what each standard is for when you are editing behaviour or answering an agent's "where do I read more?" question. They intentionally omit the README itself, which is navigation—not a behavioural standard agents load from frontmatter.

#### Foundational

| Standard | Purpose |
|----------|---------|
| `agent-standards.md` | Defines how agents should behave, recover state, use tools, and coordinate. The behavioural contract around agents, not just their roles. |
| `context-framework.md` | The framework's theory of context: reference vs actionable context, priority, handoff format, terse formats, and context quality. A foundational design text. |
| `workflow-standards.md` | Shared workflow conventions, invocation practices, and orchestration rules. The operating model that spans multiple workflow YAML files. |

#### Technical

| Standard | Purpose |
|----------|---------|
| `coding-standards.md` | Language and implementation guidance for code quality. Patterns, error handling, naming. |
| `tech-standards.md` | Primary technology stack reference. Tools, libraries, deployment targets, environment setup. |
| `testing-standards.md` | Testing philosophy and practice, including TDD expectations, coverage requirements, and phase-based thresholds. |
| `security-standards.md` | Security guidance for design, implementation, and review. |
| `tech-mobile-standards.md` | Mobile-specific technical guidance, separated to avoid bloating the main technology standard. |

#### Quality and Documentation

| Standard | Purpose |
|----------|---------|
| `doc-standards.md` | Documentation structure, quality, archival, diagram, and maintenance guidance. |
| `build-standards.md` | How build-phase work should be structured and assessed. |
| `visual-standards.md` | Guidance for design consistency, UI quality, and visual review concerns. |
| `12-factor-principles.md` | Maps framework work onto twelve-factor application principles. |
| `LESS-Engineering-Principles.md` | Captures the LESS principles used by review agents and design discussions. |

---

## Rules

Rules are short, enforceable constraints stored in `context/rules/` as `.mdc` files. Each rule addresses a real failure mode: something that breaks, drifts, or degrades if the rule is not followed. They are designed for injection into agent prompts and for validator-backed enforcement.

### How Rules Work

Each rule file has YAML frontmatter with three fields:

```yaml
---
description: Python environment setup and command execution
globs: ["**/*.py", "**/pyproject.toml", "**/requirements.txt"]
alwaysApply: false
---
```

`description`: A short summary of what the rule covers.

`globs`: File patterns that determine when this rule applies. The orchestrator matches the task's files against these globs and injects only the rules whose patterns match.

`alwaysApply`: If `true`, the rule is injected into every agent spawn regardless of file scope.

The body of the rule is concise instruction text, typically structured as a table of correct vs incorrect usage, followed by a brief rationale. The entire rule stays under 200 tokens.

### Example: Python Environment Rule

```markdown
| Action          | Correct               | Wrong                         |
|-----------------|-----------------------|-------------------------------|
| Run tests       | uv run pytest         | pytest                        |
| Install package | uv add package        | pip install package           |
| Run script      | uv run python script  | python script.py              |
```

The rationale section explains that bare `python` or `pytest` commands fail because no virtual environment is activated and dependencies are not available. `uv run` automatically uses the project's virtual environment, ensures dependencies are installed, and respects `.python-version`.

### Rules Catalogue

Only a subset of rules currently have matching Python validators under `context/scripts/validators/` (see [Scripts and Automation](#scripts-and-automation)). A rule without a validator is still binding for agents via prompt injection; a rule *with* a validator is also mechanically checkable at commit time.

#### Environment and Tooling

| Rule | Purpose |
|------|---------|
| `python-environment.md` | Enforces `uv` for all Python commands |
| `typescript-environment.md` | Enforces `yarn` for package management, `yarn dlx` for one-off tools |
| `bash-environment.md` | Prevents unsafe or inconsistent shell usage; pushes work toward approved tools |
| `mermaid-environment.md` | Constrains Mermaid diagram syntax, layout direction, and node label conventions |
| `supabase.md` | Defines constraints around Supabase-related usage |

#### Quality and Process

| Rule | Purpose |
|------|---------|
| `tdd-workflow.md` | Enforces RED then GREEN then BLUE discipline |
| `quality-gates.md` | Encodes non-negotiable review and release criteria |
| `output-locations.md` | Keeps artefacts in the correct directories |
| `handoff-hygiene.md` | Enforces durable, useful handoffs |
| `escalation.md` | Defines when agents may assume, flag, or escalate |
| `git-commits.md` | Standardises commit structure and agent session metadata |
| `metrics-logging.md` | Constrains how workflow and performance signals are recorded |
| `no-ai-slop.md` | Eliminates AI-generated writing tics from persona-driven documentation |

#### Architecture, Design, and Safety

| Rule | Purpose |
|------|---------|
| `architecture-fidelity.md` | Prevents implementation drift from approved architecture |
| `visual-fidelity.md` | Prevents drift from approved UI and visual design |
| `ui-component-reuse.md` | Encourages reuse and discourages needless UI duplication |
| `type-safety.md` | Protects typed contracts and discourages unsafe shortcuts |
| `browser-automation.md` | Constrains browser-based test and automation behaviour |
| `secrets-management.md` | Prevents unsafe handling of secrets and credentials |

#### Language and Requirements Hygiene

| Rule | Purpose |
|------|---------|
| `tech-writing.md` | Enforces British English spelling and EARS notation for requirements — consolidated from the former `british-english.md` and `EARS-notation-requirements.md` rules |

### Writing New Rules

A candidate for a new rule should pass three tests:

1. Is it binary? Can you definitively say "followed" or "not followed"?
2. Does it break things? Not just a style preference; actual failures result from ignoring it.
3. Is it actionable? Can you give clear DO/DON'T commands?

If all three are true, create a rule in `rules/*.md` and keep it under 200 tokens. If the topic requires nuance, explanation, or judgement, it belongs in a standard, not a rule. If it requires step-by-step procedural guidance to execute, it belongs in a skill.

---

## Skills

Skills are procedural runbooks stored in `context/skills/` as `.md` files. Each skill answers "how do I accomplish X?" — step-by-step instructions, tool commands, and code snippets for a specific workflow or complex technology boundary.

### How Skills Work

The physical split from rules and standards is enforced by verification mechanism:

| Layer | Verified by | Injected |
|-------|-------------|----------|
| Rules | Code (pre-commit hooks, linters) — zero token cost | Glob-matched at every spawn |
| Skills | LLM-as-a-judge — an agent runs it, a reviewer checks the outcome | JIT on glob match or explicit agent request |
| Standards | LLM-as-a-judge — used as the evaluation rubric | JIT by any agent that needs them (dev, design, reviewer) |

Canonical skills in `context/skills/` are compiled into runtime projections (e.g. `.agents/skills/` for Antigravity, `.openai/prompts/` for OpenAI) via `context/scripts/generators/generate_adapters.py`. All generated projections are gitignored — they stay on disk for IDE discovery but are never committed. Agents declare skill dependencies via the `skills:` list in their frontmatter.

### Skills Catalogue

| Skill | Purpose |
|-------|---------|
| `agent-sandbox.md` | Procedural constraints for running terminal commands inside agent sandboxes without triggering security blocks |
| `agent-workflows.md` | Agent git commits, pull requests, and metrics logging patterns |
| `api-designer.md` | RESTful and GraphQL API design with OpenAPI specifications |
| `architecture-fidelity.md` | Adherence to architecture docs and API contracts during implementation |
| `bootstrap-workflow.md` | Agent context setup, git-subrepo initialisation, and pre-commit hook activation |
| `code-reviewer.md` | PR-style code review focusing on bugs, edge cases, and maintainability |
| `database-designer.md` | Database schema design, relationships, and migrations |
| `documentation.md` | User-facing documentation, API references, and guide generation |
| `functional-tester.md` | Detroit-school TDD: intent-first, tests before implementation |
| `gemini-sdk.md` | `google-genai` Python SDK patterns, structured outputs with Pydantic, Gemini context caching, Imagen 3, and token burn guard rails |
| `git-subrepo-operations.md` | Procedural guidance for inspecting, pulling, cloning, and gated pushing with git-subrepo |
| `intent-fidelity.md` | Ensures business intent is faithfully captured in requirements, TDD, and tests |
| `mermaid-authoring.md` | Mermaid diagram syntax, layout constraints, and semantic guidance |
| `multi-agent-workflows.md` | Orchestrator triage and handoff archival |
| `orchestrator.md` | Workflow execution coordination, agent delegation, and quality gate management |
| `principles-reviewer.md` | Review against LESS Engineering Principles |
| `product-expert.md` | Eliciting clear requirements from vague ideas |
| `product-owner.md` | Transforming vague requests into structured requirements and user stories |
| `python-coder.md` | Production Python code with testing in mind |
| `python-scripting.md` | `uv`, PEP 723 inline metadata, and the `--with` pattern |
| `security-tester.md` | Threat modelling, OWASP assessment, and vulnerability scanning |
| `solution-architect.md` | System architecture, component boundaries, and data flow design |
| `supabase-operations.md` | Supabase migrations, queries, and maintenance via MCP |
| `tdd-workflow.md` | Strict RED–GREEN–REFACTOR TDD cycle |
| `tech-lead.md` | Architecture compliance, consistency, and engineering standards review |
| `technical-authoring.md` | Technical whitepapers, architecture roadmaps, and book chapters using the AS persona |
| `tokenomics-analyst.md` | Agent effectiveness, token economics, and context efficiency auditing |
| `typescript-coder.md` | Frontend/backend TypeScript integrating with Python APIs |
| `typescript-development.md` | TypeScript/JavaScript projects using Yarn Berry workspaces |
| `typst-pipeline.md` | Authoring, building, and publishing PDFs via the project's Typst/Pandoc engine — covers Markdown formatting rules, `build.yaml` registration, brand/seed selection, and `make` commands |
| `ui-designer.md` | UI components, layouts, design systems, and visual assets |
| `ui-development.md` | UI component and layout authoring |
| `ui-tester.md` | End-to-end user workflow testing, screenshots, and accessibility checks |
| `ui-testing.md` | UI testing and browser automation |
| `workflow-analyst.md` | Workflow efficiency analysis across handoffs, git history, and token usage |

---

## Agents

Agent definitions are markdown files with YAML frontmatter and an instruction body, stored in `context/agents/`. They are the role catalogue of the framework: each file defines a single specialist with a bounded responsibility, a curated set of rules and standards, and clear instructions for how to execute its work.

The repository ships one orchestrator plus nineteen delegatable specialists (twenty role files in total, excluding `README.md`). The roster below groups them by concern; `context/agents/README.md` lists the same roles with recommended model tiers for operators who tune cost versus capability. Which agent runs in which phase is never implied by the roster alone; it is declared in `context/workflows/*.yaml` and reflected in regenerated `AGENTS.md`.

### Agent Definition Format

Every agent follows this structure:

```yaml
---
name: python-coder
description: Writes production Python code with testing in mind.
model: medium
standards:
  - tech-standards.md
  - coding-standards.md
  - security-standards.md
  - doc-standards.md
rules:
  - python-environment.md
  - tdd-workflow.md
  - type-safety.md
  - git-commits.md
  # ... additional rules
# Optional — see "Tool and MCP surfaces" below
# mcp_tools:
#   - context7
---

You are an expert Python engineer. Your job is to write clean,
testable, production-grade Python code.

---

## Required Standards (Read First!)
1. context/standards/tech-standards.md
2. context/standards/coding-standards.md
...

---

## Workflow
1. Read standards
2. Read task context
3. Implement
4. Run tests
5. Write handoff
```

`name`: Identifier used in workflow YAML and spawn prompts.

`description`: Brief role summary. Helps the orchestrator select the right agent.

`model`: Recommended model tier (e.g. `large`, `medium`, `small`). Tiers are mapped to vendor-specific models via `context/models.yaml`. The orchestrator uses this as guidance, not a hard constraint.

`standards`: List of standard files the agent should read before starting work. These are loaded on demand, not injected automatically.

`rules`: List of rule files that apply to this agent's work. The orchestrator injects these into the spawn prompt.

`mcp_tools` (optional, common on specialists here): MCP server identifiers the author expects the runtime to attach for that role (for example library docs or database inspection). Other products use `allowed_tools` or an equivalent allow-list instead. Neither field executes by itself—it documents intent for whoever configures the runtime.

The body below the frontmatter is the agent's system prompt: role definition, workflow steps, output expectations, and any role-specific constraints.

### Tool and MCP surfaces (runtime vs frontmatter)

Agent YAML declares what a role *should* be able to reach; the orchestrator runtime (Cursor, Claude Code, a headless worker, and so on) still decides which tools and MCP servers actually exist, which paths are writable, and which invocations require human approval. Those layers live outside `context/agents/`—often in workspace or user settings that are not committed. In Cursor, permissions and MCP wiring frequently sit in `.cursor/settings.local.json` (typically git-ignored), so two machines with the same checkout can behave differently.

When frontmatter and local configuration diverge, the failure mode is friction: endless approval prompts, subagents that cannot attach a listed MCP server, or specialists that appear “fully defined” in markdown but never receive the tools their prompt assumes. Treat that as a deployment alignment problem: update the local settings (or your organisation’s standard Cursor profile) when you add `mcp_tools:` entries, add a new agent, or enable a new server—and keep frontmatter honest about what is truly required versus optional.

Rule injection and file scope (see `context/agents/orchestrator.md`) remain mandatory regardless of tool lists; missing rules cause as much pain as missing MCP entries.

### How the Orchestrator Resolves an Agent

When spawning an agent, the orchestrator:

1. Reads the agent definition from `context/agents/{name}.md`
2. Extracts the `rules` list from frontmatter
3. Glob-matches the task's files against each rule's scope to confirm applicability
4. Injects the applicable rules into the spawn prompt alongside the agent's system prompt
5. Constrains the agent to a defined file scope so it cannot make changes outside its boundaries
6. Constructs the full prompt using the task prompt template (`context/templates/task-prompt-template.md`)

Agents do not commit to git. Only the orchestrator commits, one at a time, preventing ref-lock collisions when parallel agents finish simultaneously.

### The Agent Roster

The framework defines 19 specialised agents, organised by kind of judgement.

#### Core Coordinator

| Agent | Purpose |
|-------|---------|
| `orchestrator` | Coordinates the system, resolves rules, assigns file scope, validates phase outputs, manages quality gates |

#### Product and Discovery

| Agent | Purpose |
|-------|---------|
| `product-expert` | Elicits problem understanding and discovery insight from the user |
| `product-owner` | Turns clarified needs into structured requirements and stories |

#### Design

| Agent | Purpose |
|-------|---------|
| `solution-architect` | Designs architecture, boundaries, and data flow |
| `database-designer` | Designs schemas, relationships, and migrations |
| `api-designer` | Designs APIs and contract artefacts |
| `ui-designer` | Designs UI structure, component behaviour, user flow, and visual assets |

#### Implementation and Test

| Agent | Purpose |
|-------|---------|
| `python-coder` | Implements Python production work |
| `typescript-coder` | Implements TypeScript and frontend work |
| `functional-tester` | Writes and runs tests in the TDD flow |
| `ui-tester` | Executes browser-based UI verification |

#### Review and Governance

| Agent | Purpose |
|-------|---------|
| `tech-lead` | Acts as the principal architecture and quality gate reviewer |
| `code-reviewer` | Performs implementation-focused review for bugs, risks, and maintainability |
| `principles-reviewer` | Reviews designs and code against higher-level engineering principles |
| `security-tester` | Reviews for vulnerabilities and security risks |

#### Operations and Maintenance

| Agent | Purpose |
|-------|---------|
| `devops` | Handles deployment and infrastructure-related work |
| `documentation` | Cleans up, archives, and maintains human-facing documentation |
| `workflow-analyst` | Reviews process effectiveness and supports retrospectives |
| `tokenomics-analyst` | Audits agent effectiveness, token economics, context efficiency, and model tiering |

### Creating a New Agent

1. Copy `context/templates/agent-template.md` to `context/agents/{name}.md` (some deployments also keep a `context/agents/TEMPLATE.md` copy; the templates directory is the canonical scaffold in this tree)
2. Set `name`, `description`, `model` in frontmatter
3. List applicable `rules` and `standards` in frontmatter
4. Write a concise body with role definition, workflow steps, and output expectations
5. Add the agent to the appropriate workflow YAML phase
6. Regenerate `AGENTS.md`

### Writing Personas

Personas are stored in `context/persona/` and provide voice guidance for human-facing content. They are used by the `documentation` agent when writing blogs, technical papers, user guides, and marketing materials. They are explicitly *not* used for technical handoffs, API documentation, architecture documents, or internal artefacts.

For the phased pipeline (research through publish) used for blogs, papers, and similar content, see [Content (`content.yaml`)](#content-contentyaml) under Workflows.

#### When to Use a Persona

Use a persona for: blog posts, articles, thought leadership, technical papers, user-facing guides for non-technical audiences, marketing materials, conference talks.

Do not use a persona for: technical handoffs (README, HANDOFF.md, build notes), API documentation, code references, architecture documents, design specifications, internal artefacts (requirements, tasks, review reports), code comments, error messages.

#### Available Personas

##### Author

File: `context/persona/author.md`
Character: AS. Technologist, engineering leader, systems thinker with over 25 years of platform and enterprise delivery experience.
Use for: Books, foundational thought leadership, whitepapers, high-impact technical essays.

Key traits: punch over preamble, zero dense technical jargon, maximum information density per sentence, echoing core ideas across different operational contexts without repetition, the "so what?" economic lens, wry realism, empirical humility.

##### Technical Writer

File: `context/persona/technical-writer.md`
Character: Amara Osei. Eight years at Stripe documenting payment APIs, four years at Hashicorp writing infrastructure guides.
Use for: Technical guides, framework documentation, practitioner reference material.

Key traits: leads with the problem, not a hook. Explains the mechanism step by step. Working examples with inputs and outputs. Names trade-offs and costs directly. Structured for reference use with scannable headings and front-loaded information. No filler.

##### Opinionated Blogger

File: `context/persona/opinionated-blogger.md`
Character: Dr. Sarah Chen. PhD from MIT, 10 years as principal engineer at Google.
Use for: Blog posts, opinion pieces, thought leadership.

Key traits: provocative opening hooks. Conversational with contractions and parenthetical asides. Personal anecdotes as entry points. Self-deprecating honesty. Question-driven framing. Memorable one-liners. Short paragraphs, 2-4 minute read times.

##### Editor

File: `context/persona/editor.md`
Use for: Refining and polishing existing content. Checking voice consistency, removing AI slop, verifying British English.

##### Expert Reviewer

File: `context/persona/expert-reviewer.md`
Use for: Reviewing technical accuracy and completeness of human-facing content.

#### Selecting a Persona

The selection depends on audience and content type:

- Writing books, foundational essays, or core thought leadership? Author.
- Writing a practitioner guide with code examples? Technical writer.
- Writing a blog post or opinion piece? Opinionated blogger.
- Writing for a non-technical audience about high-level concepts? Opinionated blogger.
- Writing implementation details for developers? Technical writer.
- Polishing an existing draft? Editor.
- Checking technical claims? Expert reviewer.

All personas use British English throughout (colour, optimise, behaviour, whilst, programme, organisation).

---

## Workflows

Workflows are YAML files in `context/workflows/` that encode phase dependencies, agent assignments, quality gates, validation criteria, state recovery procedures, and execution rules. Storing orchestration logic in versionable YAML rather than ad hoc conversation makes it inspectable, diffable, reviewable, and recoverable after context compaction.

| Workflow | File | Purpose |
|----------|------|---------|
| design | `design.yaml` | Discovery through design review; run before build |
| build | `build.yaml` | Primary TDD loop: plan, red, green, blue, review, regress, docs cleanup |
| prototype | `prototype.yaml` | Fast iteration, no quality gates; rewrite before production |
| deploy | `deploy.yaml` | GCP cloud deployment after local verification |
| bugfix | `bugfix.yaml` | Empirical reproduction, diagnosis, fix, verification |
| full-test | `full-test.yaml` | Complete regression across all modules |
| content | `content.yaml` | Human-facing writing with personas |
| continuous-improvement | `continuous-improvement.yaml` | Incident response and retrospective analysis (framework evolution) |
| retrospective | `retrospective.yaml` | Standalone process review and pattern identification |

### Design (`design.yaml`)

Purpose: Discovery through design review; run before `build.yaml`.

Pattern: Six phases, one approval gate at the end (`design-review`).

| Phase | Agents (pattern) | Role |
|-------|------------------|------|
| `discovery` | `product-expert` then `product-owner` (sequential) | Discovery notes → formal requirements and user stories in `artefacts/product/` |
| `design-architecture` | `solution-architect` | Architecture, logical API contracts, data model, component design docs |
| `design-contracts` | `database-designer` and `api-designer` (parallel) | Physical schema and migrations; OpenAPI with HTTP semantics |
| `design-ui` | `ui-designer` | Component specs, tokens, wireframes, user flows, and visual assets |
| `design-review` | `tech-lead` → `code-reviewer` → `principles-reviewer` → `ui-designer` → `security-tester` (sequential gate) | Design approval; `tech-lead` must approve before the next reviewer runs |

Design gate (`design-review`): zero architecture blockers; zero design security issues; complex components need a design doc per `design_doc_standard` in the workflow file.

### Build (`build.yaml`)

Purpose: Primary TDD implementation pipeline after design approval.

Pattern: Subtask-driven TDD with automated coverage gate, per-sprint review, local deployment, scoped regression, documentation cleanup, and two final approval gates. Runs against `artefacts/build/subtask-plan.yaml` (subtasks, file scopes, acceptance criteria). Canonical phase order and validation live in the YAML; this is a digest.

Sixteen phases (plus a sprint loop that repeats for each sprint in `subtask-plan.yaml`). High-level shape:

```text
task-planning → tasks-review (gate) → schema-migration →
  [ per sprint: tdd-red → test-plan-review → tdd-green → coverage-gate (gate) →
    tdd-blue → sprint-review ] →
local-deployment → unit-regression → integration-regression → e2e-regression →
docs-cleanup → quality-review (gate) → final-holistic-review (gate)
```

| Phase | Role |
|-------|------|
| `task-planning` | `tech-lead` decomposes work into subtasks with verifiable acceptance criteria and file scopes (`artefacts/build/subtask-plan.yaml`). |
| `tasks-review` | `tech-lead`, `solution-architect`, `principles-reviewer` in parallel; gate on subtask plan before implementation. |
| `schema-migration` | `devops` writes and applies migrations when the sprint changes schema (skippable if no schema work). |
| `tdd-red` | `functional-tester` writes failing tests for all ACs. |
| `test-plan-review` | `code-reviewer` checks every AC maps to a failing test before GREEN. |
| `tdd-green` | `python-coder` and `typescript-coder` in parallel; minimal code to pass tests; no test edits. |
| `coverage-gate` | `functional-tester`; automated gate — at least 95% coverage on changed or new files only; fail sends work back to RED. |
| `tdd-blue` | Both coders in parallel; refactor only; tests stay green. |
| `sprint-review` | `code-reviewer`, `ui-tester`, `security-tester` in parallel; browser screenshots for new UI; findings feed the next sprint. |
| `local-deployment` | `devops` local apply, smoke test, rollback notes. |
| `unit-regression` | `functional-tester` on changed modules (95% on changed scope). |
| `integration-regression` | `functional-tester` on changed interfaces. |
| `e2e-regression` | `ui-tester` and `code-reviewer` in parallel; screenshots and design compliance for changed workflows. |
| `docs-cleanup` | `documentation` archives and updates README, API docs, `HANDOFF.md`, tasks. |
| `quality-review` | `tech-lead` only; code and documentation gate before holistic review. |
| `final-holistic-review` | `solution-architect`, `tech-lead`, `ui-designer`, `principles-reviewer` in parallel; all must approve. |

Build gates (see `quality_gates` in `build.yaml`): `tasks-review` (approval), `coverage-gate` (automated threshold), `quality-review` (approval), `final-holistic-review` (approval). Thresholds and metrics are defined in YAML; aggregate coverage for quality-review is 95% on new or changed files, not a separate 97% deployment-review phase in this workflow file.

Subtask execution: RED, GREEN, and BLUE run as orchestrated subtasks per stream (Python and TypeScript can progress in parallel with disjoint `file_scope`). Recovery uses `HANDOFF.md`, `artefacts/build/dispatch.md`, and `subtask-plan.yaml` status fields (see `state_recovery` in `build.yaml`).

![Build Workflow](diagrams/build-workflow.png)

```mermaid
---
title: Default delivery (high level)
---
flowchart TD
    start([Start]) --> design_yaml["design.yaml through design-review gate"]
    design_yaml --> build_yaml["build.yaml through final-holistic-review"]
    build_yaml --> deploy_yaml["deploy.yaml when needed"]
```


#### When to use design and build

Use design then build for production features and anything that will be maintained long-term. Duration scales with sprint count and scope.

Do not use this path for throwaway spikes; use [Prototype (`prototype.yaml`)](#prototype-prototypeyaml) instead. Run [Retrospective (`retrospective.yaml`)](#retrospective-retrospectiveyaml) or [Continuous improvement (`continuous-improvement.yaml`)](#continuous-improvement-continuous-improvementyaml) when you want process or framework follow-up; they are not phases inside `build.yaml`.

### Prototype (`prototype.yaml`)

Purpose: Fast iteration without quality gates.

Use for: POCs, experiments, spikes, throwaway code.

The prototype workflow trades rigour for speed: 4 phases, no quality gates, 5 agents.

```text
quick-plan → sketch-design → build → validate (optional)
```

![Prototype Workflow](diagrams/prototype-workflow.png)

```mermaid
---
title: Prototype Workflow
---
flowchart TD
    start([Start]) --> plan

    subgraph plan["Quick Plan"]
        po["product-owner: minimal requirements"]
    end

    plan --> sketch

    subgraph sketch["Minimal Design"]
        sa["solution-architect: high-level only"]
    end

    sketch --> build

    subgraph build["Build Prototype (parallel)"]
        pc["python-coder"]
        tc["typescript-coder"]
    end

    build --> validate

    subgraph validate["Smoke Test (optional)"]
        ft["functional-tester: happy path only"]
    end

    validate --> finish(["Complete (not production-ready)"])

    classDef optionalStyle fill:#e9ecef,stroke:#868e96,stroke-dasharray: 5 5
    class validate optionalStyle
```


#### Prototype rules

- Speed over quality. Technical debt is acceptable.
- No formal reviews, no coverage requirements, no security audits.
- Tests are optional; smoke tests covering the happy path are sufficient.
- Hard-coded values, skipped error handling, and incomplete documentation are all acceptable.
- Mark code clearly as prototype.

#### Migrating prototype to production

If a prototype validates its hypothesis and should become production code:

1. Archive the prototype on a separate branch
2. Extract learnings: document what worked and what did not
3. Start fresh with design then build (this section’s default path)
4. Do not copy-paste prototype code; rewrite with TDD from the beginning

Cleaning up a prototype takes longer than rewriting it properly. The technical debt in prototype code is architectural, not superficial.

### Deploy (`deploy.yaml`)

Purpose: GCP cloud deployment and deployment review after `build.yaml` has completed local deployment and verification.

| Phase | Agents | Role |
|-------|--------|------|
| `gcp-deployment` | `devops` | Terraform, Cloud Run or Firebase Hosting, staging validation, rollback plan under `artefacts/gcp/` |
| `deployment-review` | `tech-lead` (gate) | Approve production readiness; monitoring and rollback confirmed |

`quality_gates` in the YAML require tech-lead approval on `deployment-review`. Criteria include deployment success and coverage sign-off as defined in the file (see `deploy.yaml` for thresholds and notes).

### Bugfix (`bugfix.yaml`)

Purpose: Reproduce, fix, and verify defects with empirical evidence (browser screenshots and file-cited causal chains), not feature-sized planning.

Shape: `reproduce` (gated; `ui-tester` and `functional-tester` in parallel) → `fix` (failing test first, then `python-coder` / `typescript-coder` as needed) → `verify` (gated; parallel UI and test confirmation). Evidence lands under `artefacts/bugfix/`.

Quality gates: Evidence gates on `reproduce` and `verify`—tests passing alone is not sufficient; see YAML for gate metrics and workflow rules (TDD on the fix, commit body records causal chain).

### Full-test (`full-test.yaml`)

Purpose: Full-suite testing across all modules—release confidence, not the per-feature changed-scope regressions in `build.yaml`.

Phases (sequential): `full-unit-test` → `full-integration-test` → `full-e2e-test` → `quality-check` (tech-lead gate). Reports under `artefacts/test-results/`. No code changes in this workflow—failures are reported for follow-up elsewhere.

When to run: Before merging a long-running branch to main, after large refactors, or on demand for health checks (see YAML `workflow_rules`).

### Content (`content.yaml`)

File: `context/workflows/content.yaml`
Pattern: Sequential chain — `product-expert` for research, then `documentation` with a different persona per phase (draft → editor → optional expert reviewer → finalize).
Use for: External-facing prose: blogs, papers, guides, talks, marketing where voice matters.
Do not use for: Technical handoffs, API or architecture reference, internal task or review artefacts, or anything that should stay neutral and repo-shaped — use [Design](#design-designyaml) then [Build](#build-buildyaml) with `doc-standards.md` without personas.

Five phases, no quality gates (YAML `quality_gates: []`); typical wall time about 2–4 hours. Shape, validation strings, and `workflow_rules` live in `content.yaml`; this subsection is a digest only.

```text
research → draft → review → technical-review (optional) → finalize
```

![Content Workflow](diagrams/content-workflow.png)

```mermaid
---
title: Human-Facing Content Workflow
---
flowchart TD
    start([Start]) --> research

    subgraph research["Research"]
        pe["product-expert"]
    end

    research --> draft

    subgraph draft["Draft"]
        d1["documentation + persona"]
    end

    draft --> review

    subgraph review["Editorial review"]
        d2["documentation + editor"]
    end

    review --> tech_review

    subgraph tech_review["Technical review"]
        d3["documentation + expert-reviewer"]
    end

    tech_review --> fin["Finalize: documentation"]

    fin --> finish([Published])

    classDef optionalStyle fill:#e9ecef,stroke:#868e96,stroke-dasharray: 5 5

    class tech_review optionalStyle
```


#### Phases

| Phase | Agent | Persona / role | Primary output |
|-------|--------|----------------|------------------|
| `research` | `product-expert` | Audience, purpose, key messages, sources | Research notes (see YAML `outputs`) |
| `draft` | `documentation` | `technical-writer` or `opinionated-blogger` | `artefacts/content/drafts/{title}-draft.md` |
| `review` | `documentation` | `editor` | `artefacts/content/drafts/{title}-reviewed.md` |
| `technical-review` | `documentation` | `expert-reviewer` (optional — skip for non-technical pieces) | `artefacts/content/drafts/{title}-tech-reviewed.md` |
| `finalize` | `documentation` | Publication formatting per task | `artefacts/content/published/{title}.md` |

Draft and review phases list concrete checks in YAML (persona voice, British English, opening hook, concrete examples; editorial pass strips patterns covered in `context/rules/no-ai-slop.md`). Spawn each phase with `context/templates/task-prompt-template.md`, the persona path, and file scope — long copy-paste invoke blocks belong in the task prompt, not in this reference.

### Continuous improvement (`continuous-improvement.yaml`)

Framework improvement and measurement are governed by `context/workflows/continuous-improvement.yaml`, not by ad hoc scorecards. That workflow defines two modes (incident and retrospective), explicit phases, what gets written to disk, and a quality gate in retrospective mode. The `workflow-analyst` agent appears only in retrospective review; other phases are orchestrator- and human-led as the YAML states.

#### Workflow file and modes

| Mode | Trigger | Purpose |
|------|---------|---------|
| incident | Human reports a specific failure | Capture, diagnose, fix, record one incident |
| retrospective | After deployment, after a sprint, or on demand | Mine logs and git for patterns, discuss with human, fix, record |

Workflow rules (from YAML): incident mode is human-triggered; retrospective mode is periodic or on demand; every finding or incident must identify a fixable gap in the framework (rules, standards, templates, scripts), not vanity metrics; in retrospective mode the human decides which findings to implement; incident mode proceeds once diagnosis is sound.

---

#### Incident mode (reactive)

Sequential phases:

| Phase | Agents | Role |
|-------|--------|------|
| `report` | None (orchestrator + human) | Append a new entry to `artefacts/build/agent-incidents.md`: severity, symptom, root cause and fix initially pending |
| `diagnose` | None | Trace symptom → mechanism → file → gap with path-level evidence; read configs and code, do not infer from names alone |
| `fix` | `python-coder`, `typescript-coder` (parallel) | Apply changes to rules, standards, templates, or small orchestration edits; commit after each logical fix |
| `record` | None | Update the incident entry with root cause, fix summary, and commit hash; optionally add a portability task to `artefacts/build/tasks-context-framework.md` |

Validation highlights: diagnosis must cite specific files and complete the causal chain; `fix` must satisfy acceptance checks (for example grep confirms an anti-pattern removed).

The YAML lists `fix` with `depends_on: [diagnose, discuss]`. Retrospective runs `discuss` (human gate) before `fix`. Incident runs `diagnose` after `report`; the orchestrator should advance to `fix` once diagnosis is complete (the `discuss` phase exists only in retrospective mode).

---

#### Retrospective mode (proactive)

Sequential phases:

| Phase | Agents | Role |
|-------|--------|------|
| `review` | `workflow-analyst` | Read artefacts/build/agent-interruptions.md (questions, tool approvals, escalations), artefacts/build/agent-incidents.md, and git log bodies for Agent-Session telemetry (tokens, duration, agents, dispatch, interactions, approvals injected by `prepare-commit-msg` and orchestrator). Aggregate to find patterns with counts and examples; each finding must point at concrete files that would change |
| `discuss` | None (gate: human approval) | Present pattern → root cause → proposed fix; human chooses what to act on |
| `fix` | `python-coder`, `typescript-coder` (parallel) | Same as incident mode: implement agreed fixes |
| `record` | None | Update incidents if relevant; append portability tasks to `artefacts/build/tasks-context-framework.md` when fixes should propagate to other repos |

Quality gate: `discuss` (retrospective only) requires human approval before fixes proceed.

Validation highlights: git log parsed for session metrics; interruption and incident logs read; patterns evidenced; no aggregate “health scores” (explicitly disallowed by workflow rules).

---

#### Data the retrospective `review` phase is built to consume

The YAML lists these sources explicitly:

- `artefacts/build/agent-interruptions.md`: blocking moments (questions, approvals, escalations)
- `artefacts/build/agent-incidents.md`: prior framework failures
- `git log` with `%H`, subject, body: reconstruct tokens=, duration=, agents=, dispatch=, interactions=, approvals= from commit trailers

From those, the analyst is expected to answer questions such as: total tokens per agent, sprint, or task; duration per task; which agents cost the most tokens relative to output; token trends; autonomy rate (commits with orchestrator dispatch and zero interactions); distribution of human interactions and approvals. Repeated rule violations, agents over token budget, and incidents with shared root causes are examples of valid pattern classes.

---

#### Relationship to other artefacts

Tasks and handoffs (`artefacts/build/tasks.md`, `HANDOFF.md`, `artefacts/shared/handoffs/`) remain useful secondary context when the orchestrator or `@workflow-analyst` widens an investigation, but they are not the primary contract of `continuous-improvement.yaml`; that contract is interruptions log, incidents log, and git telemetry as above.

The agent definition `context/agents/workflow-analyst.md` still describes broader analysis habits (for example task and handoff mining). When in doubt, the workflow YAML wins for phase order, outputs, and validation.

---

#### Common fix targets (illustrative)

These are examples of fixable gaps, not a separate scoring methodology:

- Coverage discipline: tests landed after GREEN instead of strengthening RED or failing `coverage-gate` (see `build.yaml`).
- Tooling drift: repeated bash-for-files or wrong package managers; tighten prompts or rules.
- Integration cost: missing fixtures or slow local setup; add shared fixtures or documented setup in standards.
- Parallel misuse: duplicated context without time savings; narrow parallel phases to truly independent work.

### Retrospective (`retrospective.yaml`)

Purpose: Standalone proactive review—`workflow-analyst` reviews accumulated operational data, the orchestrator discusses findings with a human (gate), then coders fix and record portability tasks. Not the same file as `continuous-improvement.yaml` (that file adds incident mode and git Agent-Session mining in its retrospective path).

| Phase | Agents | Role |
|-------|--------|------|
| `review` | `workflow-analyst` | Read `agent-interruptions.md`, `agent-metrics.log`, `agent-incidents.md`; report patterns with file:line evidence |
| `discuss` | None (human gate) | Human selects which findings to implement |
| `fix` | `python-coder`, `typescript-coder` (parallel) | Approved framework changes |
| `record` | None | Append portability tasks to `artefacts/build/tasks-context-framework.md` |

See `retrospective.yaml` for `quality_gates`, `workflow_rules`, and `state_recovery`.

---

## Orchestration Patterns

This section documents the four coordination shapes the shipped workflows actually use: single agent, sequential chain, hive (parallel agents on a shared contract, with orchestrator scope rules), and iterative loop (gates and rework). They are vocabulary for reading YAML—not separate runtime features. On disk, behaviour is whatever each workflow file says: phase order, `parallel: true` (see `parallel_planning` in `build.yaml`), disjoint `file_scope` where required, and gates.

### Single Agent

One specialist, one task, no dependencies. Use for isolated tasks with clear requirements: fix a specific bug, add a simple feature, write documentation.

### Sequential Chain

Agents in strict order, each depending on the previous output. Use for tasks with clear dependencies and quality gates: most of design and build is sequential between phases.

### Hive

Parallel agents working against a shared contract (same tests, same subtask plan, same architecture outputs) with orchestrator-enforced scope and merge discipline. The canonical case in `build.yaml` is TDD GREEN and TDD BLUE: `python-coder` and `typescript-coder` run together with disjoint `file_scope` but the same failing-then-passing test suite (`parallel_planning` and `subtask_execution` in the YAML spell this out). `design-contracts` is hive-like too: both designers extend the same architecture handoff. Tasks review, sprint-review, e2e-regression, and final-holistic-review are parallel reviewers on the same body of work—again shared-artefact coordination.

### Iterative Loop

Review-fix cycles until approval. Use at quality gates where output may be rejected: design review may require architectural changes before approval.

### Pattern Comparison

| Pattern | Speed | Token Cost | Coordination | Example in shipped YAML |
|---------|-------|------------|--------------|-------------------------|
| Single | Fast | Low | None | `tdd-red`, `coverage-gate`, many single-agent phases |
| Sequential | Slow | Low | Linear | Discovery, architecture → contracts → UI chain |
| Hive | Fast | High | Shared contract + scopes | `tdd-green` / `tdd-blue`; `design-contracts`; parallel review phases on one plan or codebase |
| Iterative | Varies | Medium | Approval loops | `design-review`, quality gates |

### How the default path uses patterns

`design.yaml`

- Discovery: Sequential (`product-expert` then `product-owner`).
- Architecture: Single agent (`solution-architect`).
- Contracts: Parallel hive-like pair (`database-designer` and `api-designer` on the same architecture outputs).
- UI and visuals: Single phase (`ui-designer` — component specs, wireframes, and visual assets consolidated).
- Design review: Sequential reviewers with iterative return to earlier phases when required.

`build.yaml`

- Planning and test planning: Sequential (`tech-lead` then `code-reviewer` on the test plan).
- Tasks review, sprint-review, e2e-regression, final-holistic-review: `parallel: true`, but agents share the same plan, sprint surface, workflows under test, or release candidate—hive-style coordination.
- TDD GREEN / BLUE: Hive (parallel coders, shared tests, disjoint file scopes).
- Coverage gate: Single agent; may loop back to RED.
- Regression after local deployment: Sequential unit → integration → e2e (the e2e phase may list two agents in parallel with shared workflow scope).
- Quality review then final holistic review: Gate then parallel approvers on the same implementation.

### Choosing a pattern

1. Single isolated task? Single agent.
2. Same plan, tests, or design handoff for everyone? Hive (all `parallel: true` phases in default path YAML behave this way).
3. Strict A-then-B output dependency? Sequential chain.
4. Output needs iterative refinement? Iterative loop.

### Token Optimisation

Parallel execution increases token usage because context is duplicated across agents. Three agents running in parallel typically cost ~20% more tokens than the same three agents running sequentially.

Prefer parallel execution when time is critical, tasks are large (overhead is a small percentage of the total), or agents have different contexts (minimal duplication). Prefer sequential execution when the token budget is tight, tasks are small (overhead dominates), or context is large and identical across agents.

---

## Templates

Templates are stored in `context/templates/` and define standard output shapes for recurring artefacts. The orchestrator selects the appropriate template when constructing a task prompt; the producing agent uses it to structure its output.

`context/templates/README.md` indexes every template file, when to use it, and how it relates to workflows—use it when you are adding a new artefact shape rather than guessing from filenames alone.

### Why Templates Exist

Standardised shapes reduce ambiguity for both writers and readers. When every review follows the same structure, or every handoff includes the same fields, downstream agents and humans can consume the output predictably. Automation becomes reliable when the shape is known in advance.

The `commit-message-template.md` is not only for humans formatting commits: it defines the `Agent-Session:` trailer that `prepare-commit-msg` completes and that `continuous-improvement.yaml` expects the orchestrator to parse from `git log` during retrospective review. The template specifies a machine-readable line with `tool=`, `model=`, `agents=` (role names), optional `duration=`, `dispatch=` (`orchestrator` or `human`), `interactions=`, and `approvals=`; the hook appends `tokens=` (input/output token counts). Together those fields support questions in the continuous-improvement workflow (for example cost per agent, autonomy when `dispatch=orchestrator` with zero interactions, and human-approval load). See `context/templates/commit-message-template.md` for the full field table and counting rules.

### Available Templates

| Template | Purpose |
|----------|---------|
| `agent-template.md` | Starting point for creating a new specialised agent |
| `architecture-template.md` | Standard structure for system architecture documents |
| `bugs-template.md` | Standard bug tracker format |
| `commit-message-template.md` | Standard commit message structure with agent session metadata |
| `design-template.md` | Standard design document for complex features or screens |
| `domain-rules-template.yaml` | Template for domain-specific constraints |
| `handoff-template.md` | Standard agent handoff format |
| `pr-description-template.md` | Standard pull request description format |
| `requirements-template.md` | Standard requirements structure |
| `review-template.md` | Standard review finding format |
| `task-prompt-template.md` | Orchestrator prompt scaffold for spawning agents correctly |
| `tasks-template.md` | Standard task tracking format |
| `test-dashboard-template.md` | Standard structure for test dashboards |
| `user-stories-template.md` | Standard user story format |

The task prompt template deserves particular attention. It carries rule resolution and file-scope discipline into subagent execution. When the orchestrator spawns an agent, the task prompt template ensures the agent receives its definition file path, resolved rules, immediate context, file scope constraints, and escalation instructions in a consistent structure.

---

## Scripts and Automation

Scripts are stored in `context/scripts/` and form the automation layer that turns the framework from a collection of ideas into an operating system with enforcement.

Layout on disk: `generators/` holds workflow and registry generators (today the main entry point is `generate_agents_md.py`); `validators/` holds pre-commit Python checks; `tests/` exercises validators and generators against fixtures; `prepare-commit-msg.*` (see [below](#prepare-commit-msg-hook-agent-tokens-on-commits)) appends token deltas to `Agent-Session:` lines for [Continuous improvement](#continuous-improvement-continuous-improvementyaml) telemetry. Anything invoked from git hooks or CI should stay small, deterministic, and safe to run on every commit.

### Generators

`generators/generate_agents_md.py`: Reads every workflow YAML and every agent definition, then produces the derived `AGENTS.md` registry. This is the framework's primary generation pipeline. Run it after changing any workflow or agent definition:

```bash
uv run python context/scripts/generators/generate_agents_md.py
```

The generator is also an enforcement point. If an agent definition references a non-existent rule, or a workflow references an agent with no definition, the mismatch surfaces at generation time.

### Validators

Validators are pre-commit hooks stored in `context/scripts/validators/`. Each validator enforces one or more rules at commit time. A rule without a validator is a suggestion. A rule with a validator is enforceable. Not every rule has automated enforcement yet; validator coverage is expanding.

| Validator | Rule / Purpose | What It Checks |
|-----------|----------------|---------------|
| `workspace_conventions.py` | `workspace-conventions.md` | Commit message format, `Agent-Session` trailer, metrics JSONL schema, output paths |
| `tech_writing.py` | `tech-writing.md` | British English spelling (`-ise`, `-our`, `-re`, `licence`, `artefact`), EARS requirements syntax |
| `ui_dev.py` | `ui-dev.md` | Prohibits `!important`, raw hex colors, multiple CSS files, DaisyUI tokens, Heroicons barrel |
| `supabase.py` | `supabase.md` | Supabase import boundary, `schema_migrations` audit row insert in SQL migrations |
| `testing.py` | `testing.md` | Detroit-school outcome-based assertions, prohibits mock interaction assertions on internal collaborators |
| `typescript_environment.py` | `typescript-environment.md` | Prohibits `package-lock.json` (enforces `yarn.lock`), strict `tsconfig.json` compiler options, workspaces |
| `ui_testing.py` | `ui-testing.md` | Prohibits full `puppeteer` (enforces `puppeteer-core`), prohibits `playwright` and `cypress` |
| `secrets.py` | `secrets.md` | Scans for private key blocks, API keys, credentials in `.env` files |
| `framework_docs_staleness.py` | Utility | Ensures framework docs are updated alongside changes to `context/` |
| `agent_definitions.py` | Utility | Agent definition structural integrity and schema compliance |
| `adapter_drift.py` | Utility | Adapter projection synchronisation against canonical context definitions |
| `verify_typst_formatting.py` | Utility | Typst-compatible Markdown formatting rules on staged files |

#### `workspace_conventions.py`

Enforces invariants from `context/rules/workspace-conventions.md`. Reads `.git/COMMIT_EDITMSG` at the `commit-msg` stage. Regex-checks the subject line against `type(scope): description` — valid types are `feat`, `fix`, `test`, `refactor`, `docs`, `chore`, `perf`; scope must be lowercase alphanumeric with hyphens; max 72 characters. Imperative mood is checked heuristically (flags first words ending in `-ed` or `-ing`). If an `Agent-Session:` trailer is present, validates the `tool=`, `model=`, `agents=` triplet format and requires a `Co-Authored-By:` line. Merge and revert commits are skipped. Also validates JSONL entries under `metrics/` (`ts`, `task`, `agent`, `event`, `tokens`, ISO 8601 timestamps, valid events, `to` field on handoffs) and validates output paths and filenames (`artefacts/`, `secrets/`, `services/{name}/tests/`).

#### `tech_writing.py`

Enforces invariants from `context/rules/tech-writing.md`. Scans Markdown lines outside fenced code blocks for American spellings (`color`, `behavior`, `organize`/`realize`/`recognize`, `center`, `license` noun form, `artifact`). Also validates EARS requirements notation on `requirements.md` and `user-stories.md` files: lines containing "shall" must match one of six EARS patterns (ubiquitous, event, state, optional, forbidden, complex). Lines inside code blocks, headers, and tables are skipped.

#### `ui_dev.py`

Enforces invariants from `context/rules/ui-dev.md`. Scans frontend source files for: prohibition of `!important` in CSS/SCSS/TSX; prohibition of raw hex colour codes; requirement of a single `index.css` file; enforcement of DaisyUI semantic tokens instead of concrete Tailwind colour classes; restriction of `@heroicons/react` imports to the `HeroIcons.tsx` barrel; and adherence to the allowed spacing token scale (`gap-1`, `gap-2`, `gap-4`, `p-2`, `p-4`, `px-4`).

#### `supabase.py`

Enforces invariants from `context/rules/supabase.md`. Regex-checks source files to ensure `import supabase`, `from supabase`, or `@supabase/supabase-js` imports only occur within designated database services or stores. Also verifies that SQL migration files under `**/migrations/*.sql` contain an audit row insert into `schema_migrations`.

#### `testing.py`

Enforces invariants from `context/rules/testing.md`. Enforces Detroit-school outcome-based assertions. Scans test files and flags interaction assertions (`mock.assert_called_once_with`, `assert_called_with`, `toHaveBeenCalledWith`) on internal collaborators. Mock interactions at external I/O boundaries are permitted when annotated with `# io-boundary` or `// io-boundary`.

#### `typescript_environment.py`

Enforces invariants from `context/rules/typescript-environment.md`. Flags any `package-lock.json` files (repository strictly standardises on Yarn Berry and `yarn.lock`). Verifies that `tsconfig.json` files enable `strict: true`, `noImplicitAny: true`, and `strictNullChecks: true`. Confirms that directories containing `package.json` are declared in root `package.json` workspaces.

#### `ui_testing.py`

Enforces invariants from `context/rules/ui-testing.md`. Scans UI package dependencies in `package.json` to prohibit the heavyweight `puppeteer` package (requiring lightweight `puppeteer-core`) and prohibit `playwright`, `@playwright/test`, and `cypress`. Exempts documentation typesetting engines in the root `package.json`.

#### `secrets.py`

Enforces invariants from `context/rules/secrets.md`. Scans staged files and repository paths for committed secrets, API keys, private key blocks (`BEGIN PRIVATE KEY`), and `.env` files containing credentials.

#### `framework_docs_staleness.py`

Does not receive file paths — runs with `pass_filenames: false`. Queries `git diff --cached` for any staged file under `context/`. If context files are staged, checks whether the two framework docs are also staged. If the reference doc (`agentic-framework-reference.md`) is missing, blocks the commit (exit 1). If the brief doc (`agentic-framework.md`) is missing, warns but passes (exit 0). If the commit message in `.git/COMMIT_EDITMSG` contains `[docs-ok]`, passes unconditionally — the marker is an explicit assertion that the committer assessed docs impact. Auditable via `git log --grep='docs-ok'`. The only hardcoded exclusion is the two framework docs themselves, to avoid circular triggering.

#### `agent_definitions.py`

Runs as a pre-commit hook on `context/agents/*.md` and can be run manually. Validates every `.md` file in `context/agents/` (excluding `README.md` and `TEMPLATE.md`). Checks: YAML frontmatter is present and parseable; required fields `name` and `model` exist; every entry in `standards:` points to a file that exists in `context/standards/`; every entry in `rules:` points to a file that exists in `context/rules/`; every entry in `skills:` points to a file that exists in `context/skills/`; the body contains no hardcoded absolute paths (`/Users/`, `/home/`). Existence checks are relative to the repo working directory at runtime.

#### `adapter_drift.py`

Regenerates all adapter projections in memory and compares them against on-disk projections (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/skills/`, `.claude/prompts/`, `.github/prompts/`, `.github/instructions/`, `.github/copilot-instructions.md`, `.openai/prompts/`). Fails if any projection has drifted or is missing.

#### `verify_typst_formatting.py`

Enforces Typst typesetting formatting rules on Markdown documents (ensuring at least 2 blank lines follow mermaid diagrams and a horizontal rule `---` precedes `##` section headings). Supports `--staged` and `--fix` modes.

#### Hook Activation and Deployment

Validators defined in `context/scripts/validators/` become active pre-commit gates in a host repository by deploying the configuration template:

1. **Deploy Configuration**: Copy the template to the project root:
   ```bash
   cp context/scripts/pre-commit-config-template.yaml .pre-commit-config.yaml
   ```

2. **Install Hooks**: Add `pre-commit` as a dev dependency and install both git lifecycle hooks:
   ```bash
   uv add --dev pre-commit
   uv run pre-commit install
   uv run pre-commit install --hook-type commit-msg
   ```

3. **Differential Execution**: Pre-commit inspects staged files (`git diff --cached --name-only`) against each hook's `files:` regex pattern. If no staged files match a hook's filter, that validator is skipped entirely (0ms overhead). If matching files are staged, pre-commit passes only those files to the validator for differential inspection.

4. **Baseline Verification**: Verify all files across the repository:
   ```bash
   uv run pre-commit run --all-files
   ```

Hook activation is a mandatory step in the project bootstrap sequence (`context/skills/bootstrap-workflow.md`).

### `prepare-commit-msg` hook (agent tokens on commits)

Files: `context/scripts/prepare-commit-msg.sh` (wrapper that runs `uv run python …/prepare-commit-msg.py`) and `context/scripts/prepare-commit-msg.py` (implementation).

Git calls `prepare-commit-msg` with the path to the commit message draft. The Python script only augments commits that already contain an `Agent-Session:` line (see `context/templates/commit-message-template.md`); if that trailer is absent, it assumes a human-only commit and exits without writing.

What it does

1. Finds Claude Code session telemetry — It does not look up a single hard-coded path name. From `git rev-parse --show-toplevel` it builds `~/.claude/projects/<repo-root-with-each-slash-replaced-by-a-hyphen>` (the same string transform Claude Code uses for project folders in this hook’s implementation). Under that directory it lists session subfolders and picks the most recently modified one—so the active session is whichever directory Claude last wrote to, not one global filename shared by every repository. Token lines are then read from that folder’s `*.jsonl` files as described below.
2. Sums tokens — Reads the session’s main `*.jsonl` plus `subagents/*.jsonl`, accumulating `input_tokens`, cache-related input token fields, and `output_tokens` from each line’s `message.usage` object.
3. Uses a watermark file — In that same session directory it reads `.tokens-watermark`, a JSON file `{"in": <int>, "out": <int>}` holding cumulative token totals after the last commit this hook successfully annotated. It computes deltas (`current_cumulative − watermark`) and appends `tokens=<delta_in>/<delta_out>` to the `Agent-Session:` line (replacing an existing `tokens=…` token pair if already present). `duration`, `dispatch`, `interactions`, and `approvals` are not produced by this script—they must be supplied by the orchestrator in the message body per the commit template. After updating the message, the script rewrites `.tokens-watermark` with the new cumulative totals so the next commit records only usage since this one.

Edge behaviour

- Merge and squash commit sources are skipped entirely (no token injection).
- If both deltas are zero, the hook does not touch the message or watermark.
- The watermark lives outside the repository (next to Claude’s JSONL); deleting or losing it makes the next run attribute a larger delta (everything since the lost baseline)—operators should treat it as part of session-local state, not something to version in git.

### Tests

The scripts directory includes its own test suite in `context/scripts/tests/`. Tests cover validators, generators, and agent definition validation using positive and negative fixture files in `tests/fixtures/`.

---

## Portability and Framework Adapters

The framework is designed to survive changes in agent runtime or orchestration platform. It uses a **Hexagonal (Ports and Adapters) Architecture**. Agent definitions, workflows, rules, and standards serve as the framework-agnostic "domain logic." They are written in standard Markdown and YAML, and maintained in the `context/` directory.

To run these on specific platforms, the `generate_adapters.py` CLI compiles these canonical sources into native runtime projections.

### Supported Runtime Adapters

The framework ships with deterministic compiler support for four runtimes:

- **Google Antigravity/Gemini**: Generates structured `.agents/skills/` directories, complete with `SKILL.md` frontmatter, and `GEMINI.md`.
- **Claude Code**: Projects context into `CLAUDE.md` and `.claude/`.
- **GitHub Copilot**: Projects instructions into `.github/copilot-instructions.md` and custom prompts into `.github/prompts/`.
- **OpenAI/Codex**: Generates OpenAI-compatible system prompt bundles and JSON schema tool declarations in `.openai/`.

You execute the generator via the repository's provided CLI (e.g., `uv run python context/scripts/generators/generate_adapters.py`). See the repository `README.md` for CLI usage, dry-run flags, and target filtering.

### Drift Enforcement

To prevent the generated projections from drifting out of sync with the canonical sources, the framework includes `adapter_drift.py`. It runs as a `pre-commit` validator, receiving staged file paths, regenerating all adapter projections in-memory, and failing if any projection is missing, modified, or orphaned.

### Model Tiering (`models.yaml`)

Agent definitions do not hardcode vendor model names (e.g., `claude-3-opus-20240229`). Instead, they declare abstract capability tiers (`small`, `medium`, `large`).

The `context/models.yaml` file maps these abstract tiers to concrete vendor models per runtime adapter. When `generate_adapters.py` runs, it resolves the tier declared in an agent's frontmatter into the appropriate vendor string for the target platform.

### Manual Integration (Other Runtimes)

The code samples below are illustrative. They show how you might load the portable markdown prompts and map tool names for runtimes that do not currently have a built adapter.

#### LangGraph

Load the agent markdown as a node system message, parse frontmatter for tool bindings:

```python
from langgraph.graph import StateGraph
from pathlib import Path

def load_agent(name: str) -> str:
    return Path(f"context/agents/{name}.md").read_text()

def python_coder_node(state):
    agent_prompt = load_agent("python-coder")
    task_prompt = f"{agent_prompt}\n\n## Task\n\n{state['task']}"
    response = llm.invoke(task_prompt)
    return {"output": response}

workflow = StateGraph(State)
workflow.add_node("python-coder", python_coder_node)
```

#### CrewAI

Load agent markdown as backstory, map tools to CrewAI equivalents:

```python
from crewai import Agent, Task, Crew

python_coder = Agent(
    role="Python Developer",
    goal="Write clean, tested Python code following standards",
    backstory=load_agent("python-coder"),
    tools=[WriteFileTool(), EditFileTool(), ReadFileTool()],
)

task = Task(
    description="Implement user authentication with FastAPI",
    agent=python_coder,
    expected_output="Working auth endpoints with tests"
)

crew = Crew(agents=[python_coder], tasks=[task])
```

#### AutoGen

Load agent markdown as system_message:

```python
from autogen import AssistantAgent

python_coder = AssistantAgent(
    name="python_coder",
    system_message=load_agent("python-coder"),
    llm_config={"model": "gpt-4", "functions": [write_file, edit_file]}
)
```

#### IDE-Based Systems (Cursor, Windsurf, Aider, Continue)

These are typically single-agent systems. Copy the agent definition to the IDE's context file:

```bash
# Cursor
cp context/agents/python-coder.md .cursor/rules/python-coder.md

# Windsurf
cp context/agents/python-coder.md .windsurfrules

# Aider (load as additional context)
aider --read context/agents/python-coder.md \
      --read context/standards/tech-standards.md
```

#### Tool Mapping Reference

| Expected Tool | LangGraph | CrewAI | AutoGen | IDE-Based |
|---------------|-----------|--------|---------|-----------|
| Write | `write_file()` | `FileWriterTool()` | `write_file()` func | Built-in |
| Edit | `edit_file()` | `FileWriterTool()` | `edit_file()` func | Built-in |
| Read | `read_file()` | `FileReadTool()` | `read_file()` func | Built-in |
| Glob | `glob.glob()` | `DirectorySearchTool()` | `glob()` func | Built-in |
| Grep | `grep_content()` | `FileSearchTool()` | `grep()` func | Built-in |
| Bash | `subprocess.run()` | `ShellTool()` | `execute_code()` | Built-in |

#### Handling Frontmatter

Most frameworks do not parse YAML frontmatter automatically. Two approaches:

Strip frontmatter for frameworks that only need the system prompt:

```python
def load_prompt_only(name: str) -> str:
    content = Path(f"context/agents/{name}.md").read_text()
    parts = content.split("---")
    return "---".join(parts[2:]) if len(parts) > 2 else content
```

Parse frontmatter for frameworks that can use the metadata (model choice, tool list, rule references):

```python
import yaml

def load_with_metadata(name: str):
    content = Path(f"context/agents/{name}.md").read_text()
    parts = content.split("---")
    metadata = yaml.safe_load(parts[1]) if len(parts) > 2 else {}
    prompt = "---".join(parts[2:]) if len(parts) > 2 else content
    return {"prompt": prompt, "metadata": metadata}
```

---

## How the Parts Connect

End to end: workflows pick which agent runs in each phase and which outputs must exist; the orchestrator loads that agent's rules (injected) and standards (referenced), wraps the task in the task prompt template, and dispatches execution; agents write artefacts that match templates; validators and hooks ensure the committed tree still matches the declared rules; state recovery blocks in YAML plus `HANDOFF.md` let a new session resume after compaction. The subsections below spell out each pairwise relationship.

### Agents Read Rules and Standards

Agent files point to the rules and standards they depend on via frontmatter. The orchestrator resolves these references at spawn time, injecting rules and pointing the agent to the relevant standards. This keeps prompts small and composable: the agent definition is the single source of truth for what each specialist needs.

### Workflows Sequence Agents

Workflow YAML does not replace agent definitions; it arranges them. The design separates role definition (who does what and how) from phase sequencing (when they do it and in what order). This means the same agent can appear in multiple workflows with different sequencing.

### Templates Shape Outputs

Templates are chosen by the orchestrator and used by producing agents. Output conventions are an explicit part of orchestration rather than an afterthought. When an agent produces a review, a handoff, or a set of requirements, the template defines what "complete" looks like.

### Scripts Enforce the Model

Without validators, generators, and hooks, the framework would rely on memory and goodwill. The scripts directory turns expectations into checks: validators catch rule violations at commit time, generators keep derived files in sync with authoritative sources, and hooks record session telemetry automatically.

### Recovery is Built In

Every workflow YAML includes a `state_recovery` section listing the files an orchestrator should read to reconstruct its position after context compaction. Every agent handoff writes durable state to disk. The `HANDOFF.md` file records the active phase *before* agents are spawned, not after they report back, ensuring the phase survives even if compaction occurs during execution.

---

## Reading Paths

### Extending the Framework

1. `context/README.md`
2. `context/agents/orchestrator.md`
3. `context/workflows/build.yaml` and `context/workflows/design.yaml`
4. `context/templates/task-prompt-template.md`
5. Relevant rules and standards

### Adding a New Agent

1. `context/agents/README.md`
2. `context/templates/agent-template.md`
3. `context/agents/orchestrator.md`
4. The workflow where the new agent should appear
5. [Tool and MCP surfaces (runtime vs frontmatter)](#tool-and-mcp-surfaces-runtime-vs-frontmatter) (this document) — align local runtime settings (for example Cursor `.cursor/settings.local.json`) with any `mcp_tools:` you add

### Porting the Framework to Another Runtime

1. `README.md`
2. `context/README.md`
3. [Portability and Framework Adapters](#portability-and-framework-adapters) (this document)
4. `AGENTS.md`

### Understanding Quality Enforcement

1. `context/rules/`
2. `context/workflows/`
3. `context/scripts/validators/`
4. `context/standards/testing-standards.md`
5. `context/standards/doc-standards.md`

### Running a Default Workflow

1. [Design](#design-designyaml) and [Build](#build-buildyaml) (this document); optional [Deploy](#deploy-deployyaml)
2. `context/workflows/design.yaml` and `context/workflows/build.yaml` (and `deploy.yaml` when promoting to cloud)
3. `context/agents/orchestrator.md`
4. [Orchestration Patterns](#orchestration-patterns) (this document)

### Evaluating Workflow Health

1. `context/workflows/continuous-improvement.yaml`
2. [Continuous improvement (`continuous-improvement.yaml`)](#continuous-improvement-continuous-improvementyaml) (this document — effectiveness and incident handling)
3. `context/agents/workflow-analyst.md`
4. `context/standards/workflow-standards.md`

### Writing Human-Facing Content (Blogs, Papers, Guides)

1. [Content (`content.yaml`)](#content-contentyaml) (this document)
2. [Writing Personas](#writing-personas) (this document)
3. `context/workflows/content.yaml`
4. `context/rules/no-ai-slop.md`

---

<!-- typst-skip-start -->

## Related Documents

- [GitHub Repository](https://github.com/Schmoiger/start-here): framework source code and adapters
- `context/docs/agentic-framework.md`: companion technical paper
- `context/README.md`: framework entry point

---

## Revision History

| Version | Date       | Author    | Changes |
| ------- | ---------- | --------- | ------- |
| 0.1.0   | 2026-04-13 | Initial   | Standalone framework reference: topology, source-of-truth tiers, standards, rules, agents (including personas and tool surfaces), workflows (one subsection per shipped YAML), templates, scripts and hooks, portability, orchestration patterns, reading paths; material from removed standalone docs absorbed here. |
| 0.2.0   | 2026-04-13 | Editorial | Document metadata and revision history aligned with `context/standards/doc-standards.md` section 8.2; prose emphasis normalised outside fenced examples (fence-safe). |
| 0.3.0   | 2026-04-13 | Editorial | Versioning policy: `MAJOR.MINOR.PATCH` per [Semantic Versioning 2.0.0](https://semver.org/) (section 8.2); draft documents stay on major version `0`; revision table uses three-part versions. |
| 0.5.0   | 2026-09-12 | Editorial | Document skills layer in framework topology, source-of-truth tiers, and rules/standards/skills split. |
| 0.6.0   | 2026-09-15 | AS        | Restate rules/skills/standards split by verification mechanism and runtime projection: rules verified at zero token cost by code; skills verified by LLM-as-a-judge; standards serve as judge rubrics. Update rule overhead to ~1,300 tokens (<1% of 128k–200k windows). Consolidate `british-english.md` + `EARS-notation-requirements.md` into `tech-writing.md`. Add skills catalogue with `bootstrap-workflow.md` and `intent-fidelity.md`. Document that all generated adapter projections are now gitignored. |
| 0.7.0   | 2026-09-24 | AS        | Add `gemini-sdk.md` skill covering modern `google-genai` Python SDK patterns, structured outputs with Pydantic, Gemini context caching, Imagen 3, and token burn guard rails. |

<!-- typst-skip-end -->
