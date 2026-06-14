from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from app.core.response import success, paginated, error
from app.schemas.model import ModelCreate, ModelUpdate
from app.services.model_service import get_model_service

router = APIRouter(prefix="/admin/models", tags=["管理-模型管理"])


@router.get("")
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    docs, total = await get_model_service().list(page=page, page_size=page_size, category=category, status=status)
    return paginated(docs, total, page, page_size)


@router.post("")
async def create_model(data: ModelCreate):
    try:
        existing = await get_model_service().get_by_code(data.model_code)
        if existing:
            return error("validation_error", f"模型编码已存在: {data.model_code}")
        doc = await get_model_service().create(data.model_dump())
        return success(doc)
    except Exception as e:
        return error("internal_error", str(e))


@router.get("/{model_id}")
async def get_model(model_id: str):
    doc = await get_model_service().get_by_id(model_id)
    if not doc:
        return error("not_found", "模型不存在")
    return success(doc)


@router.put("/{model_id}")
async def update_model(model_id: str, data: ModelUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    doc = await get_model_service().update(model_id, update_dict)
    if not doc:
        return error("not_found", "模型不存在")
    return success(doc)


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    result = await get_model_service().delete(model_id)
    if not result:
        return error("not_found", "模型不存在")
    return success({"deleted": True})


@router.post("/{model_id}/status")
async def set_model_status(model_id: str, body: dict = Body(...)):
    status = body.get("status", "")
    if status not in ["online", "offline", "maintenance"]:
        return error("validation_error", "状态只能是 online/offline/maintenance")
    result = await get_model_service().set_status(model_id, status)
    if not result:
        return error("not_found", "模型不存在")
    return success({"status": status})


@router.post("/batch-import")
async def batch_import_models(body: dict = Body(...)):
    channel_code = body.get("channel_code", "")
    if not channel_code:
        return error("validation_error", "缺少 channel_code")
    models_data = body.get("models", [])
    if not models_data:
        return error("validation_error", "缺少 models 数据")
    result = await get_model_service().batch_import(channel_code, models_data)
    return success(result)
