#!/usr/bin/env python3
"""
Render mermaid diagrams using mermaid.ink web service.

Alternative to mermaid-cli that requires zero Node.js dependencies.
Trade-off: Requires internet connection, relies on external service.

Output format: SVG (REQ 4.3).  PNG is not used for generated diagrams.

Skips diagrams that have a non-empty `replacement` field in the manifest —
those are manually refined images that the build step embeds directly.

Incremental rendering (REQ 4.3): re-renders a diagram only when the content
of its .mmd file has changed since the last successful render.  The SHA-256
of each rendered .mmd is stored in a sidecar file ({slug}.svg.hash) alongside
the SVG.  On each run the current hash is compared to the stored one; if they
match the diagram is skipped.

Retry behaviour: transient HTTP errors (503, 429, 502, 504) and network
timeouts are retried up to 4 times with exponential back-off (2 s, 4 s, 8 s,
16 s) using tenacity.  Permanent errors (400, 404, etc.) are not retried.
"""

import argparse
import base64
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

logging.basicConfig(level=logging.WARNING)
_log = logging.getLogger(__name__)

# HTTP status codes that warrant a retry (transient service errors).
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class _RetryableError(Exception):
    """Raised for transient errors that should trigger a retry."""


def encode_mermaid(diagram_content: str) -> str:
    """
    Encode mermaid diagram for mermaid.ink URL.

    Uses simple base64 URL-safe encoding, which is sufficient for most
    diagrams.  For very large diagrams (>2KB) pako compression could be
    used instead to avoid URL length limits.
    """
    encoded = base64.urlsafe_b64encode(diagram_content.encode('utf-8'))
    return encoded.decode('ascii')


def content_hash(text: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_stored_hash(hash_file: Path) -> str:
    """Return the hash stored in hash_file, or '' if it does not exist."""
    if hash_file.exists():
        return hash_file.read_text(encoding='utf-8').strip()
    return ''


@retry(
    retry=retry_if_exception_type(_RetryableError),
    stop=stop_after_attempt(5),          # 1 attempt + 4 retries
    wait=wait_exponential(multiplier=2, min=2, max=30),
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=False,
)
def _fetch_svg(url: str) -> bytes | None:
    """
    Fetch SVG bytes from mermaid.ink.

    Raises _RetryableError for transient HTTP/network failures so that
    tenacity will back off and retry.  Returns None for permanent errors
    (the caller skips the diagram without retrying).
    """
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (mermaid diagram renderer)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return response.read()
            if response.status in _RETRYABLE_STATUSES:
                raise _RetryableError(f"HTTP {response.status}")
            print(f"    ✗ HTTP {response.status} (permanent — skipping)")
            return None
    except urllib.error.HTTPError as e:
        if e.code in _RETRYABLE_STATUSES:
            raise _RetryableError(f"HTTP {e.code} {e.reason}") from e
        print(f"    ✗ HTTP {e.code} {e.reason} (permanent — skipping)")
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        raise _RetryableError(f"network error: {e}") from e


def render_diagram(mmd_file: Path, svg_file: Path) -> bool:
    """
    Render a mermaid diagram to SVG using mermaid.ink.

    Retries up to 4 times (with exponential back-off) on transient errors
    (503, 429, 502, 504, network timeouts).

    Args:
        mmd_file: Path to .mmd source file
        svg_file: Path to output .svg file

    Returns:
        True if successful, False otherwise.
    """
    diagram_content = mmd_file.read_text(encoding='utf-8')
    encoded = encode_mermaid(diagram_content)

    # Request SVG output (REQ 4.3)
    url = f"https://mermaid.ink/svg/{encoded}"

    svg_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Fetching: {url[:80]}...")

    try:
        svg_bytes = _fetch_svg(url)
    except _RetryableError as e:
        # All retries exhausted
        print(f"    ✗ Failed after retries: {e}")
        return False

    if svg_bytes is None:
        return False

    svg_file.write_bytes(svg_bytes)
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Render mermaid diagrams to SVG using mermaid.ink"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("build/mermaid/manifest.json"),
        help="Path to manifest.json (default: build/mermaid/manifest.json)"
    )
    parser.add_argument(
        "--mermaid-dir",
        type=Path,
        default=Path("build/mermaid"),
        help="Directory containing .mmd files (default: build/mermaid)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/diagrams"),
        help="Output directory for SVG files (default: build/diagrams)"
    )

    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"Error: {args.manifest} not found. Run 'make extract' first.")
        return 1

    with args.manifest.open('r', encoding='utf-8') as f:
        manifest = json.load(f)

    print("Rendering mermaid diagrams to SVG using mermaid.ink...")
    print("")

    rendered_count = 0
    skipped_replaced = 0
    skipped_cached = 0
    failed_count = 0

    for diagram in manifest['diagrams']:
        # Skip diagrams that have a manually refined replacement (REQ 4.1)
        if diagram.get('replacement'):
            print(f"  Skip (replacement): {diagram['slug']} → {diagram['replacement']}")
            skipped_replaced += 1
            continue

        mmd_file = args.mermaid_dir / diagram['mmd_path']
        # Use slug for output filename (consistent with .mmd naming)
        svg_file = args.output_dir / diagram['doc_name'] / f"{diagram['slug']}.svg"
        hash_file = svg_file.with_suffix('.svg.hash')

        # Incremental build: re-render only when .mmd content has changed
        # (REQ 4.3).  Compare SHA-256 of current content against stored hash.
        current_mmd = mmd_file.read_text(encoding='utf-8')
        current_hash = content_hash(current_mmd)
        stored_hash = read_stored_hash(hash_file)

        if svg_file.exists() and current_hash == stored_hash:
            print(f"  Skip (unchanged): {svg_file}")
            skipped_cached += 1
            continue

        print(f"  Rendering: {mmd_file} → {svg_file}")

        if render_diagram(mmd_file, svg_file):
            # Store hash of the .mmd that produced this SVG
            hash_file.write_text(current_hash, encoding='utf-8')
            rendered_count += 1
        else:
            failed_count += 1

    print("")
    print("✓ Rendering complete:")
    print(f"    Rendered:    {rendered_count} diagram(s)")
    print(f"    Unchanged:   {skipped_cached} diagram(s) (content hash match)")
    print(f"    Replacements:{skipped_replaced} diagram(s) (manual image, skipped)")
    if failed_count > 0:
        print(f"    Failed:      {failed_count} diagram(s)")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
