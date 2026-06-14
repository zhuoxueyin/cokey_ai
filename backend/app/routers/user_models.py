from fastapi import APIRouter, Query
from typing import Optional
from app.core.response import success, error
from app.services.model_service import get_model_service

router = APIRouter(prefix="/models", tags=["用户-模型"])


@router.get("")
async def list_public_models(category: Optional[str] = Query(None)):
    docs = await get_model_service().list_public(category=category)
    return success(docs)


@router.get("/default")
async def get_default_model(category: str = Query(..., description="text/image/video")):
    doc = await get_model_service().get_default(category)
    if not doc:
        return error("not_found", "该分类下没有可用模型")
    return success(doc)


@router.get("/{model_code}")
async def get_model_detail(model_code: str):
    doc = await get_model_service().get_by_code(model_code)
    if not doc:
        return error("not_found", "模型不存在")
    return success(doc)
