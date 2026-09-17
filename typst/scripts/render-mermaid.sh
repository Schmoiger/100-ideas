#!/usr/bin/env bash
#
# Render .mmd files to PNG using mermaid-cli (mmdc).
#
# Features:
# - Incremental builds (skips existing PNGs)
# - Uses titles from manifest.json for friendly filenames
# - High DPI output (2400x1800) for quality PDFs
# - Transparent background, neutral theme

set -euo pipefail

MERMAID_DIR="build/mermaid"
DIAGRAMS_DIR="build/diagrams"
MANIFEST="$MERMAID_DIR/manifest.json"

# Check if mermaid directory and manifest exist
if [[ ! -d "$MERMAID_DIR" ]]; then
  echo "Error: $MERMAID_DIR not found. Run 'make extract' first."
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "Error: $MANIFEST not found. Run 'make extract' first."
  exit 1
fi

# Read manifest and render diagrams
echo "Rendering mermaid diagrams to PNG..."
echo ""

rendered_count=0
skipped_count=0

# Parse manifest.json using python (requires uv)
while IFS=$'\t' read -r doc_name slug title mmd_path; do
  mmd_file="$MERMAID_DIR/$mmd_path"

  # Use title for PNG filename (matching Markdown references)
  png_file="$DIAGRAMS_DIR/$doc_name/$title.png"

  # Create output directory
  mkdir -p "$(dirname "$png_file")"

  # Skip if PNG exists (incremental build)
  if [[ -f "$png_file" ]]; then
    echo "  Skip: $png_file (already exists)"
    ((skipped_count++))
    continue
  fi

  echo "  Rendering: $mmd_file → $png_file"

  # Render with mermaid-cli
  # Note: Using yarn (NOT npm) per project standards
  # mmdc is installed as dev dependency
  if yarn mmdc \
    -i "$mmd_file" \
    -o "$png_file" \
    -w 2400 \
    -H 1800 \
    -b transparent \
    -t neutral \
    2>&1 | grep -v "^$" || true; then
    ((rendered_count++))
  else
    echo "    ✗ Failed to render: $mmd_file"
    exit 1
  fi
done < <(uv run python -c "
import json
with open('$MANIFEST') as f:
    manifest = json.load(f)
for diagram in manifest['diagrams']:
    print(f\"{diagram['doc_name']}\t{diagram['slug']}\t{diagram['title']}\t{diagram['mmd_path']}\")
")

echo ""
echo "✓ Rendering complete:"
echo "    Rendered: $rendered_count diagram(s)"
echo "    Skipped:  $skipped_count diagram(s) (already exist)"
