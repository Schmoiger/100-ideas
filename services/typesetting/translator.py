"""Markdown to Typst markup translator."""

from __future__ import annotations

import re
from pathlib import Path


def _convert_inline_formatting(text: str) -> str:
    """Convert inline Markdown syntax to Typst syntax."""
    # Protect bold with string tokens so italic doesn't clobber it
    # Markdown: **bold** -> Typst: *bold*
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"@@BOLD@@{m.group(1)}@@BOLD@@", text)
    # Markdown: *italic* -> Typst: _italic_
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: f"_{m.group(1)}_", text)
    # Restore bold as Typst *bold*
    text = text.replace("@@BOLD@@", "*")
    return text


def markdown_to_typst_body(markdown_content: str, idea_id: str) -> str:
    """Translate semantic Markdown chapter content into Typst body markup.

    Converts:
    - Headings (#, ##, ###) -> Typst headings (=, ==, ===)
    - Callout blocks (> [!NOTE] ...) -> Typst styled callout blocks
    - Tables (| ... |) -> Typst #table(...)
    - Images (![...](...)) -> Typst #figure(image(...), caption: [...])
    - Lists (- ...) -> Typst list items
    - Inline styles (**bold**, *italic*, `code`)
    """
    lines = markdown_content.splitlines()
    typst_lines: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 1. Skip horizontal rules (---)
        if stripped == "---":
            typst_lines.append("")
            i += 1
            continue

        # 2. Image: ![caption](path)
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if img_match:
            caption = img_match.group(1).strip()
            path = img_match.group(2).strip()
            caption_clause = f", caption: [{caption}]" if caption else ""
            typst_lines.extend(
                [
                    "#align(center)[",
                    f'  #figure(image("{path}", width: 80%){caption_clause})',
                    "]",
                    "",
                ]
            )
            i += 1
            continue

        # 3. Headings
        if stripped.startswith("### "):
            heading_text = _convert_inline_formatting(stripped[4:].strip())
            typst_lines.extend([f"=== {heading_text}", ""])
            i += 1
            continue
        elif stripped.startswith("## "):
            heading_text = _convert_inline_formatting(stripped[3:].strip())
            typst_lines.extend([f"== {heading_text}", ""])
            i += 1
            continue
        elif stripped.startswith("# "):
            heading_text = _convert_inline_formatting(stripped[2:].strip())
            typst_lines.extend([f"= {heading_text}", ""])
            i += 1
            continue

        # 4. Callout block: > [!NOTE] or > [!IMPORTANT]
        if (
            stripped.startswith("> [!NOTE]")
            or stripped.startswith("> [!IMPORTANT]")
            or stripped.startswith("> [!TIP]")
        ):
            callout_content: list[str] = []
            i += 1
            while i < n and lines[i].strip().startswith(">"):
                c_line = lines[i].strip()[1:].strip()
                if c_line:
                    callout_content.append(_convert_inline_formatting(c_line))
                i += 1
            callout_text = " ".join(callout_content)
            typst_lines.extend(
                [
                    "#block(",
                    '  fill: rgb("#f1f5f9"),',
                    "  inset: (x: 14pt, y: 12pt),",
                    "  radius: 4pt,",
                    '  stroke: (left: 3pt + rgb("#2563EB")),',
                    "  width: 100%,",
                    f")[{callout_text}]",
                    "",
                ]
            )
            continue

        # 5. Tables: lines starting with '|'
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines: list[str] = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                # First line is header
                headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
                # Filter out separator line (e.g. |---|---|)
                data_rows: list[list[str]] = []
                for t_row in table_lines[1:]:
                    cells = [c.strip() for c in t_row.split("|")[1:-1]]
                    if any(c.startswith("---") or c.startswith(":-") for c in cells):
                        continue
                    data_rows.append(cells)

                num_cols = len(headers)
                col_spec = ", ".join(["1fr"] * num_cols)
                typst_lines.extend(
                    [
                        "#table(",
                        f"  columns: ({col_spec}),",
                    ]
                )
                # Headers
                header_cells = ", ".join([f"[{_convert_inline_formatting(h)}]" for h in headers])
                typst_lines.append(f"  {header_cells},")
                # Rows
                for row in data_rows:
                    row_cells = ", ".join([f"[{_convert_inline_formatting(c)}]" for c in row])
                    typst_lines.append(f"  {row_cells},")
                typst_lines.extend([")", ""])
            continue

        # 6. Bullet lists
        if stripped.startswith("- "):
            item_text = _convert_inline_formatting(stripped[2:].strip())
            typst_lines.append(f"- {item_text}")
            i += 1
            continue

        # 7. Regular paragraph
        if stripped:
            typst_lines.append(_convert_inline_formatting(stripped))
        else:
            typst_lines.append("")

        i += 1

    return "\n".join(typst_lines)


def translate_chapter_to_typst(
    chapter_md_path: Path,
    output_body_path: Path,
    output_standalone_path: Path,
    idea_id: str,
    title: str,
    brand_import_path: str = "/typst/brands/neutral.typ",
) -> tuple[Path, Path]:
    """Translate Markdown chapter draft into Typst body and standalone Typst wrapper.

    Produces:
    1. output_body_path (e.g. chapter-body.typ): modular content suitable for #include
    2. output_standalone_path (e.g. chapter.typ): self-contained document for single compilation
    """
    if not chapter_md_path.is_file():
        raise FileNotFoundError(f"Chapter manuscript not found at {chapter_md_path}")

    md_content: str = chapter_md_path.read_text(encoding="utf-8")
    typst_body: str = markdown_to_typst_body(md_content, idea_id)

    # 1. Write body fragment atomically
    temp_body: Path = output_body_path.parent / f".{output_body_path.name}.tmp"
    temp_body.write_text(typst_body, encoding="utf-8")
    temp_body.replace(output_body_path)

    # 2. Write standalone wrapper atomically
    clean_title = title.replace('"', '\\"')
    standalone_content: str = (
        f'#import "{brand_import_path}": plandek-doc, plandek-orange, plandek-light, plandek-dark, plandek-endpiece\n\n'
        f"#show: plandek-doc.with(\n"
        f'  title: "{clean_title}",\n'
        f'  subtitle: "100 Ideas — {idea_id}",\n'
        f'  date: "2026",\n'
        f")\n\n"
        f'#include "{output_body_path.name}"\n\n'
        f'#plandek-endpiece(contact: "https://withineve.com")\n'
    )
    temp_standalone: Path = output_standalone_path.parent / f".{output_standalone_path.name}.tmp"
    temp_standalone.write_text(standalone_content, encoding="utf-8")
    temp_standalone.replace(output_standalone_path)

    return output_body_path, output_standalone_path
