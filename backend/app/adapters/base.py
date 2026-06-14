from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

from app.core.logging_config import get_logger

logger = get_logger()


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

    @abstractmethod
    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """通用参数转渠道专属参数"""
        pass

    @abstractmethod
    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """调用渠道接口"""
        pass

    @abstractmethod
    async def parse_result(self, category: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """渠道返回结果转平台统一格式"""
        pass

    @abstractmethod
    def parse_error(self, exception: Exception) -> tuple[str, str]:
        """渠道异常转平台统一错误码和消息"""
        pass

    def get_api_key_for_category(self, category: str) -> str:
        auth_config = self.channel_config.get("auth_config", {})
        key_map = {
            "text": "text_api_key",
            "image": "image_api_key",
            "video": "video_api_key"
        }
        return auth_config.get(key_map.get(category, "text_api_key"), "") or auth_config.get("text_api_key", "")

    async def execute(
        self,
        category: str,
        model_config: Dict[str, Any],
        params: Dict[str, Any],
        channel_model_id: str,
        api_key: str
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"[{self.trace_id}] 开始调用渠道 {self.channel_code}, 分类={category}")

        try:
            channel_params = await self.convert_params(model_config, params)
            logger.info(f"[{self.trace_id}] 参数转换完成, 渠道参数={channel_params}")

            raw_result = await self.call_api(category, channel_params, channel_model_id, api_key)
            logger.info(f"[{self.trace_id}] 渠道调用成功")

            result = await self.parse_result(category, raw_result)

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
