"""StyleSpec v1 默认字段生成（新建风格时用；运营在风格广场编辑后以 DB 为准）。"""
from __future__ import annotations

from typing import Any, Dict, List, Literal

from app.core.drama.style_model_protocol import merge_protocol_into_doc
from app.core.drama.style_enrichment import style_cover_url, tags_to_en_prompt

RenderClass = Literal["live_action", "illustration_2d", "render_3d"]

_RENDER_CLASS_EN: Dict[RenderClass, str] = {
    "live_action": "cinematic live-action photography, realistic film still",
    "illustration_2d": "2D illustration, hand-drawn anime aesthetic, flat color",
    "render_3d": "3D rendered, CGI, high quality 3D graphics",
}

_NEGATIVE_COMMON = (
    "blurry, distorted face, extra fingers, bad anatomy, watermark, text, logo, "
    "low quality, deformed"
)


def build_style_spec_document(fields: Dict[str, Any]) -> Dict[str, Any]:
    """从基础字段生成 StyleSpec v1 骨架（draft）；详细内容由风格广场 Markdown 编辑覆盖。"""
    style_id = fields["style_id"]
    name = fields["name"]
    rc: RenderClass = fields.get("render_class") or "live_action"
    rc_en = _RENDER_CLASS_EN[rc]
    tags: List[str] = list(fields.get("genre_tags") or [])
    tags_str = ", ".join(tags)
    tag_en = tags_to_en_prompt(tags)

    style_summary_zh = f"{name}风格，视觉特征：{tags_str}，适合竖屏短剧与 AIGC 出图。"
    style_summary_en = f"{name}, {rc_en}, {tag_en}, vertical 9:16 short drama visual style"

    image_positive = (
        f"{rc_en}, {name}, {tag_en}, masterpiece, best quality, "
        f"professional composition, cinematic lighting, sharp focus, vertical 9:16, 8k detail"
    )
    video_positive = (
        f"{rc_en}, {name}, {tag_en}, stable subject, smooth cinematic motion, "
        f"shallow depth of field, vertical 9:16, film look"
    )
    cover = fields.get("cover_url") or style_cover_url(style_id)

    if rc == "live_action":
        narrative_pace = "fast"
        lighting = "cinematic_natural"
        texture = "cinematic_realistic"
    elif rc == "illustration_2d":
        narrative_pace = "medium"
        lighting = "soft_illustration"
        texture = "illustration_flat"
    else:
        narrative_pace = "medium"
        lighting = "studio_3d"
        texture = "3d_render"

    doc = {
        "spec_version": "1.0",
        "style_id": style_id,
        "name": name,
        "origin": fields.get("origin", "manual"),
        "render_class": rc,
        "genre_tags": tags,
        "narrative": {
            "pace": narrative_pace,
            "hook_style": "3s_conflict",
            "dialogue_density": "short_punchy",
            "emotion_curve": "",
        },
        "visual": {
            "color_palette": [],
            "lighting": lighting,
            "texture": texture,
            "reference_films": [],
        },
        "camera_defaults": {
            "preferred_shot_sizes": ["medium_close", "close_up"],
            "movement_bias": ["slow_push_in", "static_tension"],
            "avoid": ["complex crowd scene", "extreme wide distortion"],
        },
        "model_prompts": {
            "style_summary_zh": style_summary_zh,
            "style_summary_en": style_summary_en,
            "image_positive_en": image_positive,
            "image_negative_en": _NEGATIVE_COMMON,
            "video_positive_en": video_positive,
            "video_negative_en": _NEGATIVE_COMMON + ", rapid zoom, morphing face, shaky cam",
            "character_suffix_en": f"consistent character design, {rc_en}",
            "scene_suffix_en": f"environment matching {name} aesthetic",
        },
        "locked_tokens": [],
        "reference_images": [{"url": cover, "role": "cover"}],
        "status": "draft",
    }
    return merge_protocol_into_doc(doc)
