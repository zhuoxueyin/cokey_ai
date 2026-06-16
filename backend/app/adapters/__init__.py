from __future__ import annotations

from typing import Any, Dict, Optional

from app.adapters.base import BaseChannelAdapter
from app.adapters.weelinking import WeelinkingAdapter
from app.adapters.volcengine import VolcengineAdapter
from app.core.logging_config import get_logger

logger = get_logger()


def create_adapter(channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
    channel_type = channel_config.get("channel_type", "")
    channel_code = channel_config.get("channel_code", "")

    if channel_type == "aggregator" or channel_code.startswith("weelink") or "weelink" in channel_code.lower():
        return WeelinkingAdapter(channel_config, trace_id)
    
    # Volcengine 改为平台直连模式（direct 类型）
    if channel_type == "direct" and (channel_code.startswith("volcengine") or "volcengine" in channel_code.lower()):
        return VolcengineAdapter(channel_config, trace_id)
    
    # 兼容旧配置：如果 channel_type 仍为 volcengine，也使用 VolcengineAdapter
    if channel_type == "volcengine" or channel_code.startswith("volcengine") or "volcengine" in channel_code.lower():
        logger.warning(f"[{trace_id}] 检测到旧版 volcengine 渠道类型，建议改为 direct 类型")
        return VolcengineAdapter(channel_config, trace_id)

    logger.warning(f"[{trace_id}] 未找到适配的渠道适配器: channel_code={channel_code}, channel_type={channel_type}, 将使用通用适配器")
    return WeelinkingAdapter(channel_config, trace_id)


class ChannelAdapterRegistry:
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, channel_type: str, adapter_class: type):
        cls._registry[channel_type] = adapter_class
        logger.info(f"渠道适配器已注册: {channel_type}")

    @classmethod
    def get(cls, channel_type: str, channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
        if channel_type in cls._registry:
            return cls._registry[channel_type](channel_config, trace_id)
        return WeelinkingAdapter(channel_config, trace_id)


ChannelAdapterRegistry.register("aggregator", WeelinkingAdapter)
ChannelAdapterRegistry.register("direct", WeelinkingAdapter)  # 默认直连使用 WeelinkingAdapter
ChannelAdapterRegistry.register("weelinking", WeelinkingAdapter)
# Volcengine 作为特殊的直连渠道，单独注册
ChannelAdapterRegistry.register("volcengine", VolcengineAdapter)
