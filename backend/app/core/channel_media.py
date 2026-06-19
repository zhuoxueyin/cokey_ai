"""渠道响应媒体字段归一化（url / b64_json / base64）"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.logging_config import get_logger

logger = get_logger()

UploadB64Fn = Callable[[str, str], Awaitable[Optional[str]]]


def _pick_b64(item: Any) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    for key in ("b64_json", "base64", "b64", "video_b64", "image_b64"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _pick_url(item: Any) -> Optional[str]:
    if isinstance(item, str) and item.strip():
        return item.strip()
    if isinstance(item, dict):
        for key in ("url", "video_url", "image_url", "cdn_url"):
            val = item.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _iter_data_items(response: Any) -> List[Any]:
    if not isinstance(response, dict):
        return []
    for key in ("data", "videos", "items", "results", "images"):
        val = response.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return [val]
    return []


async def _resolve_item_url(
    item: Any,
    *,
    upload_b64: UploadB64Fn,
    trace_id: str,
    default_ext: str,
) -> Optional[str]:
    url = _pick_url(item)
    if url:
        return url
    b64 = _pick_b64(item)
    if not b64:
        return None
    uploaded = await upload_b64(b64, default_ext)
    if uploaded:
        return uploaded
    if b64.startswith("data:"):
        return b64
    mime = "image/png" if default_ext in (".png", ".jpg", ".webp") else "video/mp4"
    return f"data:{mime};base64,{b64}"


async def enrich_parsed_result(
    parsed: Dict[str, Any],
    raw_response: Any,
    category: str,
    *,
    upload_b64: UploadB64Fn,
    trace_id: str = "",
) -> Dict[str, Any]:
    """补全 parse 结果：ConfigEngine 等路径未处理 b64 时从 raw 响应提取并上传。"""
    if not isinstance(parsed, dict):
        return parsed

    out = dict(parsed)
    resp = raw_response if isinstance(raw_response, dict) else {}
    items = _iter_data_items(resp)

    if category == "image" or out.get("type") in ("image", "image_edits"):
        images: List[Dict[str, Any]] = list(out.get("images") or [])
        if not images and items:
            for item in items:
                url = await _resolve_item_url(
                    item, upload_b64=upload_b64, trace_id=trace_id, default_ext=".png"
                )
                if url:
                    revised = item.get("revised_prompt", "") if isinstance(item, dict) else ""
                    images.append({"url": url, "revised_prompt": revised})
        elif images:
            fixed: List[Dict[str, Any]] = []
            for img in images:
                if isinstance(img, dict) and img.get("url"):
                    fixed.append(img)
                    continue
                url = await _resolve_item_url(
                    img, upload_b64=upload_b64, trace_id=trace_id, default_ext=".png"
                )
                if url:
                    fixed.append({"url": url, "revised_prompt": ""})
            images = fixed
        if images:
            out["type"] = "image"
            out["images"] = images
            out["count"] = len(images)

    if category == "video" or out.get("type") in ("video", "video_image"):
        videos: List[Dict[str, Any]] = list(out.get("videos") or [])
        if not videos and items:
            for item in items:
                url = await _resolve_item_url(
                    item, upload_b64=upload_b64, trace_id=trace_id, default_ext=".mp4"
                )
                if url:
                    revised = item.get("revised_prompt", "") if isinstance(item, dict) else ""
                    videos.append({"url": url, "revised_prompt": revised})
        elif videos:
            fixed_v: List[Dict[str, Any]] = []
            for vid in videos:
                if isinstance(vid, dict) and vid.get("url"):
                    fixed_v.append(vid)
                    continue
                url = await _resolve_item_url(
                    vid, upload_b64=upload_b64, trace_id=trace_id, default_ext=".mp4"
                )
                if url:
                    fixed_v.append({"url": url, "revised_prompt": ""})
            videos = fixed_v
        if videos:
            out["type"] = "video"
            out["videos"] = videos
            out["count"] = len(videos)

    return out
