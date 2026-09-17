# Rule Validators

Automated validators mapping to canonical rules in `context/rules/*.md`.

---

## Overview

Validators in this directory enforce invariants defined in `context/rules/` wherever there is concrete, verifiable file output to test (e.g. committed files, schemas, dependencies, format syntax). Rules governing runtime tool usage (e.g. executing with `uv` instead of `pip`) are enforced via prompt instructions and agent sandboxes rather than static output validators.

Additionally, this directory hosts standalone utility validators for repository integrity, formatting, and projection synchronisation.

### Rule-Mapped Validators

| Rule File | Validator Script | Enforced Invariants |
|---|---|---|
| [`workspace-conventions.md`](../../rules/workspace-conventions.md) | `workspace_conventions.py` | Conventional commit message format (`{type}({scope}): {desc}`), `Agent-Session` trailer, metrics JSONL schema, output directory structure and file naming |
| [`tech-writing.md`](../../rules/tech-writing.md) | `tech_writing.py` | British English spelling (`-ise`, `-our`, `-re`, `licence`, `artefact`), date format DD/MM/YYYY, EARS requirement syntax (`requirements.md`, `user-stories.md`) |
| [`ui-dev.md`](../../rules/ui-dev.md) | `ui_dev.py` | Prohibit `!important`, prohibit raw hex colour codes, single `index.css`, DaisyUI semantic tokens, Heroicons barrel, spacing scale |
| [`supabase.md`](../../rules/supabase.md) | `supabase.py` | Prohibit Supabase client imports outside database service / stores, require `schema_migrations` audit insert in SQL migrations |
| [`testing.md`](../../rules/testing.md) | `testing.py` | Assert on outcomes, not interactions; prohibit interaction-based assertions (`mock.assert_called_once_with`) on internal collaborators |
| [`typescript-environment.md`](../../rules/typescript-environment.md) | `typescript_environment.py` | Prohibit `package-lock.json` (enforce `yarn.lock`), require strict compiler options in `tsconfig.json`, check root `package.json` workspaces |
| [`ui-testing.md`](../../rules/ui-testing.md) | `ui_testing.py` | Prohibit full `puppeteer` (require `puppeteer-core`), prohibit `playwright` and `cypress` in `package.json` dependencies |
| [`secrets.md`](../../rules/secrets.md) | `secrets.py` | Scan for hardcoded credentials, API keys, private key blocks, `.env` files with credentials, secrets outside `/secrets/` |

### Excluded Rules (Tool Execution & Runtime Behavior)

The following rules govern real-time agent execution choices or runtime protocols and do not have static output validators:
- `bash-environment.md`: Tool substitutions, sandbox flags, bash pipe syntax, safe command invocation.
- `python-environment.md`: Runtime command invocations (`uv run` vs `pip`, `--project`).
- `multi-agent-collaboration.md`: Runtime handoff protocols and escalation triage matrices.

### Additional Purpose Validators (Non-Rule Utilities)

- **`agent_definitions.py`**: Validates agent definition frontmatter, references to rules/standards/skills, and structural integrity in `context/agents/*.md`.
- **`adapter_drift.py`**: Validates synchronisation between canonical `context/` definitions and on-disk runtime adapter projections (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.claude/`, `.github/`, `.openai/`, `.agents/skills/`).
- **`verify_typst_formatting.py`**: Enforces Typst-friendly Markdown formatting (at least 2 blank lines after mermaid code fences, horizontal rule `---` before `##` section headings).
- **`framework_docs_staleness.py`**: Ensures architectural documentation (`agentic-framework-reference.md`, `agentic-framework.md`) is updated alongside changes to `context/`.

---

## Installation

Install pre-commit hooks:

```bash
uv add --dev pre-commit
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

---

## Usage

### Manual Validation

Run individual rule validators:

```bash
# Validate commit message
uv run python context/scripts/validators/workspace_conventions.py commit-msg .git/COMMIT_EDITMSG

# Validate metrics log
uv run python context/scripts/validators/workspace_conventions.py metrics metrics/session-log.jsonl

# Validate output paths
uv run python context/scripts/validators/workspace_conventions.py paths artefacts/build/tasks.md

# Validate requirements file (EARS notation + British English)
uv run python context/scripts/validators/tech_writing.py ears artefacts/product/requirements.md

# Validate British English spelling
uv run python context/scripts/validators/tech_writing.py spelling README.md

# Validate UI styling invariants
uv run python context/scripts/validators/ui_dev.py

# Validate Supabase import boundaries and migrations
uv run python context/scripts/validators/supabase.py

# Validate testing mock constraints
uv run python context/scripts/validators/testing.py

# Validate TypeScript environment & tsconfig strictness
uv run python context/scripts/validators/typescript_environment.py

# Validate UI testing dependencies in package.json
uv run python context/scripts/validators/ui_testing.py

# Scan for committed secrets
uv run python context/scripts/validators/secrets.py

# Check runtime adapter projections for drift
uv run python context/scripts/validators/adapter_drift.py

# Validate agent definition schemas
uv run python context/scripts/validators/agent_definitions.py

# Verify and fix Typst markdown formatting
uv run python context/scripts/validators/verify_typst_formatting.py --staged
```

### Pre-Commit Hooks

Hooks run automatically on commit:

```bash
git commit -m "feat(validation): refactor rule validators"
```

Run manually across all files:

```bash
uv run pre-commit run --all-files
```

---

## Validator Details

### 1. Workspace Conventions (`workspace_conventions.py`)

Validates invariants from `context/rules/workspace-conventions.md`.

- **Commit Messages**: `{type}({scope}): {description}` subject, max 72 chars, imperative mood, lowercase alphanumeric scope.
- **Agent Trailers**: Validates `Agent-Session: tool=... model=... agents=...` and ensures `Co-Authored-By:` is present.
- **Metrics Logging**: Ensures JSONL entries in `metrics/` match schema (`ts`, `task`, `agent`, `event`, `tokens`), valid events (`start`, `handoff`, `escalate`, `complete`, `blocked`), and `to` field for handoffs.
- **Output Locations**: Verifies outputs land in designated directories (`artefacts/`, `secrets/`, `services/{name}/tests/`) with standard naming (`v2-{task-id}-results.txt`).

### 2. Technical Writing (`tech_writing.py`)

Validates invariants from `context/rules/tech-writing.md`.

- **British English**: Flags American spelling (`color` -> `colour`, `behavior` -> `behaviour`, `-ize` -> `-ise`, `center` -> `centre`, `license` (noun) -> `licence`, `artifact` -> `artefact`).
- **EARS Notation**: Enforces Easy Approach to Requirements Syntax for lines containing "shall" in requirement documents (`requirements.md`, `user-stories.md`):
  * Ubiquitous: `THE {system} SHALL {action}`
  * Event: `WHEN {trigger}, THE {system} SHALL {action}`
  * State: `WHILE {state}, THE {system} SHALL {action}`
  * Optional: `IF {condition}, THE {system} SHALL {action}`
  * Forbidden: `THE {system} SHALL NOT {action}`
  * Complex: `WHEN {trigger}, IF {condition}, THE {system} SHALL {action}`

### 3. UI Development (`ui_dev.py`)

Validates invariants from `context/rules/ui-dev.md`.

- Prohibits `!important` in `.tsx`, `.css`, `.scss`.
- Prohibits raw hex colour codes (requires DaisyUI semantic tokens).
- Enforces single `index.css` under `frontend/src` (no component-scoped CSS/SCSS).
- Prohibits concrete Tailwind colour classes for data-meaningful UI.
- Prohibits direct `@heroicons/react` imports outside `HeroIcons.tsx` barrel.
- Enforces allowed spacing scale (`gap-1`, `gap-2`, `gap-4`, `p-2`, `p-4`, `px-4`).

### 4. Supabase (`supabase.py`)

Validates invariants from `context/rules/supabase.md`.

- Prohibits `import supabase`, `from supabase`, or `@supabase/supabase-js` outside `database_service`, `database/`, or `stores/`.
- Verifies SQL migration files in `**/migrations/*.sql` insert an audit row into `schema_migrations`.

### 5. Testing Invariants (`testing.py`)

Validates invariants from `context/rules/testing.md`.

- Enforces outcome-based assertions instead of interaction-based assertions.
- Flags interaction assertions (`mock.assert_called_once_with`, `assert_called_with`, `toHaveBeenCalledWith`) on internal collaborators.
- Mocks at external I/O boundaries are permitted when marked with `# io-boundary` or `// io-boundary`.

### 6. TypeScript Environment (`typescript_environment.py`)

Validates invariants from `context/rules/typescript-environment.md`.

- Prohibits `package-lock.json` across the repository (project strictly uses Yarn Berry and `yarn.lock`).
- Enforces `strict: true`, `noImplicitAny: true`, and `strictNullChecks: true` in `tsconfig.json` files.
- Ensures all subprojects containing `package.json` are declared in root `package.json` `workspaces`.
- Flags banned `npm`/`npx` scripts in `package.json`.

### 7. UI Testing (`ui_testing.py`)

Validates invariants from `context/rules/ui-testing.md`.

- Prohibits full `puppeteer` package in `package.json` (requires lightweight `puppeteer-core`).
- Prohibits heavy testing frameworks: `playwright`, `@playwright/test`, and `cypress`.

### 8. Secrets Invariants (`secrets.py`)

Validates invariants from `context/rules/secrets.md`.

- Scans source files and staged changes for committed secrets, API keys, and private key blocks (`BEGIN PRIVATE KEY`).
- Flags any `.env` files containing credentials.
- Enforces that API keys and service accounts must live in `/secrets/*.json` (gitignored).

---

## Exit Codes

All validators follow standard exit code conventions:

- `0` - Validation passed
- `1` - Validation failed (with diagnostic error messages on stderr)

---

## References

- Rule definitions: `context/rules/*.md`
- Python scripting standards: `context/skills/python-scripting.md`
- Pre-commit documentation: <https://pre-commit.com/>
- Conventional Commits: <https://www.conventionalcommits.org/>
- EARS notation: <https://www.researchgate.net/publication/224079253_Easy_Approach_to_Requirements_Syntax_EARS>
