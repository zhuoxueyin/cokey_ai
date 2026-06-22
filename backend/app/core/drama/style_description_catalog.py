"""预设风格描述目录：从 STYLE_PROFILES 生成完整 Markdown，供批量写入 DB。"""
from __future__ import annotations

SKIP_STYLE_IDS: set[str] = set()

# 已迁移至 style_description_profiles.py + style_description_builder.py
STYLE_DESCRIPTIONS: dict[str, str] = {}


def get_style_description_md(
    style_id: str,
    name: str,
    render_class: str,
    genre_tags: list[str],
) -> str | None:
    """返回预设 Markdown；未知 id 返回 None。"""
    if style_id in SKIP_STYLE_IDS:
        return None

    from app.core.drama.style_description_builder import build_style_description_md
    from app.core.drama.style_description_profiles import STYLE_PROFILES

    profile = STYLE_PROFILES.get(style_id)
    if profile:
        return build_style_description_md(name, profile)

    return STYLE_DESCRIPTIONS.get(style_id)
