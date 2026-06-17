from __future__ import annotations

from typing import Any, Dict, Optional

from app.adapters.base import BaseChannelAdapter
from app.adapters.weelinking import WeelinkingAdapter
from app.adapters.volcengine import VolcengineAdapter
from app.core.logging_config import get_logger

logger = get_logger()


def create_adapter(channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
    """根据渠道配置选择合适的适配器

    优先级：
    1. channel_provider 精确匹配（新字段）
    2. channel_code 前缀/包含匹配（兼容旧数据）
    3. channel_type 粗粒度路由
    """
    channel_type = channel_config.get("channel_type", "")
    channel_code = channel_config.get("channel_code", "")
    channel_provider = channel_config.get("channel_provider")

    # 优先级1：精确匹配 channel_provider
    if channel_provider == "weelinking":
        logger.info(f"[{trace_id}] 使用 WeeLinking 适配器 (provider=weelinking)")
        return WeelinkingAdapter(channel_config, trace_id)
    if channel_provider == "apiyi":
        # APIYi 同样使用 OpenAI 兼容协议
        logger.info(f"[{trace_id}] 使用 WeeLinking 适配器 (provider=apiyi, OpenAI 兼容)")
        return WeelinkingAdapter(channel_config, trace_id)
    if channel_provider == "volcengine":
        logger.info(f"[{trace_id}] 使用 Volcengine 适配器 (provider=volcengine)")
        return VolcengineAdapter(channel_config, trace_id)

    # 优先级2：根据 channel_code 推断
    if "weelink" in channel_code.lower() or "weelink" in channel_code.lower():
        return WeelinkingAdapter(channel_config, trace_id)
    if "volcengine" in channel_code.lower() or "volcano" in channel_code.lower() or "huoshan" in channel_code.lower():
        return VolcengineAdapter(channel_config, trace_id)
    if "apiyi" in channel_code.lower():
        return WeelinkingAdapter(channel_config, trace_id)

    # 优先级3：channel_type 粗粒度
    if channel_type == "direct":
        # 直连渠道默认用 Volcengine 适配器（可根据后续需求扩展）
        logger.info(f"[{trace_id}] 直连渠道默认使用 Volcengine 适配器")
        return VolcengineAdapter(channel_config, trace_id)

    # 兼容旧配置：channel_type=volcengine
    if channel_type == "volcengine":
        logger.warning(f"[{trace_id}] 检测到旧版 channel_type=volcengine，建议改为 channel_type=direct, channel_provider=volcengine")
        return VolcengineAdapter(channel_config, trace_id)

    # 默认：聚合渠道走 WeeLinking/OpenAI 兼容
    logger.warning(f"[{trace_id}] 未匹配到精确适配器，默认使用 WeeLinking 适配器")
    return WeelinkingAdapter(channel_config, trace_id)


class ChannelAdapterRegistry:
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, channel_provider: str, adapter_class: type):
        cls._registry[channel_provider] = adapter_class
        logger.info(f"渠道适配器已注册: provider={channel_provider}")

    @classmethod
    def get(cls, channel_provider: str, channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
        if channel_provider and channel_provider in cls._registry:
            return cls._registry[channel_provider](channel_config, trace_id)
        return WeelinkingAdapter(channel_config, trace_id)


ChannelAdapterRegistry.register("weelinking", WeelinkingAdapter)
ChannelAdapterRegistry.register("apiyi", WeelinkingAdapter)
ChannelAdapterRegistry.register("volcengine", VolcengineAdapter)
ChannelAdapterRegistry.register("aggregator", WeelinkingAdapter)
ChannelAdapterRegistry.register("direct", VolcengineAdapter)
