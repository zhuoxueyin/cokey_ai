from fastapi import APIRouter, Body
from app.core.response import success, error
from app.schemas.task import TaskCreate
from app.services.task_service import get_task_service
from app.services.model_service import get_model_service
from app.services.session_service import get_session_service
from app.services.gateway_service import get_model_gateway
from app.core.logging_config import get_logger
import asyncio

logger = get_logger()

router = APIRouter(prefix="/tasks", tags=["用户-任务"])


@router.post("")
async def create_task(data: TaskCreate):
    try:
        model = await get_model_service().get_by_code(data.model_code)
        if not model:
            return error("model_not_found", f"模型不存在: {data.model_code}")
        if model.get("status") != "online":
            return error("model_offline", f"模型已下架")

        task = await get_task_service().create(
            model_code=data.model_code,
            category=data.category,
            params=data.params,
            session_id=data.session_id
        )

        return success({"task_id": task["task_id"], "status": task["status"]})
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return error("internal_error", str(e))


@router.post("/{task_id}/execute")
async def execute_task(task_id: str):
    try:
        task = await get_task_service().get_by_id(task_id)
        if not task:
            return error("task_not_found", "任务不存在")

        await get_task_service().update_status(task_id, "processing")

        gateway = get_model_gateway()
        result = await gateway.execute(
            model_code=task["model_code"],
            category=task["category"],
            params=task["params"],
            trace_id=task.get("trace_id")
        )

        if result.get("success"):
            await get_task_service().update_status(
                task_id, "success",
                result=result.get("data"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms")
            )
            return success({
                "task_id": task_id,
                "status": "success",
                "result": result.get("data"),
                "duration_ms": result.get("duration_ms")
            })
        else:
            await get_task_service().update_status(
                task_id, "failed",
                error_message=result.get("error_message", "任务执行失败"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms")
            )
            return error(result.get("error_code", "internal_error"), result.get("error_message", "任务执行失败"))

    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        await get_task_service().update_status(task_id, "failed", error_message=str(e))
        return error("internal_error", str(e))


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = await get_task_service().get_by_id(task_id)
    if not task:
        return error("task_not_found", "任务不存在")
    return success({
        "task_id": task["task_id"],
        "status": task["status"],
        "result": task.get("result"),
        "error_message": task.get("error_message"),
        "duration_ms": task.get("duration_ms"),
        "created_at": task["created_at"]
    })


@router.get("/session/{session_id}")
async def get_session_tasks(session_id: str):
    tasks = await get_task_service().list_by_session(session_id)
    return success(tasks)


@router.post("/generate")
async def generate(data: TaskCreate):
    try:
        model = await get_model_service().get_by_code(data.model_code)
        if not model:
            return error("model_not_found", f"模型不存在: {data.model_code}")
        if model.get("status") != "online":
            return error("model_offline", f"模型已下架")

        task = await get_task_service().create(
            model_code=data.model_code,
            category=data.category,
            params=data.params,
            session_id=data.session_id
        )

        await get_task_service().update_status(task["task_id"], "processing")

        gateway = get_model_gateway()
        result = await gateway.execute(
            model_code=task["model_code"],
            category=task["category"],
            params=task["params"],
            trace_id=task.get("trace_id")
        )

        if result.get("success"):
            await get_task_service().update_status(
                task["task_id"], "success",
                result=result.get("data"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms")
            )
            return success({
                "task_id": task["task_id"],
                "status": "success",
                "result": result.get("data"),
                "duration_ms": result.get("duration_ms"),
                "created_at": task["created_at"]
            })
        else:
            await get_task_service().update_status(
                task["task_id"], "failed",
                error_message=result.get("error_message", "生成失败"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms")
            )
            return error(result.get("error_code", "internal_error"), result.get("error_message", "生成失败"))

    except Exception as e:
        logger.error(f"生成任务失败: {e}")
        return error("internal_error", str(e))
