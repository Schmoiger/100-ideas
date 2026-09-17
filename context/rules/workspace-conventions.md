---
description: Universal workspace conventions covering output locations, git commits, and metrics logging
globs: []
alwaysApply: true
---

# Workspace Conventions

**Applies to**: All agent operations, file generation, and version control.

---

## 1. Output Locations

### Directory Structure
```
{project-root}/
├── artefacts/                    # All build outputs
│   ├── architecture/             # Architecture docs, diagrams
│   ├── build/                    # Tasks, reviews, implementation docs
│   ├── product/                  # Requirements, user stories
│   ├── test-results/             # Test output files
│   └── design/                   # UI designs, wireframes
├── secrets/                      # Credentials (gitignored)
└── services/{name}/              # Service implementation
    └── tests/                    # Service tests
```

### File Naming
| Type | Convention | Example |
|------|------------|---------|
| Test results | `v2-{task-id}-results.txt` | `v2-004-red-results.txt` |
| Reviews | `{phase}-review.md` | `phase-2-3-tech-review.md` |
| Implementation docs | `{TASK-ID}-IMPLEMENTATION.md` | `BUG-UI-030-IMPLEMENTATION.md` |

---

## 2. Git Commits

1. **Who Commits**: If invoked directly by a human, **commit directly**. If spawned as a subagent by an Orchestrator, **DO NOT commit** — write your message to `/tmp/{task-id}_commit_msg.txt` and return the file paths.
2. **Pre-Commit**: Always format before staging (e.g. `uv run ruff format {files}` or `yarn biome check --write {files}`). If a hook reverts your changes, read the formatted file and commit it.
3. **Message Format**: Commits MUST follow `{type}({scope}): {description}`.
4. **Agent Trailers**: Commits MUST include the `Agent-Session` trailer and `Co-Authored-By` for AI-authored work.

---

## 3. Metrics Logging

1. **Session Log**: Append events (start, handoff, escalate, complete, blocked) to `metrics/session-log.jsonl`.
2. **Format**: One JSON object per line. Never overwrite.
