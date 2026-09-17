#!/usr/bin/env bash
#
# User-friendly wrapper for document automation pipeline.
#
# Simplifies common operations like building PDFs, cleaning, and re-rendering
# specific diagrams without needing to remember Make commands or paths.

set -euo pipefail

# Helper function
show_help() {
  cat <<EOF
Usage: ./typst/scripts/build-docs.sh [OPTIONS] [DOCUMENTS...]

Build PDFs from Markdown drafts with mermaid diagrams.

OPTIONS:
  --clean         Clean build directory before building
  --brand ID      PDF theme: neutral (default) or plandek (same as Makefile BRAND)
  --rerender DOC DIAGRAM
                  Delete diagram baseline and rebuild PDF
  --help          Show this help

DOCUMENTS:
  Names must match keys under documents: in build.yaml (e.g. vision, journey,
  roadmap, vision-cto-summary, typeset-test, …). Not every file in docs/drafts/
  is registered.

  (Leave empty to run the full pipeline: make pdf)

EXAMPLES:
  ./typst/scripts/build-docs.sh                    # Build all PDFs
  ./typst/scripts/build-docs.sh vision             # Build just vision.pdf
  ./typst/scripts/build-docs.sh vision journey     # Build vision + journey
  ./typst/scripts/build-docs.sh --brand plandek vision
                                             # Plandek theme for listed docs
  BRAND=plandek ./typst/scripts/build-docs.sh vision
                                             # Same (Make reads \$BRAND)
  ./typst/scripts/build-docs.sh --clean            # Clean rebuild all
  ./typst/scripts/build-docs.sh --clean vision     # Clean rebuild vision
  ./typst/scripts/build-docs.sh --rerender vision new-devx-workflow
                                             # Re-render specific diagram

WORKFLOW:
  1. Edit Markdown in docs/drafts/
  2. Run: ./typst/scripts/build-docs.sh [docname]
  3. Check: build/pdf/[docname].pdf
  4. Refine diagrams with Nano Banana → save to docs/diagrams/
  5. Rebuild: ./typst/scripts/build-docs.sh [docname]

OUTPUT:
  PDFs are generated in build/pdf/

EOF
}

# Parse flags
CLEAN=false
RERENDER=false
RERENDER_DOC=""
RERENDER_DIAGRAM=""
# Optional: --brand plandek (otherwise Makefile default: neutral, or \$BRAND from env)
CLI_BRAND=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --clean)
      CLEAN=true
      shift
      ;;
    --brand)
      if [[ $# -lt 2 || "$2" == -* ]]; then
        echo "error: --brand requires a brand id (e.g. neutral, plandek)" >&2
        exit 1
      fi
      CLI_BRAND="$2"
      shift 2
      ;;
    --rerender)
      if [[ $# -lt 3 ]]; then
        echo "error: --rerender requires DOC and DIAGRAM (see --help)" >&2
        exit 1
      fi
      RERENDER=true
      RERENDER_DOC="$2"
      RERENDER_DIAGRAM="$3"
      shift 3
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      echo ""
      show_help
      exit 1
      ;;
    *)
      # Document name
      break
      ;;
  esac
done

# Propagate brand to Make / build.py (Makefile uses BRAND ?= neutral).
if [[ -n "$CLI_BRAND" ]]; then
  export BRAND="$CLI_BRAND"
fi

# Handle --rerender
if [[ "$RERENDER" == "true" ]]; then
  echo "Re-rendering diagram: $RERENDER_DOC/$RERENDER_DIAGRAM"
  rm -f "build/diagrams/$RERENDER_DOC/$RERENDER_DIAGRAM.png"
  make pdf-doc "DOC=$RERENDER_DOC"
  echo ""
  # PDF basename is {doc}-{brand}.pdf (see typst/scripts/build.py); default brand is neutral.
  _b=$(ls -1 "build/pdf/${RERENDER_DOC}"-*.pdf 2>/dev/null | head -1 || true)
  if [[ -n "$_b" ]]; then echo "✓ Rebuilt $_b"; else echo "✓ Rebuilt build/pdf/${RERENDER_DOC}-<brand>.pdf"; fi
  exit 0
fi

# Handle --clean
if [[ "$CLEAN" == "true" ]]; then
  echo "Cleaning build directory..."
  make clean
  echo ""
fi

# Build PDFs
if [[ $# -eq 0 ]]; then
  # No args: build all
  echo "Building all PDFs..."
  echo ""
  make pdf
else
  # Build specific documents (must be ids in build.yaml under documents:)
  for doc in "$@"; do
    echo "Building $doc.pdf (make pdf-doc DOC=$doc)..."
    echo ""
    make "pdf-doc" "DOC=$doc"
    echo ""
    _b=$(ls -1t "build/pdf/${doc}"-*.pdf 2>/dev/null | head -1 || true)
    if [[ -n "$_b" ]]; then echo "✓ Built $_b"; else echo "✓ Built build/pdf/${doc}-<brand>.pdf"; fi
  done
fi
