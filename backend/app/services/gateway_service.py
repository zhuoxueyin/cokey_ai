from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time

from app.core.logging_config import get_logger
from app.core.utils import generate_trace_id
from app.services.channel_service import get_channel_service
from app.services.model_service import get_model_service
from app.adapters import create_adapter

logger = get_logger()


class ModelGateway:
    def __init__(self):
        self.channel_service = get_channel_service()
        self.model_service = get_model_service()

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

    def _select_channel(self, model_config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        bindings = model_config.get("channel_bindings", [])
        active_bindings = [b for b in bindings if b.get("status", "active") == "active"]
        active_bindings.sort(key=lambda b: b.get("priority", 1), reverse=True)

        for binding in active_bindings:
            channel = self.channel_service.get_by_code(binding["channel_code"])
            if channel and channel.get("status") == "active":
                return channel, binding
        return None, None

    async def execute(self, model_code: str, category: str, params: Dict[str, Any],
                      trace_id: Optional[str] = None) -> Dict[str, Any]:
        trace_id = trace_id or generate_trace_id()
        start_time = time.time()
        logger.info(f"[{trace_id}] 开始执行: model_code={model_code}, category={category}")

        model_config = await self.model_service.get_by_code(model_code)
        if not model_config:
            return {"success": False, "error_code": "model_not_found", "error_message": f"模型不存在: {model_code}"}

        if model_config.get("status") != "online":
            return {"success": False, "error_code": "model_offline", "error_message": f"模型已下架: {model_code}"}

        is_valid, error_msg = self._validate_params(params, model_config.get("param_schema", {}))
        if not is_valid:
            return {"success": False, "error_code": "validation_error", "error_message": error_msg}

        channel, binding = self._select_channel(model_config)
        if not channel:
            return {"success": False, "error_code": "channel_error", "error_message": "没有可用的渠道绑定"}

        channel_model_id = binding.get("channel_model_id", model_code)
        adapter = create_adapter(channel, trace_id)
        if not adapter:
            return {"success": False, "error_code": "channel_error", "error_message": "渠道适配器初始化失败"}

        api_key = adapter.get_api_key_for_category(category)
        if not api_key:
            return {"success": False, "error_code": "channel_error", "error_message": "渠道API密钥未配置"}

        logger.info(f"[{trace_id}] 选中渠道: {channel['channel_code']}, 模型ID: {channel_model_id}")

        result = await adapter.execute(
            category=category,
            model_config=model_config,
            params=params,
            channel_model_id=channel_model_id,
            api_key=api_key
        )

        if not result.get("success"):
            error_code = result.get("error_code", "internal_error")
            logger.info(f"[{trace_id}] 主渠道失败, 尝试切换备用渠道, code={error_code}")
            fallback_result = await self._try_fallback_channels(model_config, category, params, trace_id, exclude_channel=channel["channel_code"])
            if fallback_result and fallback_result.get("success"):
                return fallback_result

        return result

    async def _try_fallback_channels(self, model_config: Dict[str, Any], category: str,
                                      params: Dict[str, Any], trace_id: str,
                                      exclude_channel: str) -> Optional[Dict[str, Any]]:
        bindings = model_config.get("channel_bindings", [])
        other_bindings = [b for b in bindings
                          if b.get("status", "active") == "active" and b["channel_code"] != exclude_channel]
        other_bindings.sort(key=lambda b: b.get("priority", 1), reverse=True)

        for binding in other_bindings:
            try:
                channel = await self.channel_service.get_by_code(binding["channel_code"])
                if not channel or channel.get("status") != "active":
                    continue

                channel_model_id = binding.get("channel_model_id", model_config["model_code"])
                adapter = create_adapter(channel, trace_id)
                if not adapter:
                    continue

                api_key = adapter.get_api_key_for_category(category)
                if not api_key:
                    continue

                logger.info(f"[{trace_id}] 切换到备用渠道: {channel['channel_code']}")
                result = await adapter.execute(
                    category=category,
                    model_config=model_config,
                    params=params,
                    channel_model_id=channel_model_id,
                    api_key=api_key
                )
                if result.get("success"):
                    return result
            except Exception as e:
                logger.error(f"[{trace_id}] 备用渠道调用异常: {e}")
                continue

        return None


_gateway = None


def get_model_gateway() -> ModelGateway:
    global _gateway
    if _gateway is None:
        _gateway = ModelGateway()
    return _gateway
