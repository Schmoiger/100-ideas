#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Git Hook Dispatcher (Multiplexer for Multi-Subrepo Architecture)
# ─────────────────────────────────────────────────────────────────────────────
# Discovers and sequentially executes hooks for a given lifecycle event across
# all subrepos (e.g. typst/, context/, etc.) and host-local hooks.
#
# Usage:
#   dispatch.sh <hook-event-name> [git-hook-args...]
#
# Examples:
#   dispatch.sh pre-commit
#   dispatch.sh prepare-commit-msg .git/COMMIT_EDITMSG message
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <hook-name> [args...]" >&2
  exit 1
fi

readonly HOOK_EVENT="$1"
shift

readonly REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Collect candidate hook scripts from all subrepos
declare -a HOOK_SCRIPTS=()

# 1. Scan subrepos for <subrepo>/scripts/hooks/<hook-event>
while IFS= read -r hook; do
  if [[ -n "$hook" && -x "$hook" ]]; then
    HOOK_SCRIPTS+=("$hook")
  fi
done < <(find . -mindepth 2 -maxdepth 4 -type f -path "*/scripts/hooks/${HOOK_EVENT}" \
  -not -path "./.git/*" -not -path "./.githooks/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null || true)

# 2. Scan subrepos for <subrepo>/hooks/<hook-event>
while IFS= read -r hook; do
  if [[ -n "$hook" && -x "$hook" ]]; then
    HOOK_SCRIPTS+=("$hook")
  fi
done < <(find . -mindepth 2 -maxdepth 3 -type f -path "*/hooks/${HOOK_EVENT}" \
  -not -path "./.git/*" -not -path "./.githooks/*" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "*/scripts/*" 2>/dev/null || true)

# 3. Handle special named hooks (e.g. context/scripts/prepare-commit-msg.sh)
if [[ "$HOOK_EVENT" == "prepare-commit-msg" ]]; then
  while IFS= read -r hook; do
    if [[ -n "$hook" && -x "$hook" ]]; then
      # Avoid duplicate if already added
      local_already=false
      for existing in "${HOOK_SCRIPTS[@]:-}"; do
        if [[ "$existing" == "$hook" ]]; then
          local_already=true
          break
        fi
      done
      if [[ "$local_already" == "false" ]]; then
        HOOK_SCRIPTS+=("$hook")
      fi
    fi
  done < <(find . -mindepth 2 -maxdepth 3 -type f -name "prepare-commit-msg.sh" \
    -not -path "./.git/*" -not -path "./.githooks/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null || true)
fi

# 4. Host-level optional local hook: .githooks/<hook-event>.local
if [[ -x ".githooks/${HOOK_EVENT}.local" ]]; then
  HOOK_SCRIPTS+=(".githooks/${HOOK_EVENT}.local")
fi

# If no hooks found, exit cleanly
if [[ ${#HOOK_SCRIPTS[@]} -eq 0 ]]; then
  exit 0
fi

# Execute discovered hooks in sequence
failed_hooks=0
for hook in "${HOOK_SCRIPTS[@]}"; do
  hook_rel="${hook#./}"
  echo " [hook-dispatcher] Running $HOOK_EVENT -> $hook_rel"
  
  if ! "$hook" "$@"; then
    echo " ✗ [hook-dispatcher] Hook failed: $hook_rel" >&2
    failed_hooks=$((failed_hooks + 1))
    break # Fail fast: abort commit immediately on first hook failure
  fi
done

if [[ $failed_hooks -gt 0 ]]; then
  exit 1
fi

exit 0
