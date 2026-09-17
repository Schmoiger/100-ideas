#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Repository Initialisation & Refresh Script
# ─────────────────────────────────────────────────────────────────────────────
# Bootstraps brand new repositories seeded from start-here, or freshens
# existing configurations. Handles:
#   1. Pre-flight dependency & environment checks (git, git-subrepo, uv, python)
#   2. Configuration prompts / CLI flags (LLM runtimes, Typst, metadata, remote)
#   3. Subrepo synchronisation (context/, typst/)
#   4. Runtime adapter generation & unselected target pruning (.agent-targets)
#   5. Lockfile updates & dependency synchronisation (uv lock/sync, yarn)
#   6. Pre-commit hooks & workflow configuration
#   7. Artefact folder reset to canonical skeleton
#
# Usage:
#   ./init.sh [OPTIONS]
#
# Options:
#   -h, --help                Show this help message and exit
#   -r, --runtime <targets>   Target runtimes: 'all', or comma-separated list
#                             (e.g. 'claude,gemini'). Supported: gemini, claude,
#                             github, openai, all.
#   -t, --typst               Enable Typst typesetting engine (clones/pulls typst/)
#   --no-typst                Disable Typst typesetting engine (prunes typst/)
#   -p, --project-name <name> Set project name in pyproject.toml and README.md
#   -d, --project-desc <desc> Set project description
#   -u, --git-remote <url>    Set upstream git remote origin URL
#   -y, --yes                 Non-interactive mode (use defaults for unset options)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# macOS Homebrew PATH prepending for git-subrepo (requires Bash 5+)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Text styles & colours
if [[ -t 1 ]]; then
  readonly BOLD="\033[1m"
  readonly GREEN="\033[32m"
  readonly BLUE="\033[34m"
  readonly YELLOW="\033[33m"
  readonly RED="\033[31m"
  readonly NC="\033[0m"
else
  readonly BOLD=""
  readonly GREEN=""
  readonly BLUE=""
  readonly YELLOW=""
  readonly RED=""
  readonly NC=""
fi

log_info()    { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1" >&2; }
log_step()    { echo -e "\n${BOLD}${BLUE}==>${NC} ${BOLD}$1${NC}"; }

# ── Argument Parsing ──────────────────────────────────────────────────────────

RUNTIME_ARG=""
TYPST_ARG=""
PROJECT_NAME_ARG=""
PROJECT_DESC_ARG=""
GIT_REMOTE_ARG=""
NON_INTERACTIVE=false

show_help() {
  cat << 'EOF'
Repository Initialisation Script (init.sh)

Bootstraps new projects seeded from start-here or freshens existing setups.

Usage:
  ./init.sh [OPTIONS]

Options:
  -h, --help                Show this help message and exit
  -r, --runtime <targets>   Target runtimes: 'all', or comma-separated list
                            (e.g. 'claude,gemini'). Supported: gemini, claude,
                            github, openai, all.
  -t, --typst               Enable Typst typesetting engine (clones/pulls typst/)
  --no-typst                Disable Typst typesetting engine (prunes typst/)
  -p, --project-name <name> Set project name in pyproject.toml and README.md
  -d, --project-desc <desc> Set project description
  -u, --git-remote <url>    Set upstream git remote origin URL
  -y, --yes                 Non-interactive mode (use defaults for unset options)

Examples:
  ./init.sh                                 # Interactive mode
  ./init.sh -y                              # Non-interactive with all defaults
  ./init.sh -r claude,gemini -t -y          # Claude & Gemini with Typst
  ./init.sh -p my-app -d "My awesome tool"  # Custom metadata interactive
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    -r|--runtime)
      RUNTIME_ARG="$2"
      shift 2
      ;;
    -t|--typst)
      TYPST_ARG="yes"
      shift
      ;;
    --no-typst)
      TYPST_ARG="no"
      shift
      ;;
    -p|--project-name)
      PROJECT_NAME_ARG="$2"
      shift 2
      ;;
    -d|--project-desc)
      PROJECT_DESC_ARG="$2"
      shift 2
      ;;
    -u|--git-remote)
      GIT_REMOTE_ARG="$2"
      shift 2
      ;;
    -y|--yes)
      NON_INTERACTIVE=true
      shift
      ;;
    *)
      log_error "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# ── 1. Pre-flight Checks ──────────────────────────────────────────────────────
log_step "Step 1: Pre-flight Verification"

# Verify script is run from repository root
if [[ ! -d "context" || ! -f "pyproject.toml" ]]; then
  log_error "init.sh must be executed from the repository root (containing 'context/' and 'pyproject.toml')."
  exit 1
fi
REPO_ROOT="$(pwd)"

# Check git
if ! command -v git &>/dev/null; then
  log_error "git is not installed or not in PATH."
  exit 1
fi

# Check git-subrepo
if ! command -v git-subrepo &>/dev/null && ! git subrepo --version &>/dev/null; then
  log_error "git-subrepo is not installed."
  echo "  Please install it before running init.sh:"
  echo "  brew install git-subrepo"
  exit 1
fi
log_success "git and git-subrepo found"

# Check uv
if ! command -v uv &>/dev/null; then
  log_error "uv is not installed."
  echo "  Please install uv before running init.sh:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  or: brew install uv"
  exit 1
fi
log_success "uv found ($(uv --version))"

# Check python version
PYTHON_VERSION="3.14"
if [[ -f ".python-version" ]]; then
  PYTHON_VERSION="$(head -n 1 .python-version | tr -d '[:space:]')"
fi
log_info "Configured Python version: $PYTHON_VERSION"

# Check git repository status
if [[ -d ".git" ]]; then
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    log_warn "Git working directory has uncommitted changes."
    if [[ "$NON_INTERACTIVE" == "false" ]]; then
      echo -n "Would you like to stash uncommitted changes before continuing? [Y/n]: "
      read -r stash_resp
      stash_resp="${stash_resp:-y}"
      if [[ "$stash_resp" =~ ^[Yy]$ ]]; then
        git stash
        log_success "Uncommitted changes stashed."
      else
        log_warn "Proceeding with dirty working tree (subrepo operations may fail if affected)."
      fi
    fi
  fi
fi

# ── 2. Option Selection & Configuration ───────────────────────────────────────
log_step "Step 2: Configuration & Option Selection"

# Determine current repository directory name for default project name
DEFAULT_PROJECT_NAME="$(basename "$REPO_ROOT")"
CURRENT_NAME="$(grep -m1 '^name = ' pyproject.toml | cut -d'"' -f2 || echo "$DEFAULT_PROJECT_NAME")"
CURRENT_DESC="$(grep -m1 '^description = ' pyproject.toml | cut -d'"' -f2 || echo "A new project seeded from start-here")"

SELECTED_PROJECT_NAME=""
SELECTED_PROJECT_DESC=""
SELECTED_RUNTIMES=""
SELECTED_TYPST=""
SELECTED_GIT_REMOTE=""

# Read existing .agent-targets if present
EXISTING_TARGETS=""
if [[ -f ".agent-targets" ]]; then
  EXISTING_TARGETS="$(grep -v '^#' .agent-targets | tr '\n' ',' | sed 's/,$//' | tr -d ' ')"
fi
if [[ -z "$EXISTING_TARGETS" ]]; then
  EXISTING_TARGETS="all"
fi

# Determine interactive vs flags
if [[ "$NON_INTERACTIVE" == "true" ]]; then
  SELECTED_PROJECT_NAME="${PROJECT_NAME_ARG:-$CURRENT_NAME}"
  SELECTED_PROJECT_DESC="${PROJECT_DESC_ARG:-$CURRENT_DESC}"
  SELECTED_RUNTIMES="${RUNTIME_ARG:-$EXISTING_TARGETS}"
  SELECTED_TYPST="${TYPST_ARG:-no}"
  SELECTED_GIT_REMOTE="${GIT_REMOTE_ARG:-}"
else
  # Interactive prompts
  echo -e "${BOLD}Configure Project Metadata:${NC}"
  echo -n "  Project Name [$CURRENT_NAME]: "
  read -r user_pname
  SELECTED_PROJECT_NAME="${PROJECT_NAME_ARG:-${user_pname:-$CURRENT_NAME}}"

  echo -n "  Project Description [$CURRENT_DESC]: "
  read -r user_pdesc
  SELECTED_PROJECT_DESC="${PROJECT_DESC_ARG:-${user_pdesc:-$CURRENT_DESC}}"

  echo -e "\n${BOLD}Select Target AI Coding Runtimes:${NC}"
  echo "  1) Gemini / Antigravity"
  echo "  2) Claude Code"
  echo "  3) GitHub Copilot"
  echo "  4) OpenAI / Codex"
  echo "  5) All runtimes (recommended default)"
  echo -n "  Select runtimes (comma-separated, e.g. 1,2 or 5) [current: $EXISTING_TARGETS]: "
  read -r user_rt

  if [[ -n "$RUNTIME_ARG" ]]; then
    SELECTED_RUNTIMES="$RUNTIME_ARG"
  elif [[ -z "$user_rt" ]]; then
    SELECTED_RUNTIMES="$EXISTING_TARGETS"
  else
    # Parse numbers to targets
    declare -a targets_arr=()
    IFS=',' read -ra ADDR <<< "$user_rt"
    for item in "${ADDR[@]}"; do
      trimmed="$(echo "$item" | tr -d '[:space:]')"
      case "$trimmed" in
        1) targets_arr+=("gemini") ;;
        2) targets_arr+=("claude") ;;
        3) targets_arr+=("github") ;;
        4) targets_arr+=("openai") ;;
        5|all) targets_arr+=("all") ;;
        gemini|claude|github|openai) targets_arr+=("$trimmed") ;;
        *) log_warn "Ignoring unknown runtime choice: $trimmed" ;;
      esac
    done
    if [[ " ${targets_arr[*]} " =~ " all " || ${#targets_arr[@]} -eq 0 ]]; then
      SELECTED_RUNTIMES="all"
    else
      SELECTED_RUNTIMES="$(IFS=','; echo "${targets_arr[*]}")"
    fi
  fi

  echo -e "\n${BOLD}Typesetting & PDF Engine (typst-engine):${NC}"
  if [[ -n "$TYPST_ARG" ]]; then
    SELECTED_TYPST="$TYPST_ARG"
  else
    has_typst="N"
    [[ -d "typst" ]] && has_typst="y"
    echo -n "  Include Typst typesetting engine (typst/ subrepo)? [y/N] (default: $has_typst): "
    read -r user_typst
    user_typst="${user_typst:-$has_typst}"
    if [[ "$user_typst" =~ ^[Yy]$ ]]; then
      SELECTED_TYPST="yes"
    else
      SELECTED_TYPST="no"
    fi
  fi

  echo -e "\n${BOLD}Git Remote Origin:${NC}"
  current_origin="$(git remote get-url origin 2>/dev/null || echo "")"
  if [[ -n "$GIT_REMOTE_ARG" ]]; then
    SELECTED_GIT_REMOTE="$GIT_REMOTE_ARG"
  elif [[ "$current_origin" == *"Schmoiger/start-here"* || -z "$current_origin" ]]; then
    log_info "Current origin points to seed repo: ${current_origin:-none}"
    echo -n "  Enter new Git remote origin URL (leave blank to keep current): "
    read -r user_remote
    SELECTED_GIT_REMOTE="${user_remote:-}"
  else
    SELECTED_GIT_REMOTE=""
  fi
fi

log_info "Active project: $SELECTED_PROJECT_NAME"
log_info "Target runtimes: $SELECTED_RUNTIMES"
log_info "Typst engine: $SELECTED_TYPST"

# ── 3. Subrepo Management ─────────────────────────────────────────────────────
log_step "Step 3: Synchronising Subrepos"

# Pull context subrepo
if [[ -f "context/.gitrepo" ]]; then
  log_info "Pulling latest upstream context (agents-framework)..."
  if PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull context; then
    log_success "context/ successfully synchronised"
  else
    log_warn "git subrepo pull context encountered an issue. Skipping subrepo update."
  fi
else
  log_warn "context/ is not tracked as a git-subrepo. Skipping context pull."
fi

# Handle typst subrepo
if [[ "$SELECTED_TYPST" == "yes" ]]; then
  if [[ -f "typst/.gitrepo" ]]; then
    log_info "Pulling latest upstream typst-engine..."
    if PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull typst; then
      log_success "typst/ successfully synchronised"
    else
      log_warn "git subrepo pull typst encountered an issue."
    fi
  elif [[ -d "typst" ]]; then
    log_info "typst/ directory already exists."
  else
    log_info "Cloning typst-engine subrepo..."
    if PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clone https://github.com/Schmoiger/typst-engine.git typst -b main; then
      log_success "typst-engine cloned into typst/"
    else
      log_warn "Failed to clone typst-engine subrepo. Continuing."
    fi
  fi
else
  if [[ -d "typst" ]]; then
    log_info "Pruning typst/ subrepo as typesetting is not requested..."
    rm -rf typst
    log_success "typst/ removed"
  fi
fi

# ── 4. Option C: Runtime Pruning & Projections ────────────────────────────────
log_step "Step 4: Runtime Projections & Option C Pruning"

# Save configured targets to .agent-targets
echo "# Target AI coding runtimes configured by init.sh" > .agent-targets
echo "$SELECTED_RUNTIMES" >> .agent-targets
log_success "Saved target runtimes to .agent-targets"

# Determine which runtimes are active
declare -A ACTIVE_TARGETS=()
if [[ "$SELECTED_RUNTIMES" == "all" ]]; then
  ACTIVE_TARGETS["gemini"]=1
  ACTIVE_TARGETS["claude"]=1
  ACTIVE_TARGETS["github"]=1
  ACTIVE_TARGETS["openai"]=1
else
  IFS=',' read -ra PARTS <<< "$SELECTED_RUNTIMES"
  for p in "${PARTS[@]}"; do
    cleaned="$(echo "$p" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    case "$cleaned" in
      gemini|g) ACTIVE_TARGETS["gemini"]=1 ;;
      claude|c) ACTIVE_TARGETS["claude"]=1 ;;
      github|gh|copilot|p) ACTIVE_TARGETS["github"]=1 ;;
      openai|codex|o) ACTIVE_TARGETS["openai"]=1 ;;
      all)
        ACTIVE_TARGETS["gemini"]=1
        ACTIVE_TARGETS["claude"]=1
        ACTIVE_TARGETS["github"]=1
        ACTIVE_TARGETS["openai"]=1
        ;;
    esac
  done
fi

# Prune unselected runtime files/directories from disk
if [[ -z "${ACTIVE_TARGETS["gemini"]:-}" ]]; then
  log_info "Pruning unselected Gemini / Antigravity projections..."
  rm -rf .agents/skills GEMINI.md
  rmdir .agents 2>/dev/null || true
fi

if [[ -z "${ACTIVE_TARGETS["claude"]:-}" ]]; then
  log_info "Pruning unselected Claude Code projections..."
  rm -rf .claude CLAUDE.md
fi

if [[ -z "${ACTIVE_TARGETS["github"]:-}" ]]; then
  log_info "Pruning unselected GitHub Copilot projections..."
  rm -rf .github/copilot-instructions.md .github/instructions .github/prompts
fi

if [[ -z "${ACTIVE_TARGETS["openai"]:-}" ]]; then
  log_info "Pruning unselected OpenAI / Codex projections..."
  rm -rf .openai
fi

# Run generator to project all active targets fresh
log_info "Generating runtime adapter projections..."
uv run python context/scripts/generators/generate_adapters.py -a
log_success "Runtime projections generated and synchronized"

# ── 5. Lockfiles & Dependencies ───────────────────────────────────────────────
log_step "Step 5: Updating Lockfiles & Dependencies"

log_info "Upgrading uv lockfile..."
uv lock --upgrade
log_info "Syncing Python virtual environment..."
uv sync
log_success "Python dependencies synchronized"

# If package.json exists, update Yarn / Node dependencies
if [[ -f "package.json" ]]; then
  log_info "package.json detected. Synchronising Node/Yarn dependencies..."
  if command -v yarn &>/dev/null; then
    yarn install
    log_success "Yarn dependencies installed"
  fi
fi

# ── 6. Workflows, Pre-Commit & Artefacts Reset ─────────────────────────────────
log_step "Step 6: Workflows, Pre-commit Hooks & Artefacts Reset"

# Activate pre-commit configuration
if [[ -f "context/scripts/pre-commit-config-template.yaml" ]]; then
  cp -f context/scripts/pre-commit-config-template.yaml .pre-commit-config.yaml
  log_success "Installed .pre-commit-config.yaml from template"
fi

# Install pre-commit hooks
if command -v uv &>/dev/null; then
  log_info "Activating git pre-commit hooks..."
  uv run pre-commit install >/dev/null 2>&1 || true
  uv run pre-commit install --hook-type commit-msg >/dev/null 2>&1 || true
  log_success "Git hooks activated (pre-commit, commit-msg)"
fi

# Reset historical framework artefacts and ensure canonical directories
log_info "Resetting artefacts folder structure..."
rm -rf \
  artefacts/build/tasks-align-framework.md \
  artefacts/build/tasks-context-framework.md \
  artefacts/build/agent-incidents.md \
  artefacts/build/fixtures-directory.md \
  artefacts/build/mocks-directory.md \
  artefacts/build/new-devx \
  artefacts/build/archive \
  output.log

mkdir -p artefacts/shared/{handoffs,fixtures,mocks}
mkdir -p artefacts/{product,architecture,design,api,build,test-results}
touch artefacts/shared/handoffs/.gitkeep artefacts/shared/fixtures/.gitkeep artefacts/shared/mocks/.gitkeep
log_success "Artefacts folder structure clean and ready"

# ── 7. Project Metadata & Git Remote ──────────────────────────────────────────
log_step "Step 7: Updating Project Metadata & Remote"

# Update pyproject.toml name and description
if [[ -n "$SELECTED_PROJECT_NAME" ]]; then
  uv run python -c "
import sys
pname = sys.argv[1]
pdesc = sys.argv[2]
with open('pyproject.toml', 'r') as f:
    lines = f.readlines()
with open('pyproject.toml', 'w') as f:
    for line in lines:
        if line.startswith('name = '):
            f.write(f'name = \"{pname}\"\n')
        elif line.startswith('description = '):
            f.write(f'description = \"{pdesc}\"\n')
        else:
            f.write(line)
" "$SELECTED_PROJECT_NAME" "$SELECTED_PROJECT_DESC"

  # Update top of README.md
  uv run python -c "
import sys
pname = sys.argv[1]
pdesc = sys.argv[2]
with open('README.md', 'r') as f:
    lines = f.readlines()
if lines:
    lines[0] = f'# {pname.replace(\"-\", \" \").title()}\n'
    if len(lines) > 2 and lines[1] == '\n':
        lines[2] = f'{pdesc}\n'
with open('README.md', 'w') as f:
    f.writelines(lines)
" "$SELECTED_PROJECT_NAME" "$SELECTED_PROJECT_DESC"

  log_success "Updated metadata in pyproject.toml and README.md"
fi

# Update git remote origin if specified
if [[ -n "$SELECTED_GIT_REMOTE" ]]; then
  if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$SELECTED_GIT_REMOTE"
  else
    git remote add origin "$SELECTED_GIT_REMOTE"
  fi
  log_success "Updated git remote origin to: $SELECTED_GIT_REMOTE"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}================================================================${NC}"
echo -e "${BOLD}${GREEN}  Project Initialisation & Freshening Complete!${NC}"
echo -e "${BOLD}${GREEN}================================================================${NC}"
echo -e "  • Project Name:     ${BOLD}$SELECTED_PROJECT_NAME${NC}"
echo -e "  • Target Runtimes:  ${BOLD}$SELECTED_RUNTIMES${NC}"
echo -e "  • Typesetting:      ${BOLD}$SELECTED_TYPST${NC}"
echo -e "  • Active Hooks:     pre-commit, commit-msg"
echo -e "\n${BOLD}Next steps:${NC}"
echo -e "  1. Review requirements straw-man: ${BLUE}artefacts/product/requirements.md${NC}"
echo -e "  2. Review bootstrap workflow:     ${BLUE}context/skills/bootstrap-workflow.md${NC}"
echo -e "  3. Verify clean pre-commit run:   ${BLUE}uv run pre-commit run --all-files${NC}\n"
