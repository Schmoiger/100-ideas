# Commit Message Template

---

## Format

```
<type>(<scope>): <subject>

<body>

Tasks: <task-ids>
Agent-Session: tool=<tool> model=<model> agents=<agent-ids> duration=<time>

Co-Authored-By: <tool-or-identifier> <<email>>
```

---

## Components

### Subject Line (required)

Conventional commits format, max 72 characters:

```
feat(auth): add token refresh endpoint
fix(data): prevent negative balance on refund
refactor(api): extract validation middleware
```

### Body (optional)

Brief context if subject is insufficient. Focus on "why" not "what".

```
Implements exponential backoff for webhook retries.
Previous fixed-interval approach overwhelmed failing endpoints.
```

### Tasks (required)

Reference task IDs from tasks.md:

```
Tasks: AUTH-001, AUTH-002
```

### Agent-Session (required for agent commits)

Single-line metrics block, machine-parseable. **Record the triplet accurately: tool, model, and agent(s).**

```
Agent-Session: tool=<tool> model=<model> agents=<agent-ids>
```

| Field | Authored by | Format | Example |
|-------|------------|--------|---------|
| tool | Agent or orchestrator | The IDE/platform that ran the model | tool=cursor, tool=claude-code |
| model | Agent or orchestrator | The model/backend used | model=sonnet, model=opus |
| agents | Agent or orchestrator | Agent role(s) from context/agents | agents=python-coder |
| duration | Orchestrator | Minutes or hours | duration=45m |
| dispatch | Orchestrator | Who initiated the task | dispatch=orchestrator, dispatch=human |
| interactions | Orchestrator | Total human messages across orchestrator + subagent | interactions=0 |
| approvals | Orchestrator | Total tool/action approvals across orchestrator + subagent | approvals=2 |

`tokens=` is appended automatically by the `prepare-commit-msg` hook — do not include it manually.

**Counting rule**: `interactions` and `approvals` measure the **total human cost** for the task. The orchestrator sums its own human touchpoints (e.g. asking the human about the task, getting tool approvals for the commit) plus the subagent's. `dispatch=orchestrator` with `interactions=0 approvals=0` means nobody needed a human for anything.

**Triplet**: Always list the actual (tool, model, agent) for this commit. Agent names are from `context/agents/*.md` (e.g. python-coder, typescript-coder, functional-tester, code-reviewer, tech-lead). Do not substitute a default; use what was actually used.

### Co-Authored-By (required for agent commits)

GitHub-recognised trailer format. Use a line that identifies the tool (or tool + model) so the commit is attributed correctly. The **authoritative triplet** is in the Agent-Session line; Co-Authored-By is for GitHub display.

```
Co-Authored-By: Cursor <cursor@cursor.com>
Co-Authored-By: Claude Sonnet <sonnet@anthropic.com>
Co-Authored-By: GitHub Copilot <copilot@github.com>
```

Match the tool (and optionally model) to what is in Agent-Session. Do not use a fixed co-author; use the actual tool/model that was used.

---

## Examples

### Simple Feature

```
feat(auth): add token refresh endpoint

Tasks: AUTH-001
Agent-Session: tool=cursor model=sonnet agents=python-coder duration=32m dispatch=orchestrator interactions=0 approvals=1

Co-Authored-By: Cursor <cursor@cursor.com>
```
The hook appends `tokens=8.2K/5.1K` to the Agent-Session line at commit time.

### Multi-Task with Review

```
feat(data): implement retry logic for webhooks

Exponential backoff with max 5 attempts.
Addresses reliability issues from incident INC-042.

Tasks: DATA-003, DATA-004
Agent-Session: tool=cursor model=sonnet agents=python-coder,code-reviewer duration=58m dispatch=orchestrator interactions=2 approvals=1

Co-Authored-By: Cursor <cursor@cursor.com>
```

### Bug Fix with Blocker Resolution

```
fix(payments): correct decimal precision on refunds

Tasks: PAY-012
Agent-Session: tool=claude-code model=opus agents=python-coder duration=18m dispatch=human interactions=3 approvals=0
Blocker-Resolved: PAY-042 (see domain-rules.yaml#PAY-042)

Co-Authored-By: Claude Opus <opus@anthropic.com>
```

### Human-Only Commit

```
docs: update API documentation

Tasks: DOC-001
```

No Agent-Session or Co-Authored-By for human-only commits.

---

## Parsing

The Agent-Session line is designed for automated extraction:

```bash
# Extract metrics from git log
git log --format='%b' | grep '^Agent-Session:' | \
  sed 's/Agent-Session: //' | \
  awk -F' ' '{print $0}'
```

```python
# Parse metrics line
import re
pattern = (
    r'tool=([a-z0-9-]+) model=([a-z0-9.-]+) agents=([\w,-]+)'
    r'(?: duration=(\d+[mh]))?'
    r'(?: dispatch=(human|orchestrator))?'
    r'(?: interactions=(\d+))?'
    r'(?: approvals=(\d+))?'
    r'(?: tokens=([\d.]+K?)/([\d.]+K?))?'
)
match = re.search(pattern, line)
# match.group(1)=tool, (2)=model, (3)=agents, (4)=duration,
# (5)=dispatch, (6)=interactions, (7)=approvals, (8)=tokens_in, (9)=tokens_out
```
