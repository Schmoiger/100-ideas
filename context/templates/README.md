# Templates

Reusable formats for artefacts produced during development.

**How template selection works**: the orchestrator consults this index when constructing a task prompt, identifies the appropriate template for the expected output, and references it explicitly in the task prompt. Agents do not select templates independently — they use whichever template the task prompt specifies.

---

## Template Index

| Template | Output type | Output location |
|----------|-------------|-----------------|
| `requirements-template.md` | EARS-format requirements | `artefacts/product/requirements.md` |
| `user-stories-template.md` | User stories | `artefacts/product/user-stories.md` |
| `tasks-template.md` | Task tracking | `artefacts/build/tasks.md` |
| `bugs-template.md` | Bug tracker | `artefacts/build/bugs.md` |
| `review-template.md` | Tech or code review | `artefacts/build/{tech,code}-review.md` |
| `test-dashboard-template.md` | Test results dashboard | `artefacts/test-results/dashboard.md` |
| `handoff-template.md` | Agent handoff state | `artefacts/build/HANDOFF.md` |
| `commit-message-template.md` | Git commit message | git commit |
| `pr-description-template.md` | Pull request description | GitHub PR body |
| `domain-rules-template.yaml` | Domain-specific rules and blockers | `services/{domain}/context/domain-rules.yaml` |
| `architecture-template.md` | System architecture reference | `artefacts/architecture/architecture.md` |
| `design-template.md` | Feature design document | `artefacts/design/design-{feature}.md` |
| `agent-template.md` | New agent definition | `context/agents/{name}.md` |
| `task-prompt-template.md` | Agent task prompt (orchestrator use only) | — |
| `settings-local-template.json` | Claude Code / local runtime permissions | `.claude/settings.local.json` |

---

## Format Notes

**Local Settings** — copy to `.claude/settings.local.json` to configure autonomous command permissions (Git, `uv`, `yarn`, test runners) conforming to `bash-environment.md` without triggering manual prompt friction.

**Handoffs** — keep summary under 500 characters; reference shared artefacts rather than duplicating content.

**Reviews** — issue format: `**ID** \`file:line\` Problem. → Fix.` Severity: critical / high / medium / low.

**Architecture** — use `architecture-template.md` for the system-level reference. One per project. Describes what IS built (present tense), not what will be built. Inline HTML comments mark optional sections for microservice vs monolith projects.

**Design** — use `design-template.md` for per-feature design documents. One per complex feature or screen. Update status to "Current (as-built)" after implementation. Separation from architecture: architecture describes the system; design describes a feature within it.

---

## Naming

Templates use a `-template.{ext}` suffix. Generated files drop the `-template` suffix (e.g. `review-template.md` → `tech-review.md`).
