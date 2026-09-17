# Tasks: {Feature Name}

---

## Header

Every task file begins with structured metadata:

```markdown
**Branch**: `{branch-name}`
**Status**: Planning | In Progress | Complete
**Scope**: {1–2 sentence summary of what the feature delivers}
**Design**: {path to design doc, or "N/A"}
**Created**: {YYYY-MM-DD}
**Amended**: {YYYY-MM-DD — brief summary of changes}
```

Update **Status** as the feature progresses. Update **Amended** whenever the task file is revised after creation.

---

## Format

Two formats are used depending on the scope of the task file:

### Task Index (required)

The task index is the single source of truth for task status. **Update status immediately** when
a task transitions — do not batch status updates.

- **Pri**: critical, high, medium, low
- **Status**: pending, in_progress, blocked, completed
- **Blocked By**: task/bug IDs or `-` if none

| ID | Pri | Status | Blocked By | Task |
|----|-----|--------|------------|------|
| TASK-001 | critical | completed | - | {description} |
| TASK-002 | high | in_progress | TASK-001 | {description} |
| TASK-003 | medium | pending | TASK-001 | {description} |

**Every task in the index must have a matching `### TASK-ID:` specification section** with
acceptance criteria. Tasks without specifications cannot be dispatched.

### Checklist format — sprint-based feature task tracking

For multi-sprint feature build docs (e.g., `tasks-{sprint-name}.md`), use `[ ]` / `[x]` checkboxes on
every actionable item so progress is visible at a glance. Rules:

- Every actionable line item begins with `- [ ]` (pending) or `- [x]` (done)
- Task headings also use checkboxes: `### - [ ] Task X-1: Description`
- Phase gates and review approvals also use checkboxes
- Mark `[x]` immediately when the item is confirmed complete — do not batch at end of sprint
- Sprint-level status in the file header (`**Status**: Planning | In Progress | Complete`)
  reflects the overall sprint, not individual items

```markdown
### - [ ] S1-1. Example task group

- [ ] First action item
- [ ] Second action item
- [x] Already completed item

### S1 Sprint Review

- [ ] @code-reviewer approved
- [ ] @security-tester approved
```

---

## Orchestrator Notes

Include an `## Orchestrator Notes` section after the header for multi-task sprints. This tells
the orchestrator how to dispatch work without it having to infer the strategy from the task
dependency graph.

### Parallelism Strategy

Identify independent sprints and the dispatch sequence. Use a concrete dispatch plan.

**Terminology**: use "sprint" for parallel groupings (Sprint 1, Sprint 2). Do not mix in
"wave", "track", "phase", or "batch" — keep to standard agile terminology.

For tasks with both Python and TypeScript streams, specify the full dispatch chain including
TypeScript RED/GREEN phases — do not omit TypeScript work from the dispatch plan.

Include `file_scope` per parallel group so the orchestrator can verify disjoint scopes before
dispatching (see `agent-standards.md` §6.4).

```markdown
### Parallelism Strategy

**Sprint 1** (critical path): T-1 → T-2 + T-3 (parallel) → T-4
  file_scope: services/bronze-service/
**Sprint 2** (independent):  T-5 → T-6
  file_scope: services/mq-service/

Dispatch 1 — spawn simultaneously:
  @functional-tester → T-1 RED
  @functional-tester → T-5 RED

After T-1 RED, dispatch 2:
  @python-coder → T-1 GREEN-py
  @functional-tester → T-1 RED-ts (if TypeScript stream)
  @typescript-coder → T-1 GREEN-ts (after RED-ts)
```

### Commit Strategy

Define commit granularity and message format upfront. One commit per task is the default.
Agents do not commit — they write a commit message to `/tmp/{task-id}_commit_msg.txt` and
report the file list. The orchestrator commits and pushes on their behalf (see `agent-standards.md` §4.4).

Push cadence: the orchestrator pushes immediately after each commit (commit & push per task) to protect from accidental deletion.

```markdown
### Commit Strategy

One commit per task, on the `{branch}` branch. Commit messages follow conventional commits:

| Task | Commit message |
|------|---------------|
| T-1 | `type(scope): description` |
| T-2 | `type(scope): description` |

Push after: every commit (immediate push to remote).
```

Additional guidance to include when relevant:
- **TDD discipline**: RED test commits will have failing tests — do NOT squash RED and GREEN
  into one commit; the two-commit pattern preserves TDD discipline in git history
- **Folded backlog items**: If a task folds in backlog items, the commit body should list them
- **Multi-step tasks**: If a single task touches multiple services, note whether it's one
  commit or split per service

### Effort Estimates

Include a token-based effort estimate per task:

```markdown
### Effort Estimates

| Task | Agent(s) | Effort |
|------|----------|--------|
| T-1 | solution-architect | Medium (30–50k tokens) |
| T-2 | python-coder | Large (60–90k tokens) |
| **Total** | | **~90–140k tokens** |
```

Token ranges: Small (10–30k), Medium (30–80k), Large (80–150k), XLarge (150k+).

### Backlog Cleanup

During task review, scan `artefacts/build/todo.md` for items that overlap with files or
services the sprint already touches. Items that can be completed with little additional effort
should be folded into the relevant task rather than left for a separate sprint.

After the sprint, list all resolved backlog items so todo.md is updated:

```markdown
### Backlog Cleanup

After all tasks complete, update `artefacts/build/todo.md`:
- **ITEM-001**: mark DONE (resolved in T-3)
- **ITEM-002**: remains TODO — related but out of scope
```

---

## Metrics Flow

```
session-log.jsonl  →  Per-turn (source of truth)
    ↓ aggregate
tasks.md           →  Per-task (this file)
    ↓ aggregate
git commit         →  Per-commit (Agent-Session line)
    ↓ aggregate
PR description     →  Per-PR rollup
```
