"""创作助手线程记忆：KV 滚动摘要 + 项目结构化 memory（Claude Code Auto-Compact 简化版）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger
from app.services.drama_agent_thread_service import get_drama_agent_thread_service
from app.services.kv_service import get_kv_service

logger = get_logger()

KV_NAMESPACE = "drama_agent"
SUMMARY_SUFFIX = ":summary"
META_SUFFIX = ":context_meta"

# 触发 Auto-Compact 的阈值
AUTO_COMPACT_MIN_MESSAGES = 20
AUTO_COMPACT_HISTORY_CHARS = 14_000

COMPACT_SYSTEM = """你是创作助手对话压缩子代理（summary-only 返回，保护主对话上下文）。
任务：将较早的对话轮次压缩为结构化摘要，供主 Agent 继续创作。

必须保留：
1. 用户核心目标与题材方向
2. 已确认设定（人物、风格、剧情节点）与 forbidden 事项
3. 各阶段产出要点（创意、大纲、剧本、角色、场景、分镜）
4. 待办与用户明确偏好
5. 与绑定风格/阶段相关的锁定决策
6. **已锁定绑定风格**（style_id + 名称）— 全对话不可切换，除非用户显式取消
7. **当前活跃角色**（对话焦点，与上轮「下一步可选」一致）及各角色三步进度（宏观设计/定妆/角色卡）
8. **角色设计队列**（按顺序的角色名单 + 每位 设/定/卡 完成标记），不可打乱顺序或遗漏早期角色

禁止：废话、重复全文、工具调用细节。
输出：Markdown，≤900 字，用小标题组织。"""


def _summary_key(thread_id: str) -> str:
    return f"{thread_id}{SUMMARY_SUFFIX}"


def _meta_key(thread_id: str) -> str:
    return f"{thread_id}{META_SUFFIX}"


class DramaAgentMemoryService:
    async def get_thread_summary(self, thread_id: str) -> Optional[Dict[str, Any]]:
        raw = await get_kv_service().get_json(KV_NAMESPACE, _summary_key(thread_id))
        if not raw or not isinstance(raw, dict):
            return None
        if not (raw.get("summary_md") or "").strip():
            return None
        return raw

    async def get_context_meta(self, thread_id: str) -> Dict[str, Any]:
        raw = await get_kv_service().get_json(KV_NAMESPACE, _meta_key(thread_id))
        return raw if isinstance(raw, dict) else {}

    async def get_creation_focus(self, thread_id: str) -> Dict[str, Any]:
        meta = await self.get_context_meta(thread_id)
        focus = meta.get("creation_focus")
        return focus if isinstance(focus, dict) else {}

    async def save_creation_focus(
        self,
        thread_id: str,
        *,
        active_character: str = "",
        character_substep: str = "",
        character_roster: Optional[List[str]] = None,
        character_progress: Optional[Dict[str, Any]] = None,
    ) -> None:
        meta = await self.get_context_meta(thread_id)
        focus = dict(meta.get("creation_focus") or {})
        if active_character:
            focus["active_character"] = active_character.strip()
        if character_substep:
            focus["character_substep"] = character_substep.strip()
        if character_roster is not None:
            focus["character_roster"] = character_roster
        if character_progress is not None:
            focus["character_progress"] = character_progress
        meta["creation_focus"] = focus
        await get_kv_service().set_json(KV_NAMESPACE, _meta_key(thread_id), meta)

    async def save_thread_summary(
        self,
        thread_id: str,
        *,
        summary_md: str,
        covers_message_count: int,
        compact_model: str,
        source_message_ids: Optional[List[str]] = None,
    ) -> None:
        payload = {
            "summary_md": summary_md.strip(),
            "covers_message_count": covers_message_count,
            "compact_model": compact_model,
            "version": (await self.get_context_meta(thread_id)).get("compact_version", 0) + 1,
            "source_message_ids": source_message_ids or [],
        }
        await get_kv_service().set_json(KV_NAMESPACE, _summary_key(thread_id), payload)
        meta = await self.get_context_meta(thread_id)
        meta["compact_version"] = payload["version"]
        meta["last_compact_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        await get_kv_service().set_json(KV_NAMESPACE, _meta_key(thread_id), meta)

    async def clear_thread_memory(self, thread_id: str) -> None:
        kv = get_kv_service()
        await kv.delete(KV_NAMESPACE, _summary_key(thread_id))
        await kv.delete(KV_NAMESPACE, _meta_key(thread_id))

    async def build_project_memory_block(self, project_id: Optional[str]) -> str:
        if not project_id:
            return ""
        from app.services.drama_project_service import get_drama_project_service

        snap = await get_drama_project_service().get_memory_snapshot(project_id)
        if not snap:
            return ""
        proj = snap.get("project") or {}
        confirmed = snap.get("confirmed_settings") or []
        forbidden = snap.get("forbidden_settings") or []
        parts = [
            "【项目结构化记忆】",
            f"项目：{proj.get('title') or project_id} | 题材：{proj.get('genre') or '—'} | "
            f"平台：{proj.get('target_platform') or '—'} | 阶段：{proj.get('stage') or '—'}",
        ]
        if confirmed:
            parts.append("已确认设定：")
            for item in confirmed[:12]:
                parts.append(f"- {str(item)[:200]}")
        if forbidden:
            parts.append("禁止事项：")
            for item in forbidden[:8]:
                parts.append(f"- {str(item)[:200]}")
        chars = snap.get("characters") or []
        scenes = snap.get("scenes") or []
        if chars:
            parts.append(f"角色实体：{len(chars)} 条（详情见项目 memory API）")
        if scenes:
            parts.append(f"场景实体：{len(scenes)} 条")
        return "\n".join(parts)

    async def should_auto_compact(
        self,
        thread_id: str,
        *,
        history_chars: int,
        message_count: int,
        query_source: str = "chat",
    ) -> bool:
        if query_source == "compact":
            return False
        existing = await self.get_thread_summary(thread_id)
        covered = (existing or {}).get("covers_message_count") or 0
        uncovered = max(0, message_count - covered)
        if uncovered >= AUTO_COMPACT_MIN_MESSAGES:
            return True
        if history_chars >= AUTO_COMPACT_HISTORY_CHARS and message_count >= 10:
            return True
        return False

    async def run_auto_compact(
        self,
        thread_id: str,
        *,
        model_code: Optional[str] = None,
        query_source: str = "compact",
    ) -> Optional[Dict[str, Any]]:
        """Fork 式压缩子调用：仅摘要回写 KV，不污染主 trace  verbosity。"""
        thread_svc = get_drama_agent_thread_service()
        thread = await thread_svc.get_thread(thread_id)
        if not thread:
            return None

        existing = await self.get_thread_summary(thread_id)
        covered = (existing or {}).get("covers_message_count") or 0
        all_msgs = await thread_svc.list_messages(thread_id, limit=500)
        conv = [m for m in all_msgs if m.get("role") in ("user", "assistant")]
        if len(conv) <= 8:
            return None

        to_compact = conv[covered:-6]
        if len(to_compact) < 6:
            return None

        prior = (existing or {}).get("summary_md") or ""
        transcript_lines: List[str] = []
        if prior:
            transcript_lines.append(f"【已有摘要】\n{prior}\n")
        transcript_lines.append("【待压缩对话】")
        for m in to_compact:
            role = "用户" if m["role"] == "user" else "助手"
            transcript_lines.append(f"{role}: {(m.get('content') or '')[:1200]}")
        transcript = "\n".join(transcript_lines)

        from app.services.gateway_service import get_model_gateway

        gateway = get_model_gateway()
        try:
            model_code = await gateway.pick_model_with_channel("text", model_code or thread.get("model_code"))
        except ValueError as e:
            logger.warning("compact pick model failed: %s", e)
            return None

        prompt = f"""{COMPACT_SYSTEM}

创作类型：{thread.get('agent_mode')} | 阶段：{thread.get('stage')}
绑定风格：{thread.get('style_preset_id') or '无'}

{transcript}

请输出更新后的完整对话摘要（Markdown）："""

        result = await gateway.execute(
            model_code=model_code,
            category="text",
            params={"prompt": prompt},
            trace_id=None,
            task_id=None,
        )
        if not result.get("success"):
            logger.warning("auto compact failed: %s", result.get("error_message"))
            return None

        data = result.get("data") or {}
        summary = (
            data.get("text")
            or (data.get("choices") or [{}])[0].get("message", {}).get("content")
            or ""
        )
        if isinstance(summary, list):
            summary = json.dumps(summary, ensure_ascii=False)
        summary = (summary or "").strip()
        if len(summary) < 80:
            return None

        new_covered = covered + len(to_compact)
        await self.save_thread_summary(
            thread_id,
            summary_md=summary,
            covers_message_count=new_covered,
            compact_model=model_code,
            source_message_ids=[m.get("message_id") for m in to_compact if m.get("message_id")],
        )
        return {
            "summary_md": summary,
            "covers_message_count": new_covered,
            "compact_model": model_code,
            "compacted_turns": len(to_compact),
            "query_source": query_source,
        }

    async def format_summary_block(self, thread_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        doc = await self.get_thread_summary(thread_id)
        if not doc:
            return "", None
        md = doc.get("summary_md") or ""
        block = f"【对话摘要 · 早期轮次】\n{md}"
        return block, doc


_mem_svc: Optional[DramaAgentMemoryService] = None


def get_drama_agent_memory_service() -> DramaAgentMemoryService:
    global _mem_svc
    if _mem_svc is None:
        _mem_svc = DramaAgentMemoryService()
    return _mem_svc
