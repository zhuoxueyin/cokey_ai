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

    async def _select_channel(self, model_config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        bindings = model_config.get("channel_bindings", [])
        logger.info(f"[_select_channel] 模型有 {len(bindings)} 个渠道绑定")
        active_bindings = [b for b in bindings if b.get("status", "active") == "active"]
        active_bindings.sort(key=lambda b: b.get("priority", 1), reverse=True)

        for idx, binding in enumerate(active_bindings):
            channel_code = binding.get("channel_code")
            logger.info(f"[_select_channel] 检查绑定 [{idx}]: channel_code={channel_code}")
            channel = await self.channel_service.get_by_code(channel_code)
            logger.info(f"[_select_channel] channel_service.get_by_code({channel_code}) 返回: type={type(channel)}, is_dict={isinstance(channel, dict)}")
            if channel and channel.get("status") == "active":
                logger.info(f"[_select_channel] 选中渠道: {channel_code}")
                return channel, binding
            else:
                logger.warning(f"[_select_channel] 渠道 {channel_code} 不可用: status={channel.get('status') if channel else 'None'}")
        logger.warning(f"[_select_channel] 未找到任何可用渠道")
        return None, None

    async def execute(self, model_code: str, category: str, params: Dict[str, Any],
                      trace_id: Optional[str] = None) -> Dict[str, Any]:
        trace_id = trace_id or generate_trace_id()
        start_time = time.time()
        logger.info(f"[{trace_id}] 开始执行: model_code={model_code}, category={category}")

        model_config = await self.model_service.get_by_code(model_code)
        logger.info(f"[{trace_id}] 获取模型配置: type={type(model_config)}, is_dict={isinstance(model_config, dict)}")
        if not model_config:
            return {"success": False, "error_code": "model_not_found", "error_message": f"模型不存在: {model_code}"}

        model_status = model_config.get("status") if isinstance(model_config, dict) else "INVALID"
        logger.info(f"[{trace_id}] 模型状态: {model_status}")
        if model_status != "online":
            return {"success": False, "error_code": "model_offline", "error_message": f"模型已下架: {model_code}"}

        is_valid, error_msg = self._validate_params(params, model_config.get("param_schema", {}))
        if not is_valid:
            return {"success": False, "error_code": "validation_error", "error_message": error_msg}

        logger.info(f"[{trace_id}] 调用 _select_channel...")
        channel, binding = await self._select_channel(model_config)
        logger.info(f"[{trace_id}] _select_channel 返回: channel_type={type(channel)}, binding_type={type(binding)}")
        if not channel:
            return {"success": False, "error_code": "channel_error", "error_message": "没有可用的渠道绑定"}

        try:
            channel_model_id = binding.get("channel_model_id", model_code)
        except AttributeError as e:
            logger.error(f"[{trace_id}] binding 不是字典: {type(binding)}, value={binding}")
            return {"success": False, "error_code": "channel_error", "error_message": "渠道绑定数据格式错误"}

        adapter = create_adapter(channel, trace_id)
        if not adapter:
            return {"success": False, "error_code": "channel_error", "error_message": "渠道适配器初始化失败"}

        try:
            api_key = adapter.get_api_key_for_category(category)
            logger.info(f"[{trace_id}] 获取 API Key: has_key={bool(api_key)}, key_length={len(api_key) if api_key else 0}")
        except Exception as e:
            logger.error(f"[{trace_id}] 获取 API Key 失败: {e}, channel_type={type(channel)}, channel_data={channel}")
            return {"success": False, "error_code": "channel_error", "error_message": f"渠道配置错误: {e}"}

        if not api_key:
            return {"success": False, "error_code": "channel_error", "error_message": "渠道API密钥未配置"}

        import json
        logger.info(f"[{trace_id}] 选中渠道: {channel['channel_code']}, 模型ID: {channel_model_id}")
        logger.info(f"[{trace_id}] ═══════ 网关调用完整入参 ═══════")
        logger.info(f"[{trace_id}] category={category}")
        logger.info(f"[{trace_id}] channel_model_id={channel_model_id}")
        logger.info(f"[{trace_id}] base_url={channel.get('base_url')}")
        logger.info(f"[{trace_id}] api_key_last_8=...{api_key[-8:] if api_key else 'NULL'}")
        try:
            logger.info(f"[{trace_id}] params={json.dumps(params, ensure_ascii=False, indent=2)}")
        except Exception as _e:
            logger.info(f"[{trace_id}] params_raw={params}")
        logger.info(f"[{trace_id}] ════════════════════════════════")

        # 记录渠道请求参数
        channel_request = {
            "category": category,
            "channel_model_id": channel_model_id,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await adapter.execute(
            category=category,
            model_config=model_config,
            params=params,
            channel_model_id=channel_model_id,
            api_key=api_key
        )
        
        # 记录渠道响应（视频类型包含创建和查询两次响应）
        channel_response = {}
        if hasattr(adapter, '_create_response') and adapter._create_response:
            # 视频异步任务：记录创建响应
            channel_response["create"] = adapter._create_response
            logger.info(f"[{trace_id}] 记录创建响应: task_id={adapter._create_response.get('id') or adapter._create_response.get('task_id')}")
        if result.get('data'):
            # 记录查询响应（最终结果）
            channel_response["query"] = result['data']
            logger.info(f"[{trace_id}] 记录查询响应: status={result['data'].get('status')}")
        
        # 如果是视频异步任务，记录轮询详情
        if hasattr(adapter, '_poll_attempts') and adapter._poll_attempts:
            channel_response["poll_details"] = adapter._poll_attempts

        # #region debug-image-error
        logger.info(f"[{trace_id}] ═══════ 适配器执行结果 ═══════")
        logger.info(f"[{trace_id}] result_type={type(result)}")
        logger.info(f"[{trace_id}] result_keys={list(result.keys()) if isinstance(result, dict) else 'NOT_DICT'}")
        if isinstance(result, dict):
            logger.info(f"[{trace_id}] success={result.get('success')}")
            logger.info(f"[{trace_id}] error_code={result.get('error_code')}")
            logger.info(f"[{trace_id}] error_message={result.get('error_message')}")
            if 'data' in result:
                try:
                    logger.info(f"[{trace_id}] data={json.dumps(result['data'], ensure_ascii=False, indent=2)[:500]}")
                except Exception:
                    logger.info(f"[{trace_id}] data={str(result['data'])[:500]}")
        logger.info(f"[{trace_id}] ════════════════════════════════")
        # #endregion debug-image-error

        if not result.get("success"):
            error_code = result.get("error_code", "internal_error")
            logger.info(f"[{trace_id}] 主渠道失败, 尝试切换备用渠道, code={error_code}")
            fallback_result = await self._try_fallback_channels(model_config, category, params, trace_id, exclude_channel=channel["channel_code"])
            if fallback_result and fallback_result.get("success"):
                return fallback_result

        # 添加渠道请求和响应信息到结果中
        result["channel_request"] = channel_request
        result["channel_response"] = channel_response
        
        # 提取外部任务ID（用于服务器重启后恢复状态）
        external_task_id = None
        if hasattr(adapter, '_create_response') and adapter._create_response:
            external_task_id = adapter._create_response.get('id') or adapter._create_response.get('task_id')
        result["external_task_id"] = external_task_id

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
