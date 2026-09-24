# Architecture: 100-Ideas Agentic Publishing System

> Authoritative architectural specification for the 100-Ideas content pipeline and publishing system.
> Consumed by: solution-architect, python-coder, tech-lead, orchestrator.

**Canonical references**:
- **Product Requirements**: `artefacts/product/requirements.md`

---

## 1. Prototype Architecture: Idea Ingestion & Selection Subsystem (§3.1)

### 1.1 Overview & Data Flow

```mermaid
flowchart TD
    subgraph IntakeSources["Intake Sources"]
        Symlink["artefacts/product/100-ideas.md\n(Symlink or Workspace File)"]
        InboxFile["artefacts/product/inbox.md\n(Incremental Append-Only)"]
        ChatInput["CLI / Chat Interactive Intake\n(Direct Idea Submission)"]
    end

    subgraph SyncAndParse["Ingestion & Resolution"]
        SyncManager["authoritative_sync\n(Resolves sandbox boundaries & caches snapshot)"]
        BatchParser["table_parser\n(Extracts Title, Synopsis, Source Ref)"]
        InboxParser["inbox_parser\n(Extracts markdown sections & parses metadata)"]
    end

    subgraph Governance["Governance & Selection"]
        DedupEngine["dedup_engine\n(Title & Synopsis similarity detection)"]
        IdeaSelector["selector\n(--idea N, --ideas N-M, --all, --tag/domain)"]
    end

    subgraph Storage["Intermediate Content Layer"]
        IdeaStore["artefacts/content/ideas/{idea-id}/\n├── meta.yaml\n├── research/\n├── assets/\n├── book/\n└── blog/"]
    end

    Symlink --> SyncManager --> BatchParser
    InboxFile --> InboxParser
    ChatInput --> DedupEngine
    BatchParser --> DedupEngine
    InboxParser --> DedupEngine
    DedupEngine --> IdeaSelector
    IdeaSelector --> Storage
```


### 1.2 Key Design Decisions (Prototype)

1. **Local Authoritative Snapshot for Sandbox Safety**:
   - `artefacts/product/100-ideas.md` may point outside the workspace sandbox (e.g. Google Drive symlink).
   - If symlink resolution fails due to permissions, the system falls back to `artefacts/product/100-ideas.snapshot.md`.
   - A sync command (`python -m services.ingestion.cli sync`) copies the authoritative source into the snapshot when outside sandbox access is available.

2. **Canonical Identification Scheme**:
   - Batch catalog ideas receive deterministic sequential IDs: `idea-001`, `idea-002`, ..., based on their 1-indexed table row.
   - Incremental inbox & chat ideas receive the next sequential ID or slugified UUID, ensuring zero collision with batch catalogue ideas.

3. **Intermediate Folder Provisioning**:
   - Upon ingestion/selection, each idea is initialized with `meta.yaml` containing structured YAML frontmatter (id, title, synopsis, source_reference, tags, status, linked_resources, timestamps).
   - Standard subfolders (`research/`, `assets/`, `book/`, `blog/`) are scaffolded automatically.

4. **Fuzzy Deduplication**:
   - Normalised string matching (lowercase alphanumeric token matching) alerts on title or synopsis duplicates before provisioning.

---

## 2. Shared Content & Intermediate Storage (§3.2)

### 2.1 Directory Structure

- `artefacts/content/ideas/{idea-id}/`
  - `meta.yaml`: Canonical idea state, lineage, tags, timestamps, and model/token telemetry.
  - `research/`: Idea-specific research synthesis and notes.
  - `assets/`: Generated visuals and diagrams.
  - `book/`: Typeset book chapter drafts.
  - `blog/`: Publication-ready blog drafts and platform frontmatter.
- `artefacts/content/resources/`
  - Centralised M:N library of foundational source whitepapers, book notes, and references.
  - `manifest.yaml`: Global registry of shared resources.

---

## 3. Related Documents

- **Product Requirements**: [requirements.md](product/requirements.md)
- **Idea Catalogue**: [100-ideas.md](product/100-ideas.md)
- **Ideas Inbox**: [inbox.md](product/inbox.md)
- **Task Tracking**: [tasks.md](../build/tasks.md)
