"""Unit tests for dual-target asset path resolver (Typst vs CMS)."""

from __future__ import annotations

from pathlib import Path

import yaml

from services.publishing.assets import AssetResolver, AssetTarget


def test_asset_resolver_typst_relative(tmp_path: Path) -> None:
    """Verify resolver produces correct relative path for Typst chapter embedding."""
    ideas_root = tmp_path / "ideas"
    idea_dir = ideas_root / "idea-001"
    assets_dir = idea_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "illustration.png").write_bytes(b"dummy png")

    resolver = AssetResolver(ideas_root=ideas_root, repo_root=tmp_path)
    res = resolver.resolve_illustration_path("idea-001", target=AssetTarget.TYPST)
    assert res == "../assets/illustration.png"


def test_asset_resolver_typst_root(tmp_path: Path) -> None:
    """Verify resolver produces root-relative path for aggregated volume compiling."""
    ideas_root = tmp_path / "artefacts" / "content" / "ideas"
    idea_dir = ideas_root / "idea-001"
    assets_dir = idea_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "illustration.png").write_bytes(b"dummy png")

    resolver = AssetResolver(ideas_root=ideas_root, repo_root=tmp_path)
    res = resolver.resolve_illustration_path(
        "idea-001", target=AssetTarget.TYPST, typst_mode="root"
    )
    assert res == "/artefacts/content/ideas/idea-001/assets/illustration.png"


def test_asset_resolver_cms_web_url(tmp_path: Path) -> None:
    """Verify resolver returns web_cover_url if set in meta.yaml."""
    ideas_root = tmp_path / "ideas"
    idea_dir = ideas_root / "idea-002"
    idea_dir.mkdir(parents=True)
    meta_file = idea_dir / "meta.yaml"
    meta_data = {
        "id": "idea-002",
        "assets": {"web_cover_url": "https://cdn.withineve.com/images/idea-002.png"},
    }
    meta_file.write_text(yaml.safe_dump(meta_data), encoding="utf-8")

    resolver = AssetResolver(ideas_root=ideas_root, repo_root=tmp_path)
    res = resolver.resolve_illustration_path("idea-002", target=AssetTarget.CMS)
    assert res == "https://cdn.withineve.com/images/idea-002.png"


def test_asset_resolver_cms_base_url_fallback(tmp_path: Path) -> None:
    """Verify resolver constructs clean web URL with web_base_url."""
    ideas_root = tmp_path / "ideas"
    idea_dir = ideas_root / "idea-003"
    idea_dir.mkdir(parents=True)

    resolver = AssetResolver(
        ideas_root=ideas_root,
        repo_root=tmp_path,
        web_base_url="https://withineve.com/blog-assets",
    )
    res = resolver.resolve_illustration_path("idea-003", target="web")
    assert res == "https://withineve.com/blog-assets/idea-003/illustration.png"


def test_stage_assets_for_cms(tmp_path: Path) -> None:
    """Verify stage_assets_for_cms copies files and updates meta.yaml."""
    ideas_root = tmp_path / "ideas"
    idea_dir = ideas_root / "idea-004"
    assets_dir = idea_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "illustration.png").write_bytes(b"test image payload")

    meta_file = idea_dir / "meta.yaml"
    meta_file.write_text(yaml.safe_dump({"id": "idea-004"}), encoding="utf-8")

    staging_dir = tmp_path / "public_html" / "media"
    resolver = AssetResolver(ideas_root=ideas_root, repo_root=tmp_path)
    outcome = resolver.stage_assets_for_cms(
        idea_id="idea-004",
        staging_dir=staging_dir,
        public_url_prefix="https://myblog.com/media",
    )

    assert "illustration.png" in outcome["staged_files"]
    staged_path = Path(outcome["staged_files"]["illustration.png"])
    assert staged_path.is_file()
    assert staged_path.read_bytes() == b"test image payload"
    assert outcome["web_cover_url"] == "https://myblog.com/media/idea-004/illustration.png"

    # Verify meta.yaml updated
    updated_meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert (
        updated_meta["assets"]["web_cover_url"]
        == "https://myblog.com/media/idea-004/illustration.png"
    )
