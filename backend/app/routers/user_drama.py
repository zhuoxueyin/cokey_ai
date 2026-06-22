from fastapi import APIRouter, Query, Header
from typing import Any, Dict, Optional

from app.core.response import success, paginated, error
from app.core.logging_config import get_logger
from app.core.drama.style_description import enrich_style_payload
from app.core.drama.agent_modes import AGENT_MODES
from app.schemas.drama import (
    AgentChatRequest,
    AgentThreadCreate,
    AgentThreadUpdate,
    DramaProjectCreate,
    DramaProjectUpdate,
    DramaChatRequest,
    StylePresetCreate,
    StylePresetUpdate,
)
from app.services.drama_orchestrator import get_drama_orchestrator
from app.services.drama_agent_thread_service import get_drama_agent_thread_service
from app.services.drama_super_agent_service import get_super_creative_agent
from app.services.drama_project_service import get_drama_project_service
from app.services.drama_style_service import get_drama_style_service
from app.services.drama_knowledge_service import get_drama_knowledge_service

router = APIRouter(prefix="/drama", tags=["短剧Agent"])

logger = get_logger()


def _user_id_from_header(x_user_id: Optional[str]) -> Optional[str]:
    return x_user_id


def _normalize_style_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in data.items() if k not in ("publish", "cover_url") and v is not None}
    cover = data.get("cover_url")
    if cover:
        out["reference_images"] = [{"url": cover, "role": "cover"}]
    elif data.get("reference_images"):
        out["reference_images"] = data["reference_images"]
    return enrich_style_payload(out)


@router.get("/styles")
async def list_published_styles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    render_class: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    """用户侧风格库（仅 published）。"""
    items, total = await get_drama_style_service().list(
        page=page,
        page_size=page_size,
        render_class=render_class,
        status="published",
        keyword=keyword,
    )
    return paginated(items, total, page, page_size)


@router.get("/styles/{style_id}")
async def get_published_style(style_id: str):
    doc = await get_drama_style_service().get_by_style_id(style_id)
    if not doc or doc.get("status") != "published":
        return error("not_found", "风格不存在或未发布")
    return success(doc)


@router.post("/styles")
async def create_user_style(
    data: StylePresetCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    try:
        payload = _normalize_style_payload(data.model_dump())
        payload["origin"] = "user"
        payload["status"] = "draft"
        payload["created_by"] = _user_id_from_header(x_user_id)
        doc = await get_drama_style_service().create(payload)
        if data.publish:
            doc = await get_drama_style_service().publish(doc["style_id"]) or doc
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.put("/styles/{style_id}")
async def update_user_style(style_id: str, data: StylePresetUpdate):
    doc = await get_drama_style_service().get_by_style_id(style_id)
    if not doc or doc.get("status") == "archived":
        return error("not_found", "风格不存在")
    updated = await get_drama_style_service().update(
        style_id, _normalize_style_payload(data.model_dump(exclude_none=True))
    )
    if not updated:
        return error("not_found", "风格不存在")
    return success(updated)


@router.delete("/styles/{style_id}")
async def delete_user_style(style_id: str):
    """用户侧软删风格（平台内置 preset 不可删）。"""
    doc = await get_drama_style_service().get_by_style_id(style_id)
    if not doc:
        return error("not_found", "风格不存在")
    try:
        ok = await get_drama_style_service().soft_delete(style_id)
    except ValueError as e:
        return error("validation_error", str(e))
    if not ok:
        return error("not_found", "风格不存在")
    return success({"deleted": True})


@router.get("/character-prompt-template")
async def get_character_prompt_template():
    """角色卡规范（来自 Skill 库已发布的 skill.character）。"""
    from app.core.drama.character_prompt_template import export_template_document_async

    return success(await export_template_document_async())


@router.get("/projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    items, total = await get_drama_project_service().list(
        user_id=_user_id_from_header(x_user_id),
        page=page,
        page_size=page_size,
    )
    return paginated(items, total, page, page_size)


@router.post("/projects")
async def create_project(
    data: DramaProjectCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    doc = await get_drama_project_service().create(data.model_dump(), user_id=_user_id_from_header(x_user_id))
    return success(doc)


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    doc = await get_drama_project_service().get_by_project_id(project_id)
    if not doc:
        return error("not_found", "项目不存在")
    return success(doc)


@router.put("/projects/{project_id}")
async def update_project(project_id: str, data: DramaProjectUpdate):
    try:
        doc = await get_drama_project_service().update(
            project_id, data.model_dump(exclude_none=True)
        )
    except ValueError as e:
        return error("validation_error", str(e))
    if not doc:
        return error("not_found", "项目不存在")
    return success(doc)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    ok = await get_drama_project_service().soft_delete(project_id)
    if not ok:
        return error("not_found", "项目不存在")
    return success({"deleted": True})


@router.get("/projects/{project_id}/memory")
async def get_project_memory(project_id: str):
    snap = await get_drama_project_service().get_memory_snapshot(project_id)
    if not snap:
        return error("not_found", "项目不存在")
    return success(snap)


@router.post("/projects/{project_id}/chat")
async def project_chat(project_id: str, data: DramaChatRequest):
    try:
        result = await get_drama_orchestrator().chat(
            project_id, data.message, stage_override=data.stage
        )
        return success(result)
    except ValueError as e:
        return error("validation_error", str(e))


@router.get("/agent/modes")
async def list_agent_modes():
    public = [{k: v for k, v in m.items() if k != "system_directive"} for m in AGENT_MODES]
    return success(public)


@router.get("/agent/threads")
async def list_agent_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    standalone_only: bool = Query(True),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    items, total = await get_drama_agent_thread_service().list_threads(
        user_id=_user_id_from_header(x_user_id),
        standalone_only=standalone_only,
        page=page,
        page_size=page_size,
    )
    return paginated(items, total, page, page_size)


@router.get("/agent/threads/by-canvas/{canvas_project_id}")
async def get_agent_thread_by_canvas(canvas_project_id: str):
    doc = await get_drama_agent_thread_service().get_thread_by_canvas(canvas_project_id)
    return success(doc)


@router.post("/agent/threads")
async def create_agent_thread(
    data: AgentThreadCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    doc = await get_drama_agent_thread_service().create_thread(
        {**data.model_dump(), "user_id": _user_id_from_header(x_user_id)}
    )
    return success(doc)


@router.get("/agent/threads/{thread_id}")
async def get_agent_thread(thread_id: str):
    doc = await get_drama_agent_thread_service().get_thread(thread_id)
    if not doc:
        return error("not_found", "线程不存在")
    return success(doc)


@router.patch("/agent/threads/{thread_id}")
async def update_agent_thread(thread_id: str, data: AgentThreadUpdate):
    doc = await get_drama_agent_thread_service().update_thread(
        thread_id, data.model_dump(exclude_unset=True)
    )
    if not doc:
        return error("not_found", "线程不存在")
    return success(doc)


@router.delete("/agent/threads/{thread_id}")
async def delete_agent_thread(thread_id: str):
    ok = await get_drama_agent_thread_service().delete_thread(thread_id)
    if not ok:
        return error("not_found", "线程不存在")
    return success({"deleted": True})


@router.post("/agent/threads/{thread_id}/spawn-canvas")
async def spawn_canvas_from_agent_thread(
    thread_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    from app.services.drama_agent_canvas_bridge import spawn_canvas_from_agent_thread

    try:
        result = await spawn_canvas_from_agent_thread(thread_id, user_id=_user_id_from_header(x_user_id))
        return success(result)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("spawn_canvas_from_agent_thread failed: %s", e)
        return error("internal_error", f"创建画布失败：{e}")


@router.get("/agent/threads/{thread_id}/messages")
async def list_agent_messages(
    thread_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    thread = await get_drama_agent_thread_service().get_thread(thread_id)
    if not thread:
        return error("not_found", "线程不存在")
    items = await get_drama_agent_thread_service().list_messages(thread_id, limit=limit)
    return success(items)


@router.post("/agent/threads/{thread_id}/compact")
async def compact_agent_thread(thread_id: str):
    """手动压缩早期对话为 KV 摘要（Claude Code Auto-Compact 简化版）。"""
    try:
        result = await get_super_creative_agent().compact_thread(thread_id)
        return success(result)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("compact_agent_thread failed: %s", e)
        return error("internal_error", f"压缩失败：{e}")


@router.post("/agent/threads/{thread_id}/chat")
async def agent_thread_chat(thread_id: str, data: AgentChatRequest):
    try:
        refs = [r.model_dump(exclude_none=True) for r in data.refs]
        body = data.model_dump(exclude_unset=True)
        sync_style = "style_preset_id" in body
        result = await get_super_creative_agent().chat(
            thread_id,
            data.message,
            refs=refs,
            style_preset_id=body.get("style_preset_id") if sync_style else None,
            sync_style=sync_style,
        )
        return success(result)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("agent_thread_chat failed: %s", e)
        return error("internal_error", f"创作助手调用失败：{e}")


@router.get("/knowledge/search")
async def user_knowledge_search(
    q: str = Query(""),
    category: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    top_k: int = Query(6, ge=1, le=20),
):
    items = await get_drama_knowledge_service().search(
        query=q, category=category, stage=stage, top_k=top_k, status="published"
    )
    return success(items)
