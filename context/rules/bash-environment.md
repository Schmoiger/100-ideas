---
description: Bash invocation safety for autonomous agent execution — tool substitution, sandbox compliance, and banned patterns
globs: []
alwaysApply: true
---

# Bash Environment

**Applies to**: All bash commands and file operations

---

## Tool Substitution

Always use dedicated tools instead of bash where available:

| Action | Correct | Wrong |
|--------|---------|-------|
| Create file | Write tool | `echo "..." > file`, `cat << EOF > file`, heredoc |
| Edit file | Edit tool | `sed -i`, `awk`, bash heredoc |
| Read file | Read tool | `cat file`, `head`, `tail` |
| Find files | Glob tool | `find . -name`, `ls -R` |
| Search content | Grep tool | `grep`, `rg` via bash |
| Run inline script | Write to `/tmp/script.py`, then `uv run --project /abs/path python /tmp/script.py` | `python -c "..."` multiline or with `#` comments |

Dedicated Write/Edit/Glob/Grep tools execute with higher precision, structured diffing, and reduced permission friction across runtimes.

---

## Banned Bash Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| `cd /path && command` | Triggers bare-repository attack heuristics and breaks cwd isolation | Use `git -C /path` for git; use `--project /abs/path` for uv |
| `python ...`, `python3 ...` | Bypasses project virtualenv and managed dependencies | Use `uv run [--project <path>] python ...` |
| `pytest ...` | Bypasses project virtualenv and test dependencies | Use `uv run [--project <path>] pytest ...` |
| `pip ...`, `pip3 ...` | Non-deterministic unpinned dependency management | Use `uv add` or `uv sync` |
| `PYTHONPATH=...` path hacks | Masks broken environment configurations and violates isolation | Fix project virtualenv via `uv sync` |
| Silent fallback when tool fails | Masks defects, causes environment drift, violates fail-fast invariant | Diagnose root cause of failure or escalate per `escalation.md` |
| `printf ... \| git commit -F -` | Pipe splits at `\|`; each segment checked independently | Write to `/tmp/msg.txt`, then `git commit -F /tmp/msg.txt` |
| `$(...)` command substitution | Blocked by terminal sandboxes | Write output to temp file; read separately |
| `<(...)` process substitution | Blocked by terminal sandboxes | Write to temp file |
| `VAR=value && command` | Compound token syntax breaks prefix-matching security filters | Use `ENV=value uv run ...` (env prefix before the command) |
| `(cd /path && ...)` subshell | Subshell wrapper breaks prefix matching | Use `git -C /path` or `--project /abs/path` |
| `python -c "..."` multiline with `#` lines | `#`-prefixed lines inside quoted blocks trigger injection heuristics | Write script to `/tmp/script.py`; run as file |
| Consecutive `''` at word start | Flagged as potential shell obfuscation | Write script to temp file |
| Batch Edit then report without verifying | Edits can silently fail if snapshot is stale | After batch edits, run `git diff --stat` to confirm changes are on disk before reporting back; re-read and re-apply any missing edits |

