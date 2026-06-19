from typing import Optional

from fastapi import APIRouter, Query

from app.core.response import error, paginated, success
from app.services.trace_log_service import get_trace_log_service

router = APIRouter(prefix="/admin/trace-logs", tags=["管理-链路日志"])


@router.get("")
async def list_trace_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trace_id: Optional[str] = Query(None, description="链路 ID（与 log_id 相同）"),
    task_id: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    channel_code: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    time_range: str = Query("24h"),
):
    docs, total = await get_trace_log_service().list(
        page=page,
        page_size=page_size,
        trace_id=trace_id,
        task_id=task_id,
        model_code=model_code,
        channel_code=channel_code,
        category=category,
        status=status,
        time_range=time_range,
    )
    return paginated(docs, total, page, page_size)


@router.get("/{trace_id}")
async def get_trace_log(trace_id: str):
    doc = await get_trace_log_service().get_by_trace_id(trace_id)
    if not doc:
        return error("not_found", "链路日志不存在")
    return success(doc)
