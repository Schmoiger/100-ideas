#!/usr/bin/env bash
#
# Legacy Typst helper (pandoc + optional committed typst/{doc}-book.typ).
#
# The primary pipeline is: make pdf / make pdf-doc DOC=… / typst/scripts/build.py
# (see Makefile and docs/drafts/README.md). Wrappers are generated under
# build/typst/ by build.py — this repo does not commit typst/{doc}-book.typ.
#
# When no committed wrapper exists, this script delegates to:
#   uv run python typst/scripts/build.py --profile production --docs DOC --no-books --brand BRAND
# Brand: export BRAND=plandek or TYPST_BRAND=plandek (default neutral).
#
# Usage:
#   ./typst/scripts/build-typst.sh                 # All *.md in docs/drafts (delegates per file)
#   ./typst/scripts/build-typst.sh vision          # One document

set -euo pipefail

readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[0;33m'
readonly NC='\033[0m'

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DRAFTS_DIR="docs/drafts"
readonly TYPST_DIR="typst"
readonly BUILD_TYPST_DIR="build/typst"
readonly PDF_DIR="build/pdf"
readonly DIAGRAMS_SRC="docs/diagrams"
readonly DIAGRAMS_OPT="build/diagrams-opt"

# Maximum pixel dimension for optimised images (OPT-001).
readonly OPT_MAX_PX=1024

mkdir -p "$BUILD_TYPST_DIR" "$PDF_DIR"

# Optimise source images into build/diagrams-opt/ (OPT-001).
# Delegates to typst/scripts/optimise-images.py (Pillow): resizes PNGs to
# OPT_MAX_PX and applies palette quantisation; copies other formats unchanged.
# Incremental: Python script skips files whose mtime hasn't changed.
optimise_images() {
    mkdir -p "$DIAGRAMS_OPT"
    uv run python "$SCRIPT_DIR/optimise-images.py" \
        --src "$DIAGRAMS_SRC" \
        --dest "$DIAGRAMS_OPT" \
        --max-px "$OPT_MAX_PX"
}

# Convert a Markdown file to a Typst body-only content file.
# Produces build/typst/{basename}-content.typ.
convert_to_typst() {
    local md_file=$1
    local basename
    basename=$(basename "$md_file" .md)
    local typst_content="$BUILD_TYPST_DIR/${basename}-content.typ"

    echo -e "${BLUE}Converting${NC} $basename.md → Typst..."

    # Body-only conversion: no --standalone, so no pandoc title block or
    # conflicting #set commands (REQ 4.2).
    pandoc "$md_file" \
        -f markdown \
        -t typst \
        -o "$typst_content"

    # Fix image paths: diagrams/ (markdown-relative) → ../../build/diagrams-opt/
    # Optimised copies live in build/diagrams-opt/ (OPT-001); path is relative
    # to build/typst/ where the content file resides (REQ 4.2).
    sed -i '' 's|image("diagrams/|image("../../build/diagrams-opt/|g' "$typst_content"

    # Remove #cite() artefacts introduced by @username patterns in URLs (REQ 4.2).
    sed -i '' 's|#cite(label("[^"]*"), form: "prose")||g' "$typst_content"

    # Replace #horizontalrule / #divider() with an inline rule.  #include does not inherit
    # let bindings from the parent file, so #horizontalrule is undefined in
    # included content (REQ 4.2).
    sed -i '' \
        's|#horizontalrule|#line(length: 100%, stroke: 0.4pt + rgb("#CCCCCC"))|g' \
        "$typst_content"
    sed -i '' \
        's|#divider()|#line(length: 100%, stroke: 0.4pt + rgb("#CCCCCC"))|g' \
        "$typst_content"

    # Comment out broken internal links that pandoc generates from some anchors.
    sed -i '' \
        's|^\(.*#link(<[^>]*>).*\)|// FIXME: Broken link - \1|g' \
        "$typst_content"

    # Remove table.hline() inserted by Pandoc after every header row.
    sed -i '' '/^[[:space:]]*table\.hline(),$/d' "$typst_content"

    # Replace percentage-based table columns with fractional (1fr) sizing.
    # Pandoc derives percentages from dash-padding in Markdown separator rows;
    # 1fr gives equal-width columns that fill the page.  (The primary pipeline
    # in build.py uses a smarter auto/1fr threshold variant.)
    sed -i '' '/^[[:space:]]*columns:/s/[0-9][0-9]*\(\.[0-9]*\)*%/1fr/g' "$typst_content"

    echo "$typst_content"
}

# Strip the document preamble from the generated content file.
# Removes: YAML frontmatter block (--- ... ---), the H1 title, and any
# inline table-of-contents section that precedes the first real heading.
# The Typst wrapper provides the title and cover page (REQ 4.2).
strip_preamble() {
    local content_file=$1

    uv run python - "$content_file" <<'PYEOF'
import sys, re
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text(encoding='utf-8').splitlines()

i = 0
n = len(lines)

def skip_blank(i):
    while i < n and not lines[i].strip():
        i += 1
    return i

i = skip_blank(i)

# Skip a Typst label anchor generated for the document title (e.g. <my-doc>)
if i < n and re.match(r'^<[a-z0-9][a-z0-9-]*>$', lines[i].strip()):
    i += 1

i = skip_blank(i)

# Skip document-level H1 title (pandoc renders "# Title" as "= Title" in Typst)
if i < n and lines[i].startswith('= '):
    i += 1

# Skip preamble lines: metadata, rules, blank lines, labels, ToC section.
# Stop at the first real content heading (== ...) or paragraph.
while i < n:
    s = lines[i].strip()

    # Blank line
    if s == '':
        i += 1
        continue

    # Typst label anchor
    if re.match(r'^<[a-z0-9][a-z0-9-]*>$', s):
        i += 1
        continue

    # Horizontal rule / divider
    if s in ('#divider()', '#horizontalrule') or s.startswith('#line('):
        i += 1
        continue

    # Bold metadata: #strong[Key]: value  or  **Key**: value
    if (s.startswith('#strong[') or s.startswith('*')) and ':' in s:
        i += 1
        continue

    # Inline ToC section (skip until next real heading)
    if (s.startswith('== ') or s.startswith('= ')) and any(
        kw in s.lower() for kw in ('content', 'table of', 'toc')
    ):
        i += 1
        while i < n:
            s2 = lines[i].strip()
            if (s2.startswith('= ') or s2.startswith('== ')) and not any(
                kw in s2.lower() for kw in ('content', 'table of', 'toc')
            ):
                break
            i += 1
        continue

    # Anything else is real content — stop
    break

path.write_text('\n'.join(lines[i:]) + '\n', encoding='utf-8')
PYEOF
}

# Compile a committed Typst wrapper to PDF.
compile_pdf() {
    local basename=$1
    local wrapper_file="$TYPST_DIR/${basename}-book.typ"
    local pdf_file="$PDF_DIR/${basename}.pdf"

    if [ ! -f "$wrapper_file" ]; then
        echo "Error: wrapper not found: $wrapper_file"
        echo "Create typst/${basename}-book.typ before building $basename."
        return 1
    fi

    echo -e "${BLUE}Compiling${NC} ${basename}-book.typ → PDF..."

    # --root . so that absolute paths in wrappers resolve from repo root.
    # --font-path ensures Outfit TTF files are found (REQ 5.2).
    typst compile "$wrapper_file" "$pdf_file" \
        --root . \
        --font-path docs/assets/fonts \
        2>&1 | grep -v "^$" || true

    if [ -f "$pdf_file" ]; then
        local size_human size_bytes
        size_human=$(du -h "$pdf_file" | cut -f1)
        size_bytes=$(du -k "$pdf_file" | cut -f1)   # kibibytes

        # Size check: warn if PDF exceeds 3 MB (= 3072 KiB) (OPT-001)
        local SIZE_LIMIT_KB=3072
        if [ "$size_bytes" -gt "$SIZE_LIMIT_KB" ]; then
            local YELLOW='\033[0;33m'
            echo -e "${GREEN}✓${NC} Built ${basename}.pdf (${size_human}) ${YELLOW}⚠ exceeds 3 MB target${NC}"
        else
            echo -e "${GREEN}✓${NC} Built ${basename}.pdf (${size_human})"
        fi
        return 0
    else
        echo "✗ Failed to build ${basename}.pdf"
        return 1
    fi
}

build_document() {
    local basename=$1
    local md_file="$DRAFTS_DIR/${basename}.md"
    local wrapper_file="$TYPST_DIR/${basename}-book.typ"
    local brand="${BRAND:-${TYPST_BRAND:-neutral}}"

    if [ ! -f "$md_file" ]; then
        echo "Error: $md_file not found"
        return 1
    fi

    if [ ! -f "$wrapper_file" ]; then
        echo -e "${YELLOW}No committed $wrapper_file — delegating to build.py${NC}" >&2
        echo "  Prefer: make pdf-doc DOC=$basename  (and make render if diagrams changed)" >&2
        uv run python "$SCRIPT_DIR/build.py" \
            --profile production \
            --docs "$basename" \
            --no-books \
            --brand "$brand" || return $?
        return 0
    fi

    echo ""
    echo "========================================="
    echo " Building: $basename (legacy wrapper path)"
    echo "========================================="

    # Optimise source images into build/diagrams-opt/ (OPT-001).
    # Must run before convert_to_typst so the opt directory exists and
    # the path rewrite in convert_to_typst points to the right location.
    optimise_images

    convert_to_typst "$md_file"
    strip_preamble "$BUILD_TYPST_DIR/${basename}-content.typ"

    # Replace mermaid code blocks with image references (GAP-B6, B7).
    # Blocks preceded by a figure image are deleted; others become #image() calls.
    uv run python "$SCRIPT_DIR/substitute-mermaid.py" \
        --content "$BUILD_TYPST_DIR/${basename}-content.typ" \
        --manifest build/mermaid/manifest.json \
        --doc "$basename"

    compile_pdf "$basename"
}

main() {
    if [ $# -eq 0 ]; then
        echo "Building all documents..."
        for md_file in "$DRAFTS_DIR"/*.md; do
            basename=$(basename "$md_file" .md)
            build_document "$basename" || true
        done
    else
        build_document "$1"
    fi

    echo ""
    echo -e "${GREEN}✓${NC} Build complete"
    echo ""
    echo "PDFs in: $PDF_DIR/"
    ls -lh "$PDF_DIR"/*.pdf 2>/dev/null || true
}

main "$@"
