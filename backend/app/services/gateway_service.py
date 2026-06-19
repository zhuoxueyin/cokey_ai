from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import json
import time

from app.core.logging_config import get_logger
from app.core.protocol_resolver import resolve_route
from app.core.utils import generate_trace_id
from app.services.channel_service import get_channel_service
from app.services.model_service import get_model_service
from app.services.trace_log_service import get_trace_log_service
from app.adapters import create_adapter

logger = get_logger()


class ModelGateway:
    def __init__(self):
        self.channel_service = get_channel_service()
        self.model_service = get_model_service()
        self.trace_logs = get_trace_log_service()
        self._current_task_id: Optional[str] = None

    def _has_chat_endpoint(self, channel: Dict[str, Any]) -> bool:
        endpoints = channel.get("endpoints", [])
        for endpoint in endpoints:
            if endpoint.get("type") == "chat":
                return True
        return False

    def _determine_endpoint_type(
        self,
        category: str,
        params: Dict[str, Any],
        channel: Optional[Dict[str, Any]] = None,
        channel_model_id: str = "",
        binding: Optional[Dict[str, Any]] = None,
    ) -> str:
        """兼容旧调用；新逻辑请用 resolve_route。"""
        from app.core.invocation_mode import resolve_invocation_mode, mode_to_legacy_endpoint_type

        mode = resolve_invocation_mode(category, params)
        if category == "image" and channel:
            from app.core.apiyi_image import is_apiyi_conversational_image_model

            provider = channel.get("channel_provider")
            if provider == "apiyi" and is_apiyi_conversational_image_model(channel_model_id):
                return "chat"

        if channel and self._has_chat_endpoint(channel):
            return "chat"

        return mode_to_legacy_endpoint_type(mode, category)

    def _validate_params(self, params: Dict[str, Any], param_schema: Dict[str, Any]) -> Tuple[bool, str]:
        fields = param_schema.get("fields", [])
        for field in fields:
            field_name = field["name"]
            is_required = field.get("required", False)
            value = params.get(field_name)

            if is_required and (value is None or value == ""):
                return False, f"参数 {field.get('label', field_name)} 不能为空"

            field_type = field.get("field_type", "text")
            if value is not None and value != "":
                if field_type in ["number", "slider"]:
                    try:
                        num_val = float(value)
                        if field.get("min") is not None and num_val < field["min"]:
                            return False, f"{field.get('label', field_name)} 不能小于 {field['min']}"
                        if field.get("max") is not None and num_val > field["max"]:
                            return False, f"{field.get('label', field_name)} 不能大于 {field['max']}"
                    except (ValueError, TypeError):
                        return False, f"{field.get('label', field_name)} 必须是数字"
                elif field_type == "select":
                    options = field.get("options", [])
                    valid_values = [opt.get("value") for opt in options]
                    if valid_values and value not in valid_values:
                        return False, f"{field.get('label', field_name)} 选项无效"

        return True, ""

    def _sorted_bindings(self, model_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        bindings = model_config.get("channel_bindings", [])
        active = [b for b in bindings if b.get("status", "active") == "active"]
        active.sort(key=lambda b: b.get("priority", 1), reverse=True)
        return active

    async def _select_channel(self, model_config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        active_bindings = self._sorted_bindings(model_config)
        logger.info(f"[_select_channel] 模型有 {len(active_bindings)} 个活跃渠道绑定（按 priority 降序）")
        for idx, binding in enumerate(active_bindings):
            channel_code = binding.get("channel_code")
            logger.info(
                f"[_select_channel] [{idx}] channel={channel_code} "
                f"priority={binding.get('priority')} model_id={binding.get('channel_model_id')}"
            )
            channel = await self.channel_service.get_by_code(channel_code)
            if channel and channel.get("status") == "active":
                logger.info(f"[_select_channel] 选中渠道: {channel_code}")
                return channel, binding
            logger.warning(
                f"[_select_channel] 渠道 {channel_code} 不可用: status={channel.get('status') if channel else 'None'}"
            )
        return None, None

    def _build_channel_request(
        self,
        category: str,
        params: Dict[str, Any],
        channel: Dict[str, Any],
        channel_model_id: str,
        endpoint_type: str,
        adapter: Any,
        route_ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        req: Dict[str, Any] = {
            "category": category,
            "endpoint_type": endpoint_type,
            "channel_model_id": channel_model_id,
            "channel_code": channel["channel_code"],
            "channel_provider": channel.get("channel_provider"),
            "base_url": channel.get("base_url", ""),
            "original_params": params,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if route_ctx is not None:
            req.update(route_ctx.to_trace_dict())
        if hasattr(adapter, "_http_request_info") and adapter._http_request_info:
            req["http_request"] = adapter._http_request_info
        return req

    def _build_channel_response(self, adapter: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        channel_response: Dict[str, Any] = {}
        if hasattr(adapter, "_create_response") and adapter._create_response:
            channel_response["create"] = adapter._create_response
        if result.get("raw_result"):
            channel_response["raw"] = result["raw_result"]
        if result.get("data"):
            channel_response["parsed"] = result["data"]
            channel_response["query"] = result["data"]
        if hasattr(adapter, "_poll_attempts") and adapter._poll_attempts:
            channel_response["poll_details"] = adapter._poll_attempts
        if not result.get("success"):
            channel_response["error"] = {
                "error_code": result.get("error_code"),
                "error_message": result.get("error_message"),
            }
            if hasattr(adapter, "_last_http_error") and getattr(adapter, "_last_http_error", None):
                channel_response["error"]["upstream"] = adapter._last_http_error
            if hasattr(adapter, "_http_request_info") and adapter._http_request_info:
                channel_response["http_request"] = adapter._http_request_info
        return channel_response

    async def _invoke_channel(
        self,
        trace_id: str,
        category: str,
        params: Dict[str, Any],
        model_config: Dict[str, Any],
        channel: Dict[str, Any],
        binding: Dict[str, Any],
        *,
        is_fallback: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        channel_model_id = binding.get("channel_model_id", model_config["model_code"])
        route_ctx = await resolve_route(category, params, channel, binding)
        endpoint_type = route_ctx.endpoint_type

        await self.trace_logs.append_step(
            trace_id,
            "mode_resolve",
            route_ctx.to_trace_dict(),
        )

        await self.trace_logs.append_step(
            trace_id,
            "channel_select" if not is_fallback else "channel_fallback",
            {
                "channel_code": channel["channel_code"],
                "channel_provider": channel.get("channel_provider"),
                "channel_model_id": channel_model_id,
                "priority": binding.get("priority"),
                "endpoint_type": endpoint_type,
                "is_fallback": is_fallback,
                **route_ctx.to_trace_dict(),
            },
        )

        adapter = create_adapter(channel, trace_id)
        if not adapter:
            fail = {
                "success": False,
                "error_code": "channel_error",
                "error_message": "渠道适配器初始化失败",
                "channel_code": channel["channel_code"],
            }
            return fail, {}, {}

        api_key = adapter.get_api_key_for_category(category)
        if not api_key:
            fail = {
                "success": False,
                "error_code": "channel_error",
                "error_message": "渠道API密钥未配置",
                "channel_code": channel["channel_code"],
            }
            return fail, {}, {}

        logger.info(
            f"[{trace_id}] 调用渠道 {channel['channel_code']} "
            f"endpoint={endpoint_type} model_id={channel_model_id}"
        )

        pending_meta: Dict[str, Any] = {
            "category": category,
            "endpoint_type": endpoint_type,
            "channel_model_id": channel_model_id,
            "channel_provider": channel.get("channel_provider"),
            "base_url": channel.get("base_url", ""),
            "original_params": params,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "awaiting_http": True,
            **route_ctx.to_trace_dict(),
        }
        await self.trace_logs.append_step(trace_id, "channel_invoke_prepare", pending_meta)

        if self._current_task_id:
            from app.services.task_service import get_task_service

            await get_task_service().patch_channel_request(
                self._current_task_id,
                {**pending_meta, "channel_code": channel["channel_code"]},
                channel_code=channel["channel_code"],
            )

        adapter._task_id = self._current_task_id
        adapter._pending_channel_meta = pending_meta
        adapter._outgoing_request_logged = False
        adapter._route_context = route_ctx

        result = await adapter.execute(
            category=category,
            endpoint_type=endpoint_type,
            model_config=model_config,
            params=params,
            channel_model_id=channel_model_id,
            api_key=api_key,
        )
        result["channel_code"] = channel["channel_code"]

        channel_request = self._build_channel_request(
            category, params, channel, channel_model_id, endpoint_type, adapter, route_ctx
        )
        channel_response = self._build_channel_response(adapter, result)

        await self.trace_logs.append_step(
            trace_id,
            "channel_http_response",
            {
                "success": result.get("success"),
                "channel_code": channel["channel_code"],
                "response": channel_response,
                "error_code": result.get("error_code"),
                "error_message": result.get("error_message"),
            },
            level="error" if not result.get("success") else "info",
        )

        attempt = {
            "channel_code": channel["channel_code"],
            "channel_model_id": channel_model_id,
            "endpoint_type": endpoint_type,
            "success": bool(result.get("success")),
            "request": channel_request,
            "response": channel_response,
            "error_code": result.get("error_code"),
            "error_message": result.get("error_message"),
            "duration_ms": result.get("duration_ms"),
            **route_ctx.to_trace_dict(),
        }
        await self.trace_logs.append_channel_attempt(trace_id, attempt)

        if self._current_task_id:
            from app.services.task_service import get_task_service

            await get_task_service().patch_channel_response(
                self._current_task_id, channel_response
            )

        external_task_id = None
        if hasattr(adapter, "_create_response") and adapter._create_response:
            external_task_id = adapter._create_response.get("id") or adapter._create_response.get("task_id")
        if external_task_id:
            result["external_task_id"] = external_task_id

        return result, channel_request, channel_response

    def _finalize_result(
        self,
        result: Dict[str, Any],
        channel_request: Dict[str, Any],
        channel_response: Dict[str, Any],
        *,
        primary_failed: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result["channel_request"] = channel_request
        result["channel_response"] = channel_response
        if primary_failed:
            result["channel_response"] = {
                **channel_response,
                "primary_failed": primary_failed,
            }
        return result

    async def execute(
        self,
        model_code: str,
        category: str,
        params: Dict[str, Any],
        trace_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace_id = trace_id or generate_trace_id()
        self._current_task_id = task_id
        logger.info(f"[{trace_id}] 开始执行: model_code={model_code}, category={category}")

        model_config = await self.model_service.get_by_code(model_code)
        if not model_config:
            return {"success": False, "error_code": "model_not_found", "error_message": f"模型不存在: {model_code}"}

        if model_config.get("status") != "online":
            return {"success": False, "error_code": "model_offline", "error_message": f"模型已下架: {model_code}"}

        is_valid, error_msg = self._validate_params(params, model_config.get("param_schema", {}))
        if not is_valid:
            return {"success": False, "error_code": "validation_error", "error_message": error_msg}

        bindings = self._sorted_bindings(model_config)
        allow_fallback = model_config.get("allow_channel_fallback", True)
        await self.trace_logs.append_step(
            trace_id,
            "channel_bindings",
            {
                "bindings": bindings,
                "selected_order": "priority_desc",
                "allow_channel_fallback": allow_fallback,
            },
        )

        channel, binding = await self._select_channel(model_config)
        if not channel:
            return {"success": False, "error_code": "channel_error", "error_message": "没有可用的渠道绑定"}

        result, channel_request, channel_response = await self._invoke_channel(
            trace_id, category, params, model_config, channel, binding, is_fallback=False
        )

        if result.get("success"):
            return self._finalize_result(result, channel_request, channel_response)

        primary_failed = {
            "channel_code": channel["channel_code"],
            "request": channel_request,
            "response": channel_response,
            "error_code": result.get("error_code"),
            "error_message": result.get("error_message"),
        }
        if not allow_fallback:
            logger.info(f"[{trace_id}] 模型已禁用渠道降级，主渠道失败后直接返回")
            await self.trace_logs.append_step(
                trace_id,
                "channel_fallback_skipped",
                {"reason": "allow_channel_fallback=false"},
            )
            return self._finalize_result(result, channel_request, channel_response)

        logger.info(f"[{trace_id}] 主渠道失败, 尝试备用渠道")

        for fb_binding in bindings:
            if fb_binding["channel_code"] == channel["channel_code"]:
                continue
            fb_channel = await self.channel_service.get_by_code(fb_binding["channel_code"])
            if not fb_channel or fb_channel.get("status") != "active":
                continue
            try:
                fb_result, fb_request, fb_response = await self._invoke_channel(
                    trace_id, category, params, model_config, fb_channel, fb_binding, is_fallback=True
                )
                if fb_result.get("success"):
                    return self._finalize_result(
                        fb_result, fb_request, fb_response, primary_failed=primary_failed
                    )
            except Exception as e:
                logger.error(f"[{trace_id}] 备用渠道调用异常: {e}")
                await self.trace_logs.append_step(
                    trace_id, "channel_fallback_error", {"error": str(e)}, level="error"
                )

        return self._finalize_result(result, channel_request, channel_response)


_gateway = None


def get_model_gateway() -> ModelGateway:
    global _gateway
    if _gateway is None:
        _gateway = ModelGateway()
    return _gateway
