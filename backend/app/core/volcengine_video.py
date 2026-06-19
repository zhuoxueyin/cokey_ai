"""火山引擎视频生成 — 多模态 content[] 协议（文/图/视频/音频）。"""
from __future__ import annotations

# 统一协议槽位：同一 HTTP 端点，按 content 数组组合多模态输入
VOLCENGINE_VIDEO_MULTIMODAL_SLOT = "volcengine.video.multimodal"

# 旧槽位别名（兼容历史渠道配置）
VOLCENGINE_VIDEO_SLOT_ALIASES = frozenset({
    "volcengine.video.task",
    VOLCENGINE_VIDEO_MULTIMODAL_SLOT,
})

SUPPORTED_MODALITIES = ("text", "image", "video", "audio")


def normalize_volcengine_video_slot(protocol_slot: str | None) -> str:
    if not protocol_slot:
        return VOLCENGINE_VIDEO_MULTIMODAL_SLOT
    slot = protocol_slot.strip()
    if slot == "volcengine.video.task":
        return VOLCENGINE_VIDEO_MULTIMODAL_SLOT
    return slot


def is_volcengine_video_slot(protocol_slot: str | None) -> bool:
    if not protocol_slot:
        return False
    return normalize_volcengine_video_slot(protocol_slot) == VOLCENGINE_VIDEO_MULTIMODAL_SLOT


def is_volcengine_video_endpoint(
    endpoint_config: dict | None,
    *,
    category: str = "",
) -> bool:
    if not endpoint_config:
        return category == "video"
    ep_type = endpoint_config.get("type", "")
    if ep_type in ("video", "video_image"):
        return True
    slot = endpoint_config.get("protocol_slot") or ""
    if is_volcengine_video_slot(slot):
        return True
    path = str(endpoint_config.get("endpoint", "")).lower()
    return "contents/generations/tasks" in path
