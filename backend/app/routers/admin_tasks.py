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
    model_code: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    docs, total = await get_task_service().list(
        page=page, page_size=page_size, session_id=session_id,
        model_code=model_code, category=category, status=status
    )
    return paginated(docs, total, page, page_size)


@router.get("/{task_id}")
async def get_task(task_id: str):
    doc = await get_task_service().get_by_id(task_id)
    if not doc:
        return error("not_found", "任务不存在")
    return success(doc)


@router.get("/stats/overview")
async def get_task_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None)
):
    stats = await get_task_service().get_stats(start_time=start_time, end_time=end_time, category=category)
    return success(stats)
