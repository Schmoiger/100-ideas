# Context Framework

**Status**: Draft — under development, not yet enforced.

**Principle**: Context is the primary output of agents. Code is a side effect. If an agent produces good code but poor context, the next agent (or human) wastes effort rediscovering what was already known.

---

## Context Types

All context falls into two categories based on whether it drives action.

### Reference Context (Read-Only)

Information that is consulted but not actioned. It doesn't change during a phase and doesn't need prioritisation.

| Context | Location | Purpose |
|---------|----------|---------|
| Architecture decisions | `artefacts/architecture/` | How the system is designed |
| Requirements | `artefacts/product/requirements.md` | What to build |
| API contracts | `artefacts/api/openapi.yaml` | Interface agreements |
| Standards and rules | `context/standards/`, `context/rules/` | How to work |
| Existing code | Service directories | What already exists |

**Characteristics**: Stable within a phase. Changed by design decisions, not by implementation work. Agents read it at the start of a task and refer back as needed.

### Actionable Context (Drives Work)

Information that requires someone to do something. It changes during execution and needs prioritisation because agents and humans have finite attention.

| Context | Location | Purpose |
|---------|----------|---------|
| Tasks | `artefacts/build/tasks.md` | What to build next |
| Bugs | `artefacts/build/bugs.md` | What's broken |
| Review findings | `artefacts/build/*-review.md` | What to fix or approve |
| Test results | `artefacts/test-results/` | What passed or failed |
| Handoff notes | `artefacts/build/*-handoff.md` | What the next agent needs |

**Characteristics**: Mutable. Created and consumed during execution. Needs priority, status, and ownership to be useful.

---

## Sharing Formats

Context is shared in two directions, each with different consumers and therefore different formats.

### Agent-to-Agent: Structured Data (JSON)

When the consumer is another agent, optimise for parseability and precision. No prose, no formatting — just fields with controlled vocabularies.

**Use JSON when**:
- The receiving agent needs to filter, sort, or extract specific values
- Fields have controlled vocabularies (status, priority, severity)
- The handoff is a phase transition (tdd-red to tdd-green, review to fix)
- There's no ambiguity that requires narrative explanation

**Structure**: Every agent-to-agent handoff should include:
- Who it's from and to
- What phase transition it represents
- An ordered list of actionable items with priority and status
- Gotchas or constraints the receiving agent needs to know

### Agent-to-Human: Narrative + Structure (Markdown)

When the consumer is a human (who may also be an agent reading over their shoulder), optimise for scannability and decision support.

**Use Markdown when**:
- The context needs reasoning or trade-off explanations
- Decisions are needed from the human
- The output is a report, review, or summary
- Both humans and agents will read it

**Structure**: Every agent-to-human report should include:
- A summary (what happened, what state we're in)
- A prioritised table of items needing attention
- A "decisions needed" section if anything is blocked on human input
- Enough context for the human to make a decision without reading source files

### When You Need Both

Some handoffs serve both audiences — an agent needs the structured data, and a human needs the narrative. In this case, produce both:
- A JSON handoff file for the consuming agent
- A Markdown summary for the human/orchestrator

Don't try to make one format serve both purposes. JSON with embedded prose is hard to parse. Markdown with embedded JSON is hard to read.

---

## Prioritisation Framework

All actionable context needs prioritisation. The same four levels apply everywhere, but their meaning shifts depending on the consumer.

### Priority Levels

| Level | Agent reads as... | Human reads as... |
|-------|------------------|-------------------|
| Critical | Must do before anything else; blocks phase exit | Needs your attention now; broken or blocked on you |
| High | Do before quality gate; important dependency | Should review soon; significant decision or risk |
| Medium | Planned work, do in order | FYI; will proceed unless you intervene |
| Low | Do if time permits; skip if time-boxed | No action needed; logged for awareness |

### Priority Assignment

Priority is assigned by the **producing agent** based on impact and dependencies:

- **Critical**: Without this, the current phase cannot complete
- **High**: Without this, the next quality gate will fail
- **Medium**: Planned work that contributes to phase completion
- **Low**: Nice-to-have, deferrable without impact

### Priority Inheritance

If a low-priority item blocks a higher-priority item, it inherits the higher priority. A normal-priority task that blocks a critical task becomes critical — the dependency chain is only as fast as its slowest link.

### Priority Escalation

Review agents (`@tech-lead`, `@code-reviewer`, `@security-tester`) may escalate priority or severity if they judge the impact to be higher than originally assessed. Escalation should include a reason. De-escalation follows the same rule.

### Phase Exit Criteria

Priority and severity determine whether work blocks phase progression.

| Phase Exit | Task Requirement | Bug Requirement |
|-----------|-----------------|-----------------|
| TDD RED | All critical tasks complete | N/A (no production code yet) |
| TDD GREEN | All critical/high tasks complete | Zero critical/high bugs |
| Tech Review | Review tasks complete | Zero critical bugs |
| Code Review | Review tasks complete | Zero critical/high bugs |
| Verification | Test tasks complete | Zero critical bugs; medium/low documented |
| Deployment | All critical/high tasks complete | Zero critical bugs; medium/low accepted or deferred |

---

## Work Item Types

Three types of actionable context exist. Each has different origins, lifetimes, and tracking rules.

### Tasks — Planned Work

Tasks are work items derived from requirements, design decisions, or review findings. They belong to a workflow phase and have an assignee.

**Status lifecycle**: `pending` → `in_progress` → `blocked` → `completed`

**Format**: One line per task in a markdown table. Terse but sufficient — an agent should be able to start work from the task line plus reference context (requirements, tests, architecture docs).

```markdown
| ID | Pri | Status | Phase | Assignee | Blocked By | Description |
|----|-----|--------|-------|----------|------------|-------------|
| TASK-001 | critical | completed | tdd-red | @functional-tester | - | Write failing tests for auth service |
| TASK-002 | high | in_progress | tdd-green | @python-coder | TASK-001 | Implement login endpoint (REQ-005) |
| TASK-003 | normal | pending | tdd-green | @python-coder | TASK-001 | Implement token refresh (REQ-006) |
| TASK-004 | low | pending | tdd-green | @python-coder | - | Add structured logging to auth |
```

**Description convention**: Use imperative mood. Include the requirement or test ID in parentheses when the task traces to a specific item. This gives the agent a pointer to reference context without duplicating it.

**Agent behaviour**:
- Always pick the highest-priority unblocked task in your phase
- If multiple tasks share the same priority, work in ID order (lowest first)
- Mark `blocked` with a reason if you can't proceed
- Don't self-assign low-priority tasks while high-priority ones exist in the phase

### Bugs — Unplanned Defects

Bugs are defects discovered during testing, review, or implementation. They are unplanned and need triaging by severity.

**Status lifecycle**: `open` → `in_progress` → `fixed` | `wont_fix` | `deferred`

**Format**: One line per bug. Descriptions use the **INSTEAD pattern**: `[observed behaviour] INSTEAD [expected behaviour]`. This gives the fixing agent both the symptom and the target in a single line.

```markdown
| ID | Sev | Status | Scope | Assigned To | Description | Blocks |
|----|-----|--------|-------|-------------|-------------|--------|
| BUG-001 | critical | open | auth | @python-coder | Login returns 500 INSTEAD 200 with token | TASK-005 |
| BUG-002 | high | in_progress | auth | @python-coder | Expired token returns 200 INSTEAD 401 | - |
| BUG-003 | medium | open | frontend | @typescript-coder | Error toast shows raw JSON INSTEAD user message | - |
| BUG-004 | low | deferred | frontend | - | Button alignment off by 2px on Safari | - |
```

**Severity levels**:

| Severity | Meaning | Example |
|----------|---------|---------|
| Critical | System broken, no workaround; data loss or security risk | Tests won't run, build fails, auth bypass |
| High | Major functionality broken, workaround exists | Auth fails for edge case, performance regression |
| Medium | Minor functionality broken, low user impact | Wrong validation message, UI glitch |
| Low | Cosmetic, edge case, or deferred tech debt | Inconsistent spacing, unused import warning |

**Agent behaviour**:
- Critical/high: fix before phase can progress (blocking)
- Medium: fix before the next quality gate
- Low: log for later, don't block the current phase
- The agent that finds a bug files it; the orchestrator assigns it to the fixer

### TODOs — Inline Reminders

TODOs are implementation notes within code. They exist to help the current agent track work within a single session.

**Rules**:
- Scope: single file, single agent session
- Lifetime: resolved before commit, or converted to a task or bug
- Format: `// TODO(agent-name): description`

**Conversion rules** — every TODO must be resolved before commit:

| If the TODO is... | Then... |
|-------------------|---------|
| A defect | File as bug, remove the TODO |
| Work spanning multiple sessions | Create task, remove the TODO |
| Finishable in this session | Do it now, remove the TODO |

**Anti-patterns**:
- `// TODO: fix this later` — no owner, no timeline, no conversion
- `// TODO: maybe refactor?` — vague; create a task or delete it
- TODOs surviving multiple commits — should have been converted

---

## Terse Formats

Actionable context should be as compact as possible while remaining sufficient for the consuming agent or human to act. Token cost matters — verbose context wastes agent budget and human attention.

### Principles

- **One line per item**: Tasks and bugs each fit in a single table row. If you can't describe it in one line, the item is too broad — split it.
- **Reference, don't duplicate**: Include requirement/test IDs in task descriptions so agents can look up detail. Don't copy requirement text into tasks.
- **Structured over narrative**: Tables and controlled vocabularies for actionable items. Save prose for summaries, trade-offs, and decisions.
- **Compress reference context too**: Requirements, user stories, and open questions benefit from table formats. Use legends for repeated values (`M` = MVP, `✓` = complete).

### One Line — Is It Enough?

Yes, if two conditions are met:

1. **The line contains structured fields** (ID, priority, status, assignee, blocked-by) so the reader can triage without reading the description.
2. **The description points to reference context** (requirement ID, test file, component name) so the agent can find detail when it needs it.

A task line like `Implement login endpoint (REQ-005)` is sufficient because the agent reads `REQ-005` from `requirements.md` and reads the failing tests from `tests/`. The task line tells it *what to do and where to look* — not *how to do it*.

A bug line like `Login returns 500 INSTEAD 200 with token` tells the fixing agent the symptom, the expectation, and where to start. It doesn't need a reproduction script in the table — the agent reads the test or endpoint.

---

## Context Quality

Good context is scannable, actionable, and doesn't waste the reader's attention.

### What Makes Context Good

- **Prioritised**: Most important items first. Don't make the reader triage.
- **Minimal**: Include what the consumer needs, nothing more. Reference context lives in its canonical location; don't copy it into handoffs.
- **Actionable**: Every item in actionable context has a clear next step and owner.
- **Honest about unknowns**: Flag what you don't know or couldn't verify. "I didn't check X" is more useful than silence.

### Anti-Patterns

| Anti-Pattern | Why It's Bad | Do Instead |
|-------------|-------------|------------|
| Dumping everything into one document | Reader can't find what matters | Separate reference from actionable; prioritise actionable items |
| Copying reference context into handoffs | Duplication, drift, wasted tokens | Reference by path; the reader can look it up |
| Flat lists with no priority | Reader must triage; agents may pick wrong task | Assign priority; sort by it |
| Narrative where structure is needed | Agent can't extract values; human must re-read | Use JSON for agent-to-agent; tables for agent-to-human |
| Structure where narrative is needed | Missing trade-offs, reasoning, gotchas | Add a summary section explaining decisions and constraints |
| Orphaned TODOs | Invisible to orchestration; never addressed | Convert before commit |
| Missing "decisions needed" section | Human doesn't know what's blocked on them | Explicitly flag items requiring human input |
| Verbose multi-line task descriptions | Wastes tokens, buries the signal | One line per item; reference context by ID |

---

## External Blockers

Items blocked by external dependencies (user input, third-party API, infra provisioning) are not tasks or bugs — they're **context items shared with humans**. The human needs to know what's waiting on them.

Track external blockers as TODOs in the agent-to-human report's "Decisions Needed" section. They don't belong in the task or bug table because no agent can act on them — only a human can unblock them.

If an external blocker prevents a task from proceeding, mark the task as `blocked` and note the reason. The orchestrator surfaces it to the human.

---

## Templates

Handoff templates (JSON for agent-to-agent, MD for agent-to-human) live in `context/templates/` alongside the task prompt template. This document defines the principles; the templates provide the concrete format.

---

## Superseded Documents

This framework supersedes the following documents:

| Document | Disposition |
|----------|------------|
| `context/standards/bug-standards.md` | Folded in — bug format, INSTEAD pattern, severity levels, and agent behaviour are now covered here |
| `context/standards/COMPRESSED-FORMATS.md` | Folded in — terse format principles and one-line-per-item guidance are now covered here. Specific compressed formats for requirements, user stories, and open questions remain useful as reference but are not enforced by this framework. |
