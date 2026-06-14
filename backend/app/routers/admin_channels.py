from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from app.core.response import success, paginated, error
from app.schemas.channel import ChannelCreate, ChannelUpdate
from app.services.channel_service import get_channel_service

router = APIRouter(prefix="/admin/channels", tags=["管理-渠道管理"])


@router.get("")
async def list_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    docs, total = await get_channel_service().list(page=page, page_size=page_size, status=status)
    return paginated(docs, total, page, page_size)


@router.post("")
async def create_channel(data: ChannelCreate):
    try:
        existing = await get_channel_service().get_by_code(data.channel_code)
        if existing:
            return error("validation_error", f"渠道编码已存在: {data.channel_code}")
        doc = await get_channel_service().create(data.model_dump())
        return success(doc)
    except Exception as e:
        return error("internal_error", str(e))


@router.get("/{channel_id}")
async def get_channel(channel_id: str):
    doc = await get_channel_service().get_by_id(channel_id)
    if not doc:
        return error("not_found", "渠道不存在")
    return success(doc)


@router.put("/{channel_id}")
async def update_channel(channel_id: str, data: ChannelUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    doc = await get_channel_service().update(channel_id, update_dict)
    if not doc:
        return error("not_found", "渠道不存在")
    return success(doc)


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str):
    result = await get_channel_service().delete(channel_id)
    if not result:
        return error("not_found", "渠道不存在")
    return success({"deleted": True})


@router.post("/{channel_id}/status")
async def set_channel_status(channel_id: str, body: dict = Body(...)):
    status = body.get("status", "")
    if status not in ["active", "inactive"]:
        return error("validation_error", "状态只能是 active 或 inactive")
    result = await get_channel_service().set_status(channel_id, status)
    if not result:
        return error("not_found", "渠道不存在")
    return success({"status": status})
