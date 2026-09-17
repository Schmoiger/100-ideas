#!/usr/bin/env bash
# prepare-commit-msg hook: append token usage to Agent-Session line.
# Delegates to the Python script for the actual work.
set -euo pipefail

# Resolve through symlinks to find the real script directory
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")" && pwd)"
uv run python "$SCRIPT_DIR/prepare-commit-msg.py" "$@"
