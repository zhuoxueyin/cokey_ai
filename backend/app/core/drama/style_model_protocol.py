"""StyleSpec 模型协议 v1：统一图/视频/角色/场景提示词与特点标签。"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

_RENDER_GRADIENTS = [
    "linear-gradient(135deg,#667eea 0%,#764ba2 100%)",
    "linear-gradient(135deg,#f093fb 0%,#f5576c 100%)",
    "linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)",
    "linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)",
    "linear-gradient(135deg,#fa709a 0%,#fee140 100%)",
    "linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)",
    "linear-gradient(135deg,#ff9a9e 0%,#fecfef 100%)",
    "linear-gradient(135deg,#30cfd0 0%,#330867 100%)",
]

_TRAIT_BY_RENDER = {
    "live_action": ["真人实拍", "电影质感"],
    "illustration_2d": ["2D插画", "动漫美学"],
    "render_3d": ["3D渲染", "CGI质感"],
}


def preview_gradient(style_id: str) -> str:
    idx = int(hashlib.md5(style_id.encode()).hexdigest()[:8], 16) % len(_RENDER_GRADIENTS)
    return _RENDER_GRADIENTS[idx]


def build_model_protocol(doc: Dict[str, Any]) -> Dict[str, Any]:
    """从 StyleSpec 文档生成/补全 model_protocol。"""
    style_id = doc.get("style_id") or ""
    mp = doc.get("model_prompts") or {}
    visual = doc.get("visual") or {}
    render_class = doc.get("render_class") or "live_action"
    genre_tags: List[str] = list(doc.get("genre_tags") or [])
    trait_tags = list(dict.fromkeys(_TRAIT_BY_RENDER.get(render_class, []) + genre_tags))

    cover_asset_id = doc.get("cover_asset_id")
    ref_images = doc.get("reference_images") or []
    cover_url = None
    if ref_images and isinstance(ref_images[0], dict):
        cover_url = ref_images[0].get("url")
    if not cover_url and style_id:
        from app.core.drama.style_enrichment import style_cover_url
        cover_url = style_cover_url(style_id)

    return {
        "version": "1.0",
        "render_class": render_class,
        "trait_tags": trait_tags,
        "summary": {
            "zh": mp.get("style_summary_zh") or doc.get("name") or "",
            "en": mp.get("style_summary_en") or "",
        },
        "image": {
            "positive_en": mp.get("image_positive_en") or "",
            "negative_en": mp.get("image_negative_en") or "",
        },
        "video": {
            "positive_en": mp.get("video_positive_en") or "",
            "negative_en": mp.get("video_negative_en") or "",
        },
        "character": {
            "suffix_en": mp.get("character_suffix_en") or "",
        },
        "scene": {
            "suffix_en": mp.get("scene_suffix_en") or "",
        },
        "visual": {
            "lighting": visual.get("lighting") or "",
            "texture": visual.get("texture") or "",
            "color_palette": visual.get("color_palette") or [],
        },
        "preview": {
            "gradient": preview_gradient(style_id),
            "cover_asset_id": cover_asset_id,
            "cover_url": cover_url,
        },
    }


def merge_protocol_into_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["model_protocol"] = build_model_protocol(doc)
    return doc
