---
name: agent-sandbox
description: Procedural guidance and rationale for executing terminal commands within agent sandboxes, avoiding common heuristics that trigger security blocks.
globs: []
---

# Agent Sandbox Execution Skill

---

## Overview

Modern agent execution environments and sandboxes (e.g., Antigravity, Claude Code, GitHub Copilot) evaluate terminal commands against automated security heuristics. Understanding these heuristics is critical for writing deterministic, resilient automation scripts.

All commands executed under this skill are subject to the strict invariants defined in `context/rules/bash-environment.md`.

---

## 1. Sandbox Heuristics (Rationale)

Agents run commands that are evaluated against the following security layers:

1. **Prefix and first-token matching**: The first token determines whether a command matches allowlisted tool policies. Subshells `(cd /path && ...)` or env-setting compound syntax `VAR=value && command` can break prefix matching.
2. **Pipe boundary splitting**: Compound commands are split at `|`, requiring each segment to pass independently. For example, `printf ... | git commit -F -` splits at the pipe, and the `git commit` segment might fail security checks if its source is untrusted.
3. **Line-based scanning**: Multiline strings are scanned line by line. `#`-prefixed lines inside quoted blocks or consecutive single quotes trigger injection/obfuscation warnings.
4. **Compound command heuristics**: Combining commands like `cd X && Y` triggers bare-repository security checks regardless of allowlist rules, because the context directory changes dynamically.

---

## 2. Procedural Workarounds

To safely execute complex logic without triggering the sandbox blocks:

### Avoid `cd` Commands
- **Git operations**: Use the `-C` flag (e.g., `git -C /path status`).
- **Python operations**: Use the `--project` flag (e.g., `uv run --project /abs/path ...`).

### Executing Inline Python Scripts
Do not use `python -c "..."` for multi-line scripts. The line-based scanner will flag `#` comments inside strings as potential injections.
- **Instead**: Write the script to a temporary file (e.g., `/tmp/script.py`) using a dedicated file-writing tool, and execute it via `uv run --project /abs/path python /tmp/script.py`.

### Piping and Command Substitution
Terminal sandboxes often block `$(...)` and `<(...)` constructs, as well as complex pipe chains.
- **Instead**: Write intermediate outputs to temporary files and read them back in separate steps.
  - *Bad*: `printf "Message" | git commit -F -`
  - *Good*: Write "Message" to `/tmp/msg.txt`, then run `git commit -F /tmp/msg.txt`

### File Modification and Reading
Do not use bash streams (`echo "..." > file`, `cat`, `sed -i`) if dedicated agent tools (e.g., `replace_file_content`, `read_file`) are available. Dedicated tools provide precision diffing and native permission handling that bash streams lack.

### Tool Selection Policies

Agents have access to multiple tools for different purposes. To minimise user interruption and maximise efficiency, follow these tool selection policies:

#### 1. File Operations

*   **Prefer Write/Edit tools** for creating and modifying files. These tools do not require user permission and provide immediate feedback.
*   **Avoid Bash for file operations** such as `cat`, `echo >`, `sed`, `awk`, or heredoc redirection. These require user permission and slow down execution.
*   **Exception**: Bash may be used for file operations when the operation is part of a larger script that includes non-file operations (e.g., git commit with file creation).
*   **Read immediately before each Edit**: The Edit tool validates its changes against a snapshot taken at the most recent Read. If another Edit has run since the last Read, the snapshot is stale and the Edit will fail. Always issue a Read immediately before each Edit — never batch a single Read with multiple subsequent Edits.

#### 2. Command Execution

*   **Use Bash** for running tests, validation commands, git operations, and other system commands.
*   **Use Bash** when multiple dependent operations must run sequentially (e.g., `uv add package && uv run pytest`).
*   **Preferred pattern**: Use Write/Edit to create files, then Bash to execute tests/validation on those files.

#### 3. Code Search

*   **Use Glob** for finding files by pattern (e.g., `**/*.py`).
*   **Use Grep** for searching file contents by keyword or regex.
*   **Avoid Bash alternatives** like `find`, `grep`, `rg` commands unless necessary for complex operations.

#### 4. Tool Selection Summary

| Operation | Preferred Tool | Avoid |
|-----------|---------------|-------|
| Create/modify files | Write, Edit | `echo >`, `cat <<EOF`, `sed` |
| Run tests | Bash (`uv run`, `yarn test`) | Bare `pytest`, `vitest`, `python -m pytest` |
| Git operations | Bash | N/A |
| Find files | Glob | `find`, `ls` |
| Search contents | Grep | `grep`, `rg`, `ack` |
| Install dependencies | Bash (`uv add`, `yarn add`) | Manual edits to lock files, `pip`, `npm` |

#### 5. Failure-Mode Transparency and Fail-Fast Rule (Strict Invariant)

When standard-mandated tooling (such as `uv`, `yarn dlx`, or specified linter commands) fails due to missing dependencies, path mismatches, or sandbox permissions:
*   Agents **SHALL NOT** silently substitute unapproved alternatives (e.g. falling back to system `python`, `python3`, `pip`, or injecting ad-hoc `PYTHONPATH` exports).
*   Silent fallback masks defects, creates untracked drift, and violates reproducibility.
*   Agents shall treat tool execution failures as environment defects: diagnose the root cause, fix the project configuration, or escalate uncertainty per `context/rules/escalation.md`.
