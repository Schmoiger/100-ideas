#!/usr/bin/env python3
"""
Optimise source images for PDF embedding (OPT-001).

For each PNG in --src:
  1. Resize to max --max-px pixels on the longest axis (LANCZOS).
  2. Quantise palette to 256 colours with Floyd-Steinberg dithering.

Other formats (JPG, JPEG) are copied unchanged — they are already small
or not palette-friendly.

Incremental: skips a file when the destination already exists and is
newer than the source (mtime comparison).

Output files are written to --dest with the same filename as the source.

Exit codes
----------
0  All files processed (or skipped) successfully.
1  One or more files failed; error details printed to stderr.
"""

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image

# Number of palette colours for quantisation.
# 256 is the maximum for palette-mode PNG and matches pngquant's default.
_QUANT_COLOURS = 256


def optimise_png(src: Path, dest: Path, max_px: int) -> None:
    """
    Resize and quantise a PNG.

    Args:
        src:    Source PNG path.
        dest:   Destination path (written as palette PNG).
        max_px: Maximum pixel dimension (width or height); aspect ratio preserved.
    """
    img = Image.open(src)
    w, h = img.size

    # Resize only if the image exceeds max_px on its longest side.
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # Convert to RGBA before quantising so transparency is preserved.
    img = img.convert("RGBA")
    img = img.quantize(colors=_QUANT_COLOURS, dither=Image.Dither.FLOYDSTEINBERG)

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG", compress_level=9)


def process(src_dir: Path, dest_dir: Path, max_px: int) -> int:
    """
    Process all images in src_dir into dest_dir.

    Returns the number of failed files (0 = success).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    count = skipped = failed = 0

    for src in sorted(src_dir.iterdir()):
        if src.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue

        dest = dest_dir / src.name

        # Incremental: skip if dest is newer than src.
        if dest.exists() and dest.stat().st_mtime > src.stat().st_mtime:
            skipped += 1
            continue

        try:
            if src.suffix.lower() == ".png":
                optimise_png(src, dest, max_px)
            else:
                # Non-PNG: copy as-is (already small or not palette-friendly).
                shutil.copy2(src, dest)

            count += 1

        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ {src.name}: {exc}", file=sys.stderr)
            failed += 1

    print(
        f"  Optimised images: {count} processed, {skipped} unchanged"
        f" (max {max_px}px, {_QUANT_COLOURS}-colour palette)"
    )

    return failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Optimise images for PDF embedding via resize + palette quantisation"
    )
    parser.add_argument("--src", type=Path, required=True,
                        help="Source directory containing images")
    parser.add_argument("--dest", type=Path, required=True,
                        help="Output directory for optimised images")
    parser.add_argument("--max-px", type=int, default=1024,
                        help="Maximum pixel dimension (default: 1024)")
    args = parser.parse_args()

    if not args.src.is_dir():
        print(f"Error: source directory not found: {args.src}", file=sys.stderr)
        return 1

    failed = process(args.src, args.dest, args.max_px)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
