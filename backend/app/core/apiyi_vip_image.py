"""APIYI gpt-image-2-vip 文生图（/v1/images/generations）"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.core.image_size_spec import get_presets
from app.core.weelinking_image import sanitize_image_prompt

# 官方 30 档 + auto（OpenAPI enum）
VIP_ALLOWED_SIZES = frozenset({
    "auto",
    "1280x1280", "848x1280", "1280x848", "960x1280", "1280x960",
    "1024x1280", "1280x1024", "720x1280", "1280x720", "1280x544",
    "2048x2048", "1360x2048", "2048x1360", "1536x2048", "2048x1536",
    "1632x2048", "2048x1632", "1152x2048", "2048x1152", "2048x864",
    "2880x2880", "2336x3520", "3520x2336", "2480x3312", "3312x2480",
    "2560x3216", "3216x2560", "2160x3840", "3840x2160", "3840x1632",
})

# 平台画幅 (aspect_ratio, resolution) → VIP 官方 size
VIP_PRESET_MAP: Dict[Tuple[str, str], str] = {
    ("1:1", "1k"): "1280x1280",
    ("1:1", "2k"): "2048x2048",
    ("1:1", "4k"): "2880x2880",
    ("3:2", "1k"): "1280x848",
    ("3:2", "2k"): "2048x1360",
    ("3:2", "4k"): "3520x2336",
    ("2:3", "1k"): "848x1280",
    ("2:3", "2k"): "1360x2048",
    ("2:3", "4k"): "2336x3520",
    ("4:3", "1k"): "1280x960",
    ("4:3", "2k"): "2048x1536",
    ("4:3", "4k"): "3312x2480",
    ("3:4", "1k"): "960x1280",
    ("3:4", "2k"): "1536x2048",
    ("3:4", "4k"): "2480x3312",
    ("5:4", "1k"): "1280x1024",
    ("5:4", "2k"): "2048x1632",
    ("5:4", "4k"): "3216x2560",
    ("4:5", "1k"): "1024x1280",
    ("4:5", "2k"): "1632x2048",
    ("4:5", "4k"): "2560x3216",
    ("16:9", "1k"): "1280x720",
    ("16:9", "2k"): "2048x1152",
    ("16:9", "4k"): "3840x2160",
    ("9:16", "1k"): "720x1280",
    ("9:16", "2k"): "1152x2048",
    ("9:16", "4k"): "2160x3840",
    ("2:1", "1k"): "1280x544",
    ("2:1", "2k"): "2048x864",
    ("2:1", "4k"): "3840x1632",
    ("1:2", "1k"): "720x1280",
    ("1:2", "2k"): "1152x2048",
    ("1:2", "4k"): "2160x3840",
    ("3:1", "1k"): "1280x544",
    ("3:1", "2k"): "2048x864",
    ("3:1", "4k"): "3840x1632",
    ("1:3", "1k"): "720x1280",
    ("1:3", "2k"): "1152x2048",
    ("1:3", "4k"): "2160x3840",
    ("21:9", "1k"): "1280x544",
    ("21:9", "2k"): "2048x864",
    ("21:9", "4k"): "3840x1632",
    ("9:21", "1k"): "720x1280",
    ("9:21", "2k"): "1152x2048",
    ("9:21", "4k"): "2160x3840",
}


def is_apiyi_vip_image_model(channel_model_id: str) -> bool:
    return "gpt-image-2-vip" in (channel_model_id or "").lower()


def _normalize_size_token(size: str) -> str:
    text = (size or "").strip().lower()
    text = text.replace("×", "x").replace(" ", "")
    return text


def normalize_vip_size(params: Dict[str, Any], channel_model_id: str = "") -> str:
    """
    解析 VIP size：优先使用已在 30 档内的像素值，否则按 aspect_ratio+resolution 映射，最后 auto。
  不接受 aspect_ratio 作为 API 字段，仅用于换算。
    """
    raw = _normalize_size_token(str(params.get("size") or ""))
    if raw in VIP_ALLOWED_SIZES:
        return raw

    aspect = str(params.get("aspect_ratio") or params.get("ratio") or "").strip()
    if aspect.lower() == "auto":
        aspect = ""
    resolution = str(params.get("resolution") or params.get("clarity") or "2k").strip().lower()

    if aspect and resolution:
        mapped = VIP_PRESET_MAP.get((aspect, resolution))
        if mapped:
            return mapped

    if raw and "x" in raw:
        for preset in get_presets(channel_model_id=channel_model_id):
            if preset.size == raw:
                mapped = VIP_PRESET_MAP.get((preset.aspect_ratio, preset.clarity))
                if mapped:
                    return mapped

    return "auto"


def build_apiyi_vip_generations_body(
    channel_params: Dict[str, Any],
    channel_model_id: str,
) -> Dict[str, Any]:
    """
    POST /v1/images/generations
    仅 model + prompt + size + response_format；禁止 quality / n / aspect_ratio。
    """
    prompt = sanitize_image_prompt(str(channel_params.get("prompt") or ""))
    size = normalize_vip_size(channel_params, channel_model_id)

    body: Dict[str, Any] = {
        "model": channel_model_id or "gpt-image-2-vip",
        "prompt": prompt or "生成一张图片",
        "size": size,
        "response_format": "url",
    }
    return body


def build_apiyi_vip_edits_form_fields(
    channel_params: Dict[str, Any],
    channel_model_id: str,
) -> Dict[str, Any]:
    """
    POST /v1/images/edits (multipart/form-data)

    官方仅接受：model, prompt, image(文件), size, response_format。
    禁止 quality / n / background / output_format / output_compression 等 Weelinking 字段。
    """
    prompt = sanitize_image_prompt(str(channel_params.get("prompt") or ""))
    size = normalize_vip_size(channel_params, channel_model_id)
    rf = str(channel_params.get("response_format") or "url").strip().lower()
    if rf not in ("url", "b64_json"):
        rf = "url"

    return {
        "model": channel_model_id or "gpt-image-2-vip",
        "prompt": prompt or "编辑图片",
        "size": size,
        "response_format": rf,
    }


# APIYI VIP 多图融合：重复传同名 image 字段（非 images[]）
APIYI_VIP_EDITS_IMAGE_FIELD = "image"
