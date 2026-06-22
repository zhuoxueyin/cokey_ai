"""LangChain 超级创意智能体 — 对接 ModelGateway + Skill/知识/风格。"""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional

from app.core.config import settings

from app.core.drama.agent_modes import MODE_BY_CODE
from app.core.drama.agent_process_trace import extract_model_thinking, make_trace_step
from app.core.drama.agent_prompt_assembler import assemble_agent_prompt
from app.core.drama.agent_creation_pipeline import (
    AgentCreationIntent,
    STAGE_LABELS_ZH,
    analyze_creation_intent,
    build_reply_guidance_block,
    format_pipeline_overview,
    infer_stage_from_message,
    resolve_effective_stage,
    stage_switch_reason,
    suggest_next_options,
)
from app.core.drama.agent_style_lock import (
    format_style_lock_block,
    resolve_thread_style_sync,
)
from app.core.drama.agent_character_focus import (
    extract_character_from_assistant,
    format_character_focus_block,
    resolve_character_focus,
)
from app.core.drama.agent_user_refs import (
    build_user_refs_trace_step,
    extract_ref_image_urls,
)
from app.core.drama.skill_registry import (
    SkillNotRegisteredError,
    PRODUCTION_SKILL_SKIP_DETAIL,
    STAGES_WITHOUT_SKILL,
    format_skill_for_agent_prompt,
    resolve_stage_skill,
    skill_trace_for_stage,
)
from app.core.logging_config import get_logger
from app.services.drama_agent_thread_service import get_drama_agent_thread_service
from app.services.drama_agent_memory_service import get_drama_agent_memory_service
from app.services.drama_project_service import get_drama_project_service
from app.core.drama.style_context import resolve_style_context
from app.services.gateway_service import get_model_gateway
from app.services.task_service import get_task_service

logger = get_logger()

# 创作助手主模型调用超时（秒）；慢模型可适当调大 task_timeout_seconds
AGENT_MODEL_TIMEOUT_SECONDS = max(300, int(getattr(settings, "task_timeout_seconds", 300) or 300))


async def _background_auto_compact(thread_id: str, model_code: Optional[str]) -> None:
    """回复返回后再压缩历史，避免 chat 路径连续两次 LLM 调用阻塞用户。"""
    try:
        mem_svc = get_drama_agent_memory_service()
        await mem_svc.run_auto_compact(
            thread_id, model_code=model_code, query_source="compact"
        )
    except Exception:
        logger.exception("background auto_compact failed thread_id=%s", thread_id)


SYSTEM_TEMPLATE = """你是 {platform_name}内置的「创意超级智能体」，专业辅助用户完成：
创意脑暴 → 剧本 → 分镜 → 角色 → 场景。

{mode_directive}

【创作类型 · 全对话锁定】
类型：{mode_name}（{mode_code}）
说明：本对话自创建起已锁定该创作类型；每一轮回复都必须遵循该类型的结构、节奏与输出范式，不得切换为其他类型。

{style_lock_block}

当前阶段：{stage}
{skill_block}
{style_block}
{project_block}

工作原则：
1. 用中文对话，结构清晰，必要时用 Markdown 小标题与列表。
2. 主动引用专业知识，保持人物/风格一致；不确定时追问用户。
3. 输出区分「草案 draft」与「可确认设定」。
4. 分镜与场景描述要考虑 AI 出图/出视频可执行性。
5. 不要假装已经生成图片或视频；视觉生产在无限画布完成。
6. 若已绑定视觉风格，角色/场景/分镜描述须与风格摘要及 style_analysis 一致；character 阶段须按 skill.character 三步流水线（Markdown 主力 prompt + 出图任务 JSON），人物设定仅来自用户文字。
7. 非 character 阶段禁止输出 JSON/YAML/字段模板；尤其 concept 阶段必须输出高可读创意文案，不得混入结构化对象。

{pipeline_block}

{reply_guidance}"""

_JSON_FENCE_RE = re.compile(
    r"```(?:json|yaml|yml|javascript|js|typescript|ts)?\s*([\s\S]*?)```",
    re.IGNORECASE,
)


def _looks_like_json_blob(text: str) -> bool:
    candidate = text.strip()
    if not candidate:
        return False
    if not ((candidate.startswith("{") and candidate.endswith("}")) or (candidate.startswith("[") and candidate.endswith("]"))):
        return False
    try:
        payload = json.loads(candidate)
    except Exception:
        return False
    return isinstance(payload, (dict, list))


def _strip_json_blocks(text: str) -> str:
    blocks = re.split(r"\n\s*\n", text)
    kept: List[str] = []
    for block in blocks:
        chunk = block.strip()
        if not chunk:
            continue
        if _looks_like_json_blob(chunk):
            continue
        kept.append(block)
    return "\n\n".join(kept)


def _normalize_concept_reply(reply: str) -> str:
    """概念脑暴阶段兜底清洗：移除混入的 JSON 代码块与纯 JSON 段。"""
    if not reply:
        return reply

    def _drop_json_fence(match: re.Match[str]) -> str:
        content = (match.group(1) or "").strip()
        if _looks_like_json_blob(content):
            return ""
        return match.group(0)

    cleaned = _JSON_FENCE_RE.sub(_drop_json_fence, reply)
    cleaned = _strip_json_blocks(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or reply


class SuperCreativeAgent:
    async def chat(
        self,
        thread_id: str,
        message: str,
        *,
        refs: Optional[List[Dict[str, Any]]] = None,
        style_preset_id: Optional[str] = None,
        sync_style: bool = False,
    ) -> Dict[str, Any]:
        thread_svc = get_drama_agent_thread_service()
        thread = await thread_svc.get_thread(thread_id)
        if not thread:
            raise ValueError("线程不存在")

        style_sync = resolve_thread_style_sync(
            thread, sync_style=sync_style, incoming_style_id=style_preset_id
        )
        if style_sync.updated and style_sync.persist_style_id is not None:
            updated = await thread_svc.update_thread(
                thread_id, {"style_preset_id": style_sync.persist_style_id}
            )
            if updated:
                thread = updated

        await thread_svc.append_message(thread_id, "user", message, refs=refs)

        mode = MODE_BY_CODE.get(
            thread.get("agent_mode", "creative_short_drama"),
            MODE_BY_CODE["creative_short_drama"],
        )
        stage = thread.get("stage", "concept")
        creation_intent = analyze_creation_intent(message, stage)
        stage_switch_step = None
        intent_trace_step = None
        inferred_stage = (
            creation_intent.target_stage
            if creation_intent.intent_type == "stage_switch" and creation_intent.target_stage
            else infer_stage_from_message(message, stage)
        )
        if inferred_stage:
            prev_stage = stage
            updated_thread = await thread_svc.update_thread(thread_id, {"stage": inferred_stage})
            if updated_thread:
                thread = updated_thread
                stage = inferred_stage
                creation_intent.target_stage = stage
            stage_switch_step = make_trace_step(
                "stage_switch",
                "context",
                "切换创作阶段",
                status="ok",
                summary=f"{STAGE_LABELS_ZH.get(prev_stage, prev_stage)} → {STAGE_LABELS_ZH.get(stage, stage)}",
                detail=stage_switch_reason(message, prev_stage, stage),
            )
        else:
            intent_trace_step = make_trace_step(
                "intent_analysis",
                "context",
                "创作意图识别",
                status="ok",
                summary=creation_intent.intent_type,
                detail=creation_intent.reason,
            )

        style_id = thread.get("style_preset_id")

        process_trace: List[Dict[str, Any]] = [
            make_trace_step(
                "context_mode",
                "context",
                "创作类型上下文",
                status="ok",
                summary=mode["name"],
                detail=(mode.get("system_directive") or "")[:1200],
            )
        ]
        if stage_switch_step:
            process_trace.append(stage_switch_step)
        elif intent_trace_step:
            process_trace.append(intent_trace_step)

        if sync_style:
            process_trace.append(
                make_trace_step(
                    "style_sync",
                    "style",
                    "风格绑定同步",
                    status="ok",
                    summary=style_sync.action,
                    detail=style_sync.to_trace_detail(),
                )
            )

        refs_step = build_user_refs_trace_step(refs)
        if refs_step:
            process_trace.append(refs_step)

        style_ctx = await resolve_style_context(style_id, stage=stage, refs=refs)
        style_block = style_ctx["prompt_block"]
        style_doc = style_ctx["style_doc"]
        character_style_guide = style_ctx.get("character_style_guide") or ""
        style_lock_block = ""
        if style_id:
            style_lock_block = format_style_lock_block(
                style_name=(style_doc or {}).get("name") or "",
                style_id=style_id,
            )
        trace_meta = style_ctx["trace"]
        process_trace.append(
            make_trace_step(
                "resolve_style",
                "style",
                "读取并解析风格",
                status=trace_meta["status"],
                summary=trace_meta["summary"],
                detail=trace_meta.get("detail") or "",
            )
        )
        ref_urls = extract_ref_image_urls(refs)
        if stage == "character" and ref_urls:
            process_trace.append(
                make_trace_step(
                    "character_ref_analysis",
                    "skill",
                    "参考图风格分析（ReAct Step 2）",
                    status="ok",
                    summary=f"{len(ref_urls)} 张参考图",
                    detail=(
                        "本回合须 vision 分析参考图，仅提取风格/线条/配色/光影；"
                        "人物设定仍以用户文字为准。"
                    ),
                    items=[{"title": u[:120]} for u in ref_urls[:6]],
                )
            )
        skill_block = ""
        try:
            skill_code, skill_doc_reg = await resolve_stage_skill(stage, required=True)
        except SkillNotRegisteredError as e:
            err_msg = str(e)
            process_trace.append(
                make_trace_step(
                    "skill_load",
                    "skill",
                    "加载 Skill 模板（Skill 库）",
                    status="error",
                    summary=f"{e.skill_code} 未注册",
                    detail=err_msg,
                )
            )
            reply = (
                f"**无法继续对话**\n\n{err_msg}\n\n"
                "请在 Skill 库完成「在线新建」或「从代码库导入并发布」后再试。"
            )
            assistant_msg = await thread_svc.append_message(
                thread_id,
                "assistant",
                reply,
                meta={
                    "error": True,
                    "error_code": "skill_not_registered",
                    "skill_code": e.skill_code,
                    "stage": stage,
                    "agent_mode": mode["mode"],
                    "process_trace": process_trace,
                    "creation_intent": creation_intent.to_dict(),
                },
            )
            return {
                "thread_id": thread_id,
                "message": assistant_msg,
                "reply_markdown": reply,
                "stage": stage,
                "agent_mode": mode["mode"],
                "mode_name": mode["name"],
                "model_code": thread.get("model_code"),
                "style_preset_id": style_id,
                "error": True,
                "error_code": "skill_not_registered",
                "skill_code": e.skill_code,
                "process_trace": process_trace,
                "suggested_next": ["在 Skill 库注册并发布对应 Skill"],
            }

        if skill_doc_reg:
            skill_block = format_skill_for_agent_prompt(skill_doc_reg)
            skill_version = skill_doc_reg.get("version") or ""
        elif stage in STAGES_WITHOUT_SKILL:
            skill_block = PRODUCTION_SKILL_SKIP_DETAIL
            skill_version = ""
        else:
            skill_block = "当前阶段无绑定 Skill 模板（创作助手将按通用指令回复）。"
            skill_version = ""
        process_trace.append(skill_trace_for_stage(stage, skill_code, skill_doc_reg))

        mem_svc = get_drama_agent_memory_service()
        char_focus = None
        character_focus_block = ""
        character_roster_block = ""
        all_msgs = await thread_svc.list_messages(thread_id, limit=500)
        if stage == "character":
            stored_focus = await mem_svc.get_creation_focus(thread_id)
            from app.core.drama.agent_character_roster import (
                format_character_roster_block,
                sync_roster_from_messages,
            )

            roster_focus = sync_roster_from_messages(all_msgs, stored_focus)
            history_for_focus = await thread_svc.get_recent_for_prompt(thread_id, max_turns=12)
            char_focus = resolve_character_focus(
                message,
                stored=roster_focus,
                recent_messages=history_for_focus[:-1] if history_for_focus else [],
                intent=creation_intent,
            )
            if char_focus.name:
                creation_intent.subject = char_focus.name
            if char_focus.substep:
                creation_intent.character_substep = char_focus.substep
            character_focus_block = format_character_focus_block(char_focus)
            character_roster_block = format_character_roster_block(
                roster_focus,
                active_name=char_focus.name,
                substep=char_focus.substep,
            )
            await mem_svc.save_creation_focus(
                thread_id,
                active_character=char_focus.name,
                character_substep=char_focus.substep,
                character_roster=roster_focus.get("character_roster"),
                character_progress=roster_focus.get("character_progress"),
            )
            process_trace.append(
                make_trace_step(
                    "character_focus",
                    "context",
                    "活跃角色锁定",
                    status="ok" if char_focus.name else "skip",
                    summary=char_focus.name or "未锁定",
                    detail=(
                        f"子步骤={char_focus.substep or '—'} · 来源={char_focus.source}"
                        f" · 队列={len(roster_focus.get('character_roster') or [])}人"
                    ),
                )
            )

        pipeline_block = format_pipeline_overview(stage, skill_version=skill_version)
        reply_guidance = build_reply_guidance_block(
            stage=stage,
            intent=creation_intent,
            style_name=(style_doc or {}).get("name") if style_doc else None,
            subject=creation_intent.subject,
            mode_name=mode.get("name"),
            user_message=message,
            character_substep=creation_intent.character_substep,
        )

        project_block = ""
        if thread.get("project_id"):
            proj = await get_drama_project_service().get_by_project_id(thread["project_id"])
            if proj:
                project_block = (
                    f"项目：{proj.get('title')} | 题材：{proj.get('genre')} | "
                    f"平台：{proj.get('target_platform')}"
                )

        msg_count = len([m for m in all_msgs if m.get("role") in ("user", "assistant")])
        history_raw = await thread_svc.get_recent_for_prompt(thread_id, max_turns=20)
        history_chars = sum(len(c) for _, c in (history_raw[:-1] if history_raw else []))

        compact_applied = False
        schedule_background_compact = await mem_svc.should_auto_compact(
            thread_id, history_chars=history_chars, message_count=msg_count
        )

        assembled = await assemble_agent_prompt(
            system_template=SYSTEM_TEMPLATE,
            thread=thread,
            thread_id=thread_id,
            message=message,
            mode=mode,
            stage=stage,
            skill_block=skill_block,
            style_block=style_block,
            character_style_guide=character_style_guide,
            project_block=project_block,
            refs=refs,
            style_name=(style_doc or {}).get("name") if style_doc else None,
            pipeline_block=pipeline_block,
            reply_guidance=reply_guidance,
            character_focus_block=character_focus_block,
            character_roster_block=character_roster_block,
            active_character=(char_focus.name if char_focus else None),
            character_substep=(char_focus.substep if char_focus else None),
            style_lock_block=style_lock_block,
        )
        process_trace.extend(assembled.trace_steps)
        knowledge = assembled.knowledge
        prompt_text = assembled.prompt_text

        model_code = thread.get("model_code")
        gateway = get_model_gateway()
        try:
            model_code = await gateway.pick_model_with_channel("text", model_code)
        except ValueError as e:
            raise ValueError(str(e)) from e

        process_trace.append(
            make_trace_step(
                "model_pick",
                "model",
                "选择文本模型",
                status="ok",
                summary=model_code,
                detail=f"category=text, thread_model={thread.get('model_code') or 'default'}",
            )
        )

        if model_code != thread.get("model_code"):
            await thread_svc.update_thread(thread_id, {"model_code": model_code})

        ref_image_urls = extract_ref_image_urls(refs)
        invoke_params: Dict[str, Any] = {"prompt": prompt_text}
        if ref_image_urls:
            invoke_params["images"] = ref_image_urls

        task_svc = get_task_service()
        chat_task = await task_svc.create(
            model_code=model_code,
            category="text",
            params={
                "prompt": message,
                "agent_chat": True,
                "thread_id": thread_id,
                "stage": stage,
            },
            user_id=thread.get("user_id"),
            canvas_project_id=thread.get("canvas_project_id") or None,
            canvas_node_type="agent_chat",
            canvas_node_title=f"创作助手·{STAGE_LABELS_ZH.get(stage, stage)}",
            agent_thread_id=thread_id,
            source="agent_chat",
        )
        task_id = chat_task["task_id"]
        trace_id = chat_task["trace_id"]
        model_started = time.monotonic()

        try:
            result = await asyncio.wait_for(
                gateway.execute(
                    model_code=model_code,
                    category="text",
                    params=invoke_params,
                    trace_id=trace_id,
                    task_id=task_id,
                ),
                timeout=AGENT_MODEL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            result = {
                "success": False,
                "error_message": (
                    f"模型响应超时（{AGENT_MODEL_TIMEOUT_SECONDS}s），"
                    "请稍后重试或更换更快的文本模型"
                ),
            }

        duration_ms = int((time.monotonic() - model_started) * 1000)
        channel_code = (result.get("channel_response") or {}).get("channel_code")
        if not channel_code:
            channel_code = result.get("channel_code")

        if not result.get("success"):
            reply = f"模型调用失败：{result.get('error_message', '未知错误')}"
            meta = {
                "error": True,
                "model_code": model_code,
                "agent_mode": mode["mode"],
                "mode_name": mode["name"],
                "style_preset_id": style_id,
                "style_name": (style_doc or {}).get("name") if style_doc else None,
                "task_id": task_id,
                "trace_id": trace_id,
                "process_trace": process_trace
                + [
                    make_trace_step(
                        "model_invoke",
                        "model",
                        "模型推理",
                        status="error",
                        summary=model_code,
                        detail=result.get("error_message") or "未知错误",
                    )
                ],
                "creation_intent": creation_intent.to_dict(),
            }
        else:
            data = result.get("data") or {}
            reply = (
                data.get("text")
                or (data.get("choices") or [{}])[0].get("message", {}).get("content")
                or str(data)
            )
            if isinstance(reply, list):
                reply = json.dumps(reply, ensure_ascii=False)
            if stage == "concept":
                reply = _normalize_concept_reply(reply)
            thinking = extract_model_thinking(data)
            model_steps = [
                make_trace_step(
                    "model_invoke",
                    "model",
                    "模型推理",
                    status="ok",
                    summary=model_code,
                    detail=thinking or "（渠道未返回 thinking 字段，已直接输出正文）",
                )
            ]
            if thinking:
                model_steps.append(
                    make_trace_step(
                        "model_thinking",
                        "thinking",
                        "Thinking 过程",
                        status="ok",
                        summary=f"{len(thinking)} 字",
                        detail=thinking,
                    )
                )
            meta = {
                "model_code": model_code,
                "stage": stage,
                "agent_mode": mode["mode"],
                "mode_name": mode["name"],
                "style_preset_id": style_id,
                "style_name": (style_doc or {}).get("name") if style_doc else None,
                "knowledge_refs": [k.get("entry_id") for k in knowledge],
                "context_meta": assembled.context_meta,
                "compact_applied": compact_applied,
                "task_id": task_id,
                "trace_id": trace_id,
                "process_trace": process_trace + model_steps,
                "creation_intent": creation_intent.to_dict(),
            }

        await task_svc.update_status(
            task_id,
            "success" if not meta.get("error") else "failed",
            result=result.get("data") if result.get("success") else None,
            error_message=result.get("error_message") if not result.get("success") else None,
            channel_code=channel_code,
            duration_ms=duration_ms,
            channel_request=result.get("channel_request"),
            channel_response=result.get("channel_response"),
        )

        recent_user_msgs = [
            m.get("content") or ""
            for m in all_msgs
            if m.get("role") == "user"
        ][-6:]
        recent_assistant_msgs = [
            m.get("content") or ""
            for m in all_msgs
            if m.get("role") == "assistant"
        ][-3:]
        next_options = suggest_next_options(
            stage,
            intent=creation_intent,
            subject=creation_intent.subject,
            style_name=(style_doc or {}).get("name") if style_doc else None,
            recent_user_messages=recent_user_msgs,
            character_substep=creation_intent.character_substep,
            recent_assistant_messages=recent_assistant_msgs,
        )

        if stage == "character":
            stored = await mem_svc.get_creation_focus(thread_id)
            from app.core.drama.agent_character_roster import sync_roster_from_messages

            final_msgs = await thread_svc.list_messages(thread_id, limit=500)
            roster_focus = sync_roster_from_messages(final_msgs, stored)
            persist_name = creation_intent.subject or ""
            if not persist_name and isinstance(reply, str):
                persist_name = extract_character_from_assistant(reply)
            if persist_name or creation_intent.character_substep:
                await mem_svc.save_creation_focus(
                    thread_id,
                    active_character=persist_name or roster_focus.get("active_character", ""),
                    character_substep=creation_intent.character_substep,
                    character_roster=roster_focus.get("character_roster"),
                    character_progress=roster_focus.get("character_progress"),
                )
            if char_focus:
                meta["character_focus"] = char_focus.to_dict()
                meta["character_roster"] = roster_focus.get("character_roster")

        assistant_msg = await thread_svc.append_message(
            thread_id, "assistant", reply, meta=meta
        )

        if schedule_background_compact:
            asyncio.create_task(
                _background_auto_compact(thread_id, thread.get("model_code"))
            )

        return {
            "thread_id": thread_id,
            "message": assistant_msg,
            "reply_markdown": reply,
            "stage": stage,
            "agent_mode": mode["mode"],
            "mode_name": mode["name"],
            "model_code": model_code,
            "style_preset_id": style_id,
            "style_name": meta.get("style_name"),
            "knowledge_refs": meta.get("knowledge_refs", []),
            "context_meta": meta.get("context_meta"),
            "compact_applied": meta.get("compact_applied", False),
            "process_trace": meta.get("process_trace", []),
            "creation_intent": creation_intent.to_dict(),
            "suggested_next": next_options,
            "task_id": task_id,
            "trace_id": trace_id,
        }

    async def compact_thread(
        self,
        thread_id: str,
        *,
        model_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """手动触发对话压缩（summary-only 写 KV，不追加 chat 消息）。"""
        thread_svc = get_drama_agent_thread_service()
        thread = await thread_svc.get_thread(thread_id)
        if not thread:
            raise ValueError("线程不存在")
        mem_svc = get_drama_agent_memory_service()
        result = await mem_svc.run_auto_compact(
            thread_id, model_code=model_code or thread.get("model_code"), query_source="compact"
        )
        if not result:
            return {
                "thread_id": thread_id,
                "compacted": False,
                "reason": "无需压缩或模型调用失败",
            }
        return {
            "thread_id": thread_id,
            "compacted": True,
            "covers_message_count": result.get("covers_message_count"),
            "compacted_turns": result.get("compacted_turns"),
            "summary_md": result.get("summary_md"),
            "compact_model": result.get("compact_model"),
        }


_agent: Optional[SuperCreativeAgent] = None


def get_super_creative_agent() -> SuperCreativeAgent:
    global _agent
    if _agent is None:
        _agent = SuperCreativeAgent()
    return _agent
