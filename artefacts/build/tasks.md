# Tasks: 100-Ideas Agentic Publishing System

---

## Header

**Branch**: `feature/requirements`
**Status**: In Progress
**Scope**: Agentic content pipeline automating the transformation of 100 ideas into a typeset Typst book and publication-ready blog posts.
**Design**: [requirements.md](file:///Users/avi/Repos/100-ideas/artefacts/product/requirements.md), [review-continuous-publishing.md](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md)
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
| TASK-014 | high | completed | - | Verify and validate all Non-Functional Requirements (NFR-TOK, NFR-QLT, NFR-EXT) |
| TASK-015 | critical | completed | TASK-014 | Solution Architect Review: Continuous Ingestion, Human-in-the-Loop, and Multi-Volume Architecture |
| TASK-016 | high | completed | TASK-015 | Refactor continuous ingestion lifecycle, inbox archiving, and decouple idea ID from chapter numbers |
| TASK-017 | high | completed | TASK-015 | Implement multi-volume book mapping configuration (`config/volumes.yaml`) and compilation |
| TASK-018 | high | pending | TASK-015 | Implement state machine and manual edit protection safeguards (`human_modified`) in `meta.yaml` |
| TASK-019 | medium | pending | TASK-018 | Implement interactive agentic chat revision loop and hierarchical channel syndication (SSOT) |
| TASK-020 | high | pending | TASK-015 | Implement live Gemini Python SDK integration, prompt caching, and `gemini-sdk` skill |

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

### TASK-015: Solution Architect Review: Continuous Ingestion, Human-in-the-Loop, and Multi-Volume Architecture
- **Status**: Completed
- **Assignee**: `@solution-architect`
- **Description**: Conduct comprehensive architectural review to address false assumptions: redesign ingestion for irregular inbox intake, define human-in-the-loop revision model, establish multi-volume publishing schema, and design live Gemini SDK integration with token governance.
- **Acceptance Criteria**:
  - Updated `artefacts/architecture/architecture.md` detailing the revised component boundaries and state machines.
  - Updated `artefacts/architecture/data-model.md` defining volume mapping, inbox lifecycle, and `meta.yaml` state fields.
  - Review sign-off document produced in `artefacts/architecture/review-continuous-publishing.md`.

### TASK-016: Continuous Ingestion Lifecycle & ID Decoupling
- **Status**: Completed
- **Architecture Reference**: [review-continuous-publishing.md §3](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md#3-continuous-ingestion-lifecycle--decoupled-id-architecture) (Resolves DEF-001, DEF-002)
- **Description**: Refactor ingestion subsystem to support continuous and irregular intake via `inbox.md`. Move processed inbox entries to `inbox-archive.md` (or update with status markers). Decouple internal idea identifiers (e.g. `idea-<slug>` or stable sequence) from publication chapter numbering. Remove hardcoded `max_id_num = 100` ceiling in `cli.py`.
- **Acceptance Criteria**:
  - Ingesting an idea from `inbox.md` updates the inbox file without re-parsing processed items on subsequent runs.
  - Processed ideas archived into `artefacts/product/inbox-archive.md` with timestamp and target ID.
  - Ideas can have arbitrary stable identifiers (supporting >100 ideas), with chapter numbering assigned dynamically during book assembly.
  - Dynamic index calculation (`get_next_idea_number`) without hardcoded 100 limit.

### TASK-017: Multi-Volume Book Configuration & Mapping
- **Status**: Completed
- **Architecture Reference**: [review-continuous-publishing.md §4](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md#4-multi-volume-book-configuration--compilation-configvolumesyaml) (Resolves DEF-002)
- **Description**: Implement flexible volume mapping configuration (`config/volumes.yaml`) allowing arbitrary ideas to be mapped to specific volumes (e.g. 100 ideas per book, thematic volumes), parts, and ordered chapter slots. Update Typst compiler to generate volume-specific PDFs with dedicated TOC and introduction.
- **Acceptance Criteria**:
  - Valid schema in `config/volumes.yaml` defining volumes, metadata, parts, and ordered lists of idea IDs.
  - `ideas typeset --volume <volume_id>` compiles only the ideas assigned to that volume.
  - Idea chapter numbers and running headers in Typst match their assigned position within the volume, not their raw database ID.

### TASK-018: Human-in-the-Loop Safeguards & State Machine
- **Status**: Pending
- **Architecture Reference**: [review-continuous-publishing.md §5](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md#5-human-in-the-loop--state-machine-architecture) (Resolves DEF-003, DEF-005)
- **Description**: Add workflow state machine and manual edit protection to `meta.yaml` (`stage: raw | research_ready | draft_in_progress | human_review | approved | published`, `human_modified: bool`). Prevent `--force` from destroying human edits to `chapter.md`, `post.md`, or `notes.md` unless an explicit `--overwrite-manual` flag is supplied. Incorporate editorial quality gates (voice fidelity check against `context/persona/author.md`) and dual-target asset path resolution (Typst figure embedding vs. CMS publishing staging).
- **Acceptance Criteria**:
  - `meta.yaml` tracks lifecycle stage, edit timestamps, review status, and human modification flag.
  - CLI operations refuse to overwrite files marked `human_modified: true` without explicit `--overwrite-manual`.
  - Editorial quality gate validates voice fidelity (British English, bold lead-ins, economic realism) before moving an idea from `draft_in_progress` to `approved`.
  - Downstream drafting consumes existing `research/notes.md` content rather than ignoring it.
  - Asset path resolver handles both relative figure paths for Typst compilation and web-ready image paths for CMS publishing.

### TASK-019: Interactive Agentic Chat Revision Loop & Channel Syndication
- **Status**: Pending
- **Architecture Reference**: [review-continuous-publishing.md §7 & §8](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md#7-single-source-of-truth-ssot-syndication-model) (Resolves DEF-006)
- **Description**: Implement interactive agent revision interface allowing conversational refinement of drafted text, selective prompt adjustment, and section-by-section regeneration. Refactor Blog Mode and Social Mode to syndicate from the approved master chapter manuscript (Single Source of Truth) rather than diverging from the raw synopsis.
- **Acceptance Criteria**:
  - Agentic chat interaction protocol defined for iterative review and revision.
  - Blog post and LinkedIn post generators can consume approved `book/chapter.md` to extract core arguments and ensure channel alignment.
  - Refinement commands support targeted section updates without rewriting entire documents.

### TASK-020: Live Gemini Python SDK Integration, Token Guard Rails & `gemini-sdk` Skill
- **Status**: Pending
- **Architecture Reference**: [review-continuous-publishing.md §6](file:///Users/avi/Repos/100-ideas/artefacts/architecture/review-continuous-publishing.md#6-live-gemini-sdk-integration-google-genai--token-governance) (Resolves DEF-004)
- **Description**: Author the canonical `gemini-sdk` skill (`context/skills/gemini-sdk.md` and projected `.agents/skills/gemini-sdk/SKILL.md`) providing procedural guidance for modern `google-genai` Python SDK patterns (client initialization, Pydantic structured output, Gemini Context Caching, Imagen 3, and token telemetry). Implement robust token burn guard rails and circuit breakers across `services/enrichment/` and `services/typesetting/` to prevent runaway API spend during live execution. Integrate `google-genai` into `services/enrichment/researcher.py` and `services/typesetting/drafter.py` using tiered models (`gemini-2.5-flash`, `gemini-2.5-pro`, `imagen-3.0`).
- **Token Burn Guard Rails**:
  1. **Pre-Flight Cost Estimator & `--dry-run`**: CLI commands calculate exact prompt token count and projected USD cost before dispatching any live API request.
  2. **Hard Spend Circuit Breaker**: Configurable run and session budget caps in `.env` (`MAX_SESSION_SPEND_USD`, default `$2.00`; `MAX_IDEA_TOKENS`, default 50,000 tokens). Exceeding budget raises `BudgetExhaustedError` and halts all execution immediately.
  3. **Cryptographic Input Fingerprinting**: Computes SHA-256 hash of `(model + prompt + input_documents)`. If `meta.yaml` contains a matching execution fingerprint, live API calls are completely suppressed (zero token burn) unless `--force-llm` is explicitly passed.
  4. **Context Clamping**: Hard cap on un-cached input context (maximum 12,000 tokens per call) preventing runaway file ingestion from overloading prompts.
  5. **Sequential Concurrency**: Enforces strictly sequential processing (`concurrency=1`) for batch LLM operations to eliminate runaway parallel token burn and rate limit throttling.
  6. **Interactive Batch Confirmation**: Running `--all` or multi-idea ranges displays aggregate estimated token count and USD cost, requiring explicit user approval (`[y/N]`) before any API calls fire unless `--yes` is supplied.
- **Acceptance Criteria**:
  - Canonical `gemini-sdk` skill authored and projected with zero adapter drift (`uv run agent-drift` passes).
  - Secure API key resolution from `.env` via `python-dotenv` without committing secrets.
  - Research synthesis directly extracts empirical data, trade-offs, and grounded citations from linked `artefacts/content/resources/` using Gemini context caching rather than regex keyword matching.
  - Prompt caching active for reusable context (> 32k tokens or shared resource library), dramatically reducing token costs.
  - Pre-flight token and cost estimation verified via `--dry-run`.
  - Circuit breaker verified with unit tests simulating budget exhaustion and asserting execution halts cleanly.
  - Token telemetry (cached tokens, prompt tokens, completion tokens, latency, cost estimate) recorded in `meta.yaml`.
  - Offline fallback / mock mode retained for fast local testing.



