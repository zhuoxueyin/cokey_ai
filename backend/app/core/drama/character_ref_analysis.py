"""角色 Skill：参考图风格提取与绑定风格融合（仅风格层，不覆盖用户角色设定）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

REF_ANALYSIS_KEYS = (
    "reference_style_en",
    "line_art_en",
    "color_palette_en",
    "lighting_en",
    "texture_en",
    "style_tokens_en",
    "avoid_from_ref_en",
    "notes_zh",
)

VISION_EXTRACT_SYSTEM = """你是角色设定参考图「风格层」分析器。用户会提供参考图（vision）与绑定风格摘要。
任务：只提取可用于 AI 生图的风格、线条、配色、光影、材质笔触等美学关键词，输出 JSON。

严禁从参考图推断或复制：
- 角色性别、年龄、五官、发型、肤色、体型
- 具体服装款式、配饰、武器、身份
- 剧情、人名、文字内容

若参考图含人物，在 notes_zh 中声明「仅提取画风，人物设定以用户文字为准」。"""

VISION_EXTRACT_USER_TEMPLATE = """绑定风格摘要（须兼容，冲突时风格层以绑定风格 render_class 为准）：
{style_summary}

用户角色文字（人物设定以此为准，勿从参考图覆盖）：
{user_message}

请分析附带的参考图，输出 JSON：
{{
  "reference_style_en": "整体画风 1 句",
  "line_art_en": "线条/轮廓/勾线",
  "color_palette_en": "主色与配色策略",
  "lighting_en": "光影/明暗/氛围光",
  "texture_en": "材质/笔触/平涂或厚涂",
  "style_tokens_en": ["≤8 个英文 token"],
  "avoid_from_ref_en": "参考图中应避免的元素（若有）",
  "notes_zh": "分析说明"
}}"""


def empty_ref_analysis(*, has_refs: bool = False) -> Dict[str, Any]:
    return {
        "reference_style_en": "",
        "line_art_en": "",
        "color_palette_en": "",
        "lighting_en": "",
        "texture_en": "",
        "style_tokens_en": [],
        "avoid_from_ref_en": "",
        "notes_zh": "无参考图，跳过参考图风格提取" if not has_refs else "",
        "skipped": not has_refs,
    }


def normalize_ref_analysis(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = empty_ref_analysis(has_refs=True)
    if not raw:
        return base
    for key in REF_ANALYSIS_KEYS:
        if key in raw and raw[key] is not None:
            base[key] = raw[key]
    tokens = base.get("style_tokens_en") or []
    if isinstance(tokens, str):
        tokens = [t.strip() for t in tokens.split(",") if t.strip()]
    base["style_tokens_en"] = list(dict.fromkeys(tokens))[:8]
    base["skipped"] = False
    return base


def merge_style_and_ref_analysis(
    style_analysis: Dict[str, Any],
    ref_analysis: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """融合绑定风格 + 参考图风格层 → fused_style（供 style_tokens / suffix 使用）。"""
    style = style_analysis or {}
    ref = normalize_ref_analysis(ref_analysis) if ref_analysis else empty_ref_analysis()

    trait_tags = list(style.get("trait_tags") or [])
    palette = list(style.get("color_palette") or [])

    tokens: List[str] = []
    for chunk in (
        style.get("style_summary_en") or "",
        style.get("image_positive_en") or "",
        ref.get("reference_style_en") or "",
        ref.get("line_art_en") or "",
        ref.get("color_palette_en") or "",
        ref.get("lighting_en") or "",
        ref.get("texture_en") or "",
    ):
        for part in str(chunk).replace(";", ",").split(","):
            w = part.strip()
            if w and len(w.split()) <= 6:
                tokens.append(w)
    for t in ref.get("style_tokens_en") or []:
        if t:
            tokens.append(str(t).strip())
    for t in trait_tags[:4]:
        tokens.append(str(t))

    tokens = list(dict.fromkeys(tokens))[:10]

    fused_negative = (style.get("image_negative_en") or "").strip()
    avoid_ref = (ref.get("avoid_from_ref_en") or "").strip()
    if avoid_ref:
        fused_negative = f"{fused_negative}, {avoid_ref}".strip(", ")

    sources = ["bound_style"]
    if not ref.get("skipped"):
        sources.append("reference_images")

    return {
        "render_class": style.get("render_class") or "live_action",
        "style_summary_zh": style.get("style_summary_zh") or "",
        "style_summary_en": style.get("style_summary_en") or "",
        "character_suffix_en": style.get("character_suffix_en") or "",
        "image_negative_en": fused_negative,
        "trait_tags": trait_tags,
        "color_palette": palette,
        "line_art_en": ref.get("line_art_en") or "",
        "color_palette_en": ref.get("color_palette_en") or "",
        "lighting_en": ref.get("lighting_en") or "",
        "texture_en": ref.get("texture_en") or "",
        "reference_style_en": ref.get("reference_style_en") or "",
        "style_tokens_en": tokens[:8],
        "sources": sources,
        "ref_notes_zh": ref.get("notes_zh") or "",
    }


def build_vision_extract_prompt(
    *,
    style_summary: str,
    user_message: str,
) -> str:
    return VISION_EXTRACT_USER_TEMPLATE.format(
        style_summary=style_summary[:1500],
        user_message=(user_message or "")[:2000],
    )
