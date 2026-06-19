from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from app.core.response import success, paginated, error
from app.services.task_service import get_task_service

router = APIRouter(prefix="/admin/tasks", tags=["管理-任务管理"])


@router.get("")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    trace_id: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    channel_code: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    time_range: str = Query("6h"),  # 时间范围：1h, 6h, 24h, 7d, 30d, all
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1, ge=-1, le=1)
):
    docs, total = await get_task_service().list(
        page=page, page_size=page_size, session_id=session_id,
        task_id=task_id, trace_id=trace_id,
        model_code=model_code, channel_code=channel_code, category=category, status=status,
        time_range=time_range,
        sort_by=sort_by, sort_order=sort_order
    )
    return paginated(docs, total, page, page_size)


@router.get("/stats/overview")
async def get_task_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None)
):
    stats = await get_task_service().get_stats(start_time=start_time, end_time=end_time, category=category)
    return success(stats)


@router.get("/{task_id}")
async def get_task(task_id: str):
    doc = await get_task_service().get_by_id(task_id)
    if not doc:
        return error("not_found", "任务不存在")
    return success(doc)


@router.post("/cancel/all")
async def cancel_all_running():
    result = await get_task_service().cancel_all_running()
    return success(result)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    cancelled = await get_task_service().cancel_task(task_id)
    if not cancelled:
        return error("not_found", "任务不存在或已完成")
    return success({"message": "任务已停止"})
