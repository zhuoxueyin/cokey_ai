"""APIYI gpt-image-2-all / gpt-image-2-vip 对话式生图/改图（Chat Completions）"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.core.cdn import extract_url_from_image_item
from app.core.image_size_spec import get_presets

# ![alt](url) — 支持 https 与 data:image/...;base64,...
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# gpt-image-2-all 不支持 size 像素参数，比例需写入提示词（官方示例：横版 16:9 电影画幅）
RATIO_ORIENTATION: Dict[str, str] = {
    "1:1": "方形",
    "3:2": "横版",
    "2:3": "竖版",
    "4:3": "横版",
    "3:4": "竖版",
    "5:4": "横版",
    "4:5": "竖版",
    "16:9": "横版",
    "9:16": "竖版",
    "2:1": "横版",
    "1:2": "竖版",
    "3:1": "超宽横版",
    "1:3": "超窄竖版",
    "21:9": "超宽横版",
    "9:21": "超窄竖版",
}

CINEMATIC_LANDSCAPE = frozenset({"16:9", "21:9", "2:1", "3:1"})
CINEMATIC_PORTRAIT = frozenset({"9:16", "9:21", "1:2", "1:3"})

RESOLUTION_HINT: Dict[str, str] = {
    "2k": "高清",
    "4k": "超高清",
}


def is_apiyi_chat_image_model(channel_model_id: str) -> bool:
    return "gpt-image-2-all" in (channel_model_id or "").lower()


def is_apiyi_gemini_image_model(channel_model_id: str) -> bool:
    """APIYI Nano Banana / Gemini 图像模型（对话式 chat/completions）。"""
    mid = (channel_model_id or "").lower()
    return ("gemini" in mid and "image" in mid) or "banana" in mid


def is_apiyi_conversational_image_model(channel_model_id: str) -> bool:
    """APIYI 对话式生图模型（gpt-image-2 / Gemini Banana 均走 chat/completions）。"""
    mid = (channel_model_id or "").lower()
    return (
        "gpt-image-2-all" in mid
        or "gpt-image-2-vip" in mid
        or is_apiyi_gemini_image_model(channel_model_id)
    )


def _resolve_aspect_ratio(params: Dict[str, Any], channel_model_id: str = "") -> str:
    """从 aspect_ratio / ratio / size 解析画幅比例"""
    for key in ("aspect_ratio", "ratio"):
        raw = params.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text and text.lower() != "auto":
            return text

    size = str(params.get("size") or "").strip().lower()
    if size and size != "auto" and "x" in size:
        for preset in get_presets(channel_model_id=channel_model_id):
            if preset.size == size:
                return preset.aspect_ratio
        # 兜底：按宽高比推断常见值
        try:
            w, h = [int(x) for x in size.split("x", 1)]
            if w > h:
                ratio = w / h
                if abs(ratio - 16 / 9) < 0.08:
                    return "16:9"
                if abs(ratio - 4 / 3) < 0.08:
                    return "4:3"
                return "3:2"
            if h > w:
                ratio = h / w
                if abs(ratio - 16 / 9) < 0.08:
                    return "9:16"
                if abs(ratio - 4 / 3) < 0.08:
                    return "3:4"
                return "2:3"
            return "1:1"
        except (ValueError, ZeroDivisionError):
            pass
    return ""


def build_apiyi_aspect_hint(params: Dict[str, Any], channel_model_id: str = "") -> str:
    """
    生成 gpt-image-2-all 专用画幅提示片段。
    示例：横版 16:9 电影画幅 / 竖版 9:16 竖屏画幅 / 方形 1:1
    """
    aspect = _resolve_aspect_ratio(params, channel_model_id)
    if not aspect:
        return ""

    parts: List[str] = []
    orientation = RATIO_ORIENTATION.get(aspect)
    if orientation:
        parts.append(orientation)
    parts.append(aspect)

    if aspect in CINEMATIC_LANDSCAPE:
        parts.append("电影画幅")
    elif aspect in CINEMATIC_PORTRAIT:
        parts.append("竖屏画幅")

    resolution = str(params.get("resolution") or params.get("clarity") or "").strip().lower()
    if resolution in RESOLUTION_HINT:
        parts.append(RESOLUTION_HINT[resolution])

    return " ".join(parts)


def resolve_image_count(params: Dict[str, Any], *, max_count: int = 4) -> int:
    """解析任务参数中的出图数量（n / count），与前端 1–4 张选项对齐。"""
    raw = params.get("n", params.get("count", 1))
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = 1
    return max(1, min(n, max_count))


def enrich_prompt_with_count_hint(prompt: str, params: Dict[str, Any]) -> str:
    """gpt-image-2-all 对话式端点无 n 字段，将张数要求写入 prompt。"""
    n = resolve_image_count(params)
    if n <= 1:
        return prompt
    text = (prompt or "").strip()
    markers = (f"{n}张", f"{n} 张", f"共{n}张")
    if any(m in text for m in markers):
        return text or f"请生成{n}张图片"
    hint = f"请生成{n}张不同变体的图片"
    return f"{hint}，{text}" if text else hint


def enrich_prompt_for_apiyi_chat(
    prompt: str,
    params: Dict[str, Any],
    channel_model_id: str,
) -> str:
    """
    对话式端点画幅/尺寸写入 prompt（不传 size 字段）。
    - all：横版 16:9 电影画幅 等语义 hint
    - vip：优先写入 30 档像素值（如 1280x720），否则 fallback 到 aspect hint
    """
    from app.core.apiyi_vip_image import is_apiyi_vip_image_model, normalize_vip_size

    text = (prompt or "").strip()
    if is_apiyi_vip_image_model(channel_model_id):
        vip_size = normalize_vip_size(params, channel_model_id)
        if vip_size and vip_size != "auto":
            if vip_size in text:
                return text or vip_size
            return f"{vip_size}，{text}" if text else vip_size
    sized = enrich_prompt_with_size_hint(text, params, channel_model_id)
    return enrich_prompt_with_count_hint(sized, params)


def enrich_prompt_with_size_hint(
    prompt: str,
    params: Dict[str, Any],
    channel_model_id: str = "",
) -> str:
    """
    gpt-image-2-all 对话式端点：不支持像素 size，将画幅写入提示词首部。
    仅由 ApiyiAdapter / build_apiyi_chat_image_body 调用。
    """
    text = (prompt or "").strip()
    hint = build_apiyi_aspect_hint(params, channel_model_id)
    if not hint:
        return text or "生成一张图片"

    aspect = _resolve_aspect_ratio(params, channel_model_id)
    # 用户已在提示词中写明比例时，避免重复拼接
    if aspect and aspect in text and (not RATIO_ORIENTATION.get(aspect) or RATIO_ORIENTATION[aspect] in text):
        return text

    # 官方示例风格：画幅描述在前，主体描述在后
    if text:
        return f"{hint}，{text}"
    return hint


def collect_reference_image_urls(params: Dict[str, Any]) -> List[str]:
    """收集参考图 URL（支持 images / image，多图放在同一条 user 消息）"""
    urls: List[str] = []
    raw_items: List[Any] = []
    if params.get("images"):
        val = params["images"]
        raw_items.extend(val if isinstance(val, list) else [val])
    elif params.get("image"):
        val = params["image"]
        raw_items.extend(val if isinstance(val, list) else [val])

    for item in raw_items[:16]:
        url = extract_url_from_image_item(item) if not isinstance(item, str) else item
        if isinstance(url, str) and url.strip():
            urls.append(url.strip())
    return urls


def build_apiyi_chat_image_body(
    channel_params: Dict[str, Any],
    channel_model_id: str,
) -> Dict[str, Any]:
    """
    构建 POST /v1/chat/completions 请求体。
    - 纯文本 messages → 文生图（画幅写在 prompt，不传 size 字段）
    - user 消息含 image_url → 带参考图改图
    """
    prompt = enrich_prompt_for_apiyi_chat(
        str(channel_params.get("prompt") or ""),
        channel_params,
        channel_model_id,
    )
    ref_urls = collect_reference_image_urls(channel_params)

    if ref_urls:
        content: List[Dict[str, Any]] = []
        if prompt:
            content.append({"type": "text", "text": prompt})
        for url in ref_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        messages = [{"role": "user", "content": content}]
    else:
        messages = [{"role": "user", "content": prompt or "生成一张图片"}]

    body: Dict[str, Any] = {
        "model": channel_model_id or "gpt-image-2-all",
        "messages": messages,
        "stream": False,
    }
    if "temperature" in channel_params:
        body["temperature"] = float(channel_params["temperature"])
    return body


def extract_images_from_markdown(content: str) -> List[Dict[str, str]]:
    """从 choices[0].message.content 提取 Markdown 图片链接"""
    if not content:
        return []
    images: List[Dict[str, str]] = []
    seen: set[str] = set()
    for match in MARKDOWN_IMAGE_RE.finditer(content):
        url = (match.group(1) or "").strip()
        if url and url not in seen:
            seen.add(url)
            images.append({"url": url, "revised_prompt": ""})
    return images
