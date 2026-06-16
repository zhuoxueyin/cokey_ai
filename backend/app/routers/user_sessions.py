from fastapi import APIRouter, Body
from app.core.response import success, error
from app.services.session_service import get_session_service

router = APIRouter(prefix="/sessions", tags=["用户-会话"])


@router.post("")
async def create_session(body: dict = Body(...)):
    category = body.get("category", "")
    user_id = body.get("user_id")
    if category not in ["text", "image", "video"]:
        return error("validation_error", "分类必须是 text/image/video")
    session = await get_session_service().create(category, user_id)
    return success({"session_id": session["session_id"], "category": session["category"]})


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = await get_session_service().get_by_id(session_id)
    if not session:
        return error("not_found", "会话不存在")
    return success(session)


@router.put("/{session_id}/context")
async def update_session_context(session_id: str, body: dict = Body(...)):
    """更新会话上下文（用于对话历史共享）"""
    context = body.get("context", {})
    success_flag = await get_session_service().update_context(session_id, context)
    if success_flag:
        return success({"message": "上下文更新成功"})
    return error("not_found", "会话不存在")


@router.get("")
async def list_user_sessions(user_id: str = None):
    """获取用户的会话列表"""
    sessions = await get_session_service().list_by_user(user_id)
    return success(sessions)
