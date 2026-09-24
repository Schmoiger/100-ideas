"""Tests for Single Source of Truth (SSOT) Chapter Syndication (TASK-019)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.publishing.drafter import draft_blog_post
from services.publishing.social import generate_linkedin_post
from services.publishing.syndication import (
    extract_chapter_master,
    generate_syndicated_blog_body,
    generate_syndicated_linkedin_post,
)
from services.typesetting.drafter import draft_book_chapter


def _create_sample_idea(idea_id: str = "idea-042") -> IdeaRecord:
    return IdeaRecord(
        id=idea_id,
        title="Decoupled Syntax Generation",
        synopsis="Manual syntax creation throttles architectural intent across teams.",
        tags=["Architecture", "DeveloperExperience"],
    )


SAMPLE_CUSTOM_CHAPTER = """# Chapter 42: Decoupled Syntax Generation

*Chapter 42 · 100 Ideas for Engineering Leaders*

![Editorial illustration: Decoupled Syntax Generation](../assets/illustration.png)

---

## The Unvarnished Reality

Software engineering has spent decades mistaking typing speed for delivery capacity. The cold reality is straightforward: Manual syntax creation throttles architectural intent across teams. When delivery throughput is bottlenecked by human fingers typing syntax line by line, every enterprise initiative crawls at the speed of cognitive overload.

---

## Where the Gears Bind

Every engineering organisation eventually accumulates digital rust. Abstract architectures look pristine on Miro boards, but on the ground, teams spend sixty percent of their working weeks sweating decaying assets, resolving dependency tangles, and unpicking a rat's nest of legacy cables behind the build pipeline.

Consider what happens when you adopt 'Decoupled Syntax Generation'. The constraint does not disappear; it migrates.

> [!NOTE]
> **Core Operating Mechanism**: An asynchronous compiler queue decoupling high-level intent from low-level syntax trees. True delivery velocity is not measured by how much raw code enters the repo, but by the cycle time required to prove that code is correct and safe to run.

**Empirical Grounding & Field Observations**:
- Field observation: 42% reduction in PR turnaround time when syntax boilerplate is synthesised.
- Case evidence: Deployment failure rate dropped to 0.8% under automated contract verification.

---

## The Economic Equation & Trade-offs

What does this actually cost us in delivery velocity, cognitive load, and cash?

| Operational Dimension | Conventional SDLC | Decoupled Syntax Generation |
|---|---|---|
| **Binding Constraint** | Human developer syntax bandwidth | Automated verification and test fidelity |
| **Failure Blast Radius** | Missed sprint commitments | Rapid divergence without deterministic gates |

**Constraint Dynamics & Real-World Trade-offs**:
- Higher upfront investment in verification tooling.
- Immediate relief from manual boilerplate maintenance.

---

## Puncturing the Hype

Autonomous agents will not magically fix an enterprise organisation that cannot define its own boundaries. If your business domain model is a swamp of ambiguous terminology and territorial committee meetings, accelerating code production will simply deliver a larger, faster catastrophe.

Except I might be wrong about the timeline.

---

## Actionable Takeaways

- **Map the binding constraint first**: Identify whether syntax production or validation latency throttles your team.
- **Enforce deterministic gate checks**: Run isolated automated verification suites on every generated commit.
- **Isolate domain models cleanly**: Treat architecture as executable contracts rather than slide deck diagrams.

---

## Grounded Citations & Field References

- Accelerate: The Science of Lean Software and DevOps (Forsgren, Humble, Kim).
"""


def test_extract_chapter_master() -> None:
    """Verify markdown chapter parser extracts all semantic sections faithfully."""
    parsed = extract_chapter_master(SAMPLE_CUSTOM_CHAPTER)

    assert parsed.title == "Decoupled Syntax Generation"
    assert parsed.chapter_num == 42
    assert "Manual syntax creation throttles architectural intent" in parsed.lead_punch
    assert "digital rust" in parsed.mechanics_section
    assert "An asynchronous compiler queue" in parsed.mechanics_section
    assert len(parsed.takeaways) == 3
    assert "Map the binding constraint first" in parsed.takeaways[0]
    assert "Enforce deterministic gate checks" in parsed.takeaways[1]
    assert len(parsed.citations) == 1
    assert "Accelerate" in parsed.citations[0]


def test_syndicated_blog_body_generation() -> None:
    """Verify syndicated blog post derives core arguments from master chapter."""
    idea = _create_sample_idea()
    blog_body = generate_syndicated_blog_body(idea, SAMPLE_CUSTOM_CHAPTER)

    # Adheres to persona word count
    words = len(blog_body.split())
    assert 350 <= words <= 850

    # Retains chapter master arguments and mechanisms
    assert "Decoupled Syntax Generation" in blog_body
    assert "digital rust" in blog_body.lower()
    assert "asynchronous compiler queue" in blog_body or "binding constraint" in blog_body.lower()
    assert "## The Operational Reality" in blog_body
    assert "## What Actually Changes" in blog_body
    assert "## So What? The Economic Equation" in blog_body
    assert (
        "Map the binding constraint first" in blog_body
        or "Enforce deterministic gate checks" in blog_body
    )


def test_syndicated_linkedin_post_generation() -> None:
    """Verify LinkedIn post draws hook and takeaways directly from chapter master."""
    idea = _create_sample_idea()
    post = generate_syndicated_linkedin_post(idea, SAMPLE_CUSTOM_CHAPTER)
    rendered = post.render()

    assert len(rendered) < 3000
    assert "Decoupled Syntax Generation" in rendered
    # Takeaways must directly trace to the chapter's takeaways
    takeaways_text = "\n".join(post.takeaways)
    assert "Map the binding constraint first" in takeaways_text
    assert "Enforce deterministic gate checks" in takeaways_text


def test_draft_blog_post_ssot_integration() -> None:
    """Verify draft_blog_post automatically discovers and syndicates from book/chapter.md."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea("idea-042")
        provision_idea(idea, ideas_root)

        # 1. First generate book chapter
        chapter_file, chap_gen = draft_book_chapter(idea, ideas_root, force=True)
        assert chap_gen is True
        assert chapter_file.is_file()

        # Customise the chapter file to simulate human editorial revision
        chapter_file.write_text(SAMPLE_CUSTOM_CHAPTER, encoding="utf-8")

        # 2. Generate blog post
        post_file, post_gen = draft_blog_post(idea, ideas_root, force=True)
        assert post_gen is True
        assert post_file.is_file()

        blog_content = post_file.read_text(encoding="utf-8")
        # Should reflect custom chapter text
        assert "digital rust" in blog_content
        assert (
            "Map the binding constraint first" in blog_content
            or "Enforce deterministic gate checks" in blog_content
        )

        # 3. Check meta.yaml syndication metadata
        meta_file = ideas_root / idea.id / "meta.yaml"
        meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_data.get("syndicated_from") == "book/chapter.md"
        assert "syndicated_at" in meta_data


def test_generate_linkedin_post_ssot_integration() -> None:
    """Verify generate_linkedin_post syndicates directly from book/chapter.md."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea("idea-042")
        provision_idea(idea, ideas_root)

        # Write custom chapter
        book_dir = ideas_root / idea.id / "book"
        book_dir.mkdir(parents=True, exist_ok=True)
        chapter_file = book_dir / "chapter.md"
        chapter_file.write_text(SAMPLE_CUSTOM_CHAPTER, encoding="utf-8")

        # Generate LinkedIn post
        linkedin_file, lk_gen = generate_linkedin_post(idea, ideas_root, force=True)
        assert lk_gen is True
        assert linkedin_file.is_file()

        content = linkedin_file.read_text(encoding="utf-8")
        assert "Map the binding constraint first" in content
        assert "Enforce deterministic gate checks" in content


def test_fallback_when_no_chapter() -> None:
    """Verify clean fallback to raw idea record when book/chapter.md is absent."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_sample_idea("idea-099")
        provision_idea(idea, ideas_root)

        post_file, post_gen = draft_blog_post(idea, ideas_root, force=True)
        assert post_gen is True
        assert post_file.is_file()

        linkedin_file, lk_gen = generate_linkedin_post(idea, ideas_root, force=True)
        assert lk_gen is True
        assert linkedin_file.is_file()
