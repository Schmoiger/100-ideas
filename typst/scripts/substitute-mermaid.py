#!/usr/bin/env python3
"""
Substitute mermaid code blocks in a Typst content file.

After pandoc converts a Markdown file to Typst, mermaid fences remain as
raw code blocks (```mermaid ... ```).  This script replaces them:

  - WHERE a replacement image already precedes the block (pandoc converted the
    image reference above the mermaid fence into a #figure(image(...))), the
    raw mermaid block is deleted — the image is already in place.

  - WHERE no replacement exists, the raw mermaid block is replaced with an
    #image(...) call pointing to the rendered SVG in build/diagrams/.

Diagram identity is established by matching the title extracted from the
mermaid frontmatter (or the first line of content) against the manifest.

Usage:
    uv run python typst/scripts/substitute-mermaid.py \\
        --content build/typst/vision-content.typ \\
        --manifest build/mermaid/manifest.json \\
        --doc vision
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Pattern that matches a mermaid raw block in pandoc-generated Typst output:
#
#   ```mermaid
#   ... content ...
#   ```
#
# The fence lines have no leading whitespace in the output we observed.
_MERMAID_BLOCK_RE = re.compile(
    r'```mermaid\n(.*?)```',
    re.DOTALL
)

# Pattern for a #figure(image(...)) call that immediately precedes the block.
# We check whether the text before the mermaid fence ends with a figure block,
# optionally followed by other raw mermaid blocks (so a single image can
# replace a contiguous sequence of mermaid blocks).
_FIGURE_BEFORE_RE = re.compile(
    r'#figure\(image\([^)]*\),\s*caption:\s*\[[^\]]*\]\s*\)\s*(?:```mermaid\n.*?```\s*)*\Z',
    re.DOTALL
)


def extract_title_from_mermaid(content: str) -> str:
    """
    Extract the title from mermaid frontmatter, or derive it from first content line.

    Mirrors the logic in extract-mermaid.py so we get the same slug.
    """
    # Try frontmatter title
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        title_match = re.search(r'title:\s*(.+)', fm_match.group(1))
        if title_match:
            return title_match.group(1).strip()

    # Fall back to first content line
    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    for line in body.splitlines():
        line = line.strip()
        if line:
            return ' '.join(line.split()[:4])
    return 'untitled-diagram'


def title_to_slug(text: str) -> str:
    """Convert title to slug using the same rules as extract-mermaid.py."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug


def build_slug_map(manifest_data: dict, doc_name: str) -> dict:
    """
    Build a mapping of title-slug → manifest entry for a specific document.

    Returns {slug: diagram_entry} for all diagrams belonging to doc_name.
    """
    result = {}
    for d in manifest_data['diagrams']:
        if d['doc_name'] == doc_name:
            result[d['slug']] = d
    return result


def substitute(content: str, slug_map: dict, doc_name: str) -> tuple[str, int, int]:
    """
    Replace mermaid blocks in content with image references.

    Returns (new_content, replaced_count, deleted_count).
    """
    replaced = 0
    deleted = 0

    def replace_block(m: re.Match) -> str:
        nonlocal replaced, deleted

        block_content = m.group(1)
        title = extract_title_from_mermaid(block_content)
        slug = title_to_slug(title)

        # Look up in manifest (try slug first, then linear search by title)
        entry = slug_map.get(slug)
        if entry is None:
            # Try stripping duplicate suffix (-2, -3, ...)
            for k, v in slug_map.items():
                if title_to_slug(v['title']) == slug or v['title'] == title:
                    entry = v
                    break

        # Check whether a replacement image already precedes this block.
        # m.start() is the position of the opening ``` in the full string.
        text_before = content[:m.start()]
        has_preceding_image = bool(_FIGURE_BEFORE_RE.search(text_before))

        if has_preceding_image:
            # Image already in place — remove the mermaid block entirely.
            deleted += 1
            return ''

        if entry is None:
            # No manifest entry found — leave block as-is with a comment.
            print(f"  Warning: no manifest entry for mermaid block with title '{title}' (slug '{slug}')",
                  file=sys.stderr)
            return m.group(0)

        if entry.get('replacement'):
            # Should not happen (block should have a preceding image), but
            # handle gracefully: emit the replacement image.
            img_path = entry['replacement']
            # Path from build/typst/ to docs/diagrams/ is ../../docs/diagrams/
            # The replacement path stored is "diagrams/filename" (markdown-relative)
            img_typst = re.sub(r'^diagrams/', '../../docs/diagrams/', img_path)
            deleted += 1
            return f'#image("{img_typst}")\n'

        # No replacement — use the rendered SVG.
        svg_path = f'../../build/diagrams/{doc_name}/{slug}.svg'
        replaced += 1
        return f'#image("{svg_path}")\n'

    # We need to re-run the regex over the *original* content because match
    # positions in 'm' refer to the original string.  Using re.sub with a
    # function handles this correctly as long as we don't mutate 'content'
    # inside replace_block (we only read content[:m.start()]).
    new_content = _MERMAID_BLOCK_RE.sub(replace_block, content)
    return new_content, replaced, deleted


def main():
    parser = argparse.ArgumentParser(
        description="Substitute mermaid blocks in a pandoc-generated Typst content file"
    )
    parser.add_argument(
        "--content",
        type=Path,
        required=True,
        help="Path to the Typst content file (e.g. build/typst/vision-content.typ)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("build/mermaid/manifest.json"),
        help="Path to manifest.json (default: build/mermaid/manifest.json)"
    )
    parser.add_argument(
        "--doc",
        required=True,
        help="Document name (e.g. 'vision') — used to scope manifest entries and SVG paths"
    )

    args = parser.parse_args()

    if not args.content.exists():
        print(f"Error: content file not found: {args.content}", file=sys.stderr)
        return 1

    if not args.manifest.exists():
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    manifest_data = json.loads(args.manifest.read_text(encoding='utf-8'))
    slug_map = build_slug_map(manifest_data, args.doc)

    original = args.content.read_text(encoding='utf-8')
    new_content, replaced, deleted = substitute(original, slug_map, args.doc)

    args.content.write_text(new_content, encoding='utf-8')

    print(f"  Mermaid substitution ({args.doc}): "
          f"{replaced} block(s) → SVG image, "
          f"{deleted} block(s) removed (replacement image already present)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
