"""Editorial Quality Gate and Voice Fidelity Validator against author persona."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.provisioner import update_idea_meta

# Prohibited AI clichés per context/persona/author.md §Linguistic Standards & §Core Writing Principles
PROHIBITED_AI_SLOP: tuple[str, ...] = (
    "delve",
    "testament to",
    "crucial",
    "tapestry",
    "beacon",
    "revolutionise",
    "revolutionize",
    "seamless",
    "groundbreaking",
    "pivotal",
    "furthermore",
    "it is worth noting that",
    "in today's fast-paced",
    "at the end of the day",
)

# Common Americanisms to enforce strict British English
AMERICANISM_REPLACEMENTS: dict[str, str] = {
    "optimize": "optimise",
    "optimized": "optimised",
    "optimizing": "optimising",
    "optimization": "optimisation",
    "categorize": "categorise",
    "categorized": "categorised",
    "categorizing": "categorising",
    "prioritize": "prioritise",
    "prioritized": "prioritised",
    "prioritizing": "prioritising",
    "prioritization": "prioritisation",
    "realize": "realise",
    "realized": "realised",
    "realizing": "realising",
    "organization": "organisation",
    "organizations": "organisations",
    "organizational": "organisational",
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "behavioral": "behavioural",
    "color": "colour",
    "colors": "colours",
    "defense": "defence",
    "center": "centre",
    "centers": "centres",
    "centered": "centred",
    "labor": "labour",
    "favor": "favour",
    "honor": "honour",
}

# Economic lens indicators
ECONOMIC_MARKERS: tuple[str, ...] = (
    "cost",
    "economic",
    "trade-off",
    "tradeoff",
    "maintenance tail",
    "cognitive load",
    "delivery velocity",
    "blast radius",
    "pager",
    "2 a.m.",
    "value for money",
    "budget",
)


@dataclass
class EditorialQualityReport:
    """Detailed evaluation outcomes from voice fidelity quality gate."""

    passed: bool
    voice_fidelity: bool
    score: float
    issues: list[str] = field(default_factory=list)
    metrics: dict[str, bool] = field(default_factory=dict)
    reviewed_at: str = ""

    def __post_init__(self) -> None:
        if not self.reviewed_at:
            self.reviewed_at = datetime.now(timezone.utc).isoformat()


def check_british_english(text: str) -> list[str]:
    """Check for American spellings and report British English corrections."""
    issues: list[str] = []
    # Search word boundaries (case-insensitive)
    for us_word, uk_word in AMERICANISM_REPLACEMENTS.items():
        pattern = rf"\b{us_word}\b"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            issues.append(f"Use British English spelling: replace '{matches[0]}' with '{uk_word}'.")
    return issues


def check_prohibited_ai_slop(text: str) -> list[str]:
    """Check for forbidden AI marketing slop and conversational crutches."""
    issues: list[str] = []
    text_lower = text.lower()
    for phrase in PROHIBITED_AI_SLOP:
        if phrase in text_lower:
            issues.append(f"Prohibited AI cliché detected: remove or rephrase '{phrase}'.")
    return issues


def check_bold_lead_ins(text: str) -> list[str]:
    """Verify that bullet lists enforce scannable bold lead-ins."""
    issues: list[str] = []
    lines = text.splitlines()
    in_takeaways = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("## ") and "takeaway" in stripped.lower():
            in_takeaways = True
            continue
        elif stripped.startswith("## ") or stripped == "---":
            in_takeaways = False

        if in_takeaways and stripped.startswith("- "):
            item = stripped[2:].strip()
            # Must start with **something**: or **something**
            if not (item.startswith("**") and "**" in item[2:]):
                issues.append(
                    f"Line {idx}: Takeaway bullet lacks bold initial lead-in phrase: '{item[:40]}...'"
                )
    return issues


def check_economic_realism(text: str) -> list[str]:
    """Interrogate economic lens, trade-offs, and maintenance reality."""
    issues: list[str] = []
    text_lower = text.lower()
    matches = [marker for marker in ECONOMIC_MARKERS if marker in text_lower]
    if len(matches) < 2:
        issues.append(
            "Economic lens missing: Author persona requires evaluating utility, cost, trade-offs, or the 2 a.m. maintenance tail."
        )
    return issues


def check_punch_opening(text: str) -> list[str]:
    """Ensure opening punches immediately without throat-clearing preambles."""
    issues: list[str] = []
    lines = [
        line_item.strip()
        for line_item in text.splitlines()
        if line_item.strip() and not line_item.strip().startswith(("#", "*", "!", "-", "|", ">"))
    ]
    if lines:
        first_paragraph = lines[0].lower()
        preamble_markers = (
            "in this chapter",
            "in this post",
            "we will explore",
            "let's delve",
            "today we will",
            "welcome to",
        )
        for marker in preamble_markers:
            if marker in first_paragraph:
                issues.append(
                    f"Opening lacks punch: Avoid throat-clearing preamble ('{marker}'). Open with sharp assertion or physical metaphor."
                )
    return issues


def validate_voice_fidelity(content: str) -> EditorialQualityReport:
    """Perform end-to-end voice fidelity audit against context/persona/author.md."""
    be_issues = check_british_english(content)
    slop_issues = check_prohibited_ai_slop(content)
    lead_issues = check_bold_lead_ins(content)
    econ_issues = check_economic_realism(content)
    punch_issues = check_punch_opening(content)

    all_issues = be_issues + slop_issues + lead_issues + econ_issues + punch_issues

    metrics = {
        "british_english": len(be_issues) == 0,
        "zero_ai_slop": len(slop_issues) == 0,
        "bold_lead_ins": len(lead_issues) == 0,
        "economic_realism": len(econ_issues) == 0,
        "punch_opening": len(punch_issues) == 0,
    }

    # Calculate overall fidelity score
    total_checks = len(metrics)
    passed_checks = sum(1 for v in metrics.values() if v)
    score = round(passed_checks / total_checks, 2)
    voice_fidelity = len(all_issues) == 0
    passed = voice_fidelity

    return EditorialQualityReport(
        passed=passed,
        voice_fidelity=voice_fidelity,
        score=score,
        issues=all_issues,
        metrics=metrics,
    )


def evaluate_idea_quality_gate(
    idea_dir: Path,
    reviewer: str = "editorial-gate",
) -> EditorialQualityReport:
    """Evaluate chapter manuscript in idea_dir, updating meta.yaml with gate results.

    If passed, moves idea stage from 'draft_in_progress' or 'human_review' to 'approved'.
    """
    chapter_path = idea_dir / "book" / "chapter.md"
    if not chapter_path.is_file():
        # Fall back to blog post if book chapter absent
        chapter_path = idea_dir / "blog" / "post.md"

    if not chapter_path.is_file():
        raise FileNotFoundError(
            f"No manuscript found to review in {idea_dir} (expected book/chapter.md or blog/post.md)."
        )

    content = chapter_path.read_text(encoding="utf-8")
    report = validate_voice_fidelity(content)

    meta_file = idea_dir / "meta.yaml"
    current_meta: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            current_meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:
            current_meta = {}

    now_iso = datetime.now(timezone.utc).isoformat()
    review_notes = (
        "Editorial quality gate passed: strict British English, bold lead-ins, economic realism verified."
        if report.passed
        else "; ".join(report.issues)
    )

    updates: dict[str, Any] = {
        "editorial_quality": {
            "voice_fidelity": report.voice_fidelity,
            "reviewed_by": reviewer,
            "reviewed_at": now_iso,
            "review_notes": review_notes,
            "score": report.score,
        },
        "review_status": "approved" if report.passed else "needs_revision",
        "updated_at": now_iso,
    }

    # Only promote stage to 'approved' if quality gate passed
    current_stage = current_meta.get("stage", "raw")
    if report.passed:
        if current_stage in ("draft_in_progress", "human_review", "raw", "research_ready"):
            updates["stage"] = "approved"

    update_idea_meta(idea_dir, updates)
    return report
