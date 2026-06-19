from fastapi import APIRouter, HTTPException, Query, Body
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import time

from app.core.response import success, paginated, error
from app.schemas.channel import ChannelCreate, ChannelUpdate
from app.services.channel_service import get_channel_service
from app.core.chat_image_protocol import is_openai_chat_image_slot
from app.core.utils import generate_trace_id
from app.services.trace_log_service import get_trace_log_service

router = APIRouter(prefix="/admin/channels", tags=["管理-渠道管理"])


class ChannelDebugRequest(BaseModel):
    endpoint_type: str = Field(..., description="端点类型，如 text / image / image_edits / video / chat")
    channel_model_id: str = Field(..., min_length=1, description="渠道侧模型 ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="业务参数字典，将直接传入适配器")
    category: Optional[str] = Field(None, description="可选覆盖分类：text / image / video")


def _category_for_endpoint(
    endpoint_type: str,
    override: Optional[str] = None,
    endpoint: Optional[Dict[str, Any]] = None,
) -> str:
    if override in ("text", "image", "video"):
        return override
    if endpoint and is_openai_chat_image_slot(endpoint.get("protocol_slot")):
        return "image"
    mapping = {
        "text": "text",
        "chat": "text",
        "image": "image",
        "image_edits": "image",
        "video": "video",
        "video_image": "video",
        "audio": "text",
    }
    return mapping.get(endpoint_type, "text")


def _find_endpoint(channel: Dict[str, Any], endpoint_type: str) -> Optional[Dict[str, Any]]:
    for ep in channel.get("endpoints") or []:
        if ep.get("type") == endpoint_type:
            return ep
    return None


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


@router.post("/{channel_id}/debug")
async def debug_channel(channel_id: str, data: ChannelDebugRequest):
    """渠道原生调试：直连指定端点，不经过模型绑定与网关路由。"""
    channel = await get_channel_service().get_by_id(channel_id)
    if not channel:
        return error("not_found", "渠道不存在")

    endpoint = _find_endpoint(channel, data.endpoint_type)
    if not endpoint:
        return error(
            "validation_error",
            f"渠道未配置端点类型: {data.endpoint_type}",
        )

    trace_id = generate_trace_id()
    category = _category_for_endpoint(data.endpoint_type, data.category, endpoint)
    trace_svc = get_trace_log_service()

    await trace_svc.ensure_log(
        trace_id,
        model_code=f"debug:{data.channel_model_id}",
        category=category,
    )
    await trace_svc.append_step(
        trace_id,
        "channel_debug_request",
        {
            "channel_code": channel.get("channel_code"),
            "endpoint_type": data.endpoint_type,
            "channel_model_id": data.channel_model_id,
            "category": category,
            "params": data.params,
            "endpoint": {
                "path": endpoint.get("endpoint"),
                "method": endpoint.get("method"),
                "protocol_slot": endpoint.get("protocol_slot"),
            },
        },
    )

    adapter = create_adapter(channel, trace_id)
    if not adapter:
        await trace_svc.finalize(trace_id, "failed", error_message="适配器初始化失败")
        return error("channel_error", "渠道适配器初始化失败")

    api_key = adapter.get_api_key_for_category(category)
    if not api_key:
        await trace_svc.finalize(trace_id, "failed", error_message="API 密钥未配置")
        return error("channel_error", "渠道 API 密钥未配置")

    start = time.time()
    try:
        result = await adapter.execute(
            category=category,
            endpoint_type=data.endpoint_type,
            model_config={},
            params=data.params,
            channel_model_id=data.channel_model_id,
            api_key=api_key,
        )
        duration_ms = int((time.time() - start) * 1000)

        http_request = getattr(adapter, "_http_request_info", None)
        payload: Dict[str, Any] = {
            "trace_id": trace_id,
            "success": result.get("success", False),
            "duration_ms": duration_ms,
            "channel_code": channel.get("channel_code"),
            "endpoint_type": data.endpoint_type,
            "channel_model_id": data.channel_model_id,
            "category": category,
            "http_request": http_request,
        }

        if result.get("success"):
            payload["success"] = True
            payload["result"] = result.get("data")
            await trace_svc.append_step(trace_id, "channel_debug_response", {"result": result.get("data")})
            await trace_svc.finalize(
                trace_id,
                "success",
                duration_ms=duration_ms,
                channel_code=channel.get("channel_code"),
            )
            return success(payload)

        err_msg = result.get("error_message") or "渠道调用失败"
        payload["success"] = False
        payload["error_code"] = result.get("error_code")
        payload["error_message"] = err_msg
        await trace_svc.append_step(
            trace_id,
            "channel_debug_response",
            {"error_code": result.get("error_code"), "error_message": err_msg},
            level="error",
        )
        await trace_svc.finalize(
            trace_id,
            "failed",
            duration_ms=duration_ms,
            error_message=err_msg,
            channel_code=channel.get("channel_code"),
        )
        return success(payload)

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        err_msg = str(e)
        await trace_svc.finalize(trace_id, "failed", duration_ms=duration_ms, error_message=err_msg)
        return success({
            "trace_id": trace_id,
            "success": False,
            "duration_ms": duration_ms,
            "error_message": err_msg,
            "channel_code": channel.get("channel_code"),
        })
