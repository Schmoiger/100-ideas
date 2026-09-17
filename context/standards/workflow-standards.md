# Technology Development Workflow

---

## Overview

The developer workflow follows a structured approach to ensure quality and consistency across all projects.

---

## 1. Create Git Branch

Create and switch to a new feature branch following the branch naming conventions. Add gitignore that inherits monorepo gitignore (see `README.md`)

**Branch Naming:**

- `feature/feature-name` for new features
- `bugfix/bugref-name` for bug fixes

**Commands:**

```bash
git checkout -b feature/feature-name
git push -u origin feature/feature-name
```

---

## 2. Project Setup

Set up project folder with blank files according to documentation standards.

**Files to create:**

- `/artefacts/requirements.md` - Requirements specification (system-wide)
- `/artefacts/architecture.md` - Architecture and design specification (system-wide)
- `{service}/artefacts/tasks.md` - Task breakdown (service-specific)
- README.md and other project files as per standards

---

## 3. Write Specifications

Write the specs documents in this order:

1. **Requirements** (`/artefacts/requirements.md`)
  - Detail functional and non-functional requirements using EARS notation
  - Specify acceptance criteria and constraints
2. **User Stories** (`/artefacts/user-stories.md`)
  - Define end-to-end user stories spanning multiple services
  - Identify key stakeholders and success criteria
3. **Architecture** (`/artefacts/architecture.md`)
  - Outline technical architecture and design decisions
  - Define data models, APIs, and service interactions

---

## 4. Check Specs Against Standards

Validate all specifications against the following standards:

- **Documentation Standards** (`/context/standards/`)
  - Ensure consistency with existing patterns
  - Verify adherence to formatting and structure guidelines
- **Technical Standards** (`/context/standards/tech-standards.md`)
  - Confirm technical decisions align with approved patterns
  - Validate architectural choices

---

## 5. Write Tasks

Break down the specifications into actionable development tasks in `{service}/artefacts/tasks.md` (service-specific).

**Task Structure:**

- Clear, measurable objectives
- Estimated effort and dependencies
- Acceptance criteria
- References to relevant specification sections

---

## 6. Check Tasks Against Rules

Validate tasks against the established rules and guidelines:

- **Development Rules** (`/context/rules/`)
  - Ensure tasks comply with coding standards
  - Verify testing requirements are included
  - Confirm security considerations are addressed
- **Quality Gates**
  - Unit testing plans
  - Integration testing requirements
  - Code review criteria
  - Deployment readiness checklists

---

## 7. Update Documentation

Update both project and monorepo-level documentation to reflect completed work.

**Project Documentation:**

- `README.md` - Update with implementation details, usage guides, and deployment instructions
- `{service}/artefacts/` - Update bugs, tasks, todo, test results, and fixtures
- Configuration files documentation

**Monorepo Documentation:**

- `README.md` - Update workspace description
- `/artefacts/` - Update system-wide artefacts (architecture, API contracts, requirements)


---

## Assumption Handling Protocol

### Escalation and Assumptions

See `context/rules/escalation.md` for the authoritative escalation model:

- **Decision matrix**: impact × confidence → assume / flag / escalate
- **Impact classification**: distinguishes scope deferrals (low) from operational deferrals (high)
- **Two-tier triage**: subagent → orchestrator (resolve or forward) → human
- **Logging**: escalations are logged to `artefacts/build/agent-interruptions.md`

Document assumptions in handoff with decision, confidence, rationale, and impact if wrong.

---

## Continuous Improvement

Framework improvement uses the `continuous-improvement` workflow with two modes:

- **Incident mode**: human reports a specific failure → diagnose root cause → fix → record in `agent-incidents.md` and `tasks-context-framework.md`
- **Retrospective mode**: review `agent-interruptions.md`, `agent-incidents.md`, and git log `Agent-Session` metrics → identify patterns → discuss with human → fix → record

See `context/workflows/continuous-improvement.yaml` for the full phase definitions.

---

## Communication Style

### Teaching Engineer Persona

When working with users, adopt an expert engineer teaching a novice:
- Suggest improvements, simplifications, and optimisations
- Explain clearly and simply
- Provide rationale for decisions
- Offer learning opportunities

---

## 8. Orchestrator Agent Invocation

Use `context/templates/task-prompt-template.md` when spawning subagents. The template ensures Rule Resolution and File Scope Assignment are included.

**Key points:**
- Agents do not commit — they lint, write a commit message to `/tmp/{task-id}_commit_msg.txt`, and report back with file list + message path
- The orchestrator commits and pushes on their behalf (format → stage → commit → push, one at a time to protect from accidental deletion)
- The orchestrator adds `duration=`, `dispatch=`, `interactions=`, `approvals=` to the Agent-Session line; `tokens=` is injected by the `prepare-commit-msg` hook
- The orchestrator verifies the Agent-Session line is present before committing — see `context/skills/agent-workflows.md` for the Commit Procedure
- See `context/agents/orchestrator.md` for Rule Resolution, File Scope, and Context Budget Test

### Token Metrics

Token usage is captured automatically — agents do not self-report.

**Data source**: Claude Code writes session JSONL files to `~/.claude/projects/` with exact token counts per API call (`input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`).

**Collection**: A `prepare-commit-msg` git hook (`context/scripts/prepare-commit-msg.py`) runs at commit time:

1. Derives the Claude Code project directory from `git rev-parse --show-toplevel` (portable across repos)
2. Finds the active session (most recently modified session directory)
3. Sums tokens across all JSONL files (orchestrator + subagents)
4. Reads a watermark file (`.tokens-watermark` in the session directory) to compute the delta since the last commit
5. Appends `tokens=<in>K/<out>K` to the `Agent-Session:` line in the commit message
6. Updates the watermark for the next commit

**What the numbers mean**: input tokens are everything sent to the model (prompt, context, tool results); output tokens are everything generated (responses, tool calls, code). Input is typically much larger because agents read heavily to produce concise output.

**Commit message format**: agents author the triplet, the orchestrator adds remaining fields, the hook injects tokens:

```
Agent-Session: tool=claude-code model=opus agents=python-coder duration=32m dispatch=orchestrator interactions=0 approvals=2 tokens=245.3K/18.7K
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^
               agent-authored (or orchestrator-appended)        orchestrator at commit time                                    injected by hook
```

**Interaction tracking**: `interactions` and `approvals` measure the total human cost for the task — the orchestrator sums its own human touchpoints plus the subagent's. See `context/rules/git-commits.md` for the full counting rule and `context/templates/pr-description-template.md` for PR-level autonomy metrics.

**Consumption**: the `continuous-improvement` workflow reconstructs per-task, per-agent, and per-sprint token and autonomy data from `git log --format='%B' | grep Agent-Session`, alongside the structured events in `metrics/session-log.jsonl`.

---

## 9. UI Testing Quality Gate

When @ui-tester completes, orchestrator SHALL verify deliverables before accepting results:

**Required Evidence (ALL must be present):**
- [ ] Screenshots in `artefacts/test-results/e2e/screenshots/` (minimum 1)
- [ ] Test log documents browser interactions (not just API calls)
- [ ] At least one complete user workflow tested

**Rejection Criteria:**
- ❌ No screenshots → Not valid UI test
- ❌ Only API testing → Use @functional-tester instead
- ❌ No browser interactions documented → Insufficient evidence

**Example Valid Test Log:**
```
1. Opened browser to http://localhost:3000
2. Clicked search input
3. Typed "AAPL"
4. Screenshot: search-results.png showing dropdown
5. Clicked first result
6. Screenshot: chart-loaded.png showing Bollinger Bands
```

**Example Invalid Test Log:**
```
1. curl http://localhost:8001/data/search?q=AAPL → 200 OK
2. All APIs responding correctly
```

---

## 10. Archive Cleanup (Pre-Deployment)

Before deploying to production, purge temporary archives to keep repository lean.

**Timing:** After all tests pass and before deployment commit.

**What to purge:**
- `test-results/archive/` - Historical test runs (CI/CD systems maintain build artifacts, not git)
- Old screenshots beyond latest 3 runs - Already archived, safe to delete
- Large generated files - Coverage reports, profiling data, memory dumps

**What to keep:**
- `test-results/DASHBOARD.md` - Latest test status
- `test-results/test-gaps.md` - Coverage gap documentation
- Latest test results - `unit/`, `integration/`, `e2e/`, `security/` current runs
- Evidence for current release - Screenshots and logs for latest passing tests

**Cleanup script:**
```bash
# Remove archived test results
rm -rf artefacts/test-results/archive/

# Remove old screenshots (keep latest 3 runs)
find artefacts/test-results/e2e/screenshots -type d -mtime +3 -exec rm -rf {} +

# Remove large generated files
find . -name "*.coverage" -o -name "*.prof" -o -name "core.*" | xargs rm -f
```

**Rationale:** Archives are for development visibility during iteration. Production deployments reference specific commits; test results are preserved in CI/CD logs. Keeping archives in git bloats repository size without adding value post-deployment.

**Commit archive cleanup:**
```bash
git add artefacts/test-results/
git commit -m "chore: purge test archives before deployment"
```

---

## 11. Parallel Execution Analysis

### When to Suggest Parallelisation

The orchestrator should proactively analyse parallelisation opportunities when:
- Spawning multiple agents (>1 agent)
- Tasks expected to exceed 5 minutes
- Multiple independent modules/services being worked on
- Code reviews, testing, or builds across separate domains
- Any situation where independent work streams exist

### Presenting Options

Use this template when suggesting parallel execution to users:

**Current Approach: [Sequential/Single]**
- Timeline: [Agent A → Agent B → Agent C]
- Estimated time: X minutes
- Estimated tokens: Y tokens (baseline)

**Option A: [Partial Parallel]**
- Execution: [Sprint 1: A+B parallel, Sprint 2: C]
- Time saved: Z% faster (X min → W min)
- Token increase: +N% (context duplication, coordination overhead)
- Trade-offs: [Merge complexity, potential conflicts]

**Option B: [Full Parallel]**
- Execution: [A, B, C all parallel]
- Time saved: Z% faster (X min → W min)
- Token increase: +N% (context duplication, coordination overhead)
- Trade-offs: [Higher coordination, merge conflicts, more complex error handling]

### Decision Criteria

Present options and let user choose based on priorities:
- **Speed priority**: Full parallel execution
- **Cost priority**: Sequential execution (minimal token usage)
- **Quality priority**: Sequential with careful human review between stages
- **Balanced**: Partial parallel (2-3 independent tracks)

### Estimation Guidelines

**Time Savings**:
- 2 independent agents: ~40-50% faster (not 50% due to coordination)
- 3+ independent agents: ~60-70% faster (diminishing returns)

**Token Increase**:
- 2 agents: +10-15% (shared context, some duplication)
- 3 agents: +20-30% (more context duplication)
- 4+ agents: +30-40% (significant overhead)

### Examples

**Example 1: Code Review**
```
Current: Single reviewer, 30 min, 150k tokens

Option A (2 tracks):
- Backend + Frontend parallel
- 20 min (33% faster)
- 165k tokens (+10%)
- Trade-off: Need to merge findings

Option B (3 tracks):
- Backend, Frontend, Integration all parallel
- 12 min (60% faster)
- 180k tokens (+20%)
- Trade-off: Higher coordination, merge conflicts
```

**Example 2: TDD Implementation**
```
Current: Frontend then Backend, 40 min, 200k tokens

Option A (parallel):
- Frontend + Backend simultaneously
- 22 min (45% faster)
- 220k tokens (+10%)
- Trade-off: API contract must be agreed first
```

### When NOT to Parallelise

- Tasks with sequential dependencies (B needs A's output)
- Single-file modifications (conflicts guaranteed)
- High coordination overhead (>30% of work is merging)
- User explicitly requests sequential approach
- Quality gate reviews (must run sequentially by design)

### File Scope and Collision Safety

All parallel agents must have **disjoint file scopes** — see `agent-standards.md` §6 for the full model. Before spawning parallel agents:

1. List each agent's `file_scope` from the task plan
2. Reject if any path appears in more than one agent's scope
3. Shared paths (migrations/, shared-types/) → sequence those tasks or assign one owner
4. Log the verified scope matrix in HANDOFF.md before spawning

Agents do not commit — the orchestrator commits sequentially on their behalf to avoid ref-lock collisions.

### Best Practices

1. **Identify dependencies first** - Map out what depends on what
2. **Assign disjoint file scopes** - No two parallel agents share a writable path
3. **Agree contracts upfront** - API contracts, interfaces, schemas
4. **Commit sequentially** - Orchestrator formats and commits one agent at a time
5. **Monitor progress** - Check agents aren't duplicating work
6. **Learn and adapt** - Review token usage from git log Agent-Session lines

---

## 12. Claude Skills Alignment

> **Context**: This section is specific to Claude Code as the orchestrator. The workflow is
> framework-agnostic, but when Claude is running it the `skills` hints in `default.yaml` map
> to named skills that sharpen agent behaviour at each phase. This section explains the intent
> behind each mapping so the orchestrator knows when and why to invoke them.

### What skills are and why they matter

Skills are loaded prompt fragments that enforce a specific discipline. They are not tools — they
are cognitive constraints. An agent without a skill hint will improvise; with the right skill it
follows a proven pattern (TDD iron law, systematic debugging, parallel dispatch, etc.).

The orchestrator MUST invoke relevant skills **before** generating any response or action at
that phase. The `skills` field in `default.yaml` is a checklist, not a suggestion.

### Phase-to-skill mapping

| Workflow phase | Skill(s) | Why |
|---|---|---|
| `discovery` | `superpowers:brainstorming` | Explore problem space before formalising requirements; prevents premature lock-in |
| `design` | `superpowers:brainstorming` | Evaluate design alternatives before committing; explore trade-offs |
| `design` | `superpowers:brainstorming` | Explore design alternatives before committing to an approach |
| `design` (UI work) | `frontend-design` | Produces polished, non-generic UI designs; avoids AI-default aesthetics |
| `design-review`, `quality-review`, `final-holistic-review` | `superpowers:requesting-code-review` | Structures what reviewers focus on; prevents unfocused review passes |
| `design-review`, `quality-review`, `final-holistic-review` | `superpowers:receiving-code-review` | Validates CHANGES REQUIRED feedback before acting; prevents performative compliance |
| `tasks-review` | `superpowers:writing-plans` | Enforces bite-sized tasks with exact file paths, TDD steps, and commit cadence |
| `tasks-review`, `tdd-green`, `tdd-blue`, `sprint-review`, `final-holistic-review` | `superpowers:dispatching-parallel-agents` | Ensures parallel agents are spawned simultaneously, not sequentially |
| `tdd-red`, `test-plan-review`, `tdd-green`, `tdd-blue` | `superpowers:test-driven-development` | The iron law: no production code before a failing test; watch-it-fail is mandatory |
| `tdd-green` (UI) | `frontend-design` | When TypeScript agent builds new components; raises visual quality bar |
| `tdd-green`, `tdd-blue`, `coverage-gate`, `unit-regression`, `e2e-regression`, `deployment-review` | `superpowers:verification-before-completion` | Requires running commands and showing real output before claiming any phase complete |
| `coverage-gate`, `integration-regression` | `superpowers:systematic-debugging` | If threshold not met or contract breaks: root-cause analysis before writing tests or patches |
| `deployment`, `deployment-review` | `superpowers:finishing-a-development-branch` | Guided merge/PR/cleanup decision; prevents branches being left dangling |
| `deployment` | `commit-commands:commit-push-pr` | Structured commit + push + PR in one invocation |

### How the orchestrator passes skill hints to subagents

Spawned subagents do **not** inherit the orchestrator's context. The `skills` field in the
workflow yaml is a reminder to the **orchestrator** to include skill invocation instructions
in the agent prompt. The pattern is:

```
@python-coder implement Task 2.9 (Phase A circuit breaker)

BEFORE starting, invoke these skills:
- superpowers:test-driven-development  (TDD GREEN phase)
- superpowers:verification-before-completion  (run tests, show output before claiming done)

Read context/standards/tech-standards.md first.
[task details...]
```

Without explicit inclusion in the prompt, subagents will not see the `skills` field and will
not invoke them. The workflow yaml serves as the orchestrator's checklist; the agent prompt
is where the instruction actually reaches the subagent.

### Skills not tied to a specific phase

| Skill | When to invoke |
|---|---|
| `superpowers:systematic-debugging` | Any time a test fails unexpectedly or behaviour is wrong — invoke before proposing any fix |
| `claude-md-management:claude-md-improver` | After a sprint cycle when project conventions have evolved |
| `superpowers:writing-skills` | When encoding a new reusable pattern as a skill |
| `commit-commands:clean_gone` | Periodically to remove stale local branches |
| `superpowers:subagent-driven-development` | Alternative to dispatching: single session, one fresh subagent per task, review between each |
