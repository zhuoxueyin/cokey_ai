from __future__ import annotations

from typing import Any, Dict, Optional

from app.adapters.base import BaseChannelAdapter
from app.adapters.weelinking import WeelinkingAdapter
from app.core.logging_config import get_logger

logger = get_logger()


def create_adapter(channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
    channel_type = channel_config.get("channel_type", "")
    channel_code = channel_config.get("channel_code", "")

    if channel_type == "aggregator" or channel_code.startswith("weelink") or "weelink" in channel_code.lower():
        return WeelinkingAdapter(channel_config, trace_id)

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
ChannelAdapterRegistry.register("direct", WeelinkingAdapter)
ChannelAdapterRegistry.register("weelinking", WeelinkingAdapter)
