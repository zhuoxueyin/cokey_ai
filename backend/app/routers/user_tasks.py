from fastapi import APIRouter, Body
from app.core.response import success, error
from app.schemas.task import TaskCreate
from app.services.task_service import get_task_service
from app.services.model_service import get_model_service
from app.services.session_service import get_session_service
from app.services.gateway_service import get_model_gateway
from app.services.asset_service import get_asset_service
from app.services.channel_service import get_channel_service
from app.adapters import create_adapter
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
            session_id=data.session_id,
            user_id=data.user_id  # 新增：传递用户ID
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
async def get_session_tasks(session_id: str, category: str = None, time_range: int = None):
    tasks = await get_task_service().list_by_session(session_id, category, time_range)
    return success(tasks)


@router.get("")
async def list_tasks(
    page: int = 1,
    page_size: int = 20,
    session_id: str = None,
    user_id: str = None,
    category: str = None,
    status: str = None,
    time_range: str = "6h"  # 时间范围：1h, 6h, 24h, 7d, 30d, all
):
    """获取用户任务列表（用于前端同步）
    
    Args:
        time_range: 时间范围筛选，默认最近6小时
            - 1h: 最近1小时
            - 6h: 最近6小时（默认）
            - 24h: 最近24小时
            - 7d: 最近7天
            - 30d: 最近30天
            - all: 全部时间
    """
    try:
        tasks, total = await get_task_service().list(
            page=page,
            page_size=page_size,
            session_id=session_id,
            user_id=user_id,
            category=category,
            status=status,
            time_range=time_range
        )
        return success({
            "data": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return error("internal_error", str(e))


@router.post("/generate")
async def generate(data: TaskCreate):
    try:
        import json
        logger.info(f"[GENERATE] ═══════ 收到前端请求 ═══════")
        logger.info(f"[GENERATE] model_code={data.model_code}")
        logger.info(f"[GENERATE] category={data.category}")
        logger.info(f"[GENERATE] session_id={data.session_id}")
        try:
            logger.info(f"[GENERATE] params=\n{json.dumps(data.params, ensure_ascii=False, indent=2)}")
        except Exception as _e:
            logger.info(f"[GENERATE] params_raw={data.params}")
        logger.info(f"[GENERATE] ════════════════════════════════")

        model = await get_model_service().get_by_code(data.model_code)
        if not model:
            return error("model_not_found", f"模型不存在: {data.model_code}")
        if model.get("status") != "online":
            return error("model_offline", f"模型已下架")

        if data.category in ("image", "video", "text"):
            from app.core.cdn import validate_reference_images
            try:
                validate_reference_images(data.params)
            except ValueError as ve:
                return error("validation_error", str(ve))

        logger.info(f"[GENERATE] 创建任务...")
        task = await get_task_service().create(
            model_code=data.model_code,
            category=data.category,
            params=data.params,
            session_id=data.session_id,
            user_id=data.user_id
        )

        logger.info(f"[GENERATE] 更新任务状态为 processing...")
        await get_task_service().update_status(task["task_id"], "processing")

        logger.info(f"[GENERATE] 调用网关执行...")
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
                duration_ms=result.get("duration_ms"),
                channel_request=result.get("channel_request"),
                channel_response=result.get("channel_response"),
                external_task_id=result.get("external_task_id")
            )

            # 记录生成的图片/视频到 assets 集合
            result_data = result.get("data") or {}
            res_type = result_data.get("type") or data.category
            if res_type == "image":
                images = result_data.get("images") or []
                for idx, img in enumerate(images):
                    try:
                        img_url = img.get("url") if isinstance(img, dict) else str(img)
                        if img_url:
                            await get_asset_service().create(
                                file_name=f"generated_{task['task_id']}_{idx}.png",
                                file_path="",
                                url=img_url,
                                cdn_urls=[img_url],
                                file_size=0,
                                content_type="image/png",
                                category="image",
                                source_type="generated",
                            )
                    except Exception as _e:
                        logger.warning(f"记录生成图片到 assets 失败: {_e}")
            elif res_type == "video":
                videos = result_data.get("videos") or []
                for idx, vid in enumerate(videos):
                    try:
                        vid_url = vid.get("url") if isinstance(vid, dict) else str(vid)
                        if vid_url:
                            await get_asset_service().create(
                                file_name=f"generated_{task['task_id']}_{idx}.mp4",
                                file_path="",
                                url=vid_url,
                                cdn_urls=[vid_url],
                                file_size=0,
                                content_type="video/mp4",
                                category="video",
                                source_type="generated",
                            )
                    except Exception as _e:
                        logger.warning(f"记录生成视频到 assets 失败: {_e}")

            return success({
                "task_id": task["task_id"],
                "session_id": task.get("session_id"),
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
                duration_ms=result.get("duration_ms"),
                channel_request=result.get("channel_request"),
                channel_response=result.get("channel_response")
            )
            return error(result.get("error_code", "internal_error"), result.get("error_message", "生成失败"))

    except Exception as e:
        logger.error(f"生成任务失败: {e}")
        return error("internal_error", str(e))


@router.post("/{task_id}/retry")
async def retry_task(task_id: str):
    """重试失败的任务（使用原参数重新提交）"""
    try:
        task = await get_task_service().get_by_id(task_id)
        if not task:
            return error("task_not_found", "任务不存在")
        
        if task["status"] != "failed":
            return error("invalid_status", "只有失败的任务才能重试")
        
        logger.info(f"[RETRY] 重试任务: task_id={task_id}, model_code={task['model_code']}")

        if task["category"] in ("image", "video", "text"):
            from app.core.cdn import validate_reference_images
            try:
                validate_reference_images(task["params"])
            except ValueError as ve:
                return error("validation_error", str(ve))

        # 使用原参数重新创建任务
        new_task = await get_task_service().create(
            model_code=task["model_code"],
            category=task["category"],
            params=task["params"],
            session_id=task.get("session_id")
        )
        
        await get_task_service().update_status(new_task["task_id"], "processing")
        
        # 执行任务
        gateway = get_model_gateway()
        result = await gateway.execute(
            model_code=new_task["model_code"],
            category=new_task["category"],
            params=new_task["params"],
            trace_id=new_task.get("trace_id")
        )
        
        if result.get("success"):
            await get_task_service().update_status(
                new_task["task_id"], "success",
                result=result.get("data"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms"),
                channel_request=result.get("channel_request"),
                channel_response=result.get("channel_response"),
                external_task_id=result.get("external_task_id")
            )
            return success({
                "task_id": new_task["task_id"],
                "status": "success",
                "result": result.get("data"),
                "duration_ms": result.get("duration_ms"),
                "created_at": new_task["created_at"]
            })
        else:
            await get_task_service().update_status(
                new_task["task_id"], "failed",
                error_message=result.get("error_message", "重试失败"),
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms"),
                channel_request=result.get("channel_request"),
                channel_response=result.get("channel_response")
            )
            return error(result.get("error_code", "internal_error"), result.get("error_message", "重试失败"))
    
    except Exception as e:
        logger.error(f"重试任务失败: {e}")
        return error("internal_error", str(e))


@router.post("/{task_id}/recover")
async def recover_task(task_id: str):
    """恢复任务状态（通过外部任务ID查询第三方服务状态）"""
    try:
        task = await get_task_service().get_by_id(task_id)
        if not task:
            return error("task_not_found", "任务不存在")
        
        if task["status"] != "processing":
            return error("invalid_status", "只有处理中的任务才能恢复")
        
        external_task_id = task.get("external_task_id")
        if not external_task_id:
            return error("no_external_id", "任务没有外部任务ID，无法恢复")
        
        logger.info(f"[RECOVER] 恢复任务: task_id={task_id}, external_task_id={external_task_id}")
        
        # 获取渠道配置
        channel_code = task.get("channel_code")
        if not channel_code:
            return error("channel_not_found", "无法确定任务使用的渠道")
        
        channel = await get_channel_service().get_by_code(channel_code)
        if not channel:
            return error("channel_not_found", "渠道不存在")
        
        # 创建适配器并查询外部任务状态
        adapter = create_adapter(channel, task.get("trace_id"))
        if not adapter:
            return error("adapter_error", "无法创建渠道适配器")
        
        # 查询外部任务状态
        try:
            recovery_result = await adapter.query_task(external_task_id)
            if recovery_result.get("success"):
                # 任务已完成
                await get_task_service().update_status(
                    task_id, "success",
                    result=recovery_result.get("data"),
                    channel_code=channel_code
                )
                return success({
                    "task_id": task_id,
                    "status": "success",
                    "result": recovery_result.get("data"),
                    "recovered": True
                })
            elif recovery_result.get("status") == "running":
                # 任务仍在运行
                return success({
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务仍在第三方服务中运行，请稍后重试",
                    "recovered": False
                })
            else:
                # 任务失败
                await get_task_service().update_status(
                    task_id, "failed",
                    error_message=recovery_result.get("error_message", "外部任务失败")
                )
                return error("external_task_failed", recovery_result.get("error_message", "外部任务失败"))
        except Exception as e:
            logger.error(f"查询外部任务状态失败: {e}")
            return error("query_failed", f"查询外部任务状态失败: {e}")
    
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        return error("internal_error", str(e))
