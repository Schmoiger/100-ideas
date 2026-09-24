"""CMS Publication Adapters and export transformers (REQ-BLG-004)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from services.publishing.models import CMSPlatformConfig


def get_default_config_path() -> Path:
    """Return default configuration path for publishing adapters."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "config" / "publishing.yaml"


def load_publishing_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from config/publishing.yaml."""
    cfg_file = config_path or get_default_config_path()
    if not cfg_file.is_file():
        return {
            "default_platform": "hostinger_static",
            "platforms": {
                "hostinger_static": {
                    "name": "Hostinger Static / Astro / Hugo",
                    "format": "markdown",
                }
            },
        }

    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
    return data


def get_platform_config(
    platform_id: str,
    config_path: Path | None = None,
) -> CMSPlatformConfig:
    """Retrieve typed configuration for a specific target platform."""
    full_cfg = load_publishing_config(config_path)
    platforms = full_cfg.get("platforms", {})
    if platform_id not in platforms:
        raise ValueError(
            f"Unknown CMS publishing platform: '{platform_id}'. "
            f"Available platforms: {list(platforms.keys())}"
        )

    plat_dict = platforms[platform_id]
    return CMSPlatformConfig(
        id=platform_id,
        name=plat_dict.get("name", platform_id),
        format=plat_dict.get("format", "markdown"),
        endpoint=plat_dict.get("endpoint"),
        status=plat_dict.get("status", "draft"),
        frontmatter_mapping=plat_dict.get("frontmatter_mapping", {}),
        field_mapping=plat_dict.get("field_mapping", {}),
        output_pattern=plat_dict.get("output_pattern"),
        include_toc=plat_dict.get("include_toc", False),
    )


def parse_post_markdown(post_path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and Markdown body from post.md file."""
    content = post_path.read_text(encoding="utf-8")
    fm_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = fm_pattern.match(content)
    if not match:
        return {}, content

    fm_raw = match.group(1)
    body = match.group(2)
    frontmatter = yaml.safe_load(fm_raw) or {}
    return frontmatter, body


def markdown_to_html_simple(md_text: str) -> str:
    """Convert basic Markdown elements to clean HTML for CMS payloads."""
    html_lines: list[str] = []
    in_list = False

    for line in md_text.splitlines():
        line_s = line.strip()
        if not line_s:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        # Headings
        if line_s.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line_s[3:].strip()}</h2>")
        elif line_s.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line_s[4:].strip()}</h3>")
        elif line_s.startswith("- ") or line_s.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_text = line_s[2:].strip()
            # Simple bold conversion
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            html_lines.append(f"  <li>{item_text}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # Simple bold conversion
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line_s)
            html_lines.append(f"<p>{p_text}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def export_for_platform(
    post_path: Path,
    platform_id: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Transform blog post into target CMS publication payload according to config/publishing.yaml.

    Implements REQ-BLG-004.
    """
    config = get_platform_config(platform_id, config_path)
    frontmatter, body = parse_post_markdown(post_path)

    if config.format == "markdown":
        # Hostinger Static / Astro / Hugo: Remap frontmatter keys if specified
        mapped_fm: dict[str, Any] = {}
        for src_key, val in frontmatter.items():
            target_key = config.frontmatter_mapping.get(src_key, src_key)
            mapped_fm[target_key] = val

        rendered_fm = yaml.dump(mapped_fm, sort_keys=False, allow_unicode=True).strip()
        rendered_md = f"---\n{rendered_fm}\n---\n\n{body.strip()}\n"

        return {
            "platform": platform_id,
            "format": "markdown",
            "content": rendered_md,
            "frontmatter": mapped_fm,
            "slug": frontmatter.get("slug", ""),
        }

    if config.format == "wordpress_rest":
        # WordPress REST API schema
        html_content = markdown_to_html_simple(body)
        mapped_payload: dict[str, Any] = {
            "title": frontmatter.get("title", ""),
            "slug": frontmatter.get("slug", ""),
            "status": config.status,
            "content": html_content,
            "excerpt": frontmatter.get("excerpt", ""),
            "tags": frontmatter.get("tags", []),
            "meta": {
                "author": frontmatter.get("author", "AS"),
                "reading_time": frontmatter.get("reading_time_minutes", 3),
            },
        }
        return {
            "platform": platform_id,
            "format": "wordpress_rest",
            "endpoint": config.endpoint,
            "payload": mapped_payload,
        }

    if config.format == "ghost_admin_api":
        # Ghost Admin API schema
        ghost_post: dict[str, Any] = {
            "title": frontmatter.get("title", ""),
            "slug": frontmatter.get("slug", ""),
            "status": config.status,
            "markdown": body.strip(),
            "custom_excerpt": frontmatter.get("excerpt", ""),
            "tags": [{"name": t} for t in frontmatter.get("tags", [])],
        }
        return {
            "platform": platform_id,
            "format": "ghost_admin_api",
            "endpoint": config.endpoint,
            "payload": {"posts": [ghost_post]},
        }

    raise ValueError(f"Unsupported publication format: '{config.format}'")
