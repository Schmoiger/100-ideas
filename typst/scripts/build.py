#!/usr/bin/env python3
"""
Plandek document build driver.

Reads build.yaml and orchestrates the full pipeline:
  1. Optimise images (resize + quantise) — unless profile has optimise_images: false
  2. For each document (or subset):
     a. Generate wrapper stub from build.yaml (incremental: skips if config unchanged)
     b. pandoc: Markdown → Typst content file (incremental: skips if .md unchanged)
     c. strip preamble (H1, YAML front-matter, inline ToC)
     d. fix paths and artefacts in generated Typst
     e. substitute mermaid blocks with image references
  3. Compile each document wrapper to PDF via typst
  4. Assemble books: generate combined .typ, compile to PDF

Incremental builds
------------------
Each generated file has a sidecar .hash file recording the SHA-256 of its
inputs.  A step is skipped when the output exists and its stored hash matches
the current input hash.

  {doc}-book.typ.hash   inputs: doc entry from build.yaml (title/subtitle/date/src/wrapper)
  {doc}-content.typ.hash  inputs: .md content + profile path-rewrite flag

Usage
-----
  uv run python typst/scripts/build.py                         # build all docs + books (production)
  uv run python typst/scripts/build.py --profile draft         # skip image optimisation
  uv run python typst/scripts/build.py --docs vision journey   # build specific docs only
  uv run python typst/scripts/build.py --books new-devx-full   # build specific books only
  uv run python typst/scripts/build.py --docs vision --books new-devx-full
  uv run python typst/scripts/build.py --brand plandek         # optional; Make passes BRAND
  uv run python typst/scripts/build.py --assemble PATH.md      # one file → PDF (no YAML; -{brand} in name)
  uv run python typst/scripts/build.py --assemble A.md B.md  # book + auto part dividers
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath

import yaml

# ── Colour helpers ────────────────────────────────────────────────────────────
_GREEN  = "\033[0;32m"
_BLUE   = "\033[0;34m"
_YELLOW = "\033[0;33m"
_RED    = "\033[0;31m"
_NC     = "\033[0m"

def _g(s: str) -> str: return f"{_GREEN}{s}{_NC}"
def _b(s: str) -> str: return f"{_BLUE}{s}{_NC}"
def _y(s: str) -> str: return f"{_YELLOW}{s}{_NC}"
def _r(s: str) -> str: return f"{_RED}{s}{_NC}"


# ── Incremental hash helpers ──────────────────────────────────────────────────

def _sha256(*parts: str) -> str:
    """Return the SHA-256 hex digest of the concatenation of all string parts."""
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
    return h.hexdigest()


def _read_hash(hash_file: Path) -> str:
    """Return the stored hash, or '' if the file does not exist."""
    return hash_file.read_text(encoding="utf-8").strip() if hash_file.exists() else ""


def _write_hash(hash_file: Path, digest: str) -> None:
    hash_file.write_text(digest, encoding="utf-8")


def _is_current(output: Path, hash_file: Path, current_digest: str) -> bool:
    """Return True when output exists and its stored hash matches current_digest."""
    return output.exists() and _read_hash(hash_file) == current_digest


# ── Config loading ────────────────────────────────────────────────────────────

def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg


def resolve_profile(cfg: dict, profile_name: str) -> dict:
    """Merge pipeline defaults with the named profile."""
    pipeline = cfg.get("pipeline", {})
    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        available = ", ".join(profiles)
        print(_r(f"Error: profile '{profile_name}' not found. Available: {available}"))
        sys.exit(1)
    return {**pipeline, **profiles[profile_name]}


def resolve_brand(
    cfg: dict,
    doc_or_book: dict,
    cli_brand: str | None,
    repo_root: Path | None = None,
) -> tuple[str, str]:
    """Return (typst_module_path, brand_id) for a document or book entry.

    Precedence: optional YAML ``brand:`` pin → ``--brand`` / ``$BRAND`` →
    ``pipeline.default_brand`` (fallback ``neutral``).

    When ``repo_root`` is set, verifies the Typst module file exists (clearer
    than a failed ``#import`` inside Typst).
    """
    brands = cfg.get("brands") or {}
    if not brands:
        module = "/typst/brands/plandek.typ"
        if repo_root is not None:
            _assert_brand_module_exists(repo_root, module, "plandek")
        return module, "plandek"

    pin = (doc_or_book.get("brand") or "").strip()
    cli = (cli_brand or "").strip() or None
    pipeline = cfg.get("pipeline") or {}
    default_id = str(pipeline.get("default_brand", "neutral")).strip()

    chosen = pin or cli or default_id
    if chosen not in brands:
        avail = ", ".join(sorted(brands))
        print(_r(f"Error: unknown brand '{chosen}'. Defined in build.yaml: {avail}"))
        sys.exit(1)

    entry = brands[chosen]
    module = entry.get("module")
    if not module or not isinstance(module, str):
        print(_r(f"Error: brand '{chosen}' missing string 'module' in build.yaml"))
        sys.exit(1)

    if repo_root is not None:
        _assert_brand_module_exists(repo_root, module, chosen)
    return module, chosen


def _assert_brand_module_exists(repo_root: Path, module: str, brand_id: str) -> None:
    """Exit with a clear message if ``module`` (repo-root path) is not a file."""
    rel = module.lstrip("/")
    path = (repo_root / rel).resolve()
    if not path.is_file():
        print(_r(
            f"Error: brand '{brand_id}' module is not a file: {module}\n"
            f"       expected at: {path}"
        ))
        sys.exit(1)


def _output_pdf_with_brand(path: Path, brand_id: str) -> Path:
    """Insert ``-{brand_id}`` before ``.pdf`` so different brands never overwrite.

    If the basename already ends with ``-{brand_id}`` (case-insensitive), return
    ``path`` unchanged — avoids ``new-devx-plandek-plandek.pdf`` when the YAML
    output is already brand-suffixed.
    """
    if path.suffix.lower() != ".pdf":
        return path
    stem, suf = path.stem, path.suffix
    tail = f"-{brand_id}"
    if stem.lower().endswith(tail.lower()):
        return path
    return path.with_name(f"{stem}{tail}{suf}")


def _effective_contact(doc_or_book: dict, brand_id: str) -> str:
    """Contact line for endpiece / endpage; Plandek default only for plandek brand."""
    if "contact" in doc_or_book:
        return str(doc_or_book["contact"])
    return "wlytle@plandek.com" if brand_id == "plandek" else ""


# ── Subprocess helpers ────────────────────────────────────────────────────────

def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    """Run a command."""
    return subprocess.run(cmd, check=check, **kwargs)


# ── Step 1: Image optimisation ────────────────────────────────────────────────

def optimise_images(profile: dict, repo_root: Path) -> None:
    if not profile.get("optimise_images", True):
        print(f"  {_y('Skip')} image optimisation (profile: optimise_images=false)")
        return

    max_px = profile.get("max_px", 1024)
    src = repo_root / "docs" / "diagrams"
    dest = repo_root / "build" / "diagrams-opt"
    dest.mkdir(parents=True, exist_ok=True)

    run([
        "uv", "run", "python", str(Path(__file__).parent / "optimise-images.py"),
        "--src", str(src),
        "--dest", str(dest),
        "--max-px", str(max_px),
    ])


# ── Step 2: Generate wrapper stub ─────────────────────────────────────────────

def generate_wrapper(
    doc_id: str,
    doc_cfg: dict,
    build_dir: Path,
    cfg: dict,
    cli_brand: str | None,
    repo_root: Path,
    cli_cover_style: str | None = None,
    cli_seed: int | None = None,
) -> Path:
    """
    Generate build/typst/{doc_id}-book.typ from build.yaml metadata.

    Incremental: skips generation when the doc's config entry hasn't changed.
    Returns the path to the wrapper file.
    """
    wrapper = build_dir / f"{doc_id}-book.typ"
    hash_file = build_dir / f"{doc_id}-book.typ.hash"

    brand_module, brand_id = resolve_brand(cfg, doc_cfg, cli_brand, repo_root)

    cover_style = (cli_cover_style or doc_cfg.get("cover-style") or doc_cfg.get("cover_style") or "split-mesh").strip()
    raw_seed = cli_seed if cli_seed is not None else (doc_cfg.get("seed") if doc_cfg.get("seed") is not None else doc_cfg.get("cover-seed", 0))
    try:
        seed = int(raw_seed)
    except (ValueError, TypeError):
        seed = 0

    date_val = str(doc_cfg.get("date", "") or "").strip()
    edition_val = str(doc_cfg.get("edition", "") or "").strip()
    if edition_val and date_val:
        date_line = f"{edition_val} · {date_val}"
    elif edition_val:
        date_line = edition_val
    else:
        date_line = date_val

    # Hash doc config plus effective brand, cover style, seed, and date line
    current_digest = _sha256(
        json.dumps(doc_cfg, sort_keys=True),
        brand_id,
        cover_style,
        str(seed),
        date_line,
    )

    if _is_current(wrapper, hash_file, current_digest):
        print(f"  {_y('Skip')} wrapper (unchanged): {wrapper.name}")
        return wrapper

    title    = doc_cfg.get("title", doc_id)
    subtitle = doc_cfg.get("subtitle", "")
    content_include = f"/build/typst/{doc_id}-content.typ"

    contact = _effective_contact(doc_cfg, brand_id)

    text = "\n".join([
        "// Auto-generated by typst/scripts/build.py — do not edit manually.",
        f"// Document: {doc_id}  brand: {brand_id}  cover-style: {cover_style}  seed: {seed}",
        "",
        f'#import "{brand_module}": plandek-doc, plandek-endpiece',
        "",
        "#show: plandek-doc.with(",
        f"  title:       {_typ_str(title)},",
        f"  subtitle:    {_typ_str(subtitle)},",
        f"  date:        {_typ_str(date_line)},",
        f"  cover-style: {_typ_str(cover_style)},",
        f"  cover-seed:  {seed},",
        ")",
        "",
        f'#include "{content_include}"',
        "",
        f"#plandek-endpiece(contact: {_typ_str(contact)})",
        "",
    ])

    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(text, encoding="utf-8")
    _write_hash(hash_file, current_digest)
    print(f"  {_b('Generated')} wrapper: {wrapper.name}")
    return wrapper


# ── Checkbox list fixup ───────────────────────────────────────────────────────

_UNCHECKED_MARKER = (
    'box(stroke: 0.5pt + rgb("#888"), '
    'width: 0.55em, height: 0.55em, radius: 1pt, baseline: 0.1em)'
)
_CHECKED_MARKER = (
    'box(stroke: 0.5pt + rgb("#888"), fill: rgb("#E85D1A"), '
    'width: 0.55em, height: 0.55em, radius: 1pt, baseline: 0.1em)'
)


def _replace_checkbox_runs(text: str) -> str:
    """Wrap consecutive Markdown-task-list items in a checkbox-marker list.

    Pandoc emits ``- ☐ text`` (or ``- ☑ text``) for ``- [ ]`` / ``- [x]``.
    A bare character replacement leaves both the template bullet marker *and*
    the checkbox visible.  Instead we detect runs of consecutive checkbox lines,
    strip the checkbox glyph, and wrap the run in a scoped ``#set list(marker:
    ...)`` block so the checkbox **is** the marker.
    """
    def _rewrite(match: re.Match) -> str:
        body = match.group(0)
        has_checked = "\u2611" in body
        marker = _CHECKED_MARKER if has_checked else _UNCHECKED_MARKER
        body = body.replace("\u2610 ", "").replace("\u2611 ", "")
        return f"#[\n#set list(marker: {marker})\n{body}]\n"

    return re.sub(
        r"((?:^- [\u2610\u2611] .*\n?)+)",
        _rewrite,
        text,
        flags=re.MULTILINE,
    )


# ── Table column fixup ────────────────────────────────────────────────────────

_COL_AUTO_THRESHOLD = 0.0  # all columns become 1fr (equal width)

def _replace_pct_columns(match: re.Match) -> str:
    """Replace Pandoc's percentage columns with an auto/1fr mix.

    Columns whose Pandoc-inferred width is below ``_COL_AUTO_THRESHOLD`` are
    assumed to be narrow label columns and sized to ``auto`` (shrink-to-content).
    All other columns become ``1fr`` (share remaining space equally).
    """
    pcts = re.findall(r"([\d.]+)%", match.group(1))
    if not pcts:
        return match.group(0)
    cols = ["auto" if float(p) < _COL_AUTO_THRESHOLD else "1fr" for p in pcts]
    return "columns: (" + ", ".join(cols) + ")"


# ── Step 3: pandoc conversion ─────────────────────────────────────────────────

def convert_to_typst(
    md_file: Path,
    content_file: Path,
    profile: dict,
    build_dir: Path,
) -> bool:
    """
    Run pandoc and apply all post-processing passes.

    Incremental: skips when md_file content and the optimise_images flag
    are unchanged since the last successful conversion.

    Returns True if the content file was (re)generated, False if skipped.
    """
    hash_file = build_dir / f"{content_file.name}.hash"

    # Hash inputs: markdown content + the flag that affects image path rewriting
    opt_flag = ("opt" if profile.get("optimise_images", True) else "src") + ":v2"
    current_digest = _sha256(md_file.read_text(encoding="utf-8"), opt_flag)

    if _is_current(content_file, hash_file, current_digest):
        print(f"  {_y('Skip')} conversion (unchanged): {md_file.name}")
        return False

    content_file.parent.mkdir(parents=True, exist_ok=True)

    # Pre-pandoc: strip <!-- typst-skip-start --> … <!-- typst-skip-end --> blocks.
    # This lets authors annotate sections in Markdown that should not appear in
    # the typeset output (e.g. revision history tables).
    md_text = md_file.read_text(encoding="utf-8")
    md_text = re.sub(
        r"<!--\s*typst-skip-start\s*-->.*?<!--\s*typst-skip-end\s*-->",
        "",
        md_text,
        flags=re.DOTALL,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(md_text)
        tmp_path = tmp.name
    try:
        run(["pandoc", tmp_path, "-f", "markdown", "-t", "typst", "--wrap=none", "-o", str(content_file)])
    finally:
        os.unlink(tmp_path)

    text = content_file.read_text(encoding="utf-8")

    # Image paths: diagrams/ → optimised dir (or source dir for draft profile)
    img_base = "../../build/diagrams-opt/" if profile.get("optimise_images", True) else "../../docs/diagrams/"
    text = text.replace('image("diagrams/', f'image("{img_base}')

    # Remove #cite() artefacts from @username patterns in URLs
    text = re.sub(r'#cite\(label\("[^"]*"\), form: "prose"\)', "", text)

    # Remove horizontal rules that appear immediately before H1/H2 headings.
    # The headings force page breaks; leaving the rule leaves it stranded on a blank page.
    text = re.sub(
        r'#(?:horizontalrule|divider)(?:\(\))?\n+(?=={1,2} )',
        '',
        text
    )

    # Replace remaining horizontal rules with styled inline rule
    text = re.sub(
        r'#(?:horizontalrule|divider)(?:\(\))?',
        '#line(length: 100%, stroke: 0.4pt + rgb("#CCCCCC"))',
        text
    )

    # Comment out broken internal links generated by pandoc from anchors
    text = re.sub(
        r"^(.*#link\(<[^>]*>\).*)$",
        r"// FIXME: Broken link - \1",
        text,
        flags=re.MULTILINE,
    )

    # Remove table.hline() inserted by Pandoc after every header row.
    # The template now provides its own header underline via stroke styling;
    # the Pandoc hline would draw a default 1pt black line over it.
    text = text.replace("    table.hline(),\n", "")

    # Replace percentage-based table columns with fractional (1fr) sizing.
    # Pandoc derives column percentages from dash-padding in Markdown separator
    # rows, which is fragile and non-semantic.  Columns below a threshold are
    # set to auto (shrink-to-content); the rest share remaining space equally.
    text = re.sub(
        r"columns: \(([^)]+)\)",
        _replace_pct_columns,
        text,
    )

    # Replace Markdown task-list items with checkbox-marker lists.
    # Pandoc emits "- ☐ text" / "- ☑ text" from "- [ ]" / "- [x]" but the
    # document font (Outfit) lacks those glyphs, causing [?] in the PDF.
    # We wrap consecutive checkbox lines in a scoped content block that
    # overrides the list marker to a Typst-drawn checkbox.
    text = _replace_checkbox_runs(text)

    # Prevent orphaned lead-in text before tables or lists.
    # Bold lines like "#strong[Common early triggers]:" immediately before
    # a #figure(table) or a bullet list can end up stranded at the bottom
    # of a page.  Wrapping them in block(sticky: true) keeps them with the
    # content that follows.
    text = re.sub(
        r"^(#strong\[[^\]]+\]:?)$(\n\n)(#figure\(|- )",
        r"#block(sticky: true)[\1]\2\3",
        text,
        flags=re.MULTILINE,
    )

    content_file.write_text(text, encoding="utf-8")
    return True  # signal to caller that preamble strip + mermaid sub must run


# ── Step 4: Preamble stripping ────────────────────────────────────────────────

def strip_preamble(content_file: Path) -> None:
    """Remove H1 title, YAML front-matter artefacts, and inline ToC."""
    lines = content_file.read_text(encoding="utf-8").splitlines()
    i, n = 0, len(lines)

    def skip_blank(i: int) -> int:
        while i < n and not lines[i].strip():
            i += 1
        return i

    i = skip_blank(i)

    # Skip Typst label anchor for document title (e.g. <my-doc>)
    if i < n and re.match(r"^<[a-z0-9][a-z0-9-]*>$", lines[i].strip()):
        i += 1
    i = skip_blank(i)

    # Skip document-level H1 (pandoc: "# Title" → "= Title")
    if i < n and lines[i].startswith("= "):
        i += 1

    # Skip preamble lines until the first real content heading or paragraph
    while i < n:
        s = lines[i].strip()
        if s == "":
            i += 1; continue
        if re.match(r"^<[a-z0-9][a-z0-9-]*>$", s):
            i += 1; continue
        if s in ('#divider()', '#horizontalrule') or s.startswith('#line('):
            i += 1; continue
        if (s.startswith("#strong[") or s.startswith("*")) and ":" in s:
            i += 1; continue
        # Continuation of a wrapped #strong[…] preamble line (e.g. pandoc
        # split "Last\nUpdated]: …" across lines)
        if re.match(r"^[A-Za-z]+\]", s) and ":" in s:
            i += 1; continue
        # Inline ToC section — skip until next real heading
        if (s.startswith("== ") or s.startswith("= ")) and any(
            kw in s.lower() for kw in ("content", "table of", "toc")
        ):
            i += 1
            while i < n:
                s2 = lines[i].strip()
                if (s2.startswith("= ") or s2.startswith("== ")) and not any(
                    kw in s2.lower() for kw in ("content", "table of", "toc")
                ):
                    break
                i += 1
            continue
        break  # real content starts here

    content_file.write_text("\n".join(lines[i:]) + "\n", encoding="utf-8")


# ── Step 5: Mermaid substitution ──────────────────────────────────────────────

def substitute_mermaid(content_file: Path, doc_name: str, repo_root: Path) -> None:
    manifest = repo_root / "build" / "mermaid" / "manifest.json"
    if not manifest.exists():
        print(f"  {_y('Skip')} mermaid substitution (manifest not found — run make extract first)")
        return
    run([
        "uv", "run", "python", str(Path(__file__).parent / "substitute-mermaid.py"),
        "--content", str(content_file),
        "--manifest", str(manifest),
        "--doc", doc_name,
    ])


def _finish_content(
    content_file: Path,
    hash_file: Path,
    current_digest: str,
    doc_id: str,
    repo_root: Path,
) -> None:
    """Run preamble strip + mermaid substitution, then write the content hash."""
    strip_preamble(content_file)
    substitute_mermaid(content_file, doc_id, repo_root)
    _write_hash(hash_file, current_digest)


# ── Step 6: typst compile ─────────────────────────────────────────────────────

def compile_typst(
    wrapper: Path,
    output_pdf: Path,
    repo_root: Path,
    profile: dict,
) -> bool:
    """
    Compile a Typst file to PDF.  Returns True on success.
    """
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "typst", "compile", str(wrapper), str(output_pdf),
            "--root", str(repo_root),
            "--font-path", str(repo_root / "docs" / "assets" / "fonts"),
        ],
        capture_output=True,
        text=True,
    )

    # Print typst output (warnings etc.), suppressing blank lines
    for line in (result.stdout + result.stderr).splitlines():
        if line.strip():
            print(f"  {line}")

    if not output_pdf.exists():
        print(_r(f"  ✗ Failed to produce {output_pdf.name}"))
        return False

    size_bytes = output_pdf.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{size_bytes // 1024} KB"

    limit_mb = profile.get("size_target_mb", 3)
    size_check = profile.get("size_check", True)

    if size_check and size_mb > limit_mb:
        print(f"  {_g('✓')} {output_pdf.name} ({size_str}) {_y(f'⚠ exceeds {limit_mb} MB target')}")
    else:
        print(f"  {_g('✓')} {output_pdf.name} ({size_str})")

    return True


# ── Single-document build ─────────────────────────────────────────────────────

def build_document(
    doc_id: str,
    doc_cfg: dict,
    profile: dict,
    repo_root: Path,
    cfg: dict,
    cli_brand: str | None,
    output_pdf: Path | None = None,
    *,
    brand_suffix_output: bool = True,
    cli_cover_style: str | None = None,
    cli_seed: int | None = None,
) -> bool:
    """Build one document.  Returns True on success.

    Default PDF path is ``build/pdf/{doc_id}-{brand}.pdf`` so the same document
    id can be built with different brands without overwriting.

    When ``output_pdf`` is set (e.g. ``--assemble``), pass
    ``brand_suffix_output=False`` for an explicit ``--assemble-output`` path so
    the filename is not altered.
    """
    print(f"\n{'='*45}")
    print(f"  Building: {doc_id}")
    print(f"{'='*45}")

    md_file      = repo_root / doc_cfg["src"]
    build_dir    = repo_root / "build" / "typst"
    content_file = build_dir / f"{doc_id}-content.typ"
    content_hash_file = build_dir / f"{doc_id}-content.typ.hash"
    _, brand_id = resolve_brand(cfg, doc_cfg, cli_brand, repo_root)
    if output_pdf is None:
        output_pdf = repo_root / "build" / "pdf" / f"{doc_id}.pdf"
    else:
        output_pdf = output_pdf if output_pdf.is_absolute() else repo_root / output_pdf
    if brand_suffix_output:
        output_pdf = _output_pdf_with_brand(output_pdf, brand_id)

    if not md_file.exists():
        print(_r(f"  Error: source not found: {md_file}"))
        return False

    # Step 2: generate wrapper stub from build.yaml
    wrapper = generate_wrapper(
        doc_id,
        doc_cfg,
        build_dir,
        cfg,
        cli_brand,
        repo_root,
        cli_cover_style=cli_cover_style,
        cli_seed=cli_seed,
    )

    # Step 3: pandoc conversion (incremental)
    opt_flag = ("opt" if profile.get("optimise_images", True) else "src") + ":v2"
    content_digest = _sha256(md_file.read_text(encoding="utf-8"), opt_flag)

    regenerated = convert_to_typst(md_file, content_file, profile, build_dir)

    if regenerated:
        # Steps 4 & 5: preamble strip + mermaid substitution + write hash
        print(f"  {_b('Processing')} preamble + mermaid...")
        _finish_content(content_file, content_hash_file, content_digest, doc_id, repo_root)
    # If not regenerated, content file is already fully processed from last run

    # Step 6: typst compile (always — Typst has its own incremental cache)
    print(f"  {_b('Compiling')} {wrapper.name} → PDF...")
    return compile_typst(wrapper, output_pdf, repo_root, profile)


# ── Ensure document content is available (for book assembly) ─────────────────

def ensure_content(doc_id: str, doc_cfg: dict, profile: dict, repo_root: Path) -> bool:
    """
    Ensure build/typst/{doc_id}-content.typ is up to date.
    Called by build_book for documents not already built in this session.
    Returns True on success.
    """
    md_file      = repo_root / doc_cfg["src"]
    build_dir    = repo_root / "build" / "typst"
    content_file = build_dir / f"{doc_id}-content.typ"
    content_hash_file = build_dir / f"{doc_id}-content.typ.hash"

    if not md_file.exists():
        print(_r(f"  Error: source not found: {md_file}"))
        return False

    opt_flag = ("opt" if profile.get("optimise_images", True) else "src") + ":v2"
    content_digest = _sha256(md_file.read_text(encoding="utf-8"), opt_flag)

    regenerated = convert_to_typst(md_file, content_file, profile, build_dir)
    if regenerated:
        _finish_content(content_file, content_hash_file, content_digest, doc_id, repo_root)

    return True


# ── Book assembly ─────────────────────────────────────────────────────────────

def build_book(
    book_id: str,
    book_cfg: dict,
    doc_cfgs: dict,
    profile: dict,
    repo_root: Path,
    cfg: dict,
    cli_brand: str | None,
    *,
    brand_suffix_output: bool = True,
    cli_cover_style: str | None = None,
    cli_seed: int | None = None,
) -> bool:
    """
    Assemble a multi-document book from parts and compile to PDF.
    Generates build/typst/{book_id}-book.typ at build time.
    """
    print(f"\n{'='*45}")
    print(f"  Building book: {book_id}")
    print(f"{'='*45}")

    build_dir  = repo_root / "build" / "typst"
    output_pdf = repo_root / book_cfg.get("output", f"build/pdf/{book_id}.pdf")
    parts      = book_cfg.get("parts", [])

    # Ensure all referenced document content files are current
    doc_ids_needed = {p["doc"] for p in parts if p["type"] == "document"}
    for doc_id in doc_ids_needed:
        dc = doc_cfgs.get(doc_id)
        if dc is None:
            print(_r(f"  Error: document '{doc_id}' not in registry"))
            return False
        if not ensure_content(doc_id, dc, profile, repo_root):
            return False

    # Resolve end-page by brand (supports plain string or brand-keyed mapping)
    end_page_cfg = book_cfg.get("end-page")
    end_page_src_resolved = None
    if isinstance(end_page_cfg, str):
        end_page_src_resolved = end_page_cfg
    elif isinstance(end_page_cfg, dict):
        _brand_mod, brand_id = resolve_brand(cfg, book_cfg, cli_brand, repo_root)
        end_page_src_resolved = end_page_cfg.get(brand_id) or end_page_cfg.get("neutral")
        if brand_id != "neutral" and end_page_src_resolved == end_page_cfg.get("neutral"):
            print(f"  {_y('Warning')} end-page for brand '{brand_id}' not found, falling back to neutral")
    if end_page_src_resolved:
        ep_md = repo_root / end_page_src_resolved
        if not ep_md.exists():
            print(_r(f"  Error: end-page source not found: {ep_md}"))
            return False
        ep_content = build_dir / "end-page-content.typ"
        ep_hash_file = build_dir / "end-page-content.typ.hash"
        ep_digest = _sha256(ep_md.read_text(encoding="utf-8"), "endpage")
        if not _is_current(ep_content, ep_hash_file, ep_digest):
            print(f"  {_b('Converting')} end-page.md → Typst...")
            run(["pandoc", str(ep_md), "-f", "markdown", "-t", "typst", "-o", str(ep_content)])
            _write_hash(ep_hash_file, ep_digest)
        else:
            print(f"  {_y('Skip')} end-page conversion (unchanged)")

    # Generate the book wrapper
    book_wrapper = build_dir / f"{book_id}-book.typ"
    book_hash_file = build_dir / f"{book_id}-book.typ.hash"
    _brand_mod, brand_id = resolve_brand(cfg, book_cfg, cli_brand, repo_root)
    if brand_suffix_output:
        output_pdf = _output_pdf_with_brand(output_pdf, brand_id)

    cover_style = (cli_cover_style or book_cfg.get("cover-style") or book_cfg.get("cover_style") or "split-mesh").strip()
    raw_seed = cli_seed if cli_seed is not None else (book_cfg.get("seed") if book_cfg.get("seed") is not None else book_cfg.get("cover-seed", 0))
    try:
        seed = int(raw_seed)
    except (ValueError, TypeError):
        seed = 0

    date_val = str(book_cfg.get("date", "") or "").strip()
    edition_val = str(book_cfg.get("edition", "") or "").strip()
    if edition_val and date_val:
        date_line = f"{edition_val} · {date_val}"
    elif edition_val:
        date_line = edition_val
    else:
        date_line = date_val

    book_digest = _sha256(json.dumps(book_cfg, sort_keys=True), brand_id, cover_style, str(seed), date_line)

    if _is_current(book_wrapper, book_hash_file, book_digest):
        print(f"  {_y('Skip')} book wrapper (unchanged): {book_wrapper.name}")
    else:
        _generate_book_typ(
            book_id,
            book_cfg,
            parts,
            book_wrapper,
            repo_root,
            doc_cfgs,
            _brand_mod,
            brand_id,
            end_page_src_resolved,
            cli_cover_style=cli_cover_style,
            cli_seed=cli_seed,
        )
        _write_hash(book_hash_file, book_digest)

    print(f"  {_b('Compiling')} {book_wrapper.name} → PDF...")
    return compile_typst(book_wrapper, output_pdf, repo_root, profile)


def _check_doc_headings(doc_id: str, doc_cfg: dict, repo_root: Path) -> None:
    """
    Verify that the source .md for doc_id contains at least one ## heading.
    Raises SystemExit with a clear message if none are found — this prevents
    a per-part contents page from rendering an empty outline.
    """
    md_file = repo_root / doc_cfg["src"]
    if not md_file.exists():
        print(_r(f"  Error: source not found for '{doc_id}': {md_file}"))
        sys.exit(1)
    text = md_file.read_text(encoding="utf-8")
    # Count lines that start with ## (level-2 headings or deeper)
    headings = [l for l in text.splitlines() if re.match(r"^#{2,}\s+\S", l)]
    if not headings:
        print(_r(
            f"  Error: document '{doc_id}' has no ## headings. "
            "Per-part contents requires at least one section heading. "
            "Add headings to the source .md or remove 'contents: true' from this part."
        ))
        sys.exit(1)
    print(f"  {_b('Checked')} '{doc_id}': {len(headings)} heading(s) found ✓")


def _generate_book_typ(
    book_id: str,
    book_cfg: dict,
    parts: list[dict],
    out_file: Path,
    repo_root: Path,
    doc_cfgs: dict,
    brand_module: str,
    brand_id: str,
    end_page_src: str | None = None,
    cli_cover_style: str | None = None,
    cli_seed: int | None = None,
) -> None:
    """Generate the top-level Typst file for a book."""
    title    = book_cfg.get("title", book_id)
    subtitle = book_cfg.get("subtitle", "")
    cover_style = (cli_cover_style or book_cfg.get("cover-style") or book_cfg.get("cover_style") or "split-mesh").strip()
    raw_seed = cli_seed if cli_seed is not None else (book_cfg.get("seed") if book_cfg.get("seed") is not None else book_cfg.get("cover-seed", 0))
    try:
        seed = int(raw_seed)
    except (ValueError, TypeError):
        seed = 0

    date_val = str(book_cfg.get("date", "") or "").strip()
    edition_val = str(book_cfg.get("edition", "") or "").strip()
    if edition_val and date_val:
        date_line = f"{edition_val} · {date_val}"
    elif edition_val:
        date_line = edition_val
    else:
        date_line = date_val

    contact  = _effective_contact(book_cfg, brand_id)
    # end_page_src is passed from build_book(), which resolves the brand-keyed
    # end-page config from book_cfg.get("end-page").  Do NOT look it up again
    # from book_cfg here — the YAML key is "end-page" (with hyphen), not "endpage".
    if isinstance(end_page_src, dict):
        end_page_src = None  # caller should have resolved the dict to a string

    lines = [
        "// Auto-generated by typst/scripts/build.py — do not edit manually.",
        f"// Book: {book_id}  brand: {brand_id}  cover-style: {cover_style}  seed: {seed}",
        "",
        f'#import "{brand_module}": '
        "plandek-doc, plandek-contents, plandek-part-contents, "
        "plandek-part-divider, plandek-endpiece, plandek-endpage",
        "",
        "#show: plandek-doc.with(",
        f"  title:       {_typ_str(title)},",
        f"  subtitle:    {_typ_str(subtitle)},",
        f"  date:        {_typ_str(date_line)},",
        f"  cover-style: {_typ_str(cover_style)},",
        f"  cover-seed:  {seed},",
        ")",
        "",
    ]

    # ── Pre-pass: build a mapping from document index → sentinel label name.
    # Documents get labels like "part-doc-0", "part-doc-1", etc. (index into
    # the parts list, not the document list, to keep them unique).
    # This is needed so part-dividers can reference the start label of the
    # *next* document for bounding the outline.
    doc_part_indices = []  # indices in `parts` that are documents
    for i, part in enumerate(parts):
        if part["type"] == "document":
            doc_part_indices.append(i)

    def _sentinel_label(parts_index: int) -> str:
        return f"plandek-part-{parts_index}"

    # ── Determine, for each part-divider that wants contents, which document
    # follows it and which document comes after that (for bounding the outline).
    # We walk parts once and annotate dividers.
    annotated: list[dict] = []
    for i, part in enumerate(parts):
        entry = dict(part)
        if part["type"] == "interstitial":
            params = part.get("params", {})
            if params.get("style", "part-divider") == "part-divider" and params.get("contents", False):
                # Find the next document index after this interstitial
                next_doc_idx = next((j for j in doc_part_indices if j > i), None)
                # Find the document index after that (for the end bound)
                after_doc_idx = next((j for j in doc_part_indices if j > next_doc_idx), None) if next_doc_idx is not None else None
                entry["_next_doc_idx"] = next_doc_idx
                entry["_after_doc_idx"] = after_doc_idx

                # Heading check: verify the next doc has ## headings
                if next_doc_idx is not None:
                    next_doc_id = parts[next_doc_idx].get("doc", "")
                    dc = doc_cfgs.get(next_doc_id)
                    if dc:
                        _check_doc_headings(next_doc_id, dc, repo_root)
        annotated.append(entry)

    # ── Emit Typst lines ──────────────────────────────────────────────────────
    first_doc_seen = False
    for i, part in enumerate(annotated):
        ptype = part["type"]

        if ptype == "document":
            doc_id = part["doc"]
            content_path = f"/build/typst/{doc_id}-content.typ"
            sentinel = _sentinel_label(i)
            if first_doc_seen:
                lines.append("// ── document boundary ──")
                lines.append("#pagebreak(weak: true)")
            first_doc_seen = True
            # Place sentinel label so per-part outlines can anchor to it
            lines.append(f"// ── sentinel: {sentinel} ──")
            lines.append(f"#[#metadata(none) <{sentinel}>]")
            lines.append(f'#include "{content_path}"')
            lines.append("")

        elif ptype == "interstitial":
            params      = part.get("params", {})
            style       = params.get("style", "part-divider")
            label       = params.get("label", "")
            title_param = params.get("title", "")
            depth       = params.get("depth", 2)
            show_contents = params.get("contents", False)

            if style == "contents":
                # Global contents page (full document ToC)
                lines.append("// ── interstitial: global contents page ──")
                lines.append(f"#plandek-contents(depth: {depth})")
                lines.append("")

            else:
                # Part divider (dark branded page)
                lines.append(f"// ── interstitial: {label} ──")
                lines.append("#pagebreak(weak: true)")
                if show_contents:
                    next_doc_idx  = part.get("_next_doc_idx")
                    after_doc_idx = part.get("_after_doc_idx")
                    start_lbl = _sentinel_label(next_doc_idx)  if next_doc_idx  is not None else ""
                    end_lbl   = _sentinel_label(after_doc_idx) if after_doc_idx is not None else ""
                    lines.append(
                        f"#plandek-part-divider("
                        f"label: {_typ_str(label)}, "
                        f"title: {_typ_str(title_param)}, "
                        f"contents: true, "
                        f"part-start-label: {_typ_str(start_lbl)}, "
                        f"part-end-label: {_typ_str(end_lbl)}, "
                        f"depth: {depth})"
                    )
                else:
                    lines.append(
                        f"#plandek-part-divider("
                        f"label: {_typ_str(label)}, "
                        f"title: {_typ_str(title_param)})"
                    )
                lines.append("#pagebreak(weak: true)")
                lines.append("")

    # ── Closing page ──────────────────────────────────────────────────────────
    if end_page_src:
        ep_content_id = "end-page"
        ep_content_path = f"/build/typst/{ep_content_id}-content.typ"
        lines.append("// ── end page ──")
        lines.append(f"#plandek-endpage(contact: {_typ_str(contact)})[")
        lines.append(f'  #include "{ep_content_path}"')
        lines.append("]")
        lines.append("")
    else:
        lines.append("// ── endpiece ──")
        lines.append(f"#plandek-endpiece(contact: {_typ_str(contact)})")
        lines.append("")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {_b('Generated')} {out_file.relative_to(repo_root)}")


def _typ_str(s: str) -> str:
    """Escape a Python string as a Typst string literal."""
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


# ── Ad-hoc assemble (paths → single doc or auto-parted book) ──────────────────

# When ``--assemble`` is given a bare filename, try these dirs under repo root (first hit wins).
_ASSEMBLE_INPUT_SEARCH_DIRS: tuple[str, ...] = ("docs/drafts", "context/docs")


def _assemble_is_basename_only(raw: str) -> bool:
    """True when ``raw`` is a single path segment (no directory separators)."""
    s = raw.strip()
    if not s or "/" in s or "\\" in s:
        return False
    parts = PurePath(s).parts
    if len(parts) != 1:
        return False
    return parts[0] not in (".", "..")


def _assemble_resolve_one(raw: str, repo_root: Path) -> Path:
    """Resolve one ``--assemble`` path to an absolute path under ``repo_root``."""
    raw_stripped = raw.strip()
    p_in = Path(raw_stripped).expanduser()
    if p_in.is_absolute():
        p = p_in.resolve()
    elif _assemble_is_basename_only(raw_stripped):
        name = p_in.name
        p = None
        for sub in _ASSEMBLE_INPUT_SEARCH_DIRS:
            cand = (repo_root / sub / name).resolve()
            if cand.is_file():
                p = cand
                break
        if p is None:
            p = (repo_root / name).resolve()
    else:
        p = (repo_root / p_in).resolve()

    try:
        p.relative_to(repo_root)
    except ValueError:
        print(_r(f"Error: path outside repository: {p}"))
        sys.exit(1)
    if not p.is_file():
        hint = ""
        if _assemble_is_basename_only(raw_stripped):
            hint = f" (tried {', '.join(_ASSEMBLE_INPUT_SEARCH_DIRS)} and repo root)"
        print(_r(f"Error: not a file: {p}{hint}"))
        sys.exit(1)
    if p.suffix.lower() != ".md":
        print(_r(f"Error: --assemble sources must be Markdown (.md): {p}"))
        sys.exit(1)
    return p


def _resolve_assemble_output(output: str, repo_root: Path) -> Path:
    """Resolve ``--assemble-output`` to an absolute path.

    * Absolute path → used as-is.
    * Contains a directory separator → relative to repo root.
    * Bare filename (or ``name`` without ``/``) → ``build/pdf/name`` (adds
      ``.pdf`` when there is no file extension).
    """
    o = output.strip()
    if not o:
        print(_r("Error: empty --assemble-output"))
        sys.exit(1)
    po = Path(o).expanduser()
    if po.is_absolute():
        return po.resolve()
    if "/" in o or "\\" in o:
        return (repo_root / po).resolve()
    fname = po.name
    if Path(fname).suffix == "":
        fname = fname + ".pdf"
    return (repo_root / "build" / "pdf" / fname).resolve()


def _assemble_resolve_paths(raw_paths: list[str], repo_root: Path) -> list[Path]:
    """Resolve Markdown paths; each must exist under ``repo_root``."""
    paths: list[Path] = []
    for raw in raw_paths:
        paths.append(_assemble_resolve_one(raw, repo_root))

    stems = [p.stem for p in paths]
    if len(set(stems)) != len(stems):
        print(_r(
            "Error: --assemble requires unique Markdown file stems (basename without .md) "
            "so mermaid manifest keys match; duplicate stems: "
            + ", ".join(sorted({s for s in stems if stems.count(s) > 1}))
        ))
        sys.exit(1)
    return paths


def _md_src_relative(md_path: Path, repo_root: Path) -> str:
    return str(md_path.resolve().relative_to(repo_root))


def _first_markdown_heading(text: str, level: int = 1) -> str | None:
    """Return the first ATX heading at ``level`` (1 = `#`, 2 = `##`, …)."""
    prefix = "#" * level + " "
    deeper = "#" * (level + 1) + " "
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith(prefix):
            continue
        if level < 6 and s.startswith(deeper):
            continue
        title = s[len(prefix) :].strip()
        return title if title else None
    return None


def _strip_atx_heading_trailer(title: str) -> str:
    """Strip trailing ``{#anchor}`` from ATX heading text."""
    return re.sub(r"\s*\{#[^}]+\}\s*$", "", title.strip()).strip()


# Level-2 headings that are navigational boilerplate, not part titles.
_SKIP_ASSEMBLE_PART_H2: frozenset[str] = frozenset({
    "table of contents",
    "toc",
})


def _infer_part_title(md_text: str, stem: str) -> str:
    """Title for a part-divider: first substantive ``##``, else ``#``, else stem.

    Skips common TOC headings (e.g. ``## Table of Contents``) so the divider
    matches a real section from the source file.
    """
    for line in md_text.splitlines():
        m = re.match(r"^##\s+(.+)$", line.strip())
        if not m:
            continue
        raw = _strip_atx_heading_trailer(m.group(1))
        if not raw:
            continue
        key = re.sub(r"\s+", " ", raw.lower())
        if key in _SKIP_ASSEMBLE_PART_H2:
            continue
        if key.startswith("table of contents"):
            continue
        return raw
    h1 = _first_markdown_heading(md_text, level=1)
    if h1:
        return h1
    return stem.replace("-", " ").replace("_", " ").title()


def _synthetic_doc_cfg(
    md_path: Path,
    repo_root: Path,
    *,
    title_override: str | None,
    subtitle_override: str | None,
    date_override: str | None,
) -> dict:
    text = md_path.read_text(encoding="utf-8")
    title = title_override if title_override is not None else (
        _first_markdown_heading(text, level=1)
        or md_path.stem.replace("-", " ").replace("_", " ").title()
    )
    subtitle = subtitle_override if subtitle_override is not None else ""
    date = date_override if date_override is not None else ""
    return {
        "src": _md_src_relative(md_path, repo_root),
        "title": title,
        "subtitle": subtitle,
        "date": date,
    }


def _assemble_book_parts(doc_ids: list[str], section_titles: list[str]) -> list[dict]:
    parts: list[dict] = []
    for i, doc_id in enumerate(doc_ids):
        parts.append({
            "type": "interstitial",
            "params": {
                "style": "part-divider",
                "label": f"Part {i + 1}",
                "title": section_titles[i],
                "contents": True,
                "depth": 2,
            },
        })
        parts.append({"type": "document", "doc": doc_id})
    return parts


# Max characters in the PDF basename (excluding ".pdf") for ad-hoc multi-file names.
_ASSEMBLE_MULTI_BASENAME_MAX = 64


def _assemble_short_hashed_pdf_name(paths: list[Path]) -> str:
    """Stable short name when stems joined would be unwieldy."""
    h = _sha256("|".join(str(p.resolve()) for p in paths))[:10]
    return f"assemble-{h}.pdf"


def _default_assemble_multi_pdf_name(paths: list[Path]) -> str:
    """Readable default ``*.pdf`` basename for multi-file ``--assemble``.

    * Two files, second stem extends first (``a`` + ``-`` + rest): ``a-and-rest.pdf``
      (e.g. ``agentic-framework`` + ``agentic-framework-reference`` →
      ``agentic-framework-and-reference.pdf``).
    * Two files, otherwise: ``stem1-stem2.pdf``.
    * Three or more: ``stem1-stem2-stem3…``.pdf joined with hyphens.
    * If the joined base exceeds :pydata:`_ASSEMBLE_MULTI_BASENAME_MAX`, fall back to
      :pyfunc:`_assemble_short_hashed_pdf_name`.
    """
    stems = [p.stem for p in paths]
    if len(stems) < 2:
        return f"{stems[0]}.pdf"

    if len(stems) == 2:
        a, b = stems[0], stems[1]
        if b.startswith(a + "-") and len(b) > len(a) + 1:
            rest = b[len(a) + 1 :].strip("-_")
            base = f"{a}-and-{rest}" if rest else f"{a}-{b}"
        elif a.startswith(b + "-") and len(a) > len(b) + 1:
            rest = a[len(b) + 1 :].strip("-_")
            base = f"{b}-and-{rest}" if rest else f"{a}-{b}"
        else:
            base = f"{a}-{b}"
    else:
        base = "-".join(stems)

    base = base.strip("-_")
    if len(base) < 2:
        return _assemble_short_hashed_pdf_name(paths)
    if len(base) > _ASSEMBLE_MULTI_BASENAME_MAX:
        return _assemble_short_hashed_pdf_name(paths)
    return f"{base}.pdf"


def build_assemble(
    raw_paths: list[str],
    repo_root: Path,
    cfg: dict,
    profile: dict,
    cli_brand: str | None,
    *,
    output: str | None,
    title: str | None,
    subtitle: str | None,
    date: str | None,
    cli_cover_style: str | None = None,
    cli_seed: int | None = None,
) -> bool:
    """
    Build one PDF from Markdown paths without ``build.yaml`` document entries.

    * One path → single-document flow (same pipeline as registry docs).
    * Two or more paths → book flow with one ``part-divider`` interstitial
      (``contents: true``) per file, matching the structure used for
      ``new-devx-plandek`` / ``agentic-hive-mind``. Default PDF name is a short
      readable ``stem1-and-…`` / ``stem1-stem2`` basename (see
      :pyfunc:`_default_assemble_multi_pdf_name`) unless stems exceed length limits.
    """
    paths = _assemble_resolve_paths(raw_paths, repo_root)
    doc_cfgs_registry = cfg.get("documents", {})

    if len(paths) == 1:
        p = paths[0]
        doc_id = p.stem
        doc_cfg = _synthetic_doc_cfg(
            p, repo_root,
            title_override=title,
            subtitle_override=subtitle,
            date_override=date,
        )
        out = _resolve_assemble_output(output, repo_root) if output else repo_root / "build" / "pdf" / f"{doc_id}.pdf"
        return build_document(
            doc_id,
            doc_cfg,
            profile,
            repo_root,
            cfg,
            cli_brand,
            output_pdf=out,
            brand_suffix_output=(output is None),
            cli_cover_style=cli_cover_style,
            cli_seed=cli_seed,
        )

    doc_ids: list[str] = []
    merged_cfgs: dict = dict(doc_cfgs_registry)
    section_titles: list[str] = []
    for p in paths:
        doc_id = p.stem
        doc_ids.append(doc_id)
        text = p.read_text(encoding="utf-8")
        section_titles.append(_infer_part_title(text, doc_id))
        merged_cfgs[doc_id] = _synthetic_doc_cfg(
            p, repo_root,
            title_override=None,
            subtitle_override=None,
            date_override=None,
        )

    first_text = paths[0].read_text(encoding="utf-8")
    book_title = title or (
        _first_markdown_heading(first_text, level=1)
        or "Assembled document"
    )
    book_subtitle = subtitle if subtitle is not None else " · ".join(doc_ids)
    book_date = date if date is not None else ""

    book_id = "assemble-" + _sha256("|".join(str(p.resolve()) for p in paths))[:12]
    out_path = (
        _resolve_assemble_output(output, repo_root)
        if output
        else repo_root / "build" / "pdf" / _default_assemble_multi_pdf_name(paths)
    )

    book_cfg: dict = {
        "title": book_title,
        "subtitle": book_subtitle,
        "date": book_date,
        "output": str(out_path.relative_to(repo_root)),
        "parts": _assemble_book_parts(doc_ids, section_titles),
    }

    return build_book(
        book_id,
        book_cfg,
        merged_cfgs,
        profile,
        repo_root,
        cfg,
        cli_brand,
        brand_suffix_output=(output is None),
        cli_cover_style=cli_cover_style,
        cli_seed=cli_seed,
    )


# ── Fast Cover-Only Builder ───────────────────────────────────────────────────

def build_cover_only(
    repo_root: Path,
    cfg: dict,
    doc_cfgs: dict,
    book_cfgs: dict,
    cli_brand: str | None,
    cli_cover_style: str | None,
    cli_seed: int | None,
    cli_seeds: list[int] | None,
    docs: list[str] | None,
    books: list[str] | None,
) -> int:
    """Fast standalone cover generation (1-page PDF only) for testing branding, styles, and seeds."""
    pdf_dir = repo_root / "build" / "pdf"
    covers_dir = repo_root / "build" / "covers"
    typst_dir = repo_root / "build" / "typst"
    fonts_dir = repo_root / "docs" / "assets" / "fonts"

    pdf_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)
    typst_dir.mkdir(parents=True, exist_ok=True)

    targets: list[dict] = []

    if docs:
        for d in docs:
            if d not in doc_cfgs:
                print(_r(f"Error: document '{d}' not found in build.yaml"))
                return 1
            entry = dict(doc_cfgs[d])
            entry["_id"] = d
            targets.append(entry)
    if books:
        for b in books:
            if b not in book_cfgs:
                print(_r(f"Error: book '{b}' not found in build.yaml"))
                return 1
            entry = dict(book_cfgs[b])
            entry["_id"] = b
            targets.append(entry)

    # Brand-centric fallback when no doc or book is specified
    if not targets:
        brand_module, brand_id = resolve_brand(cfg, {}, cli_brand, repo_root)
        brand_defaults = {
            "mindrocket": {
                "title": "Mind Rocket\nServices",
                "subtitle": "Architecture · Engineering · Delivery",
                "date": "2026",
            },
            "plandek": {
                "title": "Plandek\nIntelligence",
                "subtitle": "Software Delivery Metrics & Analytics",
                "date": "2026",
            },
            "neutral": {
                "title": "Publication\nSeries",
                "subtitle": "Technical Architecture & Design",
                "date": "2026",
            },
        }
        b_info = brand_defaults.get(brand_id, {
            "title": f"{brand_id.title()}\nPublication",
            "subtitle": "Technical Architecture & Design",
            "date": "2026",
        })
        targets.append({
            "_id": None,
            "title": b_info["title"],
            "subtitle": b_info["subtitle"],
            "date": b_info["date"],
            "brand": brand_id,
        })

    failed: list[str] = []

    print(f"\n{_b('Building cover PDF(s)...')}")

    for target in targets:
        brand_module, brand_id = resolve_brand(cfg, target, cli_brand, repo_root)
        target_id = target.get("_id")
        title = target.get("title", f"{brand_id.title()} Cover")
        subtitle = target.get("subtitle", "")

        date_val = str(target.get("date", "") or "").strip()
        edition_val = str(target.get("edition", "") or "").strip()
        if edition_val and date_val:
            date_line = f"{edition_val} · {date_val}"
        elif edition_val:
            date_line = edition_val
        else:
            date_line = date_val

        cover_style = (
            cli_cover_style
            or target.get("cover-style")
            or target.get("cover_style")
            or "split-mesh"
        ).strip()

        if cli_seeds is not None and len(cli_seeds) > 0:
            seeds = cli_seeds
        elif cli_seed is not None:
            seeds = [cli_seed]
        else:
            raw_seed = target.get("seed", target.get("cover-seed", 0))
            try:
                seeds = [int(raw_seed)]
            except (ValueError, TypeError):
                seeds = [0]

        is_multi_seed = len(seeds) > 1

        for seed in seeds:
            stem = f"{target_id}-{brand_id}" if target_id else f"{brand_id}"
            wrapper = typst_dir / f"cover-{stem}-s{seed}.typ"
            wrapper_content = "\n".join([
                "// Auto-generated cover preview — do not edit manually.",
                f'#import "{brand_module}": plandek-doc',
                "#show: plandek-doc.with(",
                f"  title: {_typ_str(title)},",
                f"  subtitle: {_typ_str(subtitle)},",
                f"  date: {_typ_str(date_line)},",
                f"  cover-style: {_typ_str(cover_style)},",
                f"  cover-seed: {seed},",
                ")",
                "[]",
                "",
            ])
            wrapper.write_text(wrapper_content, encoding="utf-8")

            if is_multi_seed:
                out_pdf = covers_dir / f"cover-{stem}-s{seed}.pdf"
            else:
                out_pdf = covers_dir / f"cover-{stem}.pdf"

            # Compile single-page PDF only
            cmd_pdf = [
                "typst", "compile", str(wrapper), str(out_pdf),
                "--root", str(repo_root),
                "--font-path", str(fonts_dir),
                "--pages", "1",
            ]
            res_pdf = subprocess.run(cmd_pdf, capture_output=True, text=True)
            if res_pdf.returncode != 0:
                print(_r(f"  ✗ Failed to compile cover PDF for {stem} (seed {seed})"))
                for line in (res_pdf.stdout + res_pdf.stderr).splitlines():
                    if line.strip():
                        print(f"    {line}")
                failed.append(f"{stem}:seed{seed}")
                continue

            rel_pdf = out_pdf.relative_to(repo_root)
            print(f"  ✓ Cover [{_b(brand_id)}]: style={cover_style} seed={seed}")
            print(f"    PDF: {rel_pdf}")

    if failed:
        print(_r(f"\n✗ Failed covers: {', '.join(failed)}"))
        return 1

    print(_g("\n✓ Cover build complete"))
    return 0


def _find_repo_root() -> Path:
    """Find repository root containing build.yaml or git root."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            git_root = Path(res.stdout.strip()).resolve()
            if (git_root / "build.yaml").exists() or (git_root / "typst").exists():
                return git_root
    except Exception:
        pass

    cwd = Path.cwd().resolve()
    if (cwd / "build.yaml").exists():
        return cwd

    for parent in Path(__file__).resolve().parents:
        if (parent / "build.yaml").exists():
            return parent

    return Path(__file__).resolve().parent.parent.parent


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    repo_root   = _find_repo_root()
    config_path = repo_root / "build.yaml"

    if not config_path.exists():
        print(_r(f"Error: {config_path} not found"))
        return 1

    cfg = load_config(config_path)

    parser = argparse.ArgumentParser(
        description="Build Plandek PDFs from Markdown sources"
    )
    parser.add_argument(
        "--profile", default="production",
        help="Build profile (default: production)"
    )
    parser.add_argument(
        "--docs", nargs="*", metavar="DOC",
        help="Build specific documents only (default: all from config)"
    )
    parser.add_argument(
        "--books", nargs="*", metavar="BOOK",
        help="Build specific books only (default: all from config)"
    )
    parser.add_argument(
        "--no-docs", action="store_true",
        help="Skip single-document builds (useful with --books)"
    )
    parser.add_argument(
        "--no-books", action="store_true",
        help="Skip book assembly"
    )
    parser.add_argument(
        "--config", type=Path, default=config_path,
        help=f"Path to build.yaml (default: {config_path})"
    )
    parser.add_argument(
        "--brand",
        default=None,
        metavar="ID",
        help=(
            "PDF brand id (see build.yaml `brands:`). "
            "Make passes this from $BRAND. Precedence: per-doc/book `brand:` "
            "in YAML overrides this flag."
        ),
    )
    parser.add_argument(
        "--cover-style",
        default=None,
        metavar="STYLE",
        help="Override cover style (e.g. split-mesh, minimal, full-bleed).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="INT",
        help="Override procedural cover seed (integer) for brand visual variations.",
    )
    parser.add_argument(
        "--cover-only",
        action="store_true",
        help="Fast cover-only build: compiles only the cover page (PDF + PNG preview) to test layouts and seeds.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=None,
        metavar="INT",
        help="List of seeds to build covers for when testing variations (e.g. --seeds 0 42 77 99).",
    )
    parser.add_argument(
        "--assemble",
        nargs="+",
        metavar="PATH",
        dest="assemble_paths",
        help=(
            "Build from Markdown paths only: one file → single PDF; two or more → "
            "one book PDF with a part-divider + mini-contents before each file "
            "(no build.yaml document/book entries required). "
            "Paths are relative to the repo root; a bare filename.md is searched "
            f"under {', '.join(_ASSEMBLE_INPUT_SEARCH_DIRS)} (in order). "
            "Each file stem must be unique (mermaid manifest uses basename)."
        ),
    )
    parser.add_argument(
        "--assemble-output",
        default=None,
        metavar="REL_PATH",
        help=(
            "Write the assembled PDF here. Relative paths are under the repo root; "
            "a bare name (no /) goes to build/pdf/ and adds .pdf if missing. "
            "Default: build/pdf/{stem}-{brand}.pdf for one file; for books, a readable "
            "multi-stem name (also suffixed with -{brand}) or assemble-{hash}.pdf if stems "
            "joined would be too long. Omitting this flag keeps automatic brand suffixes; "
            "when you set this path, the filename is not altered."
        ),
    )
    parser.add_argument(
        "--assemble-title",
        default=None,
        metavar="TEXT",
        help="Override cover title: for a single file, the document title; for a book, the book title.",
    )
    parser.add_argument(
        "--assemble-subtitle",
        default=None,
        metavar="TEXT",
        help="Override cover subtitle (single file or book).",
    )
    parser.add_argument(
        "--assemble-date",
        default=None,
        metavar="TEXT",
        help="Override cover date line (single file or book).",
    )
    args = parser.parse_args()

    if args.config != config_path:
        cfg = load_config(args.config)

    profile   = resolve_profile(cfg, args.profile)
    doc_cfgs  = cfg.get("documents", {})
    book_cfgs = cfg.get("books", {})

    if args.cover_only:
        cli_brand = (args.brand or "").strip() or None
        docs = args.docs if args.docs else None
        books = args.books if args.books else None
        return build_cover_only(
            repo_root=repo_root,
            cfg=cfg,
            doc_cfgs=doc_cfgs,
            book_cfgs=book_cfgs,
            cli_brand=cli_brand,
            cli_cover_style=args.cover_style,
            cli_seed=args.seed,
            cli_seeds=args.seeds,
            docs=docs,
            books=books,
        )

    if args.assemble_paths:
        if args.docs is not None:
            print(_r("Error: do not combine --assemble with --docs"))
            return 1
        if args.books is not None:
            print(_r("Error: do not combine --assemble with --books"))
            return 1

    docs_to_build  = args.docs  if args.docs  is not None else list(doc_cfgs)
    books_to_build = args.books if args.books is not None else list(book_cfgs)

    if args.no_docs:  docs_to_build  = []
    if args.no_books: books_to_build = []

    if args.assemble_paths:
        docs_to_build = []
        books_to_build = []

    for doc_id in docs_to_build:
        if doc_id not in doc_cfgs:
            print(_r(f"Error: document '{doc_id}' not in build.yaml"))
            return 1
    for book_id in books_to_build:
        if book_id not in book_cfgs:
            print(_r(f"Error: book '{book_id}' not in build.yaml"))
            return 1

    cli_brand = (args.brand or "").strip() or None

    print(f"Profile: {_b(args.profile)}")
    print(f"Brand:   {_b(cli_brand or '(from YAML default / per-item pins)')}")
    if args.cover_style:
        print(f"Cover:   {_b(args.cover_style)}")
    if args.seed is not None:
        print(f"Seed:    {_b(str(args.seed))}")
    if args.assemble_paths:
        print(f"Assemble: {len(args.assemble_paths)} Markdown file(s)")
        for p in args.assemble_paths:
            print(f"  - {p}")
    else:
        print(f"Docs:    {', '.join(docs_to_build) or '(none)'}")
        print(f"Books:   {', '.join(books_to_build) or '(none)'}")

    if docs_to_build or books_to_build or args.assemble_paths:
        optimise_images(profile, repo_root)

    failed: list[str] = []

    if args.assemble_paths:
        ok = build_assemble(
            args.assemble_paths,
            repo_root,
            cfg,
            profile,
            cli_brand,
            output=args.assemble_output,
            title=args.assemble_title,
            subtitle=args.assemble_subtitle,
            date=args.assemble_date,
            cli_cover_style=args.cover_style,
            cli_seed=args.seed,
        )
        if not ok:
            failed.append("assemble")

    for doc_id in docs_to_build:
        ok = build_document(
            doc_id,
            doc_cfgs[doc_id],
            profile,
            repo_root,
            cfg,
            cli_brand,
            cli_cover_style=args.cover_style,
            cli_seed=args.seed,
        )
        if not ok:
            failed.append(doc_id)

    for book_id in books_to_build:
        ok = build_book(
            book_id,
            book_cfgs[book_id],
            doc_cfgs,
            profile,
            repo_root,
            cfg,
            cli_brand,
            cli_cover_style=args.cover_style,
            cli_seed=args.seed,
        )
        if not ok:
            failed.append(f"book:{book_id}")

    print(f"\n{'─'*45}")
    pdf_dir = repo_root / "build" / "pdf"
    pdfs = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    if pdfs:
        for pdf in pdfs:
            mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  {pdf.name:<35} {mb:>5.1f} MB")

    if failed:
        print(_r(f"\n✗ Failed: {', '.join(failed)}"))
        return 1

    print(_g("\n✓ Build complete"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
