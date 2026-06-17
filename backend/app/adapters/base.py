from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

from app.core.logging_config import get_logger
from app.core.config import settings
from app.core.config_engine import ConfigEngine

logger = get_logger()


def _is_placeholder(value: str) -> bool:
    """判断是否为占位符（未配置的默认值）"""
    if not value:
        return True
    v = value.strip().lower()
    return (
        v.startswith("your-")
        or v == "xxx"
        or v.startswith("placeholder")
        or v.startswith("example")
    )


class BaseChannelAdapter(ABC):
    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        self.channel_config = channel_config
        self.trace_id = trace_id
        self.channel_code = channel_config.get("channel_code", "unknown")
        self.base_url = channel_config.get("base_url", "")
        self.retry_config = channel_config.get("retry_config", {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        })
        # 记录HTTP请求信息
        self._http_request_info: Optional[Dict[str, Any]] = None

    @abstractmethod
    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any], endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用参数转渠道专属参数"""
        pass

    @abstractmethod
    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str, endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调用渠道接口"""
        pass

    @abstractmethod
    async def parse_result(self, category: str, raw_result: Dict[str, Any], endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """渠道返回结果转平台统一格式"""
        pass

    @abstractmethod
    def parse_error(self, exception: Exception) -> tuple[str, str]:
        """渠道异常转平台统一错误码和消息"""
        pass

    async def query_task(self, external_task_id: str) -> Dict[str, Any]:
        """查询外部任务状态（用于服务器重启后恢复任务）
        
        默认实现返回失败，具体渠道适配器需要覆盖此方法
        """
        logger.warning(f"[{self.trace_id}] 渠道 {self.channel_code} 未实现 query_task 方法")
        return {"success": False, "error_code": "not_implemented", "error_message": "该渠道不支持任务查询"}

    def get_api_key_for_category(self, category: str) -> str:
        """获取渠道 API Key：优先用数据库值，否则从 settings.weelink_api_key 读取
        
        新配置：所有分类共用一个 api_key
        """
        auth_config = self.channel_config.get("auth_config", {})
        raw_value = auth_config.get("api_key", "")
        
        # 兼容旧配置格式（多个 api_key）
        if not raw_value:
            key_map = {
                "text": "text_api_key",
                "image": "image_api_key",
                "video": "video_api_key"
            }
            field_name = key_map.get(category, "text_api_key")
            raw_value = auth_config.get(field_name, "") or auth_config.get("text_api_key", "")

        if _is_placeholder(raw_value):
            fallback_key = (settings.weelink_api_key or "").strip()
            if fallback_key and not _is_placeholder(fallback_key):
                logger.info(
                    f"[{self.trace_id}] 渠道 {self.channel_code}: "
                    f"api_key 使用环境变量 WEELINK_API_KEY (长度={len(fallback_key)})"
                )
                return fallback_key
            logger.warning(
                f"[{self.trace_id}] 渠道 {self.channel_code}: "
                f"api_key 未配置（数据库值为占位符，settings.weelink_api_key 也为空）"
            )
            return ""

        return raw_value

    def _get_endpoint_by_type(self, endpoint_type: str) -> Optional[Dict[str, Any]]:
        """根据端点类型获取渠道配置的端点信息"""
        endpoints = self.channel_config.get("endpoints", [])
        for endpoint in endpoints:
            if endpoint.get("type") == endpoint_type:
                return endpoint
        return None

    async def execute(
        self,
        category: str,
        endpoint_type: Optional[str] = None,
        model_config: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        channel_model_id: str = "",
        api_key: str = ""
    ) -> Dict[str, Any]:
        start_time = time.time()
        # 使用 endpoint_type，如果没有则使用 category
        use_endpoint_type = endpoint_type or category
        logger.info(f"[{self.trace_id}] 开始调用渠道 {self.channel_code}, 分类={category}, 端点类型={use_endpoint_type}")

        # 获取端点配置
        endpoint_config = self._get_endpoint_by_type(use_endpoint_type)
        if not endpoint_config:
            logger.warning(f"[{self.trace_id}] 渠道 {self.channel_code} 未配置端点类型 {use_endpoint_type}")
            # 尝试使用默认端点（兼容旧配置）
            endpoint_config = self._get_endpoint_by_type(category)

        try:
            channel_params = await self.convert_params(model_config or {}, params or {}, endpoint_config)
            logger.info(f"[{self.trace_id}] 参数转换完成, 渠道参数={channel_params}")

            raw_result = await self.call_api(category, channel_params, channel_model_id, api_key, endpoint_config)
            logger.info(f"[{self.trace_id}] 渠道调用成功")

            # 优先使用配置引擎解析响应，如果没有配置则使用默认解析
            endpoint_type = endpoint_config.get("type") if endpoint_config else None
            has_response_config = endpoint_config and (
                endpoint_config.get("response_mappings")
                or endpoint_config.get("response_extract_path")
            )

            if has_response_config and endpoint_type:
                response_data = raw_result.get("response", raw_result)
                parsed = ConfigEngine.parse_response(
                    endpoint_config=endpoint_config,
                    response=response_data,
                    endpoint_type=endpoint_type,
                    trace_id=self.trace_id,
                )
                result = parsed
                logger.info(f"[{self.trace_id}] 使用配置化响应解析: type={parsed.get('type')}")
            else:
                result = await self.parse_result(category, raw_result, endpoint_config)

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"[{self.trace_id}] 结果解析完成, 耗时={duration_ms}ms")

            return {
                "success": True,
                "data": result,
                "duration_ms": duration_ms,
                "channel_code": self.channel_code,
                "raw_result": raw_result
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_code, error_message = self.parse_error(e)
            logger.error(f"[{self.trace_id}] 渠道调用失败: code={error_code}, msg={error_message}, 耗时={duration_ms}ms")
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
                "duration_ms": duration_ms,
                "channel_code": self.channel_code,
            }
