"""UTC 时间写入与 API 序列化（统一带 Z 后缀，避免前端时区歧义）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """返回 timezone-aware UTC 时间，供新写入使用。"""
    return datetime.now(timezone.utc)


def to_api_iso(value: datetime) -> str:
    """将 datetime 序列化为 ISO-8601 UTC 字符串（末尾 Z）。"""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    text = value.isoformat()
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def normalize_for_json(value: Any) -> Any:
    """递归将响应体中的 datetime 转为 API ISO 字符串。"""
    if isinstance(value, datetime):
        return to_api_iso(value)
    if isinstance(value, dict):
        return {k: normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [normalize_for_json(v) for v in value]
    return value
