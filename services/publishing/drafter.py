"""Opinionated blog article drafter implementing Dr Sarah Chen persona (REQ-BLG-001, REQ-BLG-002)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.publishing.models import BlogFrontmatter, BlogPost


def slugify(text: str) -> str:
    """Generate URL-safe slug from title or text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", slug).strip("-")


def count_words(text: str) -> int:
    """Count words in text string excluding Markdown symbols."""
    words = re.findall(r"\b[\w'-]+\b", text)
    return len(words)


def generate_opinionated_blog_body(idea: IdeaRecord, research_summary: str = "") -> str:
    """Synthesise conversational, opinionated blog post adhering to Dr Sarah Chen persona.

    Implements:
    - Provocative opening hook upfront.
    - Conversational parentheticals.
    - Question-driven framing.
    - 'So What?' practical implications.
    - Principles in parallel structure.
    - Self-deprecating honesty and real-world examples.
    - 400-800 word target length.
    """
    cat = idea.tags[0].title() if idea.tags else "Software Engineering"
    title = idea.title
    desc = idea.synopsis or (
        "Reimagining developer tooling through disciplined agentic workflows and automated synthesis."
    )

    # Clean description
    desc_clean = desc.strip()
    if not desc_clean.endswith("."):
        desc_clean += "."

    body_text = f"""Let's be brutally honest: most enterprise tooling exists to solve problems we invented for ourselves.

We spend weeks debating architectural purity, writing boilerplate that could bore a stone, and wondering why shipping a minor feature feels like wading through wet cement (incidentally, usually because someone decided three layers of caching were "strictly necessary").

Enter **{title}**.

At its core, this idea addresses an undeniable operational friction in {cat}: {desc_clean}

---

## Why Are We Still Doing This By Hand?

If you observe an engineering team tackling this problem today, you will witness a familiar ritual. Smart engineers manually orchestrate repetitive handoffs, context-switch between five browser tabs, and paste fragments of data across disjointed tools. It is tedious. It is error-prone. And frankly, it is an astonishingly expensive use of creative engineering talent.

When I was leading developer productivity initiatives at Google, we noticed a recurring paradox: teams consistently overestimated the difficulty of the core algorithm whilst underestimating the friction of the day-to-day workflow.

{title} flips that equation. Instead of demanding that developers conform to an inflexible pipeline, it automates the mechanical heavy lifting—preserving human judgement for the high-leverage edge cases.

---

## What Does This Actually Fix?

Let's dissect what happens when this capability is deployed into an active pipeline:

- **Context Preservation**: Eliminates the cognitive penalty of manual state tracking across separate tools.
- **Deterministic Guardrails**: Replaces speculative intuition with empirical checks and reproducible verification.
- **Velocity Without Chaos**: Accelerates cycle time whilst enforcing strict architectural consistency.

Is it flawless? Of course not. (Full disclosure: I have seen teams attempt to automate workflows before standardising their basic processes, and the result is merely high-speed dysfunction.) But when layered onto a solid foundation, the leverage is unmistakable.

---

## So What? The Practical Reality

So what does this mean if you are leading an engineering organisation or building production services tomorrow morning?

Simplicity is universal. Simplicity is effective. Simplicity is hard. Simplicity is ongoing.

Do not wait for a monolithic platform overhaul to address workflow friction. Start by identifying the single most repetitive, context-draining handoff in your current pipeline. Implement structured automation around that narrow boundary, verify the outcome with automated tests, and measure the cognitive relief.

You don't own the process if the process owns your engineers' focus. It's time to build tooling that respects human attention.
"""

    return body_text.strip()


def draft_blog_post(
    idea: IdeaRecord,
    ideas_root: Path,
    ideas_catalog: list[IdeaRecord] | None = None,
    force: bool = False,
) -> tuple[Path, bool]:
    """Generate Hostinger-compatible blog post with YAML frontmatter.

    Implements REQ-BLG-001 and REQ-BLG-002.
    Returns (post_path, was_generated).
    """
    idea_dir = ideas_root / idea.id
    blog_dir = idea_dir / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)
    post_file = blog_dir / "post.md"

    # Check cache / idempotency
    if post_file.is_file() and not force:
        return post_file, False

    # Extract tags
    tags: list[str] = ["SoftwareEngineering", "Architecture"]
    for t in idea.tags:
        clean_tag = re.sub(r"\W+", "", t)
        if clean_tag and clean_tag not in tags:
            tags.append(clean_tag)
    tags.append("TechLeadership")

    # Generate slug and frontmatter
    slug = f"{idea.id}-{slugify(idea.title)}"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    excerpt = (
        f"Why {idea.title} matters for modern software engineering teams, and how to eliminate "
        f"costly cognitive friction in your day-to-day development workflow."
    )

    # Synthesise body
    body_markdown = generate_opinionated_blog_body(idea)
    words = count_words(body_markdown)
    reading_time = max(1, round(words / 200))

    frontmatter = BlogFrontmatter(
        title=f"{idea.title}: A Pragmatic Guide to Cutting Development Friction",
        slug=slug,
        date=today_str,
        excerpt=excerpt,
        tags=tags,
        cover_image="../assets/illustration.png",
        author="Dr Sarah Chen",
        reading_time_minutes=reading_time,
        draft=False,
    )

    post = BlogPost(
        frontmatter=frontmatter,
        body_markdown=body_markdown,
        idea_id=idea.id,
        word_count=words,
    )

    post_content = post.render()
    post_file.write_text(post_content, encoding="utf-8")

    # Update meta.yaml
    meta_file = idea_dir / "meta.yaml"
    meta_dict: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:
            meta_dict = {}

    meta_dict["blog_post"] = "blog/post.md"
    meta_dict["blog_slug"] = slug
    meta_dict["blog_words"] = words
    meta_file.write_text(yaml.dump(meta_dict, sort_keys=False), encoding="utf-8")

    return post_file, True
