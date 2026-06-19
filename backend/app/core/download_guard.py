"""远程下载 URL 校验（防 SSRF）"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

MAX_DOWNLOAD_URL_LENGTH = 4096

_BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
}


def validate_download_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise ValueError("URL 无效")
    cleaned = url.strip()
    if len(cleaned) > MAX_DOWNLOAD_URL_LENGTH:
        raise ValueError("URL 过长")
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅支持 HTTP(S) 下载")
    host = parsed.hostname
    if not host:
        raise ValueError("URL 无效")
    if host.lower() in _BLOCKED_HOSTS:
        raise ValueError("不允许的下载地址")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("不允许的下载地址")
    except ValueError as exc:
        if "不允许" in str(exc):
            raise
    return cleaned
