# Documentation Standards

---

## 1. Introduction

This document outlines the standards for documentation across the software projects in this monorepo. Its purpose is to ensure consistent, discoverable, and useful documentation for all developers and AI agents.

---

## 2. Project Context

### 2.1. Directory Structure

This repository is a monorepo, containing multiple projects (services and packages).

*   **Monorepo Root:** The top-level directory of the repository.
*   **Project Root:** A directory within the monorepo that contains a specific project (e.g., `/services/bronze-service/`, `/packages/shared-types/python/`).

The documentation shall be structured as follows:

*   **`/context/`**: Input files at monorepo root containing standards and rules for all projects
    *   `/context/standards/`: Development standards (coding, testing, documentation, workflow)
    *   `/context/rules/`: Development guidelines (EARS notation, TDD practices)
*   **`/artefacts/`**: Output files representing work completed
    *   Monorepo root `/artefacts/`: System-wide artefacts (architecture, requirements, API contracts, design)
    *   Project-level `{service}/artefacts/`: Service-specific artefacts (bugs, tasks, todo, test results)

For example:

```
/ (monorepo root)
├── context/                         # INPUT: Standards & rules
│   ├── standards/
│   │   ├── coding-standards.md
│   │   ├── doc-standards.md
│   │   └── testing-standards.md
│   └── rules/
│       └── EARS-notation-requirements.md
│
├── artefacts/                       # OUTPUT: System-wide
│   ├── product/                     # Product & requirements
│   │   ├── requirements.md
│   │   ├── user-stories.md
│   │   └── open-questions.md
│   ├── architecture/                # System architecture
│   │   ├── architecture.md
│   │   ├── data-model.md
│   │   └── api-catalogue.md
│   ├── api/                         # API specifications
│   │   ├── openapi.yaml
│   │   └── api-design-guide.md
│   ├── design/                      # UI/UX design
│   │   ├── design-system.md         # tokens, components, accessibility, wireframes
│   │   └── user-flows.md
│   ├── build/                       # Project management & quality gates
│   │   ├── bugs.md
│   │   ├── tasks.md
│   │   ├── todo.md
│   │   ├── code-review.md
│   │   ├── tech-review.md
│   │   └── architecture-review.md
│   ├── test-results/                # Test execution outputs only
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   ├── security/
│   │   ├── test-gaps.md
│   │   └── archive/
│   └── shared/                      # Cross-service resources
│       ├── handoffs/
│       ├── fixtures/
│       └── mocks/
│
├── services/bronze-service/          # Service example
│   ├── artefacts/                   # OUTPUT: Service-specific
│   │   ├── bugs.md
│   │   ├── tasks.md
│   │   ├── todo.md
│   │   ├── test-results/
│   │   └── fixtures/
│   ├── HANDOFF.md                   # Intra-service coordination
│   ├── src/
│   ├── tests/
│   └── README.md
│
└── packages/shared-types/python/    # Package example
    ├── artefacts/
    │   ├── bugs.md
    │   ├── tasks.md
    │   ├── todo.md
    │   └── test-results/
    ├── bollinger_types/
    ├── tests/
    └── README.md
```

### 2.2. Artefact Organisation Principle

**Rule**: Context is organised by domain boundary.

*   **Service-specific artefacts** → `{service}/artefacts/`
    *   Example: Bugs only affecting bronze-service go in `services/bronze-service/artefacts/bugs.md`
*   **System-wide artefacts** → `/artefacts/` (monorepo root)
    *   Example: System architecture affecting all services goes in `/artefacts/architecture.md`
*   **Cross-service coordination** → `/artefacts/shared/`
    *   Example: Integration handoffs go in `/artefacts/shared/handoffs/`

### 2.3. Artefacts README

Every `artefacts/` directory — both the monorepo root and each service-level directory — shall contain a `README.md`. This file is the single-file orientation point used by agents after context compaction (see [agent-standards.md §2](agent-standards.md#2-state-recovery-after-compaction)).

**Required content:**

- **Current phase**: which workflow phase is active (e.g. `tdd-green`, `sprint-review`)
- **Active tasks**: brief list of in-progress work with task IDs
- **Recent decisions**: key choices made since the last major milestone (2–5 bullet points)
- **Blockers**: anything preventing progress
- **Key files**: pointers to the most important artefacts for the current phase

**Maintenance**: any agent completing significant work shall update the `README.md` in the relevant `artefacts/` directory before handing off. The `@documentation` agent owns the format but not the cadence — all agents write to it.

**Scope**: the root `artefacts/README.md` covers system-wide state; each `{service}/artefacts/README.md` covers that service only.

### 2.4. Service/Package Artefact Files

Each service or package shall maintain the following files in its `artefacts/` directory:

*   **`bugs.md`**: Current and past bugs (per context-framework.md format)
    *   Format: One line per bug with severity, status, scope, description (INSTEAD pattern), and blocks
    *   Example: `| BUG-001 | high | open | cache | Shared cache INSTEAD isolated per-user | TASK-005 |`
*   **`tasks.md`**: Current, past, and future tasks
    *   The project root shall be defined and all file paths shall be relative to the project root
    *   Agents do not commit — the orchestrator commits on their behalf after validating the report
    *   Each task description shall provide the necessary and sufficient context for an agent to execute the task, assuming it operates in a standalone context
*   **`todo.md`**: Technical debt and future improvements
    *   Smaller items not urgent enough for tasks.md
    *   Deferred low-priority bugs
    *   Future enhancements and optimisations
*   **`code-review.md`**: Code review findings (quality gate, created by @code-reviewer)
*   **`tech-review.md`**: Technical lead review findings (architecture compliance gate, created by @tech-lead)
*   **`test-results/`**: Test execution outputs organized by type (unit/, integration/, e2e/, security/, archive/)
*   **`fixtures/`**: Service-specific test data (optional)

### 2.5. Agent Handoff Files

The system shall maintain handoff documentation for agent coordination:

#### Service-Level Handoffs (`HANDOFF.md`)

Each service directory shall contain a `HANDOFF.md` file at its root for intra-domain coordination:

*   **Location**: `{service-directory}/HANDOFF.md`
*   **Purpose**: Track handoffs between agents working on the same context domain
*   **Format**: Use template from `/artefacts/shared/HANDOFF-TEMPLATE.md`

Required elements:
*   **Timestamp**: ISO 8601 with timezone (e.g., `2026-01-27T18:45:32Z`)
*   **From/To Agents**: Source and destination agent names with @ prefix
*   **Task IDs**: Range of tasks covered (e.g., `DS-001 through DS-008`)
*   **Status**: ✅ Complete | 🚧 In Progress | ⚠️ Blocked | 🔴 Failed
*   **Summary**: Brief description of work completed (2-3 sentences)
*   **Notes for Next Agent**: Critical information, gotchas, files to review
*   **Artifacts**: Paths to code, tests, fixtures, documentation
*   **Blockers**: Any issues preventing progress
*   **Commit Hash**: Git commit linking handoff to code changes

Example:
```markdown
### From: @functional-tester
**To**: @python-coder
**Timestamp**: 2026-01-27T18:45:32Z
**Tasks**: DS-001 through DS-008
**Status**: ✅ Complete

**Summary**: All bronze-service tests written and failing. Test coverage
includes yfinance integration, Bronze/Silver stores, cache management,
and API endpoints.

**Notes for Next Agent**:
- Test fixtures in tests/fixtures/
- Mock yfinance responses in tests/mocks/
- Expected cache behaviour documented in DS-005

**Artifacts**:
- Tests: `tests/`
- Fixtures: `tests/fixtures/`
- Tasks: `artefacts/tasks.md`

**Commit**: abc1234 - test(bronze-service): DS-001-008 add failing tests
```

#### Cross-Domain Handoffs

For coordination between services, use `/artefacts/shared/handoffs/`:

*   **Integration Status**: `/artefacts/shared/handoffs/integration-status.md`
  - Master coordination file showing readiness of all domains
  - Updated when services reach integration-ready state

*   **Service API Status**: `/artefacts/shared/handoffs/{service}-api.md`
  - Documents API endpoint stability for consumers
  - Created when endpoints are stable and ready for integration
  - Template: `/artefacts/shared/handoffs/TEMPLATE-service-api.md`

Required elements for API handoffs:
*   **Endpoint Status**: ✅ Stable | 🚧 In Development | ⚠️ Breaking Change | 🔴 Blocked
*   **Since Timestamp**: When endpoint became stable
*   **OpenAPI Reference**: Lines in openapi.yaml
*   **Example Response**: Path to fixture file in `/artefacts/shared/fixtures/`
*   **Mock Client**: Path to mock implementation in `/artefacts/shared/mocks/`
*   **Consumers**: Which services depend on this endpoint
*   **Dependencies**: Which services this endpoint depends on
*   **Known Issues**: Any bugs or limitations
*   **Breaking Changes**: Upcoming changes with ETAs

### 2.6. Archive Management

The system shall maintain archives of superseded artefacts to preserve project history whilst keeping active documentation focused and discoverable.

#### Archive Organisation

Archives shall be organised into separate directories by type:

```
/artefacts/
├── archive/                    # Gitignored: Local working notes
│   └── phase1/                # Individual contributor drafts
├── build/
│   └── archive/               # Tracked: Superseded build artefacts
│       ├── README.md          # Index of archived items
│       ├── old-reviews/       # Quality gate reviews
│       └── planning/          # Design docs, strategies
└── test-results/
    └── archive/               # Tracked: Historical test results
        ├── v2-tasks/          # Phase-specific test runs
        └── ui-bugs/           # Bug fix verification
```

**Decision: Separate Archives**

The project shall maintain two types of archives:
- **Tracked archives** (`/artefacts/build/archive/`, `/artefacts/test-results/archive/`) - Historical artefacts committed to git for team reference
- **Local archives** (`/artefacts/archive/`) - Gitignored working notes and drafts specific to individual contributors

**Rationale**: This separation supports **Lean** principles (eliminate clutter from active docs whilst preserving institutional knowledge) and **Token-Efficient** documentation (LLMs read focused, current docs; humans reference archives when needed).

#### When to Archive

Archive artefacts when:
- **Superseded by newer versions**: Architecture reviews replaced by current implementation
- **Phase completion**: Test results from completed development phases
- **Bug resolution**: Detailed bug investigation notes after fixes committed to `bugs.md`
- **Strategy implementation**: Planning documents after features go live

**Do NOT archive**:
- Current `bugs.md`, `todo.md`, `tasks.md` (active tracking)
- Integration test results (until next major version)
- Security audit findings (until remediated)
- Quality gate reviews (until next gate)

#### Archive Process

1. **Create archive subdirectory**: `mkdir -p artefacts/{area}/archive/{category}/`
2. **Move completed artefacts**: `mv old-doc.md artefacts/{area}/archive/{category}/`
3. **Create archive README.md**: Document what was archived, when, and why
4. **Commit with clear message**: `refactor(docs): archive superseded {area} artefacts`

#### Archive README Template

Each archive directory shall contain a `README.md` describing its contents:

```markdown
# {Area} Archive

**Archived**: {Date}
**Reason**: {Why these were archived}

## Contents

### {Category}/
{Description of archived items}

**Status**: {What superseded them}

## Current Replacements

Active documents that replaced archived ones:
- `architecture.md` (replaced architecture-v1-draft.md)
- `tech-review.md` (replaced pre-implementation-review.md)
```

#### Automation

Use `@documentation` agent to:
- Identify superseded artefacts based on timestamps and git history
- Generate archive README.md with references to current docs
- Update cross-references in active documents

### 2.7. Project `README.md`

The system shall maintain a `README.md` file in the root of each project. The `README.md` file shall describe:

-   The project's purpose
-   Instructions for setting up the development environment and running common commands
-   A summary of important architectural or technical decisions
-   A list of other projects or services that this project depends on
-   Location of project artefacts (e.g., "See `artefacts/` for bugs, tasks, and test results")

---

## 3. Common Context Resources

The system maintains shared standards and rules in `/context/` for use across all projects.

```
/ (monorepo root)
├── context/
│   ├── standards/           # Development standards
│   │   ├── agent-standards.md
│   │   ├── coding-standards.md
│   │   ├── context-framework.md
│   │   ├── doc-standards.md
│   │   ├── security-standards.md
│   │   ├── testing-standards.md
│   │   └── workflow-standards.md
│   └── rules/              # Development rules
│       └── EARS-notation-requirements.md
└── services/               # Projects reference context/
```

### 3.1. Common Context Resources

*   **`context/standards/`**: Development standards covering coding, testing, building, documentation, and workflow processes
*   **`context/rules/`**: Development guidelines including EARS requirements notation and TDD practices

### 3.2. Context File Quality Standards

All project context files shall be reviewed from the perspective of an expert context engineer to ensure they are:

*   **Necessary**: Each piece of information serves a clear purpose in understanding or developing the project
*   **Sufficient**: Contains all essential information needed for autonomous agent understanding and execution
*   **Token-Efficient**: Optimised for LLM consumption with minimal token usage while maintaining clarity
*   **Human-Friendly**: Easily understandable by humans without requiring specialised knowledge, avoiding unnecessary technical jargon
*   **Non-Verbose**: Concise and focused, avoiding redundancy
*   **Actionable**: Provides clear, specific guidance that enables effective decision-making and implementation

---

## 4. System-Wide Artefacts

The monorepo root `/artefacts/` directory contains system-wide artefacts that affect multiple services, organised by category:

### 4.1. Product (`/artefacts/product/`)

*   **`discovery-notes.md`**: Refined problem statement from exploratory conversations (created by @product-expert)
*   **`requirements.md`**: System-wide functional and non-functional requirements (EARS notation)
*   **`user-stories.md`**: End-to-end user stories spanning multiple services
*   **`open-questions.md`**: Unresolved questions about requirements or scope

### 4.2. Architecture (`/artefacts/architecture/`)

*   **`architecture.md`**: System architecture describing all services, their interactions, and data flow
*   **`architecture-decision.md`**: Running log of significant technical decisions (the *why* behind choices). Add an entry here whenever a non-obvious technical decision is made — choice between alternatives, discovered gotcha, or convention established. Format: numbered ADR with Date, Status, Context, Decision, Consequences.
*   **`data-model.md`**: Conceptual data model showing entities and relationships across the system
*   **`api-catalogue.md`**: Catalogue of all service APIs with their purposes and relationships
*   Other architecture documents (e.g., reliability strategies, ADRs)

### 4.3. API Specifications (`/artefacts/api/`)

*   **`openapi.yaml`**: Complete API specification for all services
*   **`api-design-guide.md`**: API design standards and conventions

### 4.4. Design System (`/artefacts/design/`)

*   **`design-system.md`**: Design system (tokens, components, accessibility, wireframes)
*   **`user-flows.md`**: User journey and flow diagrams
*   **`visuals/`**: Generated mockups and diagrams

### 4.5. Build & Project Management (`/artefacts/build/`)

Project management artefacts and quality gate decisions:

*   **`bugs.md`**: System-wide bugs affecting multiple services
*   **`tasks.md`**: Current, past, and future tasks for system-level work
*   **`todo.md`**: Technical debt and future improvements spanning multiple services
*   **`code-review.md`**: Code review findings (quality gate)
*   **`tech-review.md`**: Technical lead review findings (architecture compliance gate)
*   **`architecture-review.md`**: Architecture review findings (design gate)
*   **`test-and-fix-plan.md`**: Plans for addressing test failures or bugs

### 4.6. Test Results (`/artefacts/test-results/`)

Automated test execution outputs organized by test type:

*   **`DASHBOARD.md`**: Auto-generated at-a-glance test status (coverage, pass rates, trends)
*   **`unit/`**: Unit test results (pytest/vitest execution, coverage reports)
*   **`integration/`**: Integration test results (API tests, component tests with Testing Library)
*   **`e2e/`**: End-to-end test results (UI tests, scenarios, logs, screenshots/)
*   **`security/`**: Security test results (findings, threat model, remediation guide)
*   **`test-gaps.md`**: Cross-cutting test coverage gap analysis
*   **`archive/`**: Historical test results organized by date and type

### 4.7. Shared Resources (`/artefacts/shared/`)

*   **`handoffs/`**: Cross-service coordination files
*   **`fixtures/`**: Test data used by multiple services (e.g., `AAPL_1y.json`)
*   **`mocks/`**: Mock implementations for cross-service testing

---

## 5. Decision Criteria

When creating a new artefact, apply these rules:

**Q1**: Is this artefact only relevant to one service/package?
- ✅ YES → Put in `{service}/artefacts/`
- ❌ NO → Continue to Q2

**Q2**: Does this artefact describe system-wide architecture/contracts?
- ✅ YES → Put in root `/artefacts/`
- ❌ NO → Continue to Q3

**Q3**: Is this artefact for coordination between services?
- ✅ YES → Put in `/artefacts/shared/`
- ❌ NO → Re-evaluate Q1-Q3

**Q4**: Is this a standard/rule for developers to follow?
- ✅ YES → Put in `/context/standards/` or `/context/rules/`
- ❌ NO → It's an output, use artefacts per Q1-Q3

---

## 6. Diagram Standards

### 6.1. Prefer Mermaid

Use Mermaid notation for all diagrams. Renders natively in GitHub, GitLab, Notion.

**Diagram Types:**

| Type | Use For | Syntax Start |
|------|---------|--------------|
| flowchart | Workflows, processes | `flowchart TD` |
| sequenceDiagram | API calls, interactions | `sequenceDiagram` |
| stateDiagram-v2 | State machines | `stateDiagram-v2` |
| erDiagram | Data models | `erDiagram` |
| classDiagram | Class hierarchies | `classDiagram` |

**Example:**
```mermaid
flowchart TD
    A[Input] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[Other]
```


**Exceptions:**
- Inline code where ASCII is the code itself
- Terminal output representations
- Simple one-liners: `A → B → C`

---

## 7. Writing Quality Standards

### 7.1. Avoid AI Slop Patterns

**Patterns to Avoid:**

| Pattern | Example | Fix |
|---------|---------|-----|
| Em dash overuse | text — more text — even more | Use colons, semicolons, or split sentences |
| Triads | "fast, efficient, reliable" | Vary list lengths |
| Vapid transitions | "Furthermore", "Moreover" | Cut or be specific |
| Empty preambles | "In this section we will..." | Start with content |
| Hedging | "It's important to note that" | Just state the thing |
| Generic analogies | Vague metaphors | Use concrete examples |
| Monotonous rhythm | Same sentence length | Vary length |

**Self-Check Before Submitting:**
- No em dashes (use commas/semicolons)
- No three-beat patterns
- No filler transitions
- Every sentence adds value
- Varied sentence length
- Specific examples, not vague claims

**Core Test:** Human writing has intent behind every choice. If removing a sentence loses nothing, remove it.

---

## 8. Documentation Maintenance

### 8.1. Automated Integrity Checks

CI validates cross-file references on PR to main.

**Check Scope:**
- Parse: README.md, tasks.md, bugs.md, context/*
- Validate refs: `[tasks.md#L25](./tasks.md#L25)`
- Verify target exists, line in bounds

**Enforcement:** Broken ref → CI fails → Fix before merge.

### 8.2. Long-form documents (`context/docs`)

Strategic papers and long catalogue references under `context/docs/` (for example Vision, Journey, Roadmap, framework reference) shall carry **maintained metadata** immediately after the H1:

- `**Document Status**` (for example Draft, Approved)
- `**Version**` — a [Semantic Versioning 2.0.0](https://semver.org/) version number: `MAJOR.MINOR.PATCH` (three non-negative integers; each component without leading zeros, as defined in the spec). This is not used like a package dependency range; it communicates how much the document's commitments changed. Treat the published Markdown (headings, normative guidance, revision history) as the versioned public surface, analogous to a declared API in the SemVer introduction.
- While status remains Draft (or another explicitly unstable label), keep `MAJOR` at `0` (initial development: anything may change, per the spec). Prefer `0.1.0` as the first published version, then:
  - increment **PATCH** for typographical fixes, link repairs, formatting, or clarifications that do not change meaning or structure;
  - increment **MINOR** and reset **PATCH** to `0` for new sections, reorganisation, new normative guidance, or other substantive edits;
  - when the document is promoted to a stable baseline (for example Approved), set `1.0.0` and continue with SemVer semantics for later incompatible vs compatible changes to that baseline.
- Legacy metadata that used two segments only (for example `0.16`) shall be read as `0.16.0` until the line is updated to three segments.
- `**Last Updated**` — calendar date in British English long form (for example `13 April 2026`) or ISO 8601 (`2026-04-13`)
- Optional: `**Word Count**`, `**Reading Time**`, `**Companion**` (path to a paired document)

End each metadata line with two spaces so Markdown renderers break lines between fields.

Include a terminal `## Revision History` section with a table: Version, Date, Author, Changes. The **Version** column shall use the same `MAJOR.MINOR.PATCH` form. Dates in the table shall use ISO 8601 (`YYYY-MM-DD`) for sortability. When the document is also rendered through Typst, wrap the revision table in `<!-- typst-skip-start -->` and `<!-- typst-skip-end -->` so export tooling can omit boilerplate.

### 8.3. UX/UI Documentation Standards

**Component Documentation:**
- Include state variations (default, hover, focus, error, loading, disabled)
- Document responsive breakpoints
- Specify accessibility requirements (ARIA labels, keyboard navigation)
- Provide usage examples with code snippets

**Design System Documentation:**
- Maintain design tokens in `artefacts/design/design-system.md` (section 1, section 1.6)
- Document component relationships and dependencies
- Include visual examples (screenshots or Mermaid diagrams)
- Specify when to use vs when not to use each component

**User Flow Documentation:**
- Use Mermaid sequence diagrams or flowcharts
- Show happy path and error cases
- Document decision points and branching logic
- Include user feedback and loading states
