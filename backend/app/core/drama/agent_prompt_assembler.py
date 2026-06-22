"""创作助手 Prompt 组装中枢 — 统一预算、记忆、历史与协作块。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.drama.agent_context_budget import (
    DEFAULT_CHAR_BUDGET,
    RESERVE_FOR_USER_AND_REPLY,
    apply_history_budget,
    build_system_reminders,
    trim_layer,
    BudgetReport,
)
from app.core.drama.agent_process_trace import make_trace_step
from app.core.drama.agent_tools import prefetch_tool_context
from app.core.drama.agent_user_refs import format_user_refs_for_prompt
from app.services.drama_agent_memory_service import get_drama_agent_memory_service
from app.services.drama_agent_thread_service import get_drama_agent_thread_service
from app.services.drama_knowledge_service import get_drama_knowledge_service


@dataclass
class AssembledPrompt:
    prompt_text: str
    knowledge: List[Dict[str, Any]]
    knowledge_block: str
    history_report: BudgetReport
    budget_report: BudgetReport
    thread_summary: Optional[Dict[str, Any]] = None
    compact_applied: bool = False
    trace_steps: List[Dict[str, Any]] = field(default_factory=list)
    context_meta: Dict[str, Any] = field(default_factory=dict)


async def assemble_agent_prompt(
    *,
    system_template: str,
    thread: Dict[str, Any],
    thread_id: str,
    message: str,
    mode: Dict[str, Any],
    stage: str,
    skill_block: str,
    style_block: str,
    character_style_guide: str,
    project_block: str,
    refs: Optional[List[Dict[str, Any]]],
    style_name: Optional[str] = None,
    char_budget: int = DEFAULT_CHAR_BUDGET,
    pipeline_block: str = "",
    reply_guidance: str = "",
    character_focus_block: str = "",
    character_roster_block: str = "",
    active_character: Optional[str] = None,
    character_substep: Optional[str] = None,
    style_lock_block: str = "",
) -> AssembledPrompt:
    mem_svc = get_drama_agent_memory_service()
    thread_svc = get_drama_agent_thread_service()
    trace_steps: List[Dict[str, Any]] = []
    budget = BudgetReport(total_budget=char_budget - RESERVE_FOR_USER_AND_REPLY - len(message))

    # --- 项目结构化 memory ---
    project_memory = await mem_svc.build_project_memory_block(thread.get("project_id"))
    if project_block and project_memory:
        project_combined = f"{project_block}\n\n{project_memory}"
    else:
        project_combined = project_block or project_memory
    project_combined = trim_layer("project_memory", project_combined, 3000, budget)

    # --- KV 对话摘要 ---
    summary_block, summary_doc = await mem_svc.format_summary_block(thread_id)
    if summary_doc:
        summary_block = trim_layer("thread_summary", summary_block, 2500, budget)
        trace_steps.append(
            make_trace_step(
                "memory_summary",
                "context",
                "加载对话摘要",
                status="ok",
                summary=f"已覆盖约 {summary_doc.get('covers_message_count', 0)} 条消息",
                detail=(summary_doc.get("summary_md") or "")[:1200],
            )
        )
    else:
        trace_steps.append(
            make_trace_step(
                "memory_summary",
                "context",
                "加载对话摘要",
                status="skip",
                summary="无历史摘要",
            )
        )

    # --- 知识检索（按当前阶段 applicable_stages 过滤类目 + 关键词/向量混合检索）---
    from app.core.drama.agent_tools import search_knowledge_hits

    knowledge = await search_knowledge_hits(
        message,
        stage=stage,
        top_k=8 if stage == "concept" else 6,
    )
    knowledge_block = trim_layer(
        "knowledge",
        "\n".join(
            f"- {k.get('title')}: {(k.get('summary') or '')[:200]}" for k in knowledge[:8 if stage == "concept" else 4]
        )
        or "（无额外知识命中）",
        2500 if stage == "concept" else 2000,
        budget,
    )

    tool_pack = await prefetch_tool_context(
        message=message,
        knowledge_categories=mode.get("knowledge_categories"),
        stage=stage,
        knowledge_text=knowledge_block if knowledge else None,
        knowledge_hits=knowledge if isinstance(knowledge, list) else None,
    )
    tool_block = trim_layer(
        "tools",
        tool_pack.get("prompt_block") or "（无）",
        4000,
        budget,
    )
    trace_steps.extend(tool_pack.get("steps") or [])

    # --- 分层裁剪固定块 ---
    skill_trimmed = trim_layer("skill", skill_block, 12000, budget)
    style_trimmed = trim_layer("style", style_block, 5000, budget)
    char_guide = trim_layer("character_style", character_style_guide or "", 2500, budget)
    pipeline_trimmed = trim_layer("pipeline", pipeline_block or "", 1500, budget)
    guidance_trimmed = trim_layer("reply_guidance", reply_guidance or "", 2000, budget)
    focus_trimmed = trim_layer("character_focus", character_focus_block or "", 1200, budget)
    roster_trimmed = trim_layer("character_roster", character_roster_block or "", 1400, budget)
    style_lock_trimmed = trim_layer("style_lock", style_lock_block or "", 800, budget)

    all_msgs = await thread_svc.list_messages(thread_id, limit=500)
    message_count = len([m for m in all_msgs if m.get("role") in ("user", "assistant")])
    history_raw = await thread_svc.get_recent_for_prompt(thread_id, max_turns=20)
    history_for_prompt = history_raw[:-1] if history_raw else []

    history_text, _, history_report = apply_history_budget(
        history_for_prompt,
        max_turns=16,
        max_per_turn=600,
        total_cap=18_000,
    )
    budget.used += history_report.used
    budget.layers["history"] = history_report.used
    budget.actions.extend(history_report.actions)

    if history_report.actions:
        trace_steps.append(
            make_trace_step(
                "context_snip",
                "context",
                "历史上下文裁剪",
                status="ok",
                summary=f"{len(history_for_prompt)} 轮 → {history_report.used} 字",
                detail="; ".join(history_report.actions),
            )
        )

    ref_block = format_user_refs_for_prompt(refs)
    ref_block = trim_layer("refs", ref_block, 1200, budget)

    reminders = build_system_reminders(
        stage=stage,
        agent_mode_name=mode.get("name") or mode.get("mode", ""),
        style_name=style_name,
        style_id=thread.get("style_preset_id"),
        ref_count=len(refs or []),
        message_count=message_count,
        compact_summary_present=bool(summary_doc),
        compact_covers_through=(summary_doc or {}).get("covers_message_count"),
        active_character=active_character,
        character_substep=character_substep,
    )
    reminders = trim_layer("system_reminders", reminders, 800, budget)

    trace_steps.append(
        make_trace_step(
            "context_budget",
            "context",
            "上下文预算",
            status="ok",
            summary=f"{budget.used}/{budget.total_budget} 字",
            detail="; ".join(budget.actions) if budget.actions else "未触发裁剪",
        )
    )

    prompt_text = f"""{system_template.format(
        platform_name=settings.app_name,
        mode_directive=mode.get("system_directive", ""),
        mode_name=mode["name"],
        mode_code=mode["mode"],
        stage=stage,
        skill_block=skill_trimmed,
        style_block=style_trimmed,
        project_block=project_combined,
        pipeline_block=pipeline_trimmed,
        reply_guidance=guidance_trimmed,
        style_lock_block=style_lock_trimmed,
    )}

{reminders}

{char_guide}

{focus_trimmed}

{roster_trimmed}

{summary_block}

{knowledge_block}

【Tool 预检索】
{tool_block}

【对话历史】
{history_text or "（新对话）"}

【用户 @ 引用资源】
{ref_block}
（以上参考图会随请求以 vision 多模态一并送入模型；请结合用户文字理解构图、主体与风格倾向。）

【用户最新消息】
{message}

请作为助手回复（Markdown）。"""

    context_meta = {
        "budget": budget.to_dict(),
        "history": history_report.to_dict(),
        "message_count": message_count,
        "has_thread_summary": bool(summary_doc),
        "summary_covers": (summary_doc or {}).get("covers_message_count"),
    }

    return AssembledPrompt(
        prompt_text=prompt_text,
        knowledge=knowledge,
        knowledge_block=knowledge_block,
        history_report=history_report,
        budget_report=budget,
        thread_summary=summary_doc,
        trace_steps=trace_steps,
        context_meta=context_meta,
    )
