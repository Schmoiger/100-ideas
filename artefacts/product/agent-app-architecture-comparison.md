# Architectural Patterns for Agentic Applications: Career-Ops vs 100-Ideas

**Author**: @orchestrator & Engineering Team  
**Date**: 24/09/2026  
**Status**: Published Teaching Reference  
**Audience**: Software Architects, AI Engineers, and Agentic Pipeline Developers  

---

## Executive Summary & Core Comparison

As AI coding CLIs (Claude Code, Google Antigravity, OpenCode, Codex, Gemini CLI) transition from simple conversational interfaces to autonomous execution runtimes, two distinct architectural archetypes have emerged for building production-grade agentic applications:

1. **The Interactive CLI Co-Pilot (The *Career-Ops* Pattern)**: An agile, prompt-mode driven command centre designed for direct human-in-the-loop decision-making, powered by flat zero-token scripts and structured Markdown prompts.
2. **The Autonomous Multi-Agent Software Factory (The *100-Ideas* Pattern)**: A formal, compiled multi-agent assembly line governed by canonical context specifications, Detroit-school Test-Driven Development (TDD), and modular micro-services.

Both applications automate domain-specific pipelines on local filesystems, but their architectural trade-offs reflect differing operational priorities:

| Architectural Dimension | Career-Ops (`career-ops`) | 100-Ideas (`100-ideas`) |
|---|---|---|
| **Primary Archetype** | Interactive CLI Co-Pilot & Command Centre | Autonomous Multi-Agent Publishing Factory |
| **Control Loop** | Human-in-the-loop conversation & mode switching | Orchestrated phased workflows (`prototype`, `build`, `content`) |
| **Source of Context Truth** | Directly authored `AGENTS.md` + `modes/*.md` | Centralised `context/` specifications (`agents/`, `rules/`, `workflows/`) |
| **Agent / Prompt Projection** | Hand-crafted multi-CLI redirect wrappers (`CLAUDE.md`, `CODEX.md`) | Automated compilation via `uv run agent-harness` with zero-drift CI enforcement |
| **Execution Mechanics** | Flat Node.js scripts (`scan.mjs`) + Markdown mode instructions | Scoped Python packages (`services/ingestion/`, `services/enrichment/`) + CLI dispatcher |
| **Data Contract Boundary** | Rigid Two-Layer Contract (`SYSTEM_PATHS` vs `USER_PATHS`) | Three-Layer Store (`context/` vs `services/` vs `artefacts/content/`) |
| **Deterministic Fast Paths** | Zero-token API scanners, liveness probes, Playwright PDF renderer | Zero-dependency table parsers, pure-Python PNG binary synthesis, atomic file replacement |
| **State Tracking** | Centralised ledger (`data/applications.md`, `data/status-log.tsv`) | Distributed per-idea directories (`artefacts/content/ideas/{id}/meta.yaml`) |

---

## Architecture Archetypes: Co-Pilot Assistant vs Software Factory

### The Career-Ops Archetype: The Interactive Co-Pilot

Career-Ops was designed to help an individual evaluate hundreds of job opportunities, score them against a personal CV, and track applications without cloud lock-in.

Key architectural characteristics:
- **Markdown Prompt Modes (`modes/`)**: Prompts are broken down into specialised operational modes (`oferta.md` for evaluation, `apply.md` for tailoring, `scan.md` for discovery). The AI coding assistant loads these prompt files dynamically into its active context window to assume a specific operational persona.
- **Flat Script Architecture**: Approximately 70 single-purpose scripts live directly at the repository root (`scan.mjs`, `tracker.mjs`, `check-liveness.mjs`). Path stability is prioritised over deep nesting to maintain compatibility with community forks, shell aliases, and external plugins.
- **Two-Layer Data Contract**: A strict separation guarantees that when the system is updated via `node update-system.mjs`, user data (`cv.md`, `data/applications.md`, `reports/`) is never overwritten by upstream code changes.
- **Human-in-the-Loop Gate**: The system evaluates, scores, and prepares artefacts, but the human retains agency: the software explicitly forbids automated application submission.

### The 100-Ideas Archetype: The Autonomous Multi-Agent Factory

100-Ideas is engineered to transform a raw catalogue of 100 architectural theses into an editorial book (typeset in Typst) and syndicated blog posts with zero human typing required for syntax.

Key architectural characteristics:
- **Canonical Context Engine (`context/`)**: Prompts and rules are not scattered or manually duplicated across CLI configuration files. Instead, `context/` serves as the authoritative specification repository.
- **Compiled Runtime Projections**: Developer tools do not read custom files ad-hoc. The generator `uv run agent-harness` compiles the canonical context into standard runtime files (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.agents/skills/`). The test `uv run agent-drift` guards against uncommitted manual edits in CI.
- **Scoped Service Architecture**: Code is organised into formal domain packages (`services/ingestion/`, `services/enrichment/`, `services/drafting/`) equipped with strict type hints, dependency isolation via `uv`, and comprehensive Detroit-school TDD test suites.
- **M:N Shared Resource Model**: Ideas link dynamically to a shared library of whitepapers, books, and frameworks (`artefacts/content/resources/`), enabling cross-cutting citations without duplicated content.

---

## Answering Key Architecture Questions

### Question 1: How Should Agents Be Defined?

> *"Do we need to change `AGENTS.md` or can we have a new `agent-app.md` (resembling Career-Ops' `AGENTS.md`) since `AGENTS.md` is automatically generated? Or is there a better solution?"*

#### Why Hand-Editing `AGENTS.md` Fails in 100-Ideas
In Career-Ops, `AGENTS.md` is authored directly by the developer. It acts as the primary system prompt for the entire application.

In 100-Ideas, however, `AGENTS.md` is an **auto-generated compiler artefact** produced by `context/scripts/generators/generate_adapters.py`. Attempting to edit `AGENTS.md` directly introduces two fatal issues:
1. **Compilation Overwrites**: The next time `uv run agent-harness` is executed (or triggered automatically during a build workflow), all manual edits will be permanently wiped out.
2. **Pre-Commit and CI Failures**: The pre-commit hook `adapter-drift` runs `uv run agent-drift` on every commit. If `AGENTS.md` diverges by even a single character from the canonical definitions in `context/`, git rejects the commit.

#### Why a Disconnected `agent-app.md` Is Fragile
Creating a standalone file such as `agent-app.md` creates a split-brain problem:
- Standard AI coding assistants (such as Antigravity, Claude Code, and Gemini CLI) look specifically for their native entry files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) at workspace roots.
- An arbitrary `agent-app.md` will not be loaded automatically by coding assistants unless the user explicitly reminds the agent to read it at the start of every single session. Experience shows that prompt-level reminders decay rapidly across conversation compactions.

#### The Canonical Solution: Compile Context and Scoped Services
The architecturally sound approach in the 100-Ideas ecosystem follows a two-pronged model:

```
[ Canonical Definition in context/ ]
                 │
                 ▼
   uv run agent-harness (Compiler)
                 │
                 ├───────────────────────────────┐
                 ▼                               ▼
       AGENTS.md / GEMINI.md          .agents/skills/ideas-publishing/
     (System Persona & Rules)            (Operational Action Guide)
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     [ Python CLI Engine ]
                    services/ingestion/cli.py
                    (uv run ideas <command>)
```

1. **Author the Role in Canonical Context**: Define application roles (e.g. `@book-author`, `@illustrator`, or specialised publishing workflows) within `context/agents/` and `context/workflows/`.
2. **Compile Adapters**: Run `uv run agent-harness`. The generator automatically projects these roles into `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, and `.agents/skills/`.
3. **Execute via Scoped Deterministic Services**: Instead of forcing the LLM to interpret paragraphs of instructions to perform structural operations, wrap pipeline logic into deterministic Python CLI tools (`uv run ideas ingest`, `uv run ideas enrich`). The agent role merely decides *when* and *with what parameters* to call the tool.

---

### Question 2: Skills vs Slash Commands vs Subcommands

> *"Should we build skills that can be invoked (e.g. `/blog-ingest`), or is there a better solution?"*

#### The Problem with Tool-Specific Slash Commands
Slash commands (such as `/blog-ingest` or `/scan`) are proprietary conventions tied to specific host IDEs or CLI chat clients. Relying exclusively on slash commands creates vendor lock-in:
- A slash command defined in Antigravity cannot be executed inside a GitHub Action or CI pipeline.
- It cannot be invoked by an autonomous background worker running headless in Claude Code or Codex.
- It lacks programmatic input validation and error return codes.

#### The Three-Tier Architecture
The most robust, reproducible architecture decouples operational logic into three complementary tiers:

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Workflow Orchestration & State Tracking            │
│ (context/workflows/ + artefacts/build/HANDOFF.md)            │
│ Coordinates multi-agent handoffs, reviews, and quality gates│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Open Agent Skill Standard                           │
│ (.agents/skills/ideas-publishing/SKILL.md)                  │
│ Tells the LLM how to translate user goals into CLI actions  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Deterministic CLI Engine                            │
│ (uv run ideas <subcommand>)                                 │
│ Fast, zero-token, idempotent, and testable via pytest       │
└─────────────────────────────────────────────────────────────┘
```

#### Tier 1: Deterministic Python CLI Engine (`uv run ideas`)
All filesystem manipulation, parsing, image generation, data validation, and state updating must exist as deterministic Python code in `services/`:
```bash
# Ingestion
uv run ideas ingest --snapshot

# Enrichment
uv run ideas enrich --idea 1
uv run ideas enrich --idea 1 --regenerate-image --refinement "Minimalist linocut"

# Drafting
uv run ideas draft --idea 1 --mode book
uv run ideas draft --idea 1 --mode blog
```
**Benefits**:
- **Zero Token Waste**: File reads, directory provisioning, and binary generation cost zero LLM tokens.
- **Idempotency**: Running the command twice will not overwrite existing work unless `--force` is supplied (`REQ-ORC-005`).
- **Verifiability**: Deterministic behaviour can be verified using unit and smoke tests in `pytest`.

#### Tier 2: Unified Skill Entrypoint (`.agents/skills/`)
Following the Open Agent Skill Standard, expose an agent skill (such as `.agents/skills/ideas-publishing/SKILL.md`). This document informs any coding agent:
- What capabilities exist in the pipeline.
- What CLI commands to execute in response to user requests.
- How to evaluate outputs and handle error recovery.

When a user asks: *"Please enrich idea 42 with a dark architectural illustration"*, the agent reads the skill and executes:
```bash
uv run ideas enrich --idea 42 --refinement "Dark architectural linework"
```

#### Tier 3: Workflow Orchestration (`context/workflows/`)
For long-running tasks involving multiple agents (e.g. Drafting -> Technical Review -> Principles Review -> Typesetting), the system tracks progress via `HANDOFF.md` and coordinates execution using formal workflow definitions.

---

## Deep Dive: Data Boundaries and State Management

### Career-Ops: Centralised Flat-Table State

In Career-Ops, the core state is stored in a single tabular file: [`data/applications.md`](file:///Users/avi/Repos/career-ops/data/applications.md).
- Status changes append events to [`data/status-log.tsv`](file:///Users/avi/Repos/career-ops/data/status-log.tsv).
- Supporting evaluations are stored flat in `reports/{NNN}-{company}-{date}.md`.
- Concurrency and file integrity are safeguarded by shared filesystem locks (`tracker-writer-lock-tests.mjs`).

This model is ideal for CRM-style workflows where an individual tracks a single stream of opportunities transitioning through linear states (Saved -> Applied -> Screen -> Interview -> Offer).

### 100-Ideas: Distributed Per-Idea Content Trees

In 100-Ideas, a centralised table is insufficient because each idea represents an independent creative publication unit with multiple heterogeneous assets:

```
artefacts/content/ideas/idea-001/
├── meta.yaml               <-- Machine-readable status, resource links, tokens
├── research/
│   └── notes.md            <-- Synthesised evidence, trade-offs, and citations
├── assets/
│   ├── prompt.txt          <-- Editorial visual direction and negative constraints
│   └── illustration.png    <-- Genuine binary graphic asset
├── book/
│   └── chapter.md          <-- Book mode manuscript (author persona)
├── blog/
│   └── post.md             <-- Blog mode syndicate (blogger persona + SEO frontmatter)
└── exports/
    └── bundle.zip          <-- Standalone portable bundle
```

**Architectural Advantages**:
1. **Zero Merge Conflicts**: Multiple autonomous agents (or developers) can work on different ideas concurrently in separate branches without causing merge conflicts in a shared database or table.
2. **Granular Handoffs**: An agent can verify the readiness of `idea-001` simply by validating the presence and status of `meta.yaml` and its subdirectories.
3. **M:N Resource Coupling**: Shared literature is decoupled into `artefacts/content/resources/` with a central `manifest.yaml`. Ideas reference resources by ID without duplicating whitepapers across ideas.

---

## Execution Models: Zero-Token Fast Paths

A common architectural trap in agentic software engineering is using an expensive LLM to do jobs that can be accomplished reliably in ordinary code. Both Career-Ops and 100-Ideas implement aggressive **zero-token fast paths**.

### Comparison of Zero-Token Strategies

```
Problem: "Is the job posting still open?"
Career-Ops: check-liveness.mjs fetches HTTP status and regex checks expired tokens.
Zero LLM tokens consumed.

Problem: "Generate an editorial illustration for the chapter."
100-Ideas: visuals.py uses Python standard library zlib and struct to construct
a valid 800x450 RGB PNG binary with authentic IHDR, IDAT, and IEND chunks.
Zero third-party graphics dependencies, zero LLM image synthesis tokens.

Problem: "Parse 100 ideas from catalogue."
100-Ideas: parsers.py parses Markdown pipe tables with regex and dataclasses.
Zero prompt tokens wasted feeding 50KB tables to an LLM.
```

### Pure Python Binary Synthesis in 100-Ideas
To prevent dependency bloat (e.g. requiring `Pillow` or heavy C-extensions) while satisfying strict packaging rules, `services/enrichment/visuals.py` generates valid PNG binaries using only Python's built-in `zlib` and `struct` libraries:

```python
def create_editorial_png(seed_str: str, width: int = 800, height: int = 450) -> bytes:
    # 1. Deterministic colour palette derived from idea hash
    digest = hashlib.sha256(seed_str.encode()).digest()
    
    # 2. Raw scanlines with None (0) filter byte and geometric patterns
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # Filter byte
        for x in range(width):
            # Calculate geometric shapes and colours
            raw_data.extend((r, g, b))

    # 3. Pack genuine PNG chunks (IHDR, IDAT, IEND) with CRC32 checksums
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = make_chunk(b"IHDR", ihdr_data)
    idat_chunk = make_chunk(b"IDAT", zlib.compress(bytes(raw_data), level=9))
    iend_chunk = make_chunk(b"IEND", b"")
    
    return b"\x89PNG\r\n\x1a\n" + ihdr_chunk + idat_chunk + iend_chunk
```

This guarantees that every provisioned idea receives a valid visual binary asset without requiring network calls or third-party image libraries.

---

## Synthesis: Best Practices for Agentic System Architects

When designing an agentic application, adopt the following principles derived from Career-Ops and 100-Ideas:

1. **Prompts Are Code; Keep a Single Source of Truth**:
   If an application requires agent personas or instructions, maintain them in canonical specifications (`context/` in 100-Ideas, `modes/` in Career-Ops). Never duplicate prompts by hand across multiple vendor configs (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`); use a compiler script and enforce zero drift in CI.

2. **Never Delegate Deterministic Work to an LLM**:
   Use LLMs strictly for subjective reasoning, synthesis, linguistic tone, and conceptual ideation. All file system indexing, table parsing, HTTP checking, hash filtering, and binary asset generation belong in deterministic code.

3. **Separate System Operations from User Data**:
   Maintain a strict boundary between application code and user content. Ensure that pipeline upgrades and code updates can be pulled safely without threatening user assets.

4. **Build CLI-First, Agent-Second**:
   Every capability an agent can perform should be accessible via a standard command-line interface. When the CLI is clean, idempotent, and testable with standard unit testing tools (`pytest`, `node:test`), agent orchestration becomes a lightweight wrapper rather than a fragile monolith.
