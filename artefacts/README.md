# Artefacts Directory

System-wide outputs representing completed work across discovery, design, development, and testing.

---

## Quick Reference

| Category | Location | Typical Files | Primary Agents |
|----------|----------|---------------|----------------|
| **Product** | `product/` | `requirements.md`, `user-stories.md`, `open-questions.md` | `@product-expert`, `@product-owner` |
| **Architecture** | `architecture/` | `architecture.md`, `data-model.md`, `api-catalogue.md` | `@solution-architect`, `@database-designer` |
| **API** | `api/` | `openapi.yaml`, `api-contract.json`, `api-design-guide.md` | `@api-designer` |
| **Design** | `design/` | `design-tokens.json`, `components.md`, `user-flows.md`, `visuals/` | `@ui-designer` |
| **Build & Tasks** | `build/` | `tasks.md`, `todo.md`, `bugs.md`, quality gate reviews | `@orchestrator`, `@tech-lead`, `@code-reviewer` |
| **Test Results** | `test-results/` | `DASHBOARD.md`, `unit/`, `integration/`, `e2e/`, `security/` | `@functional-tester`, `@ui-tester`, `@security-tester` |
| **Cross-Service** | `shared/` | `handoffs/`, `fixtures/`, `mocks/` | All agents |

---

## For Agents

**Quick scan** - Locate relevant artefacts by workflow phase:

- **Discovery & Requirements**: [requirements](product/requirements.md) · [user-stories](product/user-stories.md) · [open-questions](product/open-questions.md)
- **Architecture & Data**: [architecture](architecture/architecture.md) · [data-model](architecture/data-model.md) · [api-catalogue](architecture/api-catalogue.md)
- **API Contracts**: [openapi](api/openapi.yaml) · [contract](api/api-contract.json) · [design-guide](api/api-design-guide.md)
- **UI & UX**: [tokens](design/design-tokens.json) · [components](design/components.md) · [user-flows](design/user-flows.md) · [accessibility](design/accessibility.md) · [wireframes](design/wireframes.md)
- **Task Tracking & Gates**: [tasks](build/tasks-align-framework.md) · [todo](build/todo.md) · [incidents](build/agent-incidents.md)
- **Test Outcomes**: [coverage-gaps](test-results/test-coverage-gaps.md) · [functional-tests](test-results/functional-tests.json)
- **Coordination**: [shared-handoffs](shared/handoffs/) · [shared-fixtures](shared/fixtures/) · [shared-mocks](shared/mocks/)

---

## Directory Structure

```
artefacts/
├── README.md                      # This file (quick search index)
├── product/                       # Requirements, user stories, discovery notes
│   ├── requirements.md            # System requirements (EARS notation)
│   ├── user-stories.md            # End-to-end user journeys
│   └── open-questions.md          # Open requirements or scope questions
├── architecture/                  # Macro system design, data topology, ADRs
│   ├── architecture.md            # System topology and service interactions
│   ├── data-model.md              # Conceptual data model and entity relations
│   ├── api-catalogue.md           # Service API registry and ownership
│   └── architecture-decision.md   # Architectural Decision Records (ADRs)
├── api/                           # Formal API interface contracts
│   ├── openapi.yaml               # Canonical OpenAPI 3.x specification
│   ├── api-contract.json          # Machine-readable schemas and payloads
│   └── api-design-guide.md        # API design conventions and headers
├── design/                        # UI/UX design specifications and assets
│   ├── design-tokens.json         # Tokens (colors, typography, spacing)
│   ├── components.md              # Component specs and state variations
│   ├── accessibility.md           # WCAG criteria and keyboard/ARIA patterns
│   ├── user-flows.md              # User interaction and state flowcharts
│   ├── wireframes.md              # Screen layout wireframes
│   ├── visuals-manifest.md        # Visual asset inventory
│   └── visuals/                   # Visual exports and rendered diagrams
├── build/                         # Project management and quality reviews
│   ├── tasks.md                   # Task specs (or phase tasks like tasks-*.md)
│   ├── todo.md                    # Technical debt and deferred items
│   ├── bugs.md                    # Cross-cutting defects (INSTEAD pattern)
│   ├── code-review.md             # Code review gate findings
│   ├── tech-review.md             # Technical lead architecture compliance
│   ├── architecture-review.md     # Design review gate evaluations
│   ├── agent-incidents.md         # Agent failure logs and remediation records
│   └── archive/                   # Tracked historical build plans and reviews
├── test-results/                  # Test execution logs and coverage analyses
│   ├── DASHBOARD.md               # Summary metrics (pass rates, coverage)
│   ├── test-coverage-gaps.md      # Gap analysis and missing scenarios
│   ├── functional-tests.json      # Machine-readable test execution report
│   ├── unit/                      # Unit test outputs
│   ├── integration/               # API and multi-component test outputs
│   ├── e2e/                       # Browser automation logs and screenshots
│   ├── security/                  # Security test findings and scans
│   └── archive/                   # Tracked historical test results
├── shared/                        # Cross-service coordination assets
│   ├── handoffs/                  # Integration readiness and endpoint status
│   ├── fixtures/                  # Common test fixtures across services
│   └── mocks/                     # Reusable mock clients and servers
└── archive/                       # Gitignored local contributor drafts
```

---

## Where to Place Files

Detailed decision criteria and standards reside in `context/standards/doc-standards.md`.

- **System-wide**: Root `/artefacts/{category}/`
- **Service-specific**: Project subfolder `{service}/artefacts/` (e.g., `services/bronze-service/artefacts/`)
- **Cross-service coordination**: Root `/artefacts/shared/`
- **Standards & rules**: Root `/context/standards/` or `/context/rules/`
- **Superseded artefacts**: Move to tracked `{category}/archive/` subdirectories rather than deleting

---

## See Also

- **Documentation Standards**: `context/standards/doc-standards.md` - Complete organisation rules and templates
- **Orchestration Guide**: `AGENTS.md` - Workflow phases, quality gates, and agent definitions
- **Context Index**: `context/README.md` - Standards, rules, workflows, and templates
