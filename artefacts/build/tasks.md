# Tasks: 100-Ideas Agentic Publishing System

---

## Header

**Branch**: `feature/requirements`
**Status**: In Progress
**Scope**: Agentic content pipeline automating the transformation of 100 ideas into a typeset Typst book and publication-ready blog posts.
**Design**: [requirements.md](file:///Users/avi/Repos/100-ideas/artefacts/product/requirements.md)
**Created**: 2026-09-17
**Amended**: 2026-09-17 — Initial task breakdown and workflow/agent tracking setup

---

## Task Index

| ID | Pri | Status | Blocked By | Task |
|---|---|---|---|---|
| TASK-001 | critical | completed | - | Define product requirements in `artefacts/product/requirements.md` |
| TASK-002 | high | completed | TASK-001 | Audit existing agents/workflows vs new agent needs and document mapping |
| TASK-003 | high | completed | TASK-002 | Evaluate workflow reuse (`content.yaml`) and CLI delegation model |
| TASK-004 | high | completed | TASK-002 | Reuse existing agents via lean deterministic CLI execution |
| TASK-005 | medium | completed | TASK-003, TASK-004 | Run `uv run agent-harness` to compile adapters and verify zero drift (`uv run agent-drift`) |
| TASK-006 | high | completed | TASK-001 | Resolve `100-ideas.md` symlink/sandbox ingestion and test batch catalog parsing |
| TASK-007 | medium | completed | TASK-006 | Implement incremental inbox ingestion parser (`artefacts/product/inbox.md`) |
| TASK-008 | high | completed | - | Implement shared M:N resource library indexing and idea linking |
| TASK-009 | high | completed | - | Implement visual prompt derivation and editorial image generation engine |
| TASK-010 | high | completed | - | Implement Book Mode drafting (author persona) and Typst typesetting pipeline |
| TASK-011 | high | completed | - | Implement Blog Mode drafting (author persona), Hostinger frontmatter, and LinkedIn exports |
| TASK-012 | medium | completed | TASK-008 | Verify Markdown portability export bundling and GFM compatibility |
| TASK-013 | high | completed | - | Implement batch processing and pipeline runner in CLI (REQ-ORC-001 - REQ-ORC-005) |
| TASK-014 | high | in-progress | - | Verify and validate all Non-Functional Requirements (NFR-TOK, NFR-QLT, NFR-EXT) |

---

## Specifications

### TASK-001: Define Product Requirements
- **Status**: Completed
- **Acceptance Criteria**:
  - Structured EARS notation in `artefacts/product/requirements.md`.
  - Defined dual-path ingestion, M:N shared resource library, book & blog modes, and token governance.

### TASK-002: Audit Existing Agents and Workflows
- **Status**: Completed
- **Description**: Review existing agents (`product-expert`, `documentation`, `ui-designer`, `orchestrator`) and workflows (`context/workflows/content.yaml`) to determine which can be reused directly vs where new specialised definitions are required.
- **Acceptance Criteria**:
  - Mapping matrix produced comparing required pipeline roles to existing agents.
  - Documented in `artefacts/architecture/agent-app-architecture-comparison.md`.

### TASK-003: Pipeline Workflow Definition & CLI Integration
- **Status**: Completed
- **Description**: Reused the content workflow patterns via CLI-delegated deterministic scripts (`ideas pipeline`), avoiding unnecessary duplicate harness workflows while keeping context lean.
- **Acceptance Criteria**:
  - Valid CLI dispatcher in `services/ingestion/cli.py`.
  - Lean prompt overhead (< 4,000 tokens).

### TASK-004: Agent Lifecycle & Reuse Governance
- **Status**: Completed
- **Description**: Reused existing harness agents and personas (`author.md`) in combination with deterministic Python microservices rather than authoring redundant agent personas.
- **Acceptance Criteria**:
  - Preserved existing agent taxonomy with full compliance to `agent-standards.md`.

### TASK-005: Adapter Compilation & Drift Check
- **Status**: Completed
- **Description**: Run `uv run agent-harness` to project context definitions into runtime adapters (`AGENTS.md`, `GEMINI.md`) and verify zero drift.
- **Acceptance Criteria**:
  - `uv run agent-drift` exits with code 0.

### TASK-008: Shared M:N Resource Library Indexing & Idea Linking
- **Status**: Completed
- **Description**: Implement shared resource loader in `services/enrichment/resource_library.py` and research synthesiser in `services/enrichment/researcher.py` that extracts empirical evidence, economic trade-offs, and counterarguments to `research/notes.md`.
- **Acceptance Criteria**:
  - Verified resource links from `manifest.yaml` and tag overlap.
  - Generates structured markdown notes with mandatory sections.
  - Idempotent execution unless forced.

### TASK-009: Visual Prompt Derivation & Editorial Image Generation
- **Status**: Completed
- **Description**: Implement prompt generator in `services/enrichment/visuals.py` producing metaphorical prompts and valid PNG binaries without third-party graphics dependencies.
- **Acceptance Criteria**:
  - Valid PNG binary starting with `\x89PNG\r\n\x1a\n` saved to `assets/illustration.png`.
  - Negative constraints avoid AI art clichés.
  - Independent `--regenerate-image` preserves research notes.

### TASK-010: Book Mode Drafting & Typst Typesetting Pipeline
- **Status**: Completed
- **Description**: Implement chapter drafter adopting the AS author persona, Markdown-to-Typst translator, and Typst compiler producing single-chapter and aggregated book PDFs.
- **Acceptance Criteria**:
  - Chapter draft strictly adheres to `context/persona/author.md` (punch over preamble, plain language, information density, economic equation, hype puncturing, bold lead-in takeaways).
  - Semantic Markdown converted to Typst markup embedding callouts, comparison tables, and illustrations.
  - Typst CLI invokes `neutral.typ` to produce valid publication-grade PDFs for single chapters and aggregated multi-chapter volumes with Table of Contents.
  - Idempotent CLI execution via `ideas draft` and `ideas typeset`.

### TASK-011: Blog Mode Drafting, Hostinger Frontmatter, and LinkedIn Exports
- **Status**: Completed
- **Description**: Implement blog drafter adopting Dr Sarah Chen opinionated blogger persona, Hostinger-compatible YAML frontmatter generation, companion LinkedIn post export, and configurable CMS publishing adapters.
- **Acceptance Criteria**:
  - Article draft strictly adheres to `context/persona/opinionated-blogger.md` (provocative opening hook, conversational parentheticals, question-driven sections, "So What?" analysis, and 400-800 word count).
  - Hostinger blog post saved to `artefacts/content/ideas/{idea-id}/blog/post.md` with standardised YAML frontmatter (`title`, `slug`, `date`, `excerpt`, `tags`, `cover_image`).
  - Companion LinkedIn post saved to `artefacts/content/ideas/{idea-id}/blog/linkedin.md` with high-converting hook, 3-5 scannable bullets, CTA, hashtags, and < 3,000 characters.
  - CMS adapter engine configurable via `config/publishing.yaml` supporting WordPress, Ghost, and Static Astro/Hugo outputs.
  - Idempotent CLI integration via `ideas blog` and `ideas social`.



