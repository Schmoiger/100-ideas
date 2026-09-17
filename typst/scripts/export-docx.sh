#!/usr/bin/env bash
#
# Export markdown drafts to DOCX using pandoc.
# Image paths in the markdown (e.g. diagrams/...) are resolved from docs/.
#
# Usage:
#   ./typst/scripts/export-docx.sh -v              # vision + vision-summary
#   ./typst/scripts/export-docx.sh -j              # journey + journey-summary
#   ./typst/scripts/export-docx.sh -v -j           # all of the above
#   ./typst/scripts/export-docx.sh --vision --journey
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../.." && pwd))"
DOCS_DIR="$REPO_ROOT/docs"
DRAFTS_DIR="$DOCS_DIR/drafts"

# Ensure we run from repo root so paths are consistent
cd "$REPO_ROOT"

if ! command -v pandoc &>/dev/null; then
  echo "error: pandoc is not installed" >&2
  exit 1
fi

# Resource path so that "diagrams/..." in md resolves to docs/diagrams
RESOURCE_PATH="$DOCS_DIR/drafts:$DOCS_DIR"

# Decode percent-encoded path for filesystem (e.g. %20 -> space)
decode_path() {
  local path="$1"
  # Handle common percent-encoding
  path="${path//%20/ }"
  path="${path//%2F/\/}"
  path="${path//%2E/.}"
  echo "$path"
}

# Check that all images referenced in a markdown file exist under RESOURCE_PATH.
# Exits with 1 and prints missing paths if any are not found.
check_images_in_md() {
  local md_file="$1"
  local missing_paths=()
  local missing_in=()
  local path path_decoded base found
  local md_relative="${md_file#$REPO_ROOT/}"

  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    path_decoded=$(decode_path "$path")
    found=false
    IFS=: read -ra bases <<< "$RESOURCE_PATH"
    for base in "${bases[@]}"; do
      if [[ -f "$base/$path_decoded" ]]; then
        found=true
        break
      fi
    done
    if [[ "$found" != true ]]; then
      missing_paths+=("$path_decoded")
      missing_in+=("$md_relative")
    fi
  done < <(grep -oE '!\[[^]]*\]\([^)]+\)' "$md_file" | sed 's/^!\[[^]]*\](\(.*\))$/\1/')

  if [[ ${#missing_paths[@]} -gt 0 ]]; then
    echo "error: missing diagram(s):" >&2
    for i in "${!missing_paths[@]}"; do
      echo "  Missing: ${missing_paths[$i]}" >&2
      echo "  Referenced in: ${missing_in[$i]}" >&2
    done
    return 1
  fi
  return 0
}

export_vision() {
  check_images_in_md "$DRAFTS_DIR/vision.md"
  check_images_in_md "$DRAFTS_DIR/vision-summary.md"
  pandoc "$DRAFTS_DIR/vision.md" -o "$DRAFTS_DIR/vision.docx" --resource-path="$RESOURCE_PATH"
  echo "  docs/drafts/vision.docx"
  pandoc "$DRAFTS_DIR/vision-summary.md" -o "$DRAFTS_DIR/vision-summary.docx" --resource-path="$RESOURCE_PATH"
  echo "  docs/drafts/vision-summary.docx"
}

export_journey() {
  check_images_in_md "$DRAFTS_DIR/journey.md"
  check_images_in_md "$DRAFTS_DIR/journey-summary.md"
  pandoc "$DRAFTS_DIR/journey.md" -o "$DRAFTS_DIR/journey.docx" --resource-path="$RESOURCE_PATH"
  echo "  docs/drafts/journey.docx"
  pandoc "$DRAFTS_DIR/journey-summary.md" -o "$DRAFTS_DIR/journey-summary.docx" --resource-path="$RESOURCE_PATH"
  echo "  docs/drafts/journey-summary.docx"
}

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Export markdown drafts to DOCX. At least one option is required."
  echo ""
  echo "Options:"
  echo "  -v, --vision    Export vision.md and vision-summary.md"
  echo "  -j, --journey   Export journey.md and journey-summary.md"
  echo "  -h, --help      Show this help"
  echo ""
  echo "Examples:"
  echo "  $0 -v"
  echo "  $0 -v -j"
  echo "  $0 --vision --journey"
}

DO_VISION=false
DO_JOURNEY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--vision)
      DO_VISION=true
      shift
      ;;
    -j|--journey)
      DO_JOURNEY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$DO_VISION" != true && "$DO_JOURNEY" != true ]]; then
  echo "error: at least one of -v/--vision or -j/--journey is required" >&2
  usage >&2
  exit 1
fi

echo "Exporting to DOCX..."

if [[ "$DO_VISION" == true ]]; then
  echo "Vision:"
  export_vision
fi

if [[ "$DO_JOURNEY" == true ]]; then
  echo "Journey:"
  export_journey
fi

echo "Done."
