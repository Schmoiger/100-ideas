# Product Decisions & Open Items: 100-Ideas Pipeline

Date: 17/09/2026

---

## Resolved Decisions

1. **Tone & Persona Authority**:
   - **Book Mode**: Strictly adheres to `context/persona/author.md` ("AS" persona: punch over preamble, systems thinker, wry realism, economic lens).
   - **Blog Mode**: Strictly adheres to `context/persona/opinionated-blogger.md` (provocative hook, conversational, parentheticals, question-driven, "so what?" analysis).

2. **Illustration & Visuals Generation**:
   - Engine: Gemini API / Imagen model.
   - Prompt Strategy: Visual prompts are dynamically derived from the idea's core thesis and metaphorical concepts, introducing intentional stylistic variety while avoiding monotony.

3. **Shared DRY Intermediate Layer**:
   - Location: `artefacts/content/ideas/{idea-id}/`.
   - Layout:
     - `meta.yaml` (metadata, status, model tiers, token metrics)
     - `research/` (folder housing synthesised research notes, source PDFs, and reference materials)
     - `assets/` (prompt text and generated illustrations)
     - `book/` (chapter manuscript and Typst markup)
     - `blog/` (blog post markdown and LinkedIn text)

4. **Execution Model**:
   - Invocation: Agentic application operated interactively via Chat CLI.

---

## Active Experimentation & Operational Items

1. **Input File Symlink Resolution**:
   - `artefacts/product/100-ideas.md` is a symlink pointing outside the workspace.
   - *Next Step*: Implement an ingestion mechanism or syncing utility so agents in standard sandbox environments can seamlessly read the table without system permission warnings.

2. **Hostinger Blog Format Verification**:
   - Verify specific CMS / web format requirements for the user's Hostinger website (e.g. Markdown with YAML frontmatter vs HTML import) through empirical testing.

