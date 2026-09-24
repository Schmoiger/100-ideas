# Product Requirements: 100-Ideas Agentic Publishing System

---

## 1. Executive Summary

The **100-Ideas Agentic Publishing System** is an agentic content pipeline coordinated by an orchestrator that ingests conceptual ideas from `artefacts/product/100-ideas.md`, enriches each idea with deep technical research, synthesised evidence, and dynamic illustrations generated via Gemini, and compiles them into two distinct delivery modes:
1. **Book Mode**: Transforms ideas into substantive, rigorous book chapters rendered in the authoritative voice of "AS" (`context/persona/author.md`), compiled and typeset into publication-grade documents using the embedded Typst typesetting engine (`typst/`).
2. **Blog Mode**: Adapts ideas into punchy, conversational thought-leadership articles written in an opinionated blogger persona (`context/persona/opinionated-blogger.md`), packaged with YAML frontmatter for web hosting (Hostinger) and tailored for publication on LinkedIn.

To maintain strict economy over LLM token consumption and eliminate duplicate effort, all research, core conceptual structures, and visual assets are stored in a canonical, shared intermediate representation layer (Don't Repeat Yourself - DRY) accessible across both delivery modes.

---

## 2. Legend & Prioritisation

| Symbol | Meaning | Description |
|---|---|---|
| **M** | MVP (P0) | Must have for initial functional release |
| **P** | Post-MVP (P1) | Next iteration (enhanced automation, additional targets) |
| **F** | Future (P2) | Backlog and exploratory capabilities |
| ✓ | Complete | Fully implemented and verified |
| ○ | In progress | Under active development |
| · | Pending | Scheduled for future implementation |

---

## 3. Functional Requirements

### 3.1. Idea Ingestion & Selection Subsystem

The Idea Ingestion subsystem provides two complementary intake pathways:
1. **Batch Catalogue Ingestion**: Ingests and indexes the full set of foundational ideas from `artefacts/product/100-ideas.md` for periodic or one-off bulk processing.
2. **Incremental Idea Intake (Inbox & Chat)**: Allows frequent, low-friction addition of new ideas via an append-only inbox file (`artefacts/product/inbox.md`) or directly through interactive Chat CLI commands.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-ING-001 | M | THE system SHALL parse the Markdown table in `artefacts/product/100-ideas.md` into structured records containing Idea Title, Synopsis, and Source Reference. | Parser correctly extracts all idea rows and validates non-empty title and synopsis strings. |
| REQ-ING-002 | M | WHEN an execution run is triggered, THE system SHALL support selecting ideas by single index (e.g. `--idea 1`), index range (e.g. `--ideas 1-5`), or batch execution (e.g. `--all`). | CLI and agent invocations accept individual idea identifiers, bounded numeric ranges, or full batch flags without error. |
| REQ-ING-003 | M | IF `artefacts/product/100-ideas.md` is a symbolic link resolving outside the workspace sandbox, THE system SHALL provide an automated ingestion mechanism that copies or syncs the authoritative source into the workspace boundary. | Tools executing within the standard security sandbox can read idea records without filesystem permission exceptions. |
| REQ-ING-004 | M | THE system SHALL monitor an incremental inbox file at `artefacts/product/inbox.md` to ingest newly added ideas without re-parsing or altering `100-ideas.md`. | System reads newly appended entries from `inbox.md`, assigns canonical unique identifiers, and provisions intermediate idea folders. |
| REQ-ING-005 | M | WHEN the user submits a new idea directly through the Chat CLI (e.g. "Add idea: [Title] - [Synopsis]"), THE system SHALL validate, assign a unique identifier, and provision its intermediate structure in `artefacts/content/ideas/{idea-id}/`. | System creates `meta.yaml` and initialized subdirectories immediately without requiring manual file editing. |
| REQ-ING-006 | M | WHEN ingesting an idea from `inbox.md` or Chat CLI, THE system SHALL check for title or synopsis duplication against existing records in the shared content layer. | System warns the user if a semantically similar or identically titled idea already exists before provisioning. |
| REQ-ING-007 | P | THE system SHALL allow filtering idea ingestion by tags, thematic keywords, or development lifecycle domains (e.g. Tooling, Architecture, Governance). | The orchestrator accepts a `--tag` or `--domain` filter and isolates matching idea entries from the catalogue. |

### 3.2. DRY Shared Content & Intermediate Layer

The Shared Content subsystem maintains a persistent, deduplicated intermediate representation of enriched knowledge, visual prompts, and media assets. It decouples shared reference materials from individual ideas via a **many-to-many (M:N) resource library**, ensuring that foundational whitepapers, case studies, and books are stored once and referenced by multiple ideas without content duplication.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-DRY-001 | M | THE system SHALL persist idea-specific assets under `artefacts/content/ideas/{idea-id}/` and shared reference materials under a centralised library at `artefacts/content/resources/`. | Idea folders contain `meta.yaml`, `research/`, `assets/`, `book/`, and `blog/`; shared resources reside in `artefacts/content/resources/`. |
| REQ-DRY-002 | M | THE system SHALL store execution metadata in `artefacts/content/ideas/{idea-id}/meta.yaml` including title, synopsis, linked resource IDs, timestamps, status, model tiers used, and token usage metrics. | `meta.yaml` is updated atomically upon the completion of each subagent phase with valid YAML syntax. |
| REQ-DRY-003 | M | WHEN Book Mode or Blog Mode is invoked for an idea, THE system SHALL first inspect the shared intermediate store and reuse existing research and illustrations rather than re-executing generation. | Re-running the pipeline on an already-enriched idea does not make redundant web search or image generation API calls unless `--force` is specified. |
| REQ-DRY-004 | M | THE system SHALL maintain a centralised resource library in `artefacts/content/resources/` supporting many-to-many (M:N) associations with multiple ideas. | Resources (PDFs, whitepapers, book notes, synthesised frameworks) are stored once with unique IDs and can be cited by any number of ideas. |
| REQ-DRY-005 | M | WHEN an idea is enriched, THE research agent SHALL ingest both linked shared resources from `artefacts/content/resources/` and any idea-specific materials in `artefacts/content/ideas/{idea-id}/research/`. | Research synthesiser pulls extracts, quotes, and data from linked global resources without duplicating the source files into the idea folder. |
| REQ-DRY-006 | M | WHEN an export command is issued, THE system SHALL export enriched ideas from the shared content layer as self-contained, portable Markdown bundles. | Exported files include frontmatter metadata, research summaries, drafted content, and relative links to generated illustrations without internal framework coupling. |
| REQ-DRY-007 | M | THE system SHALL support exporting either individual ideas or aggregating multiple/all ideas into a single unified Markdown document or export directory (e.g. `artefacts/content/exports/`). | CLI and chat commands accept `--idea {id}`, `--ideas {range}`, or `--all` targeting an export folder, resolving assets and references cleanly. |
| REQ-DRY-008 | P | THE system SHALL maintain an index manifest in `artefacts/content/resources/manifest.yaml` mapping resource IDs, titles, summaries, and idea citation counts. | Manifest is automatically updated when new resources are ingested or linked to ideas. |

### 3.3. Content Enrichment Subsystem (Research, Drafting, Visuals)

The Content Enrichment subsystem deploys specialised agents to expand raw synopses into substantive empirical arguments by synthesizing shared resources, idea-specific research, and custom illustrations.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-ENR-001 | M | WHEN an idea is enriched, THE research agent SHALL extract relevant context, empirical evidence, and counterarguments from linked shared resources and targeted web research, saving synthesis notes to `artefacts/content/ideas/{idea-id}/research/notes.md`. | Research notes contain verified empirical examples, economic trade-offs, and citations linking back to resource IDs without hallucinated facts. |
| REQ-ENR-002 | M | WHEN generating visuals, THE visual agent SHALL dynamically derive an image generation prompt from the idea's core thesis and metaphorical concepts. | Prompt specifies conceptual subject, composition, mood, and intentional stylistic variety to avoid monotonous imagery. |
| REQ-ENR-003 | M | THE system SHALL invoke the Gemini API / Imagen model using the derived prompt to generate an editorial illustration, persisting the output image in `artefacts/content/ideas/{idea-id}/assets/illustration.png`. | Visual file exists on disk with valid image headers, and the generation prompt is preserved in `assets/prompt.txt`. |
| REQ-ENR-004 | P | IF image generation fails or returns an unsatisfactory result, THE system SHALL allow regenerating the illustration with prompt refinement without altering the underlying research notes. | Visual agent can be re-run independently via CLI or chat command (`--regenerate-image`). |

### 3.4. Book Mode & Typst Typesetting Subsystem

Book Mode transforms enriched ideas into comprehensive, publication-ready book chapters typeset through the project's embedded Typst engine.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-BOK-001 | M | THE book drafting agent SHALL rewrite the enriched idea into a substantive chapter draft following the persona and style rules in `context/persona/author.md`. | Generated text adheres to principles: punch over preamble, plain language, maximum information density, wry realism, and economic scrutiny. |
| REQ-BOK-002 | M | THE book drafting agent SHALL save the finalised chapter manuscript to `artefacts/content/ideas/{idea-id}/book/chapter.md`. | Chapter manuscript is formatted with semantic Markdown headings, embedded figure references, and callout blocks. |
| REQ-BOK-003 | M | THE system SHALL translate Markdown chapter drafts into Typst markup (`chapter.typ`) referencing the generated illustration from `assets/illustration.png`. | Typst source compiles cleanly without unresolved asset paths or syntax errors. |
| REQ-BOK-004 | M | WHEN book compilation is triggered, THE system SHALL invoke the Typst CLI engine (`typst compile`) using the templates and brand assets in `typst/` to produce publication-grade PDF output. | High-resolution PDF is generated in `artefacts/content/book/` with correct margins, typography, page numbers, and figures. |
| REQ-BOK-005 | P | THE system SHALL support compiling an aggregated book manuscript containing all processed ideas with a table of contents, introduction, and unified index. | Multi-chapter book manuscript compiles into a single cohesive PDF volume matching the project's editorial layout. |

### 3.5. Blog & Social Publishing Subsystem

Blog Mode adapts the enriched idea into conversational, opinionated articles formatted for web hosting and professional social networks.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-BLG-001 | M | THE blog drafting agent SHALL adapt the enriched idea into an article draft adhering to the persona and writing style in `context/persona/opinionated-blogger.md`. | Article features a provocative opening hook, parenthetical commentary, question-driven sections, "So What?" analysis, and a 400-800 word target length. |
| REQ-BLG-002 | M | THE system SHALL format the blog article for Hostinger web hosting with standardised YAML frontmatter (including `title`, `slug`, `date`, `excerpt`, `tags`, and `cover_image`) in `artefacts/content/ideas/{idea-id}/blog/post.md`. | Output file contains valid YAML frontmatter followed by clean Markdown, ready for upload or CMS ingestion. |
| REQ-BLG-003 | M | THE system SHALL generate a companion LinkedIn social post saved to `artefacts/content/ideas/{idea-id}/blog/linkedin.md`. | LinkedIn text contains a high-converting hook, 3-5 scannable bullet takeaways, character count compliance (under 3,000 characters), and relevant hashtags. |
| REQ-BLG-004 | P | THE system SHALL support configuring custom CMS publication adapters (e.g. WordPress, Ghost, or static site exports) for direct web deployment on Hostinger. | Configuration in `config/publishing.yaml` allows mapping frontmatter fields to external CMS requirements. |

### 3.6. Orchestration & Token Governance Subsystem

The Orchestrator coordinates agent workflow execution, enforces context boundaries, and minimises token expenditure.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-ORC-001 | M | THE system SHALL be invoked and operated via chat CLI commands within the AI coding assistant environment. | Users can instruct the orchestrator using natural language or structured commands (e.g. "Enrich idea 12", "Build book chapter 12", "Generate blog post for idea 12"). |
| REQ-ORC-002 | M | THE orchestrator SHALL delegate discrete phases (Research, Drafting, Visual Prompting, Typesetting) to specialised subagents or deterministic Python scripts. | The orchestrator context remains lean (< 4,000 tokens overhead) by delegating heavy text processing to child tasks. |
| REQ-ORC-003 | M | THE system SHALL enforce model tiering: small/medium models for data extraction and parsing, and large/thinking models for voice synthesis and creative rewriting. | Model configurations in `context/models.yaml` are strictly respected when spawning subagents. |
| REQ-ORC-004 | M | WHILE executing batch processing across multiple ideas, THE system SHALL process ideas sequentially or in bounded parallel tasks to prevent context exhaustion and API rate-limiting. | Batch execution across multiple ideas logs progress per idea and safely resumes interrupted batches without data loss. |
| REQ-ORC-005 | M | THE system SHALL NOT re-run completed phases unless the user explicitly passes an overwrite or force flag. | Idempotent execution preserves existing research and drafts, preventing unnecessary token burn. |

### 3.7. Harness Extension & Agent Lifecycle Governance

The Harness Extension subsystem defines the governance rules for assessing existing agents and workflows, tracking the creation of new agents, and maintaining runtime adapter synchronization.

| ID | Pri | Requirement (EARS) | Acceptance Criteria |
|---|---|---|---|
| REQ-HAR-001 | M | THE system SHALL evaluate and prioritise the reuse of existing harness agents (`product-expert`, `documentation`, `ui-designer`, `orchestrator`) and workflows (`context/workflows/content.yaml`) before proposing new agent definitions. | Architecture and design specifications explicitly document capability mappings to existing agents, identifying concrete gaps before new definitions are authored. |
| REQ-HAR-002 | M | IF new agents (e.g. specialized illustrator, typesetter) or new pipeline workflows (e.g. `ideas-publishing.yaml`) are required, THE work SHALL be tracked as formal specification and implementation tasks in `artefacts/build/tasks.md`. | Every proposed agent or workflow has a discrete task ID with priority, status, dependencies, and verifiable acceptance criteria in `tasks.md`. |
| REQ-HAR-003 | M | WHEN any agent, rule, or workflow is added or modified in `context/`, THE system SHALL execute the adapter compilation generator (`uv run agent-harness`) to regenerate runtime adapters (`AGENTS.md`, `GEMINI.md`). | Pre-commit and CI adapter drift checks (`uv run agent-drift`) pass with zero divergence. |
| REQ-HAR-004 | M | THE system SHALL ensure all newly authored agents conform to `context/standards/agent-standards.md` and newly defined workflows conform to `context/standards/workflow-standards.md`. | Agent definitions specify model tiers, scoped file permissions, and applicable rules; workflows specify phase dependencies and quality gates. |

---

## 4. Non-Functional Requirements

### 4.1. Token Economics & Performance

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-TOK-001 | Token Efficiency | Context overhead per orchestrator coordination turn | < 3,500 tokens |
| NFR-TOK-002 | Token Efficiency | Cost per fully enriched idea (Research + Visual Prompt + Book + Blog) | < $0.15 average using tiered routing |
| NFR-TOK-003 | Performance | Typst PDF chapter compilation time | < 2.0 seconds per chapter |
| NFR-TOK-004 | Scalability | Batch throughput capacity | Capable of processing 1 to 100 ideas reliably without context overflow |

### 4.2. Quality, Voice & Editorial Standards

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-QLT-001 | Voice Fidelity | Alignment of book chapters to `context/persona/author.md` | 100% compliance with non-preamble, information density, and British English rules |
| NFR-QLT-002 | Voice Fidelity | Alignment of blog posts to `context/persona/opinionated-blogger.md` | 100% compliance with hook-first structure and 400-800 word target length |
| NFR-QLT-003 | Visual Variety | Editorial illustration style differentiation | Prompts dynamically vary composition, art medium, and metaphor across ideas |
| NFR-QLT-004 | Code & Text Standards | Documentation and prose conventions | British English spelling (`-ise`, `-our`, `artefact`) and `DD/MM/YYYY` dates |

### 4.3. Portability & Extensibility

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-EXT-001 | Portability | Typst engine modularity | Typst compiler executes locally via CLI without external cloud dependencies |
| NFR-EXT-002 | Pluggability | Multi-target export support | Adding new social or CMS output targets requires only a new output adapter template |
| NFR-EXT-003 | Interoperability | Markdown export compatibility | Exported Markdown complies with CommonMark and GitHub Flavored Markdown (GFM), opening seamlessly in external PKM tools (Obsidian, Notion, Logseq) |

---

## 5. Out of Scope

The following capabilities are explicitly excluded from the initial release:
1. **Automated Direct-to-Production Social Posting**: Autonomous posting directly to LinkedIn or Hostinger without human editorial review and sign-off.
2. **Proprietary CMS API Integrations**: Direct database or OAuth publishing to Hostinger cPanel/WordPress in the MVP; publication will be handled via exported publication-ready Markdown/HTML files.
3. **Physical Print-on-Demand (POD) Distribution**: Direct integration with Kindle Direct Publishing (KDP) or IngramSpark APIs for physical printing (PDF output is typeset to print specs, but distribution uploads remain manual).
4. **Interactive GUI / Web Dashboard**: A web-based front-end application; all interactions are conducted through the agentic Chat CLI interface.

---

## 6. Revision History

| Date | Author | Version | Description of Changes |
|---|---|---|---|
| 17/09/2026 | Antigravity (Product Owner Agent) | 1.0.0 | Initial comprehensive product requirements for 100-Ideas system replacing framework template |
| 17/09/2026 | Antigravity (Product Owner Agent) | 1.1.0 | Added dual-path ingestion (batch catalogue + incremental inbox/chat) and Markdown portability export capabilities |
