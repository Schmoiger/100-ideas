"""Data models for Book Mode and Typst Typesetting Subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ChapterDraft:
    """Substantive book chapter manuscript."""

    idea_id: str
    chapter_num: int
    title: str
    subtitle: str
    lead_punch: str
    mechanics_section: str
    economic_section: str
    hype_section: str
    takeaways: list[str]
    citations: list[str] = field(default_factory=list)
    illustration_path: str = ""
    generated_at: str = ""

    def __post_init__(self) -> None:
        """Initialise timestamp if not set."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_markdown(self) -> str:
        """Render chapter as semantic Markdown adhering to author persona."""
        lines: list[str] = [
            f"# Chapter {self.chapter_num}: {self.title}",
            "",
            f"*{self.subtitle}*",
            "",
        ]

        if self.illustration_path:
            lines.extend(
                [
                    f"![Editorial illustration: {self.title}]({self.illustration_path})",
                    "",
                ]
            )

        lines.extend(
            [
                "---",
                "",
                "## The Unvarnished Reality",
                "",
                self.lead_punch,
                "",
                "---",
                "",
                "## Where the Gears Bind",
                "",
                self.mechanics_section,
                "",
                "---",
                "",
                "## The Economic Equation & Trade-offs",
                "",
                self.economic_section,
                "",
                "---",
                "",
                "## Puncturing the Hype",
                "",
                self.hype_section,
                "",
                "---",
                "",
                "## Actionable Takeaways",
                "",
            ]
        )

        for item in self.takeaways:
            lines.append(f"- {item}")

        if self.citations:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Grounded Citations & Field References",
                    "",
                ]
            )
            for item in self.citations:
                lines.append(f"- {item}")

        lines.append("")
        return "\n".join(lines)


@dataclass
class CompilationResult:
    """Result of Typst document compilation."""

    target_type: str  # "chapter" or "book"
    idea_id: str | None
    typst_source: Path
    pdf_output: Path
    success: bool
    page_count: int = 0
    error_message: str | None = None
