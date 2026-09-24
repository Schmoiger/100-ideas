"""Dual-target asset path resolver for Typst and CMS publishing."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class AssetTarget(str, Enum):
    """Supported compilation and publishing asset targets."""

    TYPST = "typst"
    CMS = "cms"
    WEB = "web"


class AssetResolver:
    """Resolves asset paths for Typst figure embedding and CMS publication staging."""

    def __init__(
        self,
        ideas_root: Path,
        repo_root: Path | None = None,
        web_base_url: str | None = None,
    ) -> None:
        self.ideas_root = ideas_root.resolve()
        self.repo_root = (
            repo_root.resolve() if repo_root else Path(__file__).resolve().parent.parent.parent
        )
        self.web_base_url = web_base_url.rstrip("/") if web_base_url else ""

    def resolve_illustration_path(
        self,
        idea_id: str,
        target: str | AssetTarget = AssetTarget.TYPST,
        typst_mode: str = "relative",  # "relative" or "root"
    ) -> str:
        """Resolve publication-ready path for an idea's editorial illustration.

        Handles dual-target resolution:
        1. Typst: Returns relative path (e.g. '../assets/illustration.png') or root-relative path.
        2. CMS/Web: Returns web_cover_url from meta.yaml, CDN URL, or web staging path.
        """
        target_val = target.value if isinstance(target, AssetTarget) else str(target).lower()
        idea_dir = self.ideas_root / idea_id
        assets_dir = idea_dir / "assets"
        meta_file = idea_dir / "meta.yaml"

        # Check existing asset extensions
        img_name = "illustration.png"
        if not (assets_dir / img_name).is_file() and (assets_dir / "illustration.webp").is_file():
            img_name = "illustration.webp"

        if target_val == AssetTarget.TYPST.value:
            if typst_mode == "root":
                img_path = assets_dir / img_name
                try:
                    rel_to_repo = img_path.resolve().relative_to(self.repo_root)
                    return f"/{rel_to_repo.as_posix()}"
                except ValueError:
                    return img_path.as_posix()
            return f"../assets/{img_name}"

        # Target is CMS or WEB
        if meta_file.is_file():
            try:
                data = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
                assets_meta = data.get("assets", {})
                if isinstance(assets_meta, dict) and assets_meta.get("web_cover_url"):
                    return str(assets_meta["web_cover_url"])
            except Exception:
                pass

        if self.web_base_url:
            return f"{self.web_base_url}/{idea_id}/{img_name}"

        # Default web-ready static asset path
        return f"/assets/ideas/{idea_id}/{img_name}"

    def stage_assets_for_cms(
        self,
        idea_id: str,
        staging_dir: Path,
        public_url_prefix: str = "",
    ) -> dict[str, Any]:
        """Stage assets to a web-accessible directory and update meta.yaml with web_cover_url."""
        idea_dir = self.ideas_root / idea_id
        assets_dir = idea_dir / "assets"
        dest_dir = staging_dir / idea_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        staged_files: dict[str, str] = {}
        web_cover_url = ""

        for file_path in assets_dir.glob("illustration.*"):
            if file_path.is_file():
                dest_file = dest_dir / file_path.name
                dest_file.write_bytes(file_path.read_bytes())
                staged_files[file_path.name] = str(dest_file)
                if not web_cover_url:
                    prefix = (
                        public_url_prefix.rstrip("/") if public_url_prefix else "/static/images"
                    )
                    web_cover_url = f"{prefix}/{idea_id}/{file_path.name}"

        # Update meta.yaml
        meta_file = idea_dir / "meta.yaml"
        if meta_file.is_file() and web_cover_url:
            try:
                data = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
                assets_meta = dict(data.get("assets", {}))
                assets_meta["web_cover_url"] = web_cover_url
                data["assets"] = assets_meta

                temp_meta = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                temp_meta.replace(meta_file)
            except Exception:
                pass

        return {
            "idea_id": idea_id,
            "staged_files": staged_files,
            "web_cover_url": web_cover_url,
        }
