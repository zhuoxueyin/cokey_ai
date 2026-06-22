"""创作助手单轮对话过程追踪（Skill / 知识 / 风格 / 模型）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def make_trace_step(
    step_id: str,
    kind: str,
    title: str,
    *,
    status: str = "ok",
    summary: str = "",
    detail: str = "",
    items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "step_id": step_id,
        "kind": kind,
        "title": title,
        "status": status,
        "summary": summary,
        "detail": detail,
        "items": items or [],
    }


def extract_model_thinking(data: Any) -> Optional[str]:
    """从网关文本响应中提取 thinking / reasoning 字段（若渠道返回）。"""
    if not isinstance(data, dict):
        return None
    for key in ("reasoning_content", "thinking", "reasoning", "thought"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    choices = data.get("choices") or []
    if choices and isinstance(choices[0], dict):
        msg = choices[0].get("message") or {}
        if isinstance(msg, dict):
            for key in ("reasoning_content", "thinking", "reasoning", "thought"):
                val = msg.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
    return None
