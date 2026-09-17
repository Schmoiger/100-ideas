---
name: bootstrap-workflow
description: Procedural workflow for bootstrapping a new project or feature context.
globs: []
---

# Bootstrap Workflow Skill

---

## Overview

This skill provides the procedural steps for an agent to set up the necessary context documents, placeholders, and scripts when assigned to work on a new product or feature.

---

## 1. Product Description Verification

- If no product description is provided in the initial context, the agent shall request one from the user.
- The product description shall include sufficient detail about the purpose, target users, and key functionality to enable proper requirements analysis.

---

## 2. Common Subrepositories

If the project requires standardised context rules or PDF generation/typesetting, the agent shall clone the standard subrepositories using `git subrepo` if they are not already present:

- **Context Subrepo**:
  ```bash
  PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clone https://github.com/Schmoiger/agents-framework.git context -b main
  ```
- **Typst Subrepo**:
  ```bash
  PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clone https://github.com/Schmoiger/typst-engine.git typst -b main
  ```

*For more information on operating subrepositories, refer to `context/skills/git-subrepo-operations.md`.*

---

## 3. Documentation Creation Sequence

After obtaining the product description, the agent shall create or amend the following documents in strict order:

1. **`/artefacts/requirements.md`**: Functional and non-functional requirements capturing user intent and structured using EARS notation, following the procedural guide in `context/skills/intent-fidelity.md`.

2. **`/artefacts/architecture.md`**: Architectural and design decisions describing system boundaries, data flow, and contracts, following the procedural guide in `context/skills/architecture-fidelity.md`.

3. **`{service}/artefacts/tasks.md`**: Comprehensive task breakdown with direct requirement traceability and verifiable acceptance criteria, following `context/skills/intent-fidelity.md`.

*If system diagrams or entity relationships are required in these documents, follow the syntax and layout conventions in `context/skills/mermaid-authoring.md`.*

**For each document created or amended, the agent shall pause and wait for explicit human review and approval before proceeding to the next document.**

---

## 4. Placeholder Document Creation

Following the core specification documents, the agent shall create blank placeholder documents:

- **`{service}/artefacts/todo.md`**: For listing smaller items, technical debt, or future improvements.
- **`{service}/artefacts/bugs.md`**: For listing current and past bugs.

---

## 5. Documentation Standards Compliance

All documentation created during this workflow shall conform to the standards outlined in `context/standards/doc-standards.md`, including:

- Proper file location within the project structure (system-wide in `/artefacts/`, service-specific in `{service}/artefacts/`)
- Content formatting and structure requirements
- Required elements for requirements (`context/skills/intent-fidelity.md`), architecture decisions (`context/skills/architecture-fidelity.md`), and task specifications

---

## 6. Start Scripts

The agent shall create `(project)/scripts/start.sh` for local development startup and a root-level start script for the monorepo. The root-level script orchestrates starting all the needed local services.

---

## 7. Build Script

The agent shall create `scripts/build.yaml` following the standards in `context/standards/build-standards.md`.

---

## 8. Pre-Commit Hook Activation

To enforce repository rules and invariants automatically at commit time, the agent shall activate the pre-commit configuration and install git hooks:

1. Copy the pre-commit configuration template to the repository root:
   ```bash
   cp context/scripts/pre-commit-config-template.yaml .pre-commit-config.yaml
   ```

2. Ensure `pre-commit` is available as a development dependency:
   ```bash
   uv add --dev pre-commit
   ```

3. Install the pre-commit hooks for both code changes and commit messages:
   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type commit-msg
   ```

4. Run pre-commit across all files to verify baseline repository integrity:
   ```bash
   uv run pre-commit run --all-files
   ```

---

## 9. Workflow Completion

- Upon completion of all build work, the agent shall review common documents as outlined in `context/standards/doc-standards.md` and make very concise changes as required, in particular:
  - `README.md` (service root)
  - Project-specific artefacts in `{service}/artefacts/`

- Upon completion of all documents, the agent shall summarise what was created and confirm with the user before beginning any implementation work.
- The agent shall not commence task execution until all context documents have been reviewed and approved by humans.
