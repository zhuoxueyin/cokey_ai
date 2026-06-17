"""CDN URL 校验工具 — 与 frontend/src/utils/cdnUrl.ts 白名单保持一致"""

from __future__ import annotations

from typing import Any, List, Union

KNOWN_CDN_PREFIXES = [
    "https://cdn.jsdmirror.com/",
    "https://cdn.jsdelivr.net/",
    "https://fastly.jsdelivr.net/",
    "https://ghproxy.net/",
    "https://raw.githubusercontent.com/",
]

MAX_CDN_URL_LENGTH = 2048


def is_cdn_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    if url.startswith("data:") or url.startswith("blob:"):
        return False
    return any(url.startswith(prefix) for prefix in KNOWN_CDN_PREFIXES)


def require_cdn_url(url: str, label: str = "图片") -> str:
    if not url or not isinstance(url, str):
        raise ValueError(f"{label}地址无效，请先上传")
    if url.startswith("data:") or url.startswith("blob:"):
        raise ValueError(f"{label}须使用已上传的 CDN 地址，不支持本地或 Base64")
    if not is_cdn_url(url):
        raise ValueError(f"{label}须使用已上传的 CDN 地址")
    if len(url) > MAX_CDN_URL_LENGTH:
        raise ValueError(f"{label}地址异常，请重新上传")
    return url


def extract_url_from_image_item(item: Union[str, dict]) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("cdn_url") or item.get("url") or "")
    return ""


def validate_reference_images(params: dict, field_names: tuple = ("images", "image")) -> None:
    """校验 params 中的参考图字段，必须为 CDN HTTP URL"""
    for field in field_names:
        raw = params.get(field)
        if not raw:
            continue
        items: List[Any]
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, str):
            items = [raw]
        else:
            raise ValueError(f"参数 {field} 格式无效")

        for i, item in enumerate(items):
            url = extract_url_from_image_item(item)
            require_cdn_url(url, label=f"参考图[{i + 1}]")
