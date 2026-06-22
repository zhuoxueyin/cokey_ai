"""从 STYLE_PROFILES 组装标准 Markdown 风格描述（v2 分节规范）。"""
from __future__ import annotations

from typing import Any

# 与 style_description.SECTION_DEFS 视觉维度一致
VISUAL_SECTIONS: list[tuple[str, str]] = [
    ("category", "画风大类"),
    ("artist_refs", "画师/工作室参考"),
    ("era_texture", "年代质感"),
    ("line_control", "线条与轮廓控制"),
    ("lighting_color", "光影与色彩"),
    ("palette_strategy", "配色搭配"),
    ("atmosphere", "氛围气质"),
    ("materials", "材质细节"),
    ("quality", "画质要求"),
    ("taboos", "约束禁忌"),
]


def _refs_block(refs: list[str]) -> str:
    lines = "\n".join(refs)
    return f"{lines}\n\n（以上作品仅作美学与镜头语言参考，不涉及角色或剧情复刻。）"


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def build_style_description_md(name: str, profile: dict[str, Any]) -> str:
    """将 profile 字典渲染为 style_description_md 标准 Markdown（独立分节）。"""
    title = name.strip() or "风格"
    parts = [f"# {title}\n", _section("风格摘要", profile["summary"])]

    for key, heading in VISUAL_SECTIONS:
        parts.append(_section(heading, profile.get(key) or ""))

    parts.append(
        _section(
            "人物角色",
            f"{profile['characters_zh'].strip()}\n\n{profile['characters_en'].strip()}",
        )
    )
    parts.append(
        _section(
            "场景描述",
            f"{profile['scenes_zh'].strip()}\n\n{profile['scenes_en'].strip()}",
        )
    )
    parts.append(_section("色彩倾向", profile["colors"]))
    parts.append(_section("代表作品", _refs_block(list(profile["references"]))))
    parts.append(_section("生图提示词参考", profile["image_prompt"]))
    parts.append(_section("生视频提示词参考", profile["video_prompt"]))

    return "\n".join(parts)
