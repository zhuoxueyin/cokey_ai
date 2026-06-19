"""Body 入参解析 — source 与取值配置分离，兼容旧 value_type/value 格式。"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.cdn import extract_url_from_image_item, require_cdn_url
from app.core.logging_config import get_logger

logger = get_logger()

# 取值来源（与前端 bodyParamPresets 一致）
SOURCE_LITERAL = "literal"
SOURCE_TASK_PARAM = "task_param"
SOURCE_BUILTIN = "builtin"
SOURCE_IMAGE_URLS = "image_urls"
SOURCE_CHAT_MESSAGES = "chat_messages"

BUILTIN_CHANNEL_MODEL_ID = "channel_model_id"
BUILTIN_CHANNEL_CODE = "channel_code"
BUILTIN_TRACE_ID = "trace_id"

VALID_BUILTINS = frozenset({
    BUILTIN_CHANNEL_MODEL_ID,
    BUILTIN_CHANNEL_CODE,
    BUILTIN_TRACE_ID,
})


def normalize_body_param(item: Dict[str, Any]) -> Dict[str, Any]:
    """统一为新格式；旧 value_type + value 自动迁移。"""
    if not isinstance(item, dict):
        return {}
    key = (item.get("key") or "").strip()
    if not key:
        return {}

    source = (item.get("source") or "").strip().lower()
    if source:
        return {**item, "key": key, "source": source}

    value_type = (item.get("value_type") or SOURCE_TASK_PARAM).lower()
    raw_value = item.get("value") or ""

    if value_type in ("fixed", "static", "constant"):
        return {
            **item,
            "key": key,
            "source": SOURCE_LITERAL,
            "literal": raw_value,
        }
    if value_type in ("image", "images", "picture"):
        return {
            **item,
            "key": key,
            "source": SOURCE_IMAGE_URLS,
            "param": raw_value or "images",
        }
    if key == "messages":
        return {**item, "key": key, "source": SOURCE_CHAT_MESSAGES}
    if raw_value in VALID_BUILTINS or (key == "model" and raw_value in ("", "model")):
        builtin = raw_value if raw_value in VALID_BUILTINS else BUILTIN_CHANNEL_MODEL_ID
        return {**item, "key": key, "source": SOURCE_BUILTIN, "builtin": builtin}
    if raw_value in ("model",) and key == "model":
        return {
            **item,
            "key": key,
            "source": SOURCE_BUILTIN,
            "builtin": BUILTIN_CHANNEL_MODEL_ID,
        }
    return {
        **item,
        "key": key,
        "source": SOURCE_TASK_PARAM,
        "param": raw_value or key,
    }


def _smart_parse_literal(raw: str) -> Any:
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        if text[0] in "{[":
            return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        pass
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _get_nested_field(data: Dict[str, Any], path: str) -> Any:
    if not path or not data:
        return None
    parts = path.split(".")
    cur: Any = data
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _build_chat_messages(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt_text = params.get("prompt") or params.get("positive_prompt") or ""
    image_list = params.get("images") or params.get("image") or []
    has_images = bool(image_list) and (
        isinstance(image_list, list) and len(image_list) > 0
        or isinstance(image_list, str) and str(image_list).strip()
    )

    if not prompt_text and not has_images:
        return []

    if has_images:
        content: List[Dict[str, Any]] = []
        if prompt_text:
            content.append({"type": "text", "text": prompt_text})
        urls = image_list if isinstance(image_list, list) else [image_list]
        for idx, img_item in enumerate(urls):
            img_url = extract_url_from_image_item(img_item) or str(img_item)
            if img_url:
                cdn_url = require_cdn_url(img_url, label=f"messages-image[{idx}]")
                content.append({"type": "image_url", "image_url": {"url": cdn_url}})
    else:
        content = prompt_text  # type: ignore[assignment]

    return [{"role": "user", "content": content}]


def resolve_body_param_item(
    item: Dict[str, Any],
    params: Dict[str, Any],
    *,
    model_id: str = "",
    channel_code: str = "",
    trace_id: str = "",
) -> tuple[str, Any] | None:
    """解析单条入参，返回 (body_key, value) 或 None（跳过）。"""
    norm = normalize_body_param(item)
    key = norm.get("key", "")
    if not key:
        return None

    source = norm.get("source", SOURCE_TASK_PARAM)

    if source == SOURCE_LITERAL:
        return key, _smart_parse_literal(norm.get("literal", norm.get("value", "")))

    if source == SOURCE_BUILTIN:
        builtin = norm.get("builtin") or BUILTIN_CHANNEL_MODEL_ID
        builtin_map = {
            BUILTIN_CHANNEL_MODEL_ID: model_id,
            BUILTIN_CHANNEL_CODE: channel_code,
            BUILTIN_TRACE_ID: trace_id,
        }
        val = builtin_map.get(builtin, "")
        return (key, val) if val else None

    if source == SOURCE_IMAGE_URLS:
        param_name = norm.get("param") or "images"
        img_raw = params.get(param_name) or params.get("image")
        if not img_raw:
            return None
        if isinstance(img_raw, list):
            urls = [
                require_cdn_url(extract_url_from_image_item(x) or str(x), label=f"image[{i}]")
                for i, x in enumerate(img_raw)
            ]
        elif isinstance(img_raw, dict):
            urls = require_cdn_url(extract_url_from_image_item(img_raw) or "", label="image")
        else:
            urls = require_cdn_url(str(img_raw), label="image")
        return key, urls

    if source == SOURCE_CHAT_MESSAGES:
        messages = _build_chat_messages(params)
        return (key, messages) if messages else None

    # task_param
    param_name = norm.get("param") or key
    val = _get_nested_field(params, param_name)
    if val is not None:
        return key, val
    if key == "model" and model_id:
        return key, model_id
    return None


def build_body_from_params(
    body_params: List[Dict[str, Any]],
    params: Dict[str, Any],
    *,
    model_id: str = "",
    channel_code: str = "",
    trace_id: str = "",
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    for raw_item in body_params:
        if not isinstance(raw_item, dict):
            continue
        resolved = resolve_body_param_item(
            raw_item,
            params,
            model_id=model_id,
            channel_code=channel_code,
            trace_id=trace_id,
        )
        if not resolved:
            continue
        key, val = resolved
        if key in body and isinstance(body[key], list) and isinstance(val, list):
            for v in val:
                if v not in body[key]:
                    body[key].append(v)
        else:
            body[key] = val

    if "model" not in body and model_id:
        body["model"] = model_id
    return body
