from fastapi import APIRouter, Query, Body
from typing import Optional

from app.core.response import success, paginated, error
from app.schemas.protocol_profile import ProtocolProfileCreate, ProtocolProfileUpdate
from app.services.protocol_profile_service import get_protocol_profile_service

router = APIRouter(prefix="/admin/protocol-profiles", tags=["管理-协议画像"])


@router.get("")
async def list_protocol_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    provider: Optional[str] = Query(None),
    invocation_mode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_builtin: bool = Query(True),
):
    docs, total = await get_protocol_profile_service().list(
        page=page,
        page_size=page_size,
        provider=provider,
        invocation_mode=invocation_mode,
        status=status,
        include_builtin=include_builtin,
    )
    return paginated(docs, total, page, page_size)


@router.post("")
async def create_protocol_profile(data: ProtocolProfileCreate):
    try:
        doc = await get_protocol_profile_service().create(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        return error("internal_error", str(e))


@router.get("/{profile_doc_id}")
async def get_protocol_profile(profile_doc_id: str):
    doc = await get_protocol_profile_service().get_by_id(profile_doc_id)
    if not doc:
        return error("not_found", "协议画像不存在")
    return success(doc)


@router.get("/by-id/{profile_id}")
async def get_protocol_profile_by_profile_id(profile_id: str):
    doc = await get_protocol_profile_service().get_by_profile_id(profile_id)
    if not doc:
        return error("not_found", "协议画像不存在")
    return success(doc)


@router.put("/{profile_doc_id}")
async def update_protocol_profile(profile_doc_id: str, data: ProtocolProfileUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    doc = await get_protocol_profile_service().update(profile_doc_id, update_dict)
    if not doc:
        return error("not_found", "协议画像不存在")
    return success(doc)


@router.delete("/{profile_doc_id}")
async def delete_protocol_profile(profile_doc_id: str):
    ok = await get_protocol_profile_service().delete(profile_doc_id)
    if not ok:
        return error("not_found", "协议画像不存在")
    return success({"deleted": True})


@router.post("/seed-builtin")
async def seed_builtin_profiles():
    """手动触发内置画像种子写入。"""
    count = await get_protocol_profile_service().ensure_builtin_seeded()
    return success({"inserted": count})
