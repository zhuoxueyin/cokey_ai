"""画布提示词 @ 引用占位符 — 与 frontend/src/utils/canvasPromptMention.ts 对齐"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

REF_TOKEN_RE = re.compile(r"\{\{@node:([a-zA-Z0-9_]+)\}\}")


def build_ref_token(node_id: str) -> str:
    return f"{{{{@node:{node_id}}}}}"


def expand_prompt_refs(prompt: str, ref_contents: Dict[str, str]) -> str:
    if not prompt:
        return ""

    def repl(match: re.Match) -> str:
        node_id = match.group(1)
        content = ref_contents.get(node_id)
        if content is None:
            return match.group(0)
        return content

    return REF_TOKEN_RE.sub(repl, prompt)


def extract_ref_node_ids(prompt: str) -> list[str]:
    return REF_TOKEN_RE.findall(prompt or "")


def append_attached_text_refs(
    prompt: str,
    ref_contents: Dict[str, str],
    cited_ids: list[str],
) -> str:
    """将连线中未通过 @ 引用的文本参考追加到 prompt 末尾（@ 仅控制插入位置）。"""
    cited = set(cited_ids or [])
    extras: list[str] = []
    for node_id, content in (ref_contents or {}).items():
        if node_id in cited:
            continue
        text = (content or "").strip()
        if text:
            extras.append(text)
    if not extras:
        return prompt
    suffix = "\n\n".join(extras)
    base = (prompt or "").strip()
    return f"{base}\n\n{suffix}" if base else suffix


def text_from_source_node(source: Dict[str, Any]) -> Optional[str]:
    src_type = source.get("node_type")
    result = source.get("result") or {}
    cfg = source.get("config") or {}

    if src_type == "text":
        text = result.get("text") or cfg.get("content")
        return str(text).strip() if text else None
    if src_type == "image":
        title = source.get("title") or "图片"
        return f"[参考图:{title}]"
    if src_type == "resource":
        if (cfg.get("resource_type") or "image") == "video":
            return None
        title = source.get("title") or cfg.get("resource_name") or "资源"
        return f"[参考图:{title}]"
    return None


def image_url_from_source_node(source: Dict[str, Any]) -> Optional[str]:
    """从上游节点提取可供多模态文本调用的图片 URL。"""
    src_type = source.get("node_type")
    result = source.get("result") or {}
    cfg = source.get("config") or {}

    if src_type == "resource":
        if (cfg.get("resource_type") or "image") == "video":
            return None
        url = cfg.get("resource_url")
        return str(url).strip() if url else None
    if src_type == "image":
        imgs = result.get("images") or []
        if not imgs:
            return None
        idx = int(cfg.get("output_image_index") or 0)
        idx = max(0, min(idx, len(imgs) - 1))
        img = imgs[idx]
        if isinstance(img, dict):
            return (img.get("url") or img.get("cdn_url") or "").strip() or None
        return str(img).strip() or None
    return None
