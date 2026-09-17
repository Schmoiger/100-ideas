# Git Hooks Dispatcher

A unified Git hook multiplexing system designed for multi-subrepo architectures.

---

## Overview

In a repository with multiple subrepos (such as `context/`, `typst-engine/`, and domain services), each subrepo may define its own lifecycle hooks (linters, validators, commit message formatters). 

Git natively executes hooks only from a single designated directory. The dispatcher in `.githooks/` bridges this limitation by discovering and executing hooks across all subrepos sequentially while providing clean fallback and fail-fast guarantees.

---

## Setup

Configure Git to point its hooks path to this directory:

```bash
git config core.hooksPath .githooks
```

---

## How It Works

```
Git Lifecycle Event (e.g., git commit)
  │
  ▼
.githooks/<event> (wrapper script)
  │
  ▼
.githooks/dispatch.sh <event> "$@"
  │
  ├── 1. Discovers subrepo hooks via find
  │      ├── <subrepo>/scripts/hooks/<event>
  │      └── <subrepo>/hooks/<event>
  │
  ├── 2. Discovers host-local hooks
  │      └── .githooks/<event>.local
  │
  └── 3. Sequential Execution (Fail-Fast)
         ├── Subrepo Hook A  ──► [Success]
         ├── Subrepo Hook B  ──► [Failure] ──► Abort commit
         └── ...
```

---

## Hook Discovery Rules

When an event triggers (for example, `pre-commit`), `dispatch.sh` scans the repository root:

1. **Subrepo Scripts Hook Directory**:
   - Pattern: `<subrepo>/scripts/hooks/<event>` (depth 2 to 4)
   - Example: `context/scripts/hooks/pre-commit`
2. **Subrepo Root Hooks Directory**:
   - Pattern: `<subrepo>/hooks/<event>` (depth 2 to 3)
   - Example: `typst-engine/hooks/pre-commit`
3. **Lifecycle-Specific Exceptions**:
   - For `prepare-commit-msg`, also discovers `<subrepo>/scripts/prepare-commit-msg.sh`.
4. **Host-Local Hooks**:
   - Pattern: `.githooks/<event>.local`
   - Use this for developer-specific or repository-level checks that do not belong inside any individual subrepo.

If no hooks are discovered for an event across the codebase, `dispatch.sh` exits cleanly with code `0`.

---

## Subrepo Hook Authoring Guidelines

When adding or implementing a new subrepo:

1. **Location**: Place hook scripts in `<subrepo>/scripts/hooks/<event>` or `<subrepo>/hooks/<event>`.
2. **Permissions**: Ensure hook scripts are executable (`chmod +x <path-to-hook>`).
3. **Execution Context**:
   - `dispatch.sh` always executes hooks from the repository root (`$REPO_ROOT`).
   - Scripts must resolve their own directories dynamically relative to `$0` rather than assuming current working directory `$PWD` is inside the subrepo:
     ```bash
     SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")" && pwd)"
     ```
4. **Fail-Fast Behaviour**: Return a non-zero exit code on validation failure to abort the Git operation immediately.

---

## Adding New Lifecycle Events

To dispatch a new Git hook event (for example, `pre-push`):

1. Create `.githooks/pre-push`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   exec "$SCRIPT_DIR/dispatch.sh" "pre-push" "$@"
   ```
2. Make it executable:
   ```bash
   chmod +x .githooks/pre-push
   ```
