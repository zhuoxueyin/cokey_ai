"""创作助手：用户 @ 引用资源格式化。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.cdn import is_cdn_url, require_cdn_url
from app.core.drama.agent_process_trace import make_trace_step


def extract_ref_image_urls(refs: Optional[List[Dict[str, Any]]]) -> List[str]:
    """从用户引用中提取可用于多模态 chat 的 CDN 图片 URL。"""
    if not refs:
        return []
    urls: List[str] = []
    seen: set[str] = set()
    for ref in refs:
        raw = (ref.get("url") or "").strip()
        if not raw:
            continue
        try:
            cdn = require_cdn_url(raw, label="引用资源")
        except ValueError:
            if is_cdn_url(raw):
                cdn = raw
            else:
                continue
        if cdn not in seen:
            seen.add(cdn)
            urls.append(cdn)
    return urls


def format_user_refs_for_prompt(refs: Optional[List[Dict[str, Any]]]) -> str:
    if not refs:
        return "（无）"
    lines: List[str] = []
    for i, ref in enumerate(refs, 1):
        url = (ref.get("url") or "").strip()
        ref_type = ref.get("type") or "asset"
        asset_id = ref.get("id") or ""
        if url:
            id_part = f" id={asset_id}" if asset_id else ""
            lines.append(f"- 参考图 {i} [{ref_type}{id_part}]: {url}")
        else:
            lines.append(f"- 引用 {i} [{ref_type}]: （无 URL，请结合用户文字理解）")
    return "\n".join(lines)


def build_user_refs_trace_step(refs: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    if not refs:
        return None
    urls = extract_ref_image_urls(refs)
    summary = f"{len(urls)} 张参考图（多模态）" if urls else f"{len(refs)} 项引用"
    items = [
        {"id": r.get("id"), "title": (r.get("url") or r.get("name") or "")[:120]}
        for r in refs
    ]
    return make_trace_step(
        "user_refs",
        "context",
        "用户引用资源",
        status="ok" if urls else "empty",
        summary=summary,
        detail="\n".join(urls) if urls else "引用项缺少图片 URL",
        items=items,
    )
