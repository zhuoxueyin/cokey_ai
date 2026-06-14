from fastapi import APIRouter, Body
from app.core.response import success, error
from app.services.session_service import get_session_service

router = APIRouter(prefix="/sessions", tags=["用户-会话"])


@router.post("")
async def create_session(body: dict = Body(...)):
    category = body.get("category", "")
    if category not in ["text", "image", "video"]:
        return error("validation_error", "分类必须是 text/image/video")
    session = await get_session_service().create(category)
    return success({"session_id": session["session_id"], "category": session["category"]})


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = await get_session_service().get_by_id(session_id)
    if not session:
        return error("not_found", "会话不存在")
    return success(session)
