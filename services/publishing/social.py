"""LinkedIn and social snippet generator (REQ-BLG-003)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from services.ingestion.models import IdeaRecord
from services.publishing.models import LinkedInPost


def generate_linkedin_post(
    idea: IdeaRecord,
    ideas_root: Path,
    force: bool = False,
    overwrite_manual: bool = False,
) -> tuple[Path, bool]:
    """Generate high-converting companion LinkedIn post adhering to REQ-BLG-003.

    Acceptance criteria:
    - High-converting hook.
    - 3-5 scannable bullet takeaways.
    - Character count strictly under 3,000 characters.
    - Relevant hashtags.
    - Saved to artefacts/content/ideas/{idea-id}/blog/linkedin.md.
    - Refuses to overwrite if human_modified=True without overwrite_manual=True.
    """
    from services.ingestion.safeguards import check_manual_edit_safeguard

    idea_dir = ideas_root / idea.id
    blog_dir = idea_dir / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)
    linkedin_file = blog_dir / "linkedin.md"

    # Check cache / idempotency & manual edit protection
    if linkedin_file.is_file():
        if not force and not overwrite_manual:
            return linkedin_file, False
        check_manual_edit_safeguard(
            target_file=linkedin_file,
            idea=idea,
            force=force,
            overwrite_manual=overwrite_manual,
        )

    # Check for Single Source of Truth: master chapter manuscript
    chapter_file = idea_dir / "book" / "chapter.md"
    syndicated_from: str | None = None
    if chapter_file.is_file():
        from services.publishing.syndication import generate_syndicated_linkedin_post

        post = generate_syndicated_linkedin_post(idea, chapter_file)
        syndicated_from = "book/chapter.md"
    else:
        title = idea.title
        cat = idea.tags[0].title() if idea.tags else "Engineering"
        desc = (
            idea.synopsis or "Eliminating cognitive drag and automating routine developer friction."
        ).strip()
        if not desc.endswith("."):
            desc += "."

        hook = (
            "Most engineering teams aren't slowed down by complex algorithms.\n"
            "They are slowed down by the invisible tax of manual context switching."
        )

        body_paragraphs = [
            f"When we look at {cat.lower()} pipelines, the biggest bottleneck isn't raw computing power—it's the friction between thought and execution.",
            f"That is why '{title}' is such an important pattern:\n👉 {desc}",
            "Instead of asking developers to manage mechanical coordination across fragmented tools, structured automation handles the heavy lifting whilst preserving engineering judgement where it counts.",
        ]

        takeaways = [
            "Protect Context: Manual handoffs destroy deep work faster than any meeting.",
            "Deterministic Guardrails: Replace speculative tribal knowledge with empirical verification.",
            "Measure Leverage: Automate the predictable so your team can focus on the novel.",
            "Ship Smaller, Ship Confidently: Narrow boundaries enable continuous, low-risk deployments.",
        ]

        call_to_action = (
            "How is your engineering team systematically addressing developer friction this quarter? "
            "I'd love to hear your experiences in the comments below."
        )

        raw_category = re.sub(r"\W+", "", cat)
        hashtags = [
            "SoftwareEngineering",
            "DeveloperExperience",
            "TechLeadership",
            raw_category if raw_category else "CloudNative",
            "Productivity",
        ]

        post = LinkedInPost(
            hook=hook,
            body_paragraphs=body_paragraphs,
            takeaways=takeaways,
            call_to_action=call_to_action,
            hashtags=hashtags,
        )

    content = post.render()

    # Enforce strictly under 3,000 characters
    if len(content) > 2900:
        content = content[:2850] + "...\n\n#SoftwareEngineering #TechLeadership\n"

    linkedin_file.write_text(content, encoding="utf-8")

    # Update meta.yaml
    meta_file = idea_dir / "meta.yaml"
    meta_dict: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            meta_dict = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:
            meta_dict = {}

    meta_dict["linkedin_post"] = "blog/linkedin.md"
    meta_dict["linkedin_chars"] = len(content)
    if syndicated_from:
        meta_dict["linkedin_syndicated_from"] = syndicated_from
    meta_file.write_text(yaml.dump(meta_dict, sort_keys=False), encoding="utf-8")

    return linkedin_file, True
