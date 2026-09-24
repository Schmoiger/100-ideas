"""Data models for Blog & Social Publishing Subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlogFrontmatter:
    """Standardised YAML frontmatter for Hostinger and modern CMSs."""

    title: str
    slug: str
    date: str
    excerpt: str
    tags: list[str] = field(default_factory=list)
    cover_image: str = "../assets/illustration.png"
    author: str = "Dr Sarah Chen"
    reading_time_minutes: int = 3
    draft: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert frontmatter to dictionary for YAML serialisation."""
        return {
            "title": self.title,
            "slug": self.slug,
            "date": self.date,
            "excerpt": self.excerpt,
            "tags": self.tags,
            "cover_image": self.cover_image,
            "author": self.author,
            "reading_time_minutes": self.reading_time_minutes,
            "draft": self.draft,
        }


@dataclass
class BlogPost:
    """Full blog post entity comprising frontmatter and markdown body."""

    frontmatter: BlogFrontmatter
    body_markdown: str
    idea_id: str
    word_count: int = 0

    def render(self) -> str:
        """Render complete document with YAML frontmatter delimiters."""
        import yaml

        fm_yaml = yaml.dump(
            self.frontmatter.to_dict(),
            sort_keys=False,
            allow_unicode=True,
        ).strip()
        return f"---\n{fm_yaml}\n---\n\n{self.body_markdown.strip()}\n"


@dataclass
class LinkedInPost:
    """Companion LinkedIn post formatted for high organic conversion."""

    hook: str
    body_paragraphs: list[str]
    takeaways: list[str]
    call_to_action: str
    hashtags: list[str]
    character_count: int = 0

    def render(self) -> str:
        """Render formatted LinkedIn post."""
        sections = [self.hook.strip(), ""]
        for p in self.body_paragraphs:
            sections.append(p.strip())
            sections.append("")

        sections.append("Key Takeaways:")
        for t in self.takeaways:
            sections.append(f"• {t.strip()}")
        sections.append("")

        sections.append(self.call_to_action.strip())
        sections.append("")

        tag_line = " ".join(f"#{t.lstrip('#')}" for t in self.hashtags)
        sections.append(tag_line)

        rendered = "\n".join(sections).strip() + "\n"
        self.character_count = len(rendered)
        return rendered


@dataclass
class CMSPlatformConfig:
    """Configuration definition for a single CMS target platform."""

    id: str
    name: str
    format: str
    endpoint: str | None = None
    status: str = "draft"
    frontmatter_mapping: dict[str, str] = field(default_factory=dict)
    field_mapping: dict[str, str] = field(default_factory=dict)
    output_pattern: str | None = None
    include_toc: bool = False
