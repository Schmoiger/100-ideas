# Context & Documentation Unit Tests

Unit tests for validating context documentation consistency, frontmatter, and cross-references.

For tests covering runtime adapters, generators, and pre-commit validators, see [`context/scripts/tests/`](../../context/scripts/tests/README.md).

---

## Quick Start

```bash
# Install dependencies (using uv per tech-standards.md)
cd tests/context-unit-tests
uv sync

# Run all Python tests
uv run pytest . -v

# Run LLM consistency check (requires API key)
ANTHROPIC_API_KEY=your-key uv run pytest test_llm_consistency.py -v
```

---

## Test Files

| File | Description | LLM Required |
|------|-------------|--------------|
| `test_doc_format.py` | Validates YAML frontmatter, required sections, markdown syntax | No |
| `test_references.py` | Validates cross-references between docs, agent-standards consistency | No |
| `test_llm_consistency.py` | Semantic consistency checks via LLM call | Yes |

---

## Running Tests

### Static Analysis (Fast, No LLM)

Run on every PR - these tests are fast and don't require API keys:

```bash
cd tests/context-unit-tests

# Format validation
uv run pytest test_doc_format.py -v

# Cross-reference validation
uv run pytest test_references.py -v
```

### LLM Consistency Check (Slow, Requires API Key)

Run periodically or on significant doc changes:

```bash
cd tests/docs-unit-tests
ANTHROPIC_API_KEY=your-key uv run pytest test_llm_consistency.py -v
```

The LLM test performs a single API call to check for:
- File reference errors
- Agent name mismatches
- Domain inconsistencies between agent-standards.md and workflow definitions
- Artifact path conflicts
- Standards contradictions
- Missing cross-references

---

## What Each Test Validates

### test_doc_format.py

**Agent Files:**
- All agent files have YAML frontmatter
- Frontmatter is valid YAML
- Required fields present: `name`, `description`
- Frontmatter `name` matches filename
- `{$ARGUMENTS}` placeholder present
- `## Constraints` section present

**Standards Files:**
- Introduction section present (warning only)

**Rules Files:**
- YAML frontmatter present (warning only)

**All Markdown:**
- No malformed link syntax

### test_references.py

- Context paths in agents reference valid patterns
- File references in standards point to existing files
- Agents listed in agent-standards.md have definition files

---

## CI Integration

The GitHub Actions workflow (`.github/workflows/docs-test.yml`) runs:

1. **lint** job: Static analysis tests (always runs, uses uv)
2. **llm-consistency** job: LLM checks (optional, requires secret)

To enable LLM tests in CI:
1. Add `ANTHROPIC_API_KEY` as a repository secret
2. Set repository variable `RUN_LLM_TESTS=true`

---

## Adding New Tests

When adding new documentation:
1. Agent definitions → Tests in `test_doc_format.py` validate automatically
2. New standards → Add to skip patterns if using example paths
3. New rules → Frontmatter optional but recommended
4. New cross-references → `test_references.py` validates automatically

---

## Dependencies

Managed via `pyproject.toml`:

```toml
[project]
dependencies = [
    "pytest>=7.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
llm = [
    "anthropic>=0.18.0",
]
```
