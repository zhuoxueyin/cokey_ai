"""外部创作助手 → 无限画布：thread 与画布 1:1 绑定（不在画布上预置节点）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging_config import get_logger
from app.services.canvas_service import get_canvas_service
from app.services.drama_agent_thread_service import get_drama_agent_thread_service

logger = get_logger()


async def _repair_thread_canvas_binding(thread_id: str, project_id: str) -> None:
    """将 thread.canvas_project_id 与已有画布对齐（幂等）。"""
    thread_svc = get_drama_agent_thread_service()
    thread = await thread_svc.get_thread(thread_id, resolve_canvas=False)
    if not thread:
        raise ValueError("创作助手对话不存在")
    bound = (thread.get("canvas_project_id") or "").strip()
    if bound == project_id:
        return
    if bound:
        raise ValueError("该创作助手已绑定其他画布，无法重复创建")
    await thread_svc.bind_canvas(thread_id, project_id)


async def spawn_canvas_from_agent_thread(
    thread_id: str,
    *,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    创作助手进入画布二阶段：创建空白画布并与 thread 1:1 绑定。
    对话上下文仅通过右侧创作助手侧栏关联，不在画布上写入文本/出图节点。
    若已绑定则返回已有画布（幂等）；若 thread 侧缺失绑定但画布已有 agent_thread_id 则自动修复。
    """
    thread_svc = get_drama_agent_thread_service()
    canvas_svc = get_canvas_service()

    thread = await thread_svc.get_thread(thread_id, resolve_canvas=False)
    if not thread:
        raise ValueError("创作助手对话不存在")

    binding_repaired = False
    existing_pid = (thread.get("canvas_project_id") or "").strip()
    if existing_pid:
        proj = await canvas_svc.get_project(existing_pid)
        if proj:
            return {
                "thread_id": thread_id,
                "project_id": existing_pid,
                "already_bound": True,
                "binding_repaired": False,
                "seed_node_ids": [],
            }
        await thread_svc.update_thread(thread_id, {"canvas_project_id": None})
        existing_pid = ""

    if not existing_pid:
        reverse = await canvas_svc.get_project_by_agent_thread(thread_id)
        if reverse:
            project_id = reverse["project_id"]
            await _repair_thread_canvas_binding(thread_id, project_id)
            logger.info(
                "repair canvas binding thread=%s project=%s (reverse lookup)",
                thread_id,
                project_id,
            )
            return {
                "thread_id": thread_id,
                "project_id": project_id,
                "already_bound": True,
                "binding_repaired": True,
                "seed_node_ids": [],
            }

    title = thread.get("title") or "未命名创作"
    canvas_title = f"{title} · 画布"
    uid = user_id or thread.get("user_id")

    project = await canvas_svc.create_project(canvas_title, uid, agent_thread_id=thread_id)
    project_id = project["project_id"]

    try:
        await thread_svc.bind_canvas(thread_id, project_id)
    except Exception:
        await canvas_svc.delete_project(project_id)
        raise

    logger.info("spawn canvas from agent thread=%s project=%s (assistant bind only)", thread_id, project_id)
    return {
        "thread_id": thread_id,
        "project_id": project_id,
        "already_bound": False,
        "binding_repaired": False,
        "seed_node_ids": [],
    }


def get_drama_agent_canvas_bridge():
    return spawn_canvas_from_agent_thread
