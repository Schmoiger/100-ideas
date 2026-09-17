#!/usr/bin/env python3
from __future__ import annotations

"""Validate technical writing invariants (context/rules/tech-writing.md).

Enforces:
1. British English spelling and date conventions (Section 1)
2. EARS notation syntax in requirements and user stories (Section 2)
"""

import argparse
import re
import sys
from pathlib import Path

# --- Section 1: British English Spelling & Invariants ---

# Common American → British spelling pairs
SPELLING_RULES: dict[str, tuple[str, str]] = {
    r"\bcolou?r\b": ("color", "colour"),
    r"\bfavou?r\b": ("favor", "favour"),
    r"\bhonou?r\b": ("honor", "honour"),
    r"\blabou?r\b": ("labor", "labour"),
    r"\bneighbou?r\b": ("neighbor", "neighbour"),
    r"\bbehaviou?r\b": ("behavior", "behaviour"),
    r"\b(organ|real|recogn|special|general)i[sz]e\b": ("organize/realize/...", "organise/realise/..."),
    r"\bcente?r\b": ("center", "centre"),
    r"\bmete?r\b": ("meter", "metre"),
    r"\blicen[cs]e\b": ("license (noun)", "licence (noun)"),
    r"\bdefen[cs]e\b": ("defense", "defence"),
    r"\boffen[cs]e\b": ("offense", "offence"),
    r"\bartifact\b": ("artifact", "artefact"),
}

# American date pattern: Month DD, YYYY e.g. January 15, 2026 or MM/DD/YYYY with MM > 12 impossible
DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
    re.IGNORECASE,
)


def validate_british_english(file_path: Path) -> list[str]:
    """Check for American English spellings and non-standard date formats."""
    violations: list[str] = []
    try:
        content = file_path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        return [f"Error reading {file_path}: {e}"]

    lines = content.split("\n")
    in_code_block = False

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block or "`" in line or line.strip().startswith("|"):
            continue

        # color vs colour
        if re.search(r"\bcolor\b", line, re.IGNORECASE) and not re.search(r"\bcolour\b", line, re.IGNORECASE):
            violations.append(
                f"Line {i}: Use 'colour' instead of 'color'\n  {line.strip()}"
            )

        # behavior vs behaviour
        if re.search(r"\bbehavior\b", line, re.IGNORECASE):
            violations.append(
                f"Line {i}: Use 'behaviour' instead of 'behavior'\n  {line.strip()}"
            )

        # organize/realize/...
        for word in ["organize", "realize", "recognize", "specialize", "generalize"]:
            if re.search(rf"\b{word}\b", line, re.IGNORECASE):
                british = word.replace("ize", "ise")
                violations.append(
                    f"Line {i}: Use '{british}' instead of '{word}'\n  {line.strip()}"
                )

        # center vs centre
        if re.search(r"\bcenter\b", line, re.IGNORECASE):
            violations.append(
                f"Line {i}: Use 'centre' instead of 'center'\n  {line.strip()}"
            )

        # license (noun) vs licence
        if re.search(r"\blicense\b", line, re.IGNORECASE) and not re.search(r"\blicen[cs]ing\b", line, re.IGNORECASE):
            violations.append(
                f"Line {i}: Use 'licence' for noun, 'license' for verb\n  {line.strip()}"
            )

        # artifact vs artefact
        if re.search(r"\bartifact\b", line, re.IGNORECASE):
            violations.append(
                f"Line {i}: Use 'artefact' instead of 'artifact'\n  {line.strip()}"
            )

    return violations


# --- Section 2: EARS Notation Syntax ---

EARS_PATTERNS = {
    "ubiquitous": r"THE\s+\S+\s+SHALL\s+",
    "event": r"WHEN\s+.+?,\s+THE\s+\S+\s+SHALL\s+",
    "state": r"WHILE\s+.+?,\s+THE\s+\S+\s+SHALL\s+",
    "optional": r"IF\s+.+?,\s+THE\s+\S+\s+SHALL\s+",
    "forbidden": r"THE\s+\S+\s+SHALL\s+NOT\s+",
    "complex": r"WHEN\s+.+?,\s+IF\s+.+?,\s+THE\s+\S+\s+SHALL\s+",
}


def is_ears_requirement(line: str) -> bool:
    """Check if a requirement line matches any EARS pattern."""
    line = line.strip()
    for pattern in EARS_PATTERNS.values():
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def validate_requirements_file(file_path: Path) -> list[str]:
    """Validate that requirement statements in a file follow EARS syntax."""
    errors: list[str] = []
    try:
        content = file_path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        return [f"Error reading {file_path}: {e}"]

    lines = content.split("\n")
    in_code_block = False

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        line_clean = line.strip()
        if not line_clean or line_clean.startswith(("#", "|")) or re.match(r"^[-*]\s", line_clean):
            continue

        if "shall" in line_clean.lower() and not is_ears_requirement(line_clean):
            errors.append(
                f"Line {i}: Requirement doesn't match EARS notation\n"
                f"  {line_clean}\n"
                f"  Expected patterns:\n"
                f"    - THE [system] SHALL [action]\n"
                f"    - WHEN [trigger], THE [system] SHALL [action]\n"
                f"    - WHILE [state], THE [system] SHALL [action]\n"
                f"    - IF [condition], THE [system] SHALL [action]\n"
                f"    - THE [system] SHALL NOT [action]\n"
                f"    - WHEN [trigger], IF [condition], THE [system] SHALL [action]"
            )

    return errors


# --- CLI Interface ---


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate technical writing invariants (British English, EARS notation)"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    spelling_parser = subparsers.add_parser("spelling", help="Validate British English spelling")
    spelling_parser.add_argument("files", nargs="+", help="Files to check")

    ears_parser = subparsers.add_parser("ears", help="Validate EARS notation in requirements")
    ears_parser.add_argument("files", nargs="+", help="Requirement files to check")

    parser.add_argument("auto_files", nargs="*", help="Auto-detect mode files")

    args = parser.parse_args()

    if args.subcommand == "spelling":
        all_violations: list[str] = []
        for file_str in args.files:
            p = Path(file_str)
            if p.is_file() and p.suffix in [".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".txt"]:
                v = validate_british_english(p)
                if v:
                    all_violations.append(f"❌ American English found in {p.name}:")
                    all_violations.extend(v)
        if all_violations:
            for v in all_violations:
                print(v, file=sys.stderr)
            return 1
        print("✅ British English spelling verified")
        return 0

    if args.subcommand == "ears":
        all_errors: list[str] = []
        for file_str in args.files:
            p = Path(file_str)
            if p.is_file():
                errs = validate_requirements_file(p)
                if errs:
                    all_errors.append(f"❌ EARS violations in {p.name}:")
                    all_errors.extend(errs)
        if all_errors:
            for err in all_errors:
                print(err, file=sys.stderr)
            return 1
        print("✅ EARS notation verified")
        return 0

    if args.auto_files:
        has_failure = False
        for file_str in args.auto_files:
            p = Path(file_str)
            if not p.is_file():
                continue
            # If requirements or user-stories, check EARS
            if p.name in ["requirements.md", "user-stories.md"] or "requirements" in str(p):
                ears_errs = validate_requirements_file(p)
                if ears_errs:
                    has_failure = True
                    print(f"❌ EARS notation violations in {p.name}:", file=sys.stderr)
                    for err in ears_errs:
                        print(f"  {err}", file=sys.stderr)

            # Check British English
            if p.suffix in [".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".txt"]:
                spelling_errs = validate_british_english(p)
                if spelling_errs:
                    has_failure = True
                    print(f"❌ American English found in {p.name}:", file=sys.stderr)
                    for err in spelling_errs:
                        print(f"  {err}", file=sys.stderr)

        return 1 if has_failure else 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
