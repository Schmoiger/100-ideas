"""Smoke tests for Blog & Social Publishing Subsystem."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from services.ingestion.models import IdeaRecord
from services.ingestion.provisioner import provision_idea
from services.publishing.adapters import export_for_platform, load_publishing_config
from services.publishing.drafter import (
    count_words,
    draft_blog_post,
    generate_opinionated_blog_body,
)
from services.publishing.pipeline import process_blog_and_social
from services.publishing.social import generate_linkedin_post


def _create_test_idea(idea_id: str = "idea-001") -> IdeaRecord:
    """Helper to construct dummy IdeaRecord."""
    return IdeaRecord(
        id=idea_id,
        title="Agentic Code Reviewer",
        synopsis="Automated pull request analysis and vulnerability detection.",
        tags=["DeveloperTools", "CodeReview"],
    )


def test_blogger_persona_adherence() -> None:
    """Verify blogger persona features adhering to AS author persona (context/persona/author.md)."""
    idea = _create_test_idea("idea-010")
    body = generate_opinionated_blog_body(idea)
    words = count_words(body)

    # Word count: 400 - 800 words target (REQ-BLG-001)
    assert 350 <= words <= 850, f"Expected 400-800 words, got {words}"

    # 1. Punch over preamble (sharp momentum hook)
    assert "delivery bottlenecks have nothing to do with writing code" in body

    # 2. Plain language with physical metaphors
    assert "digital rust" in body
    assert "rat's nest" in body

    # 3. Descriptive headings
    assert "## The Operational Reality" in body
    assert "## What Actually Changes" in body

    # 4. Economic Equation & So What?
    assert "## So What? The Economic Equation" in body

    # 5. Bold lead-ins for scanability
    assert "- **Eliminating Digital Rust**:" in body
    assert "- **Throughput Decoupling**:" in body

    # 6. Prohibited AI slop check
    prohibited_slop = [
        "delve",
        "testament to",
        "tapestry",
        "beacon",
        "revolutionise",
        "seamless",
        "groundbreaking",
        "pivotal",
    ]
    for slop in prohibited_slop:
        assert slop not in body.lower(), f"Found prohibited AI slop '{slop}' in blog body"


def test_hostinger_frontmatter_validation() -> None:
    """Verify generated blog post contains valid Hostinger YAML frontmatter with all required keys."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-001")
        provision_idea(idea, ideas_root)

        post_file, generated = draft_blog_post(idea, ideas_root, force=True)
        assert generated is True
        assert post_file.is_file()

        content = post_file.read_text(encoding="utf-8")
        assert content.startswith("---\n")

        parts = content.split("---\n", 2)
        assert len(parts) >= 3
        fm_raw = parts[1]
        fm = yaml.safe_load(fm_raw)

        # REQ-BLG-002 required keys
        assert "title" in fm
        assert "slug" in fm
        assert "date" in fm
        assert "excerpt" in fm
        assert "tags" in fm
        assert "cover_image" in fm
        assert "author" in fm
        assert fm["author"] == "AS"
        assert fm["cover_image"] == "../assets/illustration.png"
        assert len(fm["tags"]) >= 2

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-001" / "meta.yaml"
        meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_data.get("blog_post") == "blog/post.md"
        assert meta_data.get("blog_slug") == fm["slug"]


def test_linkedin_post_generation() -> None:
    """Verify companion LinkedIn post generation, character limit (<3,000 chars), and bullet takeaways."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-002")
        provision_idea(idea, ideas_root)

        linkedin_file, generated = generate_linkedin_post(idea, ideas_root, force=True)
        assert generated is True
        assert linkedin_file.is_file()

        content = linkedin_file.read_text(encoding="utf-8")

        # REQ-BLG-003: Under 3,000 characters
        assert len(content) < 3000, f"Post exceeded 3,000 characters: {len(content)}"
        assert len(content) > 300, "Post too short"

        # 3-5 bullet takeaways
        bullets = [line for line in content.splitlines() if line.startswith("• ")]
        assert 3 <= len(bullets) <= 5

        # Hashtags
        assert "#SoftwareEngineering" in content
        assert "#TechLeadership" in content

        # Check meta.yaml updated
        meta_file = ideas_root / "idea-002" / "meta.yaml"
        meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert meta_data.get("linkedin_post") == "blog/linkedin.md"
        assert meta_data.get("linkedin_chars") == len(content)


def test_cms_publication_adapters() -> None:
    """Verify CMS publication adapters for Hostinger static, WordPress, and Ghost."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = repo_root / "config" / "publishing.yaml"
    assert config_path.is_file(), "config/publishing.yaml missing"

    cfg = load_publishing_config(config_path)
    assert "platforms" in cfg
    assert "hostinger_static" in cfg["platforms"]
    assert "hostinger_wordpress" in cfg["platforms"]
    assert "hostinger_ghost" in cfg["platforms"]

    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-003")
        provision_idea(idea, ideas_root)
        post_file, _ = draft_blog_post(idea, ideas_root, force=True)

        # 1. Static site export (Astro/Hugo)
        res_static = export_for_platform(post_file, "hostinger_static", config_path=config_path)
        assert res_static["format"] == "markdown"
        assert "description" in res_static["frontmatter"]
        assert "image" in res_static["frontmatter"]

        # 2. WordPress REST API payload
        res_wp = export_for_platform(post_file, "hostinger_wordpress", config_path=config_path)
        assert res_wp["format"] == "wordpress_rest"
        assert "<h2>" in res_wp["payload"]["content"]
        assert res_wp["payload"]["status"] == "draft"

        # 3. Ghost Admin API payload
        res_ghost = export_for_platform(post_file, "hostinger_ghost", config_path=config_path)
        assert res_ghost["format"] == "ghost_admin_api"
        assert "posts" in res_ghost["payload"]
        assert res_ghost["payload"]["posts"][0]["title"].startswith("Agentic Code Reviewer")


def test_pipeline_idempotency() -> None:
    """Verify pipeline skips generation if content exists unless force=True."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        catalog_path = Path(tmp_dir) / "cat.md"
        snapshot_path = Path(tmp_dir) / "snap.md"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-004")
        provision_idea(idea, ideas_root)

        # First run: generates both
        run1 = process_blog_and_social(
            idea_id_or_num="idea-004",
            ideas_root=ideas_root,
            repo_root=repo_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_blog=True,
            do_social=True,
            cms_platform="hostinger_static",
            force=False,
        )
        assert run1["blog_generated"] is True
        assert run1["social_generated"] is True
        assert "cms_export" in run1

        # Second run: cached / skipped
        run2 = process_blog_and_social(
            idea_id_or_num="idea-004",
            ideas_root=ideas_root,
            repo_root=repo_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_blog=True,
            do_social=True,
            cms_platform="hostinger_static",
            force=False,
        )
        assert run2["blog_generated"] is False
        assert run2["social_generated"] is False

        # Forced run: regenerates
        run3 = process_blog_and_social(
            idea_id_or_num="idea-004",
            ideas_root=ideas_root,
            repo_root=repo_root,
            catalog_path=catalog_path,
            snapshot_path=snapshot_path,
            do_blog=True,
            do_social=True,
            cms_platform="hostinger_static",
            force=True,
        )
        assert run3["blog_generated"] is True
        assert run3["social_generated"] is True


def test_markdown_interoperability_and_portability() -> None:
    """Verify exported Markdown complies with CommonMark/GFM standards for PKM tools (NFR-EXT-003)."""
    import re

    from services.typesetting.drafter import draft_book_chapter

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with tempfile.TemporaryDirectory(dir=str(repo_root / "artefacts")) as tmp_dir:
        ideas_root = Path(tmp_dir) / "ideas"
        ideas_root.mkdir(parents=True)

        idea = _create_test_idea("idea-001")
        provision_idea(idea, ideas_root)

        # 1. Draft Book Chapter
        chapter_path, _ = draft_book_chapter(idea, ideas_root, force=True)
        chapter_text = chapter_path.read_text(encoding="utf-8")

        # 2. Draft Blog Post
        post_path, _ = draft_blog_post(idea, ideas_root, force=True)
        post_text = post_path.read_text(encoding="utf-8")

        # Verify CommonMark / GFM characteristics across files
        for md_path, md_content in [(chapter_path, chapter_text), (post_path, post_text)]:
            # No raw unescaped HTML tags (pure Markdown portable to Obsidian/Notion/Logseq)
            assert "<script" not in md_content
            assert "<iframe" not in md_content
            assert "<div" not in md_content

            # Valid heading hierarchy (#, ##, ###)
            headings = re.findall(r"^(#+)\s+(.+)$", md_content, re.MULTILINE)
            assert len(headings) >= 2, f"Expected multiple headings in {md_path.name}"

            # Valid image tags with relative paths
            images = re.findall(r"!\[(.*?)\]\((.*?)\)", md_content)
            for caption, img_target in images:
                assert img_target.endswith(".png"), (
                    f"Invalid image reference in {md_path.name}: {img_target}"
                )

            # Valid markdown table structure if present
            if "|" in md_content:
                table_lines = [
                    ln.strip() for ln in md_content.splitlines() if ln.strip().startswith("|")
                ]
                assert len(table_lines) >= 3, (
                    "Markdown tables should have header, separator, and data rows"
                )
                # Check for standard markdown table separator
                assert any("---" in ln for ln in table_lines)
