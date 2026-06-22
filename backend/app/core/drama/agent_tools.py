"""Agent Tools：对接知识库 / 风格库 / Skill（LangChain Tool 兼容结构，无硬依赖）。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.logging_config import get_logger

logger = get_logger()


@dataclass
class AgentToolSpec:
    name: str
    description: str
    handler: Callable[..., Awaitable[str]]


async def search_knowledge_tool(
    query: str,
    *,
    stage: Optional[str] = None,
    categories: Optional[List[str]] = None,
    top_k: int = 5,
) -> str:
    hits = await search_knowledge_hits(query, stage=stage, categories=categories, top_k=top_k)
    if not hits:
        return "未找到相关知识条目。"
    lines = [
        f"- [{h.get('entry_id')}] {h.get('title')}: {h.get('snippet', h.get('summary', ''))}"
        for h in hits
    ]
    return "\n".join(lines)


async def search_knowledge_hits(
    query: str,
    *,
    stage: Optional[str] = None,
    categories: Optional[List[str]] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    from app.services.drama_knowledge_service import get_drama_knowledge_service

    svc = get_drama_knowledge_service()
    cats = [c for c in (categories or []) if c]

    def _dedupe(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for h in hits:
            eid = str(h.get("entry_id") or h.get("title") or "")
            if eid in seen:
                continue
            seen.add(eid)
            deduped.append(h)
            if len(deduped) >= top_k:
                break
        return deduped

    hits = await svc.search(query=query, categories=cats or None, stage=stage, top_k=top_k)
    if hits:
        return _dedupe(hits)

    # 用户短指令与正文不匹配时，按阶段类目浏览已发布条目
    if stage or cats:
        hits = await svc.search(query="", categories=cats or None, stage=stage, top_k=top_k)
        if hits:
            return _dedupe(hits)

    hits = await svc.search(query=query, categories=None, stage=None, top_k=top_k)
    return _dedupe(hits)


from app.core.drama.style_context import resolve_style_context


async def resolve_style_tool(style_id: str) -> str:
    """按需 Tool：与 resolve_style_context 同源，返回 style_analysis JSON。"""
    ctx = await resolve_style_context(style_id)
    if not ctx.get("style_doc"):
        return ctx["prompt_block"]
    doc = ctx["style_doc"]
    sa = ctx["style_analysis"]
    payload = {
        "style_id": style_id,
        "name": doc.get("name"),
        **sa,
        "model_protocol": doc.get("model_protocol") or {},
    }
    return json.dumps(payload, ensure_ascii=False)


from app.core.drama.skill_registry import (
    SkillNotRegisteredError,
    format_skill_hint_json,
    get_registered_skill,
    require_registered_skill,
)


async def invoke_skill_hint_tool(skill_code: str) -> str:
    sk = await get_registered_skill(skill_code)
    if not sk:
        return (
            f"Skill「{skill_code}」未在 Skill 库注册发布。"
            "请先在 Skill 库新增/导入并发布；代码库 skills/ 目录不会直接被创作助手读取。"
        )
    return format_skill_hint_json(sk, skill_code)


def build_agent_tool_specs(
    *,
    style_preset_id: Optional[str] = None,
    knowledge_categories: Optional[List[str]] = None,
) -> List[AgentToolSpec]:
    cats = knowledge_categories or ["short_drama", "film"]

    async def _search(query: str, top_k: int = 5) -> str:
        return await search_knowledge_tool(query, stage=None, categories=cats, top_k=top_k)

    async def _style(style_id: str = "") -> str:
        return await resolve_style_tool(style_id or style_preset_id or "")

    async def _skill(skill_code: str) -> str:
        return await invoke_skill_hint_tool(skill_code)

    return [
        AgentToolSpec("search_knowledge", "检索专业知识库", _search),
        AgentToolSpec("resolve_style", "获取绑定风格 style_analysis", _style),
        AgentToolSpec("invoke_skill_hint", "读取 Skill 库已注册 Skill", _skill),
    ]


async def prefetch_tool_context(
    *,
    message: str,
    knowledge_categories: Optional[List[str]],
    stage: str,
    knowledge_text: Optional[str] = None,
    knowledge_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """预检索 Tool 结果注入 Prompt（知识检索可复用 assemble 层已查结果，避免重复）。"""
    from app.core.drama.agent_process_trace import make_trace_step

    blocks: List[str] = []
    steps: List[Dict[str, Any]] = []

    search_top_k = 8 if stage == "concept" else 6

    if knowledge_text is not None and knowledge_hits is not None:
        knowledge = knowledge_text
        hits = knowledge_hits
    else:
        hits = await search_knowledge_hits(
            message,
            stage=stage,
            top_k=search_top_k,
        )
        if hits:
            knowledge = "\n".join(
                f"- [{h.get('entry_id')}] {h.get('title')}: {(h.get('summary') or h.get('snippet') or '')[:240]}"
                for h in hits
            )
        else:
            knowledge = "未找到相关知识条目。"
    blocks.append(f"【Tool:search_knowledge】\n{knowledge}")
    if stage == "concept":
        blocks.append(
            "【创意融合提示】须结合以上知识 + 经典影片/短片/平台热梗的公开叙事模式做创意碰撞；"
            "知识库无命中时可用「参考联想」标注的外部参照，禁止伪造具体播放数据。"
        )
    if knowledge.startswith("未找到"):
        steps.append(
            make_trace_step(
                "knowledge",
                "knowledge",
                "检索知识库",
                status="empty",
                summary="未命中相关知识",
                detail=knowledge,
            )
        )
    else:
        items = []
        kw_hint = ""
        if hits:
            kw_set: set[str] = set()
            for h in hits:
                for k in (h.get("match_keywords") or []):
                    kw_set.add(str(k))
            if kw_set:
                kw_hint = f"关键词：{', '.join(list(kw_set)[:10])}"
            items = [
                {
                    "title": f"{h.get('title', '')}: {(h.get('summary') or '')[:80]}",
                }
                for h in hits[:8]
            ]
        else:
            for line in knowledge.splitlines():
                line = line.strip()
                if line.startswith("- "):
                    items.append({"title": line[2:120]})
        summary = f"命中 {len(items)} 条"
        if kw_hint:
            summary = f"{summary} · {kw_hint}"
        steps.append(
            make_trace_step(
                "knowledge",
                "knowledge",
                "检索知识库",
                status="ok",
                summary=summary,
                detail=knowledge,
                items=items[:8],
            )
        )

    return {
        "prompt_block": "\n\n".join(blocks),
        "steps": steps,
    }


def to_langchain_tools(specs: List[AgentToolSpec]) -> list:
    """可选：安装 langchain-core 后转为 StructuredTool。"""
    try:
        from langchain_core.tools import StructuredTool
    except ImportError:
        return []

    out = []
    for spec in specs:
        out.append(
            StructuredTool.from_function(
                coroutine=spec.handler,
                name=spec.name,
                description=spec.description,
            )
        )
    return out
