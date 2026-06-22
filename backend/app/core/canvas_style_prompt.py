"""画布 / 工作台 image/video：绑定风格 → 合并完整风格参考到 prompt。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _positive_negative_from_style(style_doc: Dict[str, Any], node_type: str) -> tuple[str, str]:
    mp = style_doc.get("model_prompts") or {}
    proto = style_doc.get("model_protocol") or {}
    if node_type == "video":
        block = proto.get("video") or {}
        positive = (block.get("positive_en") or mp.get("video_positive_en") or "").strip()
        negative = (block.get("negative_en") or mp.get("video_negative_en") or "").strip()
    else:
        block = proto.get("image") or {}
        positive = (block.get("positive_en") or mp.get("image_positive_en") or "").strip()
        negative = (block.get("negative_en") or mp.get("image_negative_en") or "").strip()
    return positive, negative


def _append_unique(parts: List[str], text: str) -> None:
    t = (text or "").strip()
    if not t:
        return
    blob = "\n\n".join(parts)
    if t in blob:
        return
    parts.append(t)


def build_full_style_reference(style_doc: Dict[str, Any], node_type: str) -> Tuple[str, str]:
    """
    构建完整风格参考文本（正向）与 negative_prompt。
    优先 style_description_md 全文，并补充 model_prompts / visual / protocol 字段。
    """
    if node_type not in ("image", "video"):
        return "", ""

    positive, negative = _positive_negative_from_style(style_doc, node_type)
    parts: List[str] = []

    name = (style_doc.get("name") or "").strip()
    style_id = (style_doc.get("style_id") or "").strip()
    header = f"Visual Style: {name} ({style_id})" if name else f"Visual Style: {style_id}"
    render_class = (style_doc.get("render_class") or "").strip()
    if render_class:
        header = f"{header}\nRender class: {render_class}"
    _append_unique(parts, header)

    md = (style_doc.get("style_description_md") or "").strip()
    if md:
        _append_unique(parts, md)
    else:
        mp = style_doc.get("model_prompts") or {}
        visual = style_doc.get("visual") or {}
        proto = style_doc.get("model_protocol") or {}
        summary_bits = [
            mp.get("style_summary_zh") or "",
            mp.get("style_summary_en") or "",
        ]
        summary = "\n".join(s for s in summary_bits if s).strip()
        if summary:
            _append_unique(parts, f"Style summary:\n{summary}")

        traits = list(dict.fromkeys((proto.get("trait_tags") or []) + (style_doc.get("genre_tags") or [])))
        if traits:
            _append_unique(parts, f"Trait tags: {', '.join(traits)}")

        refs = visual.get("reference_films") or []
        if refs:
            _append_unique(parts, "Reference works:\n" + "\n".join(f"- {r}" for r in refs))

        palette = visual.get("color_palette") or []
        if palette:
            _append_unique(parts, f"Color palette: {', '.join(palette)}")

        if visual.get("lighting"):
            _append_unique(parts, f"Lighting: {visual['lighting']}")
        if visual.get("texture"):
            _append_unique(parts, f"Texture: {visual['texture']}")
        if mp.get("character_suffix_en"):
            _append_unique(parts, f"Character suffix: {mp['character_suffix_en']}")
        if mp.get("scene_suffix_en"):
            _append_unique(parts, f"Scene suffix: {mp['scene_suffix_en']}")

    mp = style_doc.get("model_prompts") or {}
    if node_type == "video":
        if mp.get("video_prompt") and mp["video_prompt"] not in "\n\n".join(parts):
            _append_unique(parts, f"Video prompt reference:\n{mp['video_prompt']}")
        if positive:
            _append_unique(parts, f"Video positive prompt:\n{positive}")
    else:
        if mp.get("image_prompt") and mp["image_prompt"] not in "\n\n".join(parts):
            _append_unique(parts, f"Image prompt reference:\n{mp['image_prompt']}")
        if positive:
            _append_unique(parts, f"Image positive prompt:\n{positive}")

    return "\n\n".join(parts).strip(), negative


def merge_style_into_params(
    params: Dict[str, Any],
    *,
    style_doc: Optional[Dict[str, Any]],
    node_type: str,
) -> Dict[str, Any]:
    """用户 prompt 在前，完整风格参考在后。"""
    if not style_doc or node_type not in ("image", "video"):
        return params

    style_text, negative = build_full_style_reference(style_doc, node_type)
    out = dict(params)
    user_prompt = (out.get("prompt") or "").strip()

    if style_text:
        out["prompt"] = (
            f"{user_prompt}\n\n[Visual Style Reference]\n{style_text}"
            if user_prompt
            else style_text
        )

    if negative and not (out.get("negative_prompt") or "").strip():
        out["negative_prompt"] = negative

    return out


async def apply_canvas_style_preset(
    params: Dict[str, Any],
    *,
    style_preset_id: Optional[str],
    node_type: str,
) -> Dict[str, Any]:
    if not style_preset_id or node_type not in ("image", "video"):
        return params
    from app.services.drama_style_service import get_drama_style_service

    style = await get_drama_style_service().get_by_style_id(style_preset_id)
    if not style or style.get("status") not in (None, "published"):
        return params
    return merge_style_into_params(params, style_doc=style, node_type=node_type)
