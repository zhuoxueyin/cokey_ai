"""用户侧远程文件下载代理（解决浏览器 CORS 无法 fetch 外部视频等问题）"""

from __future__ import annotations

import re
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.download_guard import validate_download_url
from app.core.logging_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/download", tags=["用户-下载"])

_SAFE_FILENAME = re.compile(r"[^a-zA-Z0-9._\-()\u4e00-\u9fff]+")

_EXT_MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _safe_filename(name: str) -> str:
    cleaned = _SAFE_FILENAME.sub("_", (name or "").strip()) or "download"
    return cleaned[:180]


def _guess_content_type(filename: str, url: str) -> str:
    for source in (filename, url):
        lower = source.lower()
        for ext, mime in _EXT_MIME.items():
            if lower.endswith(ext):
                return mime
    return "application/octet-stream"


@router.get("/proxy")
async def proxy_download(
    url: str = Query(..., description="远程文件 URL"),
    filename: str = Query(None, description="下载文件名"),
):
    try:
        target = validate_download_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    safe_name = _safe_filename(filename) if filename else "download"
    disposition = f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{quote(safe_name)}"
    timeout = httpx.Timeout(connect=30.0, read=600.0, write=60.0, pool=30.0)

    client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    try:
        req = client.build_request("GET", target)
        resp = await client.send(req, stream=True)
    except httpx.RequestError as exc:
        await client.aclose()
        logger.warning("下载代理连接失败: %s", exc)
        raise HTTPException(status_code=502, detail="无法连接远程资源") from exc

    if resp.status_code >= 400:
        preview = (await resp.aread())[:200]
        await resp.aclose()
        await client.aclose()
        logger.warning(
            "下载代理失败 HTTP %s: %s",
            resp.status_code,
            preview.decode("utf-8", errors="replace"),
        )
        raise HTTPException(status_code=502, detail=f"远程资源不可用 (HTTP {resp.status_code})")

    content_type = resp.headers.get("content-type") or _guess_content_type(safe_name, target)
    if ";" in content_type:
        content_type = content_type.split(";", 1)[0].strip()

    async def iter_bytes():
        try:
            async for chunk in resp.aiter_bytes(65536):
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(
        iter_bytes(),
        media_type=content_type,
        headers={"Content-Disposition": disposition},
    )
