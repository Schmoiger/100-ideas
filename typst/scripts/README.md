# Document Automation Scripts

## Overview

Automates conversion of Markdown drafts to professional PDFs with rendered mermaid diagrams using **Typst** (modern typesetting system).

**What it does:**
1. Extracts mermaid diagrams from Markdown → `.mmd` files
2. Renders `.mmd` files → baseline PNG images (via mermaid.ink)
3. Builds PDFs using Pandoc + Typst + Plandek template

**What you control:**
- Step 2 generates baseline renders
- You refine with Nano Banana → save to `docs/diagrams/`
- Step 3 uses your manual images (if present), baselines otherwise

## Quick Start

```bash
# Full pipeline (build all PDFs)
make pdf

# OR use the friendly wrapper
./typst/scripts/build-docs.sh
```

That's it! Your PDFs will be in `build/pdf/`.

## Individual Steps

```bash
make extract       # Extract .mmd from markdown
make render        # Render .mmd to PNG via mermaid.ink (incremental)
make pdf           # Generate PDFs with Typst
make clean         # Remove build directory
```

## Build Specific Documents

```bash
# Just one document
./typst/scripts/build-typst.sh vision

# OR using wrapper
./typst/scripts/build-docs.sh vision

# Multiple specific documents
./typst/scripts/build-docs.sh vision journey

# Build all documents
make pdf
```

## Manual Refinement Workflow

The automation preserves your creative workflow with Nano Banana:

### 1. Generate Baselines

```bash
make extract render
```

This creates baseline PNG renders in `build/diagrams/`:

```
build/diagrams/
├── vision/
│   ├── New DevX Workflow.png
│   ├── Agentic Toolchain.png
│   └── ...
├── journey/
│   └── Three Stages of DevX Maturity.png
└── ...
```

### 2. Refine with Nano Banana

- Open baseline: `build/diagrams/vision/New DevX Workflow.png`
- Refine aesthetics in Nano Banana (better fonts, colors, layout)
- **Save to `docs/diagrams/`** with existing filename format

**Important:** Use the existing filename from `docs/diagrams/`:
```bash
# If docs/diagrams/ has "New DevX Workflow v2.png"
# Save your refined version with EXACTLY that name
```

### 3. Build PDFs (uses refined images)

```bash
make pdf
```

The build uses your refined images from `docs/diagrams/` where present, falling back to baselines from `build/diagrams/` otherwise.

**How it works:**
The build script checks directories in order:
1. `docs/diagrams/` (manual refined images) ← **checked first**
2. `build/diagrams/{doc}/` (auto-generated baselines for that doc)
3. `build/diagrams/` (auto-generated baselines from other docs)

No manual tracking needed!

## Incremental Builds

### You edited text in vision.md (no diagram changes)

```bash
./typst/scripts/build-typst.sh vision    # Rebuilds just vision.pdf (~5 seconds)
# OR
make pdf                           # Rebuilds only changed PDFs
```

### You edited a mermaid diagram in vision.md

```bash
# Delete the baseline to force re-render
rm build/diagrams/vision/New\ DevX\ Workflow.png

# Rebuild
./typst/scripts/build-typst.sh vision
```

### You refined a diagram with Nano Banana

```bash
# Save refined version to docs/diagrams/New DevX Workflow v2.png

# Rebuild (uses refined image, no re-render needed)
./typst/scripts/build-typst.sh vision
```

### Full clean rebuild

```bash
make clean && make pdf
```

## Wrapper Script

For easier commands, use `./typst/scripts/build-docs.sh`:

```bash
# Build all
./typst/scripts/build-docs.sh

# Build specific
./typst/scripts/build-docs.sh vision

# Clean rebuild
./typst/scripts/build-docs.sh --clean

# Re-render specific diagram
./typst/scripts/build-docs.sh --rerender vision new-devx-workflow

# Help
./typst/scripts/build-docs.sh --help
```

## Adding/Removing Documents

### Add a new document

1. Create Markdown file:
   ```bash
   touch docs/drafts/my-new-doc.md
   # Add frontmatter (title, subtitle, author, date)
   # Add content with mermaid diagrams
   ```

2. Add to Makefile `DRAFTS` list (line ~4):
   ```makefile
   DRAFTS := vision journey roadmap new-org-plandek my-new-doc
   ```

3. Build:
   ```bash
   make pdf
   ```

### Remove a document

1. Remove from Makefile `DRAFTS` list:
   ```makefile
   DRAFTS := vision journey roadmap  # Removed new-org-plandek
   ```

2. Optional cleanup:
   ```bash
   rm -rf build/mermaid/new-org-plandek
   rm -rf build/diagrams/new-org-plandek
   rm -rf build/typst/new-org-plandek*
   rm build/pdf/new-org-plandek.pdf
   ```

## File Structure

```
build/                    # Gitignored build artefacts
├── mermaid/              # Extracted .mmd source files
│   ├── vision/
│   │   ├── new-devx-workflow.mmd
│   │   └── ...
│   ├── journey/
│   ├── roadmap/
│   ├── new-org-plandek/
│   ├── typeset-test/
│   └── manifest.json     # Metadata for all diagrams
├── diagrams/             # Auto-generated baseline PNGs
│   └── [same structure as mermaid/]
├── typst/                # Typst intermediate files
│   ├── vision-content.typ       # Pandoc-generated content
│   ├── vision.typ               # Wrapper with template
│   └── ...
└── pdf/                  # Generated PDFs
    ├── vision.pdf        (55MB)
    ├── journey.pdf       (62MB)
    ├── roadmap.pdf       (386KB)
    ├── new-org-plandek.pdf (5.4MB)
    └── typeset-test.pdf  (668KB)

docs/
├── drafts/               # Markdown source files
│   ├── vision.md
│   ├── journey.md
│   ├── roadmap.md
│   ├── new-org-plandek.md
│   └── typeset-test.md   # Test document with all elements
├── diagrams/             # Manual/refined images (git tracked)
│   └── *.png             # Existing refined diagrams
└── assets/
    └── plandek-logo.png  # Plandek logo for PDFs

typst/
├── plandek-template.typ  # Shim → re-exports Plandek pack (back-compat paths)
└── brands/
    ├── neutral.typ       # Default theme: no customer assets
    └── plandek.typ       # Plandek theme (logos, CETZ cover panel, QR)
```

## Scripts

- **`typst/scripts/extract-mermaid.py`** - Extract mermaid blocks from Markdown
  - Parses frontmatter for titles
  - Generates stable slugs
  - Creates manifest.json

- **`typst/scripts/render-mermaid-ink.py`** - Render .mmd to PNG using mermaid.ink
  - Incremental builds (skips existing)
  - Uses web service (no mermaid-cli needed)
  - Fast renders with caching

- **`typst/scripts/build-typst.sh`** - Legacy pandoc path; **if** `typst/{doc}-book.typ` exists, compiles it; otherwise **delegates to `build.py`** (matches how this repo builds). Prefer **`make pdf-doc DOC=…`**.

- **`typst/scripts/build-docs.sh`** - Thin wrapper around **`make pdf`** / **`make pdf-doc`**
  - Per-document builds use **`make pdf-doc DOC=<id>`** (ids from `build.yaml`, not raw filenames).
  - Optional **`--brand plandek`** (or **`BRAND=`** in the environment) is forwarded like the Makefile.

## Dependencies

All dependencies installed per project setup:

- **Typst** (40.7MB) - Modern typesetting system
- **Pandoc 3.9** - Markdown → Typst conversion
- **uv** - Python package/script runner
- **requests** (Python) - HTTP client for mermaid.ink

**Removed dependencies:**
- ~~BasicTeX (989MB)~~ → Replaced by Typst (40.7MB)
- ~~mermaid-cli (307MB node_modules)~~ → Replaced by mermaid.ink web service
- **Disk savings: 1,643MB → 313MB (81% reduction)**

## Performance

- **Extraction**: ~1-2 seconds (all files)
- **Rendering**: ~3-5 seconds per diagram (12 diagrams = ~40 seconds first time)
- **PDF build (Typst)**: ~2-3 seconds per file (5 files = ~15 seconds)
- **Total first build**: ~60 seconds
- **Incremental (one file changed)**: ~5 seconds
- **Speed improvement: 5x faster than LaTeX**

## PDF branding (Typst)

Themes live under **`typst/brands/`**. The build driver (`typst/scripts/build.py` + `build.yaml`) generates wrappers that `#import` one pack per PDF.

| Brand id   | Module                    | Use case |
|------------|---------------------------|----------|
| `neutral`  | `typst/brands/neutral.typ` | **Default** — generic cover/footer, no customer logos or QR. |
| `plandek`  | `typst/brands/plandek.typ` | Plandek logos, CETZ network panel, QR, legal footer. |
| `mindrocket` | `typst/brands/mindrocket.typ` | Mind Rocket — CV-inspired teal palette; vector **`icon.svg`** on cover/footer; vector **`logo.svg`** wordmark on closing pages (`docs/assets/mindrocket/`). |

**Choose a brand (prefer Make — do not flip `build.yaml` for day-to-day work):**

- **`make pdf`** uses **`BRAND=neutral`** by default (`Makefile`: `BRAND ?= neutral` → `--brand` on `build.py`).
- **Plandek PDFs:** `make pdf BRAND=plandek`, or shortcuts **`make pdf-plandek`** / **`make pdf-draft-plandek`**.
- **Mind Rocket PDFs:** `make pdf BRAND=mindrocket` or `make pdf-doc DOC=… BRAND=mindrocket`.
- **One document:** `make pdf-doc DOC=vision BRAND=plandek`.
- **One book:** `make pdf-book BOOK=new-devx-plandek BRAND=plandek` (same as any book: theme follows **`BRAND`** unless you add a per-book `brand:` pin in `build.yaml`).
- **Ad-hoc (no YAML):** `uv run python typst/scripts/build.py --assemble path/to/a.md` for a single PDF, or `--assemble a.md b.md` for one book with automatic part-divider interstitials (same pattern as registered multi-part books). **Bare `*.md` names** (no `/`) are resolved under **`docs/drafts/`**, then **`context/docs/`**, then the repo root. **Default PDF names include `-{brand}`** before `.pdf` (e.g. `journey-neutral.pdf`, `journey-plandek.pdf`) so different brands never overwrite the same file; YAML book outputs that already end with `-{brand}` (e.g. **`new-devx-plandek.pdf`**) are left unchanged. **`--assemble-output`** accepts repo-relative paths; a bare name (no `/`) is written to **`build/pdf/`** and gets **`.pdf`** if you omit an extension (e.g. `--assemble-output hive-preview` → `build/pdf/hive-preview.pdf` — **no** automatic brand suffix when you set this flag). Multi-file default output prefers a **readable basename** (e.g. `agentic-framework.md` + `agentic-framework-reference.md` → **`build/pdf/agentic-framework-and-reference-{brand}.pdf`**); if stems joined would exceed 64 characters, output falls back to **`build/pdf/assemble-{10-char-hash}-{brand}.pdf`**. Optional: `--assemble-title`, `--assemble-subtitle`, `--assemble-date`. From Make: `make pdf-assemble ASSEMBLE="docs/drafts/a.md docs/drafts/b.md"`. Each Markdown file must have a **unique basename** (stem) so mermaid extraction lines up with `substitute-mermaid.py`. When a book is already defined in `build.yaml` (e.g. **`agentic-hive-mind`**), use **`make pdf-book BOOK=…`** for the canonical PDF name and metadata — do not rely on `--assemble` for that deliverable.

Optional **`local.mk`** (see **`local.mk.example`**, gitignored): set `BRAND = plandek` once per machine.

**Registry:** `build.yaml` keys under **`brands:`** map id → Typst `module` path. Rare edits only when adding a new pack. Optional per-document / per-book **`brand:`** pins override `--brand` (for CI or fixed deliverables).

**Shim:** `typst/plandek-template.typ` re-exports the Plandek pack so older notes and paths keep working.

## Troubleshooting

### Error: "typst not found"

Install Typst:
```bash
brew install typst
```

Verify installation:
```bash
typst --version  # Should show 0.12.0 or later
```

### Error: "file not found" for logo

Ensure logo exists:
```bash
ls docs/assets/plandek-logo.png
```

Should show a ~5KB PNG file (234x67px).

### Error: "requests module not found"

Install Python dependencies:
```bash
uv pip install requests
```

### Diagrams render but look wrong in PDF

Check image path resolution:
1. Does the image exist in `docs/diagrams/`? (manual refinement)
2. Does the image exist in `build/diagrams/{doc}/`? (doc's own diagrams)
3. Does the image exist in `build/diagrams/`? (cross-doc references)
4. Does the Markdown reference match the filename exactly?

### PDF file sizes are very large (55MB+)

This is currently expected behaviour for documents with many embedded images. Vision and journey documents include large PNG diagrams which increase file size. Ways to reduce:

1. **Compress images before embedding**:
   ```bash
   pngquant build/diagrams/vision/*.png --force --ext .png
   ```

2. **Reduce image DPI** in mermaid.ink renders (edit `typst/scripts/render-mermaid-ink.py`)

3. **Use SVG instead of PNG** (requires different rendering approach)

The roadmap (386KB) and typeset-test (668KB) documents are reasonably sized because they have fewer/smaller images.

### Incremental build doesn't re-render changed diagram

Delete the baseline PNG manually:
```bash
rm build/diagrams/{doc}/{diagram}.png
make render
```

OR use the wrapper:
```bash
./typst/scripts/build-docs.sh --rerender {doc} {diagram}
```

### Typst compilation errors

Check the generated Typst file for issues:
```bash
# View the content file
cat build/typst/vision-content.typ

# Try compiling manually to see full errors
typst compile build/typst/vision-book.typ build/pdf/vision-neutral.pdf --root .
```

Common issues:
- **Broken citations**: Pandoc may incorrectly parse `@username` in URLs
  - Fixed by sed in build script
- **Broken links**: Pandoc may generate invalid `#link(<label>)` references
  - Fixed by sed in build script (commented out)
- **Image paths**: Wrong relative paths to images
  - Fixed by sed in build script

## Examples

### Example 1: First-time build

```bash
$ make pdf
Extracting mermaid diagrams from markdown...

journey.md: 1 diagram(s)
new-org-plandek.md: 2 diagram(s)
roadmap.md: 1 diagram(s)
typeset-test.md: 1 diagram(s)
vision.md: 7 diagram(s)

Total diagrams found: 12

  Extracted: build/mermaid/journey/three-stages-of-devx-maturity.mmd
  Extracted: build/mermaid/vision/new-devx-workflow.mmd
  ...

  Created manifest: build/mermaid/manifest.json

✓ Extraction complete: 12 diagrams

Rendering mermaid diagrams to PNG...

  Rendering: build/mermaid/journey/three-stages-of-devx-maturity.mmd
  Fetching: https://mermaid.ink/img/...
  Rendering: build/mermaid/vision/new-devx-workflow.mmd
  ...

✓ Rendering complete:
    Rendered: 12 diagram(s)
    Skipped:  0 diagram(s)

Building PDFs with Typst...

=========================================
 Building: vision
=========================================
Compiling vision.typ → PDF...
✓ Built vision.pdf ( 55M)

=========================================
 Building: journey
=========================================
Compiling journey.typ → PDF...
✓ Built journey.pdf ( 62M)

[... roadmap, new-org-plandek, typeset-test ...]

✓ All PDFs built successfully in build/pdf/
```

### Example 2: Rebuild after text edit

```bash
$ ./typst/scripts/build-typst.sh vision

=========================================
 Building: vision
=========================================
Compiling vision.typ → PDF...
✓ Built vision.pdf ( 55M)

✓ Build complete
```

(Skips extraction and rendering - just rebuilds PDF in ~5 seconds)

### Example 3: Using wrapper script

```bash
$ ./typst/scripts/build-docs.sh vision

Building vision.pdf...

=========================================
 Building: vision
=========================================
Compiling vision.typ → PDF...
✓ Built vision.pdf ( 55M)

✓ Built build/pdf/vision-neutral.pdf
```

### Example 4: Clean rebuild

```bash
$ make clean && make pdf
Cleaning build directory...
✓ Build directory removed

[... full extraction, rendering, building ...]

✓ All PDFs built successfully in build/pdf/
```

## Test Document

The `typeset-test.md` document tests all typographic elements:

- Title page with logo
- Table of contents
- Copyright footer
- Typography: bold, italic, inline code
- Headings (levels 1-4)
- Lists (unordered, ordered, nested, mixed)
- Tables (simple, complex, aligned)
- Code blocks (Python, JavaScript, Bash)
- Block quotes
- Mermaid diagrams
- Cross-document diagram references
- Special blocks (info, warning, note)
- Long paragraphs (wrapping test)
- Emoji support
- Horizontal rules
- Definition lists
- Footnotes

Build it first when making template changes to avoid re-rendering large documents:

```bash
make pdf-doc DOC=typeset-test
open build/pdf/typeset-test-neutral.pdf
```

## See Also

- Main README: `/Users/avi/Repos/new-devx/README.md`
- Typst documentation: https://typst.app/docs
- Typst packs: `typst/brands/neutral.typ`, `typst/brands/plandek.typ` (shim: `typst/plandek-template.typ`)
- Mermaid documentation: https://mermaid.js.org/
- mermaid.ink service: https://mermaid.ink/
