# Task Prompt Template

Used by orchestrator when spawning agents. Agents must read their definition from `context/agents/{agent-name}.md`.

---

## Structure

```markdown
You are @{agent-name} running {task-id}.

BEFORE starting, read:
1. context/agents/{agent-name}.md
{resolved-rules — orchestrator: resolve using Rule Resolution in orchestrator.md.
 List each rule as a numbered item with its full path, e.g.:
  2. context/rules/bash-environment.md
  3. context/rules/python-environment.md
  4. context/rules/escalation.md
 Also add relevant standards:
  - context/standards/coding-standards.md       (implementation tasks)
  - context/standards/testing-standards.md      (test tasks)
  - context/standards/doc-standards.md          (documentation tasks)
  - context/templates/README.md                 (tasks that produce a templated artefact)}
{resolved-skills — orchestrator: resolve using Skill Resolution in orchestrator.md.
 List matching procedural skills from the ## Skills index in AGENTS.md, e.g.:
  5. context/skills/python-scripting.md         (tasks touching Python files or scripts)
  6. context/skills/technical-authoring.md      (tasks involving human-facing documentation)}

ESCALATION (MANDATORY):
Log to `artefacts/build/agent-interruptions.md` under the current sprint section
whenever the user's or orchestrator's attention was required:

1. QUESTION — you cannot proceed without an external answer:
   **Type**: Question | **Question**: ... | **Answered by**: _(blank)_ | **Resolution**: _(blank)_

2. TOOL APPROVAL — user was prompted to approve a tool use:
   **Type**: Tool approval | **Tool**: ... | **Approved by**: User | **Resolution**: Approved/Denied

Do NOT log autonomous decisions or self-resolved issues.

---

## IMMEDIATE CONTEXT

Branch: `{branch}`
Working directory: `{project-root}`
Current state: {1–3 sentences describing what exists and what has just completed}

Key files for this task:
- `{file}` — {what it contains / why it matters}
- `{file}` — {what it contains / why it matters}

---

## FILE SCOPE

You may only write or edit files within this scope:
- `{path}` — {what you are writing here}
- `{path}` — {what you are writing here}

Do NOT write to HANDOFF.md, tasks.md, or bugs.md — report changes back to the orchestrator.
Do NOT run `git add` or `git commit` — the orchestrator commits on your behalf (see COMMIT section).

---

## TASK: {task-id}

{task-description}

---

## IMPLEMENTATION

{numbered-implementation-steps}

---

## ACCEPTANCE

{bulleted-acceptance-criteria}

---

## COMMIT

Do NOT run `git add` or `git commit` — the orchestrator formats, commits, and pushes on your behalf.
Before reporting back, **lint your own code** — the orchestrator only auto-formats, it will not fix lint errors:
- Python: `uv run --project /abs/path/to/service ruff check {files}` (fix any errors yourself)
- TypeScript: `yarn --cwd /abs/path/to/project-root biome check {files}` (fix any errors yourself)

Write your commit message to `/tmp/{task-id}_commit_msg.txt` following `context/templates/commit-message-template.md`.
{any task-specific commit notes, e.g. conventional commit type and scope}

---

## REPORT BACK

Include in your report:
- **Files changed**: exact paths you wrote or edited (these become the `git add` list)
- **Commit message**: path to your `/tmp/{task-id}_commit_msg.txt`

{what the orchestrator needs to know when the agent finishes}
```

---

## Orchestrator Usage

1. Read `artefacts/build/tasks.md` for the current task
2. Fill ALL placeholders — never leave `{...}` in the prompt
3. **Resolve rules** using the Rule Resolution procedure in `context/agents/orchestrator.md`:
   - Read the agent's `rules:` frontmatter for the candidate pool
   - Include all `alwaysApply: true` rules from the pool
   - Include rules whose `globs` match the task's target files
   - Omit rules whose `globs` don't match
   - Add domain standards (coding, testing, doc, tech) as appropriate for the task type
4. **Assign file scope** — list the exact paths the agent may write or edit (see `agent-standards.md` §6.2). For parallel dispatches, verify scopes are disjoint. For read-only agents, state `(read-only)`.
5. Always include IMMEDIATE CONTEXT — agents have no inherited context
6. Always include ESCALATION block — agents must know where to log blockers
7. If the task produces an artefact, consult `context/templates/README.md` and reference the appropriate template in IMPLEMENTATION
8. Spawn agent

**Placeholders**:
- `{agent-name}`: Without @ (e.g., `python-coder`)
- `{task-id}`: From tasks.md (e.g., `TASK-001`)
- `{branch}`: Current git branch
- `{project-root}`: Absolute path to project root
- `{path}`: Files/directories the agent may commit (from §6.2 scope assignment)
- `{task-description}`: Brief context — what this agent is building and why
- `{numbered-implementation-steps}`: Numbered list with specific file paths
- `{acceptance-criteria}`: Bulleted list — what DONE looks like
- `{report-back}`: What the orchestrator needs from the agent's summary

---

## Phase Variants

When running a workflow with defined phases, add a `MODE:` line in the TASK section to orient the agent. Examples:

**TDD RED** — `MODE: TDD RED`
- Implementation: write failing tests only, no production code
- Acceptance: ALL tests fail on first run; confirm failure count

**TDD GREEN** — `MODE: TDD GREEN`
- Acceptance: ALL tests pass; no test file modifications

**TDD BLUE** — `MODE: TDD BLUE`
- Acceptance: ALL tests still pass; no new functionality added

Add other workflow-specific mode annotations (e.g. `MODE: DESIGN`, `MODE: REVIEW`) as needed for the active workflow.

---

## Anti-Patterns

❌ Override agent definition inline — agents read it from `context/agents/`
❌ Omit IMMEDIATE CONTEXT — agents have zero inherited state
❌ Omit ESCALATION block — agents won't know where to log blockers
✅ Reference agent definition: `Read: context/agents/{agent-name}.md`
✅ Provide specific file paths in implementation steps
✅ Tell the agent exactly what to report back
