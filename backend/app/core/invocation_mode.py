"""任务调用模式（InvocationMode）— 与 category 解耦的业务语义层。"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class InvocationMode(str, Enum):
    TEXT_CHAT = "text_chat"
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


ALL_INVOCATION_MODES = [m.value for m in InvocationMode]

# category → 默认可用模式（binding 未声明 supported_modes 时使用）
CATEGORY_DEFAULT_MODES: Dict[str, list[str]] = {
    "text": [InvocationMode.TEXT_CHAT.value],
    "image": [
        InvocationMode.TEXT_TO_IMAGE.value,
        InvocationMode.IMAGE_TO_IMAGE.value,
    ],
    "video": [
        InvocationMode.TEXT_TO_VIDEO.value,
        InvocationMode.IMAGE_TO_VIDEO.value,
    ],
}


def has_reference_images(params: Dict[str, Any]) -> bool:
    """是否携带参考图（image / images）。"""
    if params.get("image"):
        img_val = params["image"]
        if isinstance(img_val, list) and len(img_val) > 0:
            return True
        if isinstance(img_val, str) and img_val.strip():
            return True
    if params.get("images"):
        imgs_val = params["images"]
        if isinstance(imgs_val, list) and len(imgs_val) > 0:
            return True
    return False


def has_reference_video(params: Dict[str, Any]) -> bool:
    """是否携带参考视频/图（video / videos / image 用于图生视频）。"""
    if has_reference_images(params):
        return True
    for key in ("video", "videos"):
        val = params.get(key)
        if isinstance(val, list) and len(val) > 0:
            return True
        if isinstance(val, str) and val.strip():
            return True
    return False


def resolve_invocation_mode(
    category: str,
    params: Dict[str, Any],
    *,
    override: Optional[str] = None,
) -> str:
    """
    解析本次调用的 InvocationMode。
    override: params.invocation_mode 或调用方显式传入。
    """
    explicit = override or params.get("invocation_mode")
    if explicit and explicit in ALL_INVOCATION_MODES:
        return explicit

    cat = (category or "").lower()
    if cat == "text":
        return InvocationMode.TEXT_CHAT.value
    if cat == "image":
        return (
            InvocationMode.IMAGE_TO_IMAGE.value
            if has_reference_images(params)
            else InvocationMode.TEXT_TO_IMAGE.value
        )
    if cat == "video":
        return (
            InvocationMode.IMAGE_TO_VIDEO.value
            if has_reference_video(params)
            else InvocationMode.TEXT_TO_VIDEO.value
        )
    return InvocationMode.TEXT_CHAT.value


def mode_to_legacy_endpoint_type(mode: str, category: str = "") -> str:
    """InvocationMode → 旧 endpoint_type（适配器兼容）。"""
    mapping = {
        InvocationMode.TEXT_CHAT.value: "chat" if category == "text" else "text",
        InvocationMode.TEXT_TO_IMAGE.value: "image",
        InvocationMode.IMAGE_TO_IMAGE.value: "image_edits",
        InvocationMode.TEXT_TO_VIDEO.value: "video",
        InvocationMode.IMAGE_TO_VIDEO.value: "video_image",
    }
    return mapping.get(mode, category or "text")
