"""Data models for Content Enrichment Subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ResearchNotes:
    """Structured empirical research and citation dossier."""

    idea_id: str
    title: str
    synopsis: str
    empirical_evidence: list[str] = field(default_factory=list)
    economic_tradeoffs: list[str] = field(default_factory=list)
    counterarguments: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self) -> None:
        """Initialise timestamp if not set."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_markdown(self) -> str:
        """Render research dossier as standard Markdown for notes.md."""
        lines: list[str] = [
            f"# Research Dossier: {self.title}",
            "",
            f"**Idea ID**: `{self.idea_id}`",
            f"**Generated**: `{self.generated_at}`",
            "",
            "---",
            "",
            "## Core Thesis & Synopsis",
            "",
            self.synopsis,
            "",
            "---",
            "",
            "## Empirical Evidence & Real-World Observations",
            "",
        ]
        if self.empirical_evidence:
            for item in self.empirical_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- *No empirical evidence recorded.*")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Economic Trade-offs & Constraint Dynamics",
                "",
            ]
        )
        if self.economic_tradeoffs:
            for item in self.economic_tradeoffs:
                lines.append(f"- {item}")
        else:
            lines.append("- *No economic trade-offs recorded.*")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Counterarguments, Tensions & Anti-Patterns",
                "",
            ]
        )
        if self.counterarguments:
            for item in self.counterarguments:
                lines.append(f"- {item}")
        else:
            lines.append("- *No counterarguments recorded.*")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Citations & Verified Resource Links",
                "",
            ]
        )
        if self.citations:
            for item in self.citations:
                lines.append(f"- {item}")
        else:
            lines.append("- *No formal citations recorded.*")

        lines.append("")
        return "\n".join(lines)


@dataclass
class VisualPrompt:
    """Conceptual visual generation prompt and stylistic directions."""

    idea_id: str
    concept_metaphor: str
    subject: str
    composition: str
    mood_lighting: str
    style_direction: str
    negative_prompt: str
    full_prompt: str
    generated_at: str = ""

    def __post_init__(self) -> None:
        """Initialise timestamp if not set."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_text_payload(self) -> str:
        """Render prompt details for prompt.txt."""
        return (
            f"# Visual Generation Prompt for {self.idea_id}\n\n"
            f"**Metaphor**: {self.concept_metaphor}\n"
            f"**Subject**: {self.subject}\n"
            f"**Composition**: {self.composition}\n"
            f"**Mood & Lighting**: {self.mood_lighting}\n"
            f"**Style**: {self.style_direction}\n"
            f"**Negative Prompt**: {self.negative_prompt}\n\n"
            f"## Final Prompt Payload\n\n{self.full_prompt}\n"
        )
