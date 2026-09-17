#!/usr/bin/env python3
"""
Extract mermaid diagrams from Markdown files.

Parses Markdown documents, finds mermaid code blocks, extracts them to
separate .mmd files with stable filenames, and creates a manifest.json
tracking metadata.

Replacement convention (REQ 4.1):
    A Markdown image reference on the line immediately preceding a ```mermaid
    fence signals that a manually refined image replaces that diagram:

        ![Diagram Title](diagrams/my-diagram.png)

        ```mermaid
        flowchart LR
            A --> B
        ```

    When a replacement is detected the diagram is recorded in the manifest
    with a `replacement` field and no .mmd file is written.  The renderer
    skips these entries; the build step embeds the replacement image directly.
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


# Pattern for a Markdown image reference pointing into the diagrams directory.
# Matches: ![alt text](diagrams/filename.ext) or ![alt](../diagrams/...)
_IMAGE_REF_RE = re.compile(r'^!\[.*?\]\(([^)]+)\)\s*$')


@dataclass
class MermaidDiagram:
    """Represents a single mermaid diagram."""
    source_file: str
    line_number: int
    title: str
    slug: str
    content: str
    doc_name: str           # vision, journey, etc.
    replacement: str        # path from image ref, or "" if none


def generate_slug(text: str, used_slugs: set) -> str:
    """
    Generate a URL-friendly slug from text.

    Args:
        text: Input text to slugify
        used_slugs: Set of already used slugs (for deduplication)

    Returns:
        Unique slug string
    """
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')

    original_slug = slug
    counter = 2
    while slug in used_slugs:
        slug = f"{original_slug}-{counter}"
        counter += 1

    used_slugs.add(slug)
    return slug


def extract_title_from_frontmatter(content: str) -> Optional[str]:
    """
    Extract title from mermaid frontmatter block.

    Example:
        ---
        title: My Diagram
        ---
        flowchart LR

    Returns:
        Title string or None if not found.
    """
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        title_match = re.search(r'title:\s*(.+)', frontmatter)
        if title_match:
            return title_match.group(1).strip()
    return None


def generate_title_from_content(content: str) -> str:
    """
    Generate a title from the first few words of diagram content.

    Used when no frontmatter title is present.
    """
    content_no_frontmatter = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

    for line in content_no_frontmatter.split('\n'):
        line = line.strip()
        if line:
            words = line.split()[:4]
            return ' '.join(words)

    return "untitled-diagram"


def extract_diagrams_from_file(md_file: Path) -> List[MermaidDiagram]:
    """
    Extract all mermaid diagrams from a Markdown file.

    For each ```mermaid fence, inspect the line immediately before it.
    If that line is a Markdown image reference, record the image path as
    the replacement and skip writing a .mmd file for this diagram.

    Args:
        md_file: Path to Markdown file

    Returns:
        List of MermaidDiagram objects (includes replaced diagrams for manifest).
    """
    diagrams = []
    used_slugs = set()
    doc_name = md_file.stem  # e.g., "vision" from "vision.md"

    content = md_file.read_text(encoding='utf-8')
    lines = content.split('\n')

    in_mermaid = False
    current_diagram_lines = []
    diagram_start_line = 0
    replacement_path = ""

    for line_num, line in enumerate(lines, 1):
        if not in_mermaid and line.strip() == '```mermaid':
            in_mermaid = True
            diagram_start_line = line_num
            current_diagram_lines = []

            # Check the line immediately preceding this fence for a replacement
            # image reference.  line_num is 1-based; lines is 0-based.
            preceding_index = line_num - 2  # index of the line before this one
            if preceding_index >= 0:
                preceding_line = lines[preceding_index].strip()
                m = _IMAGE_REF_RE.match(preceding_line)
                replacement_path = m.group(1) if m else ""
            else:
                replacement_path = ""

        elif in_mermaid:
            if line.strip() == '```':
                # End of mermaid block
                diagram_content = '\n'.join(current_diagram_lines)

                title = extract_title_from_frontmatter(diagram_content)
                if not title:
                    title = generate_title_from_content(diagram_content)

                slug = generate_slug(title, used_slugs)

                try:
                    relative_path = str(md_file.relative_to(Path.cwd()))
                except ValueError:
                    relative_path = str(md_file)

                diagrams.append(MermaidDiagram(
                    source_file=relative_path,
                    line_number=diagram_start_line,
                    title=title,
                    slug=slug,
                    content=diagram_content,
                    doc_name=doc_name,
                    replacement=replacement_path,
                ))

                in_mermaid = False
                current_diagram_lines = []
                replacement_path = ""
            else:
                current_diagram_lines.append(line)

    return diagrams


def write_mmd_files(diagrams: List[MermaidDiagram], output_dir: Path):
    """
    Write .mmd files for diagrams that have no replacement image.

    Diagrams with a replacement field set are skipped — there is nothing
    to render because the build step will embed the replacement image.

    Args:
        diagrams: List of MermaidDiagram objects
        output_dir: Base output directory (e.g., build/mermaid)
    """
    for diagram in diagrams:
        if diagram.replacement:
            try:
                display_src = Path(diagram.source_file).name
            except Exception:
                display_src = diagram.source_file
            print(f"  Skipped (replacement): {diagram.slug} → {diagram.replacement}")
            continue

        doc_dir = output_dir / diagram.doc_name
        doc_dir.mkdir(parents=True, exist_ok=True)

        mmd_file = doc_dir / f"{diagram.slug}.mmd"

        with mmd_file.open('w', encoding='utf-8') as f:
            f.write(f"{diagram.content}\n")

        try:
            display_path = mmd_file.relative_to(Path.cwd())
        except ValueError:
            display_path = mmd_file
        print(f"  Extracted: {display_path}")


def create_manifest(diagrams: List[MermaidDiagram], output_dir: Path):
    """
    Create manifest.json with metadata for all diagrams.

    Each entry includes a `replacement` field (non-empty string means this
    diagram has a manually refined image; empty string means it should be
    rendered from the .mmd file).

    Args:
        diagrams: List of MermaidDiagram objects
        output_dir: Base output directory (e.g., build/mermaid)
    """
    manifest_path = output_dir / "manifest.json"

    manifest_data = {
        "total_diagrams": len(diagrams),
        "diagrams": [
            {
                "source_file": d.source_file,
                "line_number": d.line_number,
                "title": d.title,
                "slug": d.slug,
                "doc_name": d.doc_name,
                "mmd_path": f"{d.doc_name}/{d.slug}.mmd",
                "replacement": d.replacement,
            }
            for d in diagrams
        ]
    }

    with manifest_path.open('w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)

    try:
        display_path = manifest_path.relative_to(Path.cwd())
    except ValueError:
        display_path = manifest_path
    print(f"\n  Created manifest: {display_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract mermaid diagrams from Markdown files"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/drafts"),
        help="Input directory containing Markdown files (default: docs/drafts)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/mermaid"),
        help="Output directory for .mmd files (default: build/mermaid)"
    )

    args = parser.parse_args()

    md_files = sorted(args.input.glob("*.md"))

    if not md_files:
        print(f"No Markdown files found in {args.input}")
        return

    print(f"Extracting mermaid diagrams from {len(md_files)} files...\n")

    all_diagrams = []
    for md_file in md_files:
        diagrams = extract_diagrams_from_file(md_file)
        if diagrams:
            replaced = sum(1 for d in diagrams if d.replacement)
            print(f"{md_file.name}: {len(diagrams)} diagram(s)"
                  + (f" ({replaced} with replacement)" if replaced else ""))
            all_diagrams.extend(diagrams)

    if not all_diagrams:
        print("\nNo mermaid diagrams found.")
        return

    print(f"\nTotal diagrams found: {len(all_diagrams)}\n")

    write_mmd_files(all_diagrams, args.output)
    create_manifest(all_diagrams, args.output)

    to_render = sum(1 for d in all_diagrams if not d.replacement)
    print(f"\n✓ Extraction complete: {len(all_diagrams)} diagrams "
          f"({to_render} to render, "
          f"{len(all_diagrams) - to_render} with replacements)")


if __name__ == "__main__":
    main()
