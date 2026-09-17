---
name: agent-workflows
description: Procedural guidance for agent git commits, pull requests, and metrics logging.
globs: []
---

# Agent Workflows Skill

---

## Overview

This skill provides the procedural steps for assembling git commits, formatting PR descriptions, and logging agent metrics, enforcing the invariants defined in `context/rules/workspace-conventions.md`.

---

## 1. Commit Procedure

When committing on behalf of an agent (or yourself), verify the message:

1. **Ensure Trailers Exist**: Check for an `Agent-Session:` line and a `Co-Authored-By:` line.
2. **Trailer Format**:
   ```
   Agent-Session: tool={tool} model={model} agents={agent-role} duration={time} dispatch={human|orchestrator} interactions={N} approvals={N}
   ```
   *Note: `tokens=` is appended automatically by the `prepare-commit-msg` hook — never include it manually.*
3. **Format**: Format source files (ruff/biome) before staging.
4. **Commit**: Write the message to a temporary file (e.g., `/tmp/msg.txt`) and run `git add {files} && git commit -F /tmp/msg.txt`. Do NOT use `git commit -m "$(...)"`.
5. **Push**: `git push` immediately to publish the commit.

---

## 2. Pull Requests

When creating a PR, use `context/templates/pr-description-template.md`. Compute the Agent Metrics section by parsing Agent-Session lines from all commits on the branch:

```bash
git log main..HEAD --format='%b' | grep '^Agent-Session:'
```

---

## 3. Metrics Logging Schema

Append events to `metrics/session-log.jsonl` using the following schema:

```json
{
  "ts": "ISO8601 timestamp",
  "task": "task-id",
  "agent": "agent-id",
  "event": "start|handoff|escalate|complete|blocked",
  "tokens": {
    "in": 0,
    "out": 0,
    "source": "api_response|estimated|unavailable"
  },
  "to": "target-agent (for handoff/escalate)",
  "notes": "optional context"
}
```

### Token Estimation
| Source | When | Accuracy |
|--------|------|----------|
| api_response | Platform provides usage metadata | Exact |
| estimated | Calculate as chars/4 | ~80% accurate |
| unavailable | Platform doesn't expose, can't estimate | Log anyway |

---

## 4. Commit Cadence

Agents shall request commits at **natural checkpoints**, not only at task completion:

| Checkpoint | Example |
|------------|---------|
| Test written and failing (RED) | `test(bronze): add ticker_info validation tests` |
| Implementation passing (GREEN) | `feat(bronze): implement ticker_info validation` |
| Refactor complete (BLUE) | `refactor(bronze): extract validation helpers` |
| File group complete | `feat(bronze): add all ohlcv router endpoints` |

At each checkpoint, write your message to `/tmp/{task-id}_commit_msg.txt` and return the file paths if operating as a subagent. If operating directly, follow the commit procedure in Section 1.
