"""协议路由解析：InvocationMode → ProtocolProfile → endpoint_type。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.core.builtin_protocol_profiles import BUILTIN_PROFILE_BY_ID, MODEL_ID_PROFILE_HINTS
from app.core.invocation_mode import (
    CATEGORY_DEFAULT_MODES,
    InvocationMode,
    mode_to_legacy_endpoint_type,
    resolve_invocation_mode,
)
from app.core.logging_config import get_logger
from app.services.protocol_profile_service import get_protocol_profile_service

logger = get_logger()


@dataclass
class RouteContext:
    invocation_mode: str
    endpoint_type: str
    protocol_slot: str = ""
    profile_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    route_source: str = "legacy"  # binding | hint | legacy | profile

    def to_trace_dict(self) -> Dict[str, Any]:
        return {
            "invocation_mode": self.invocation_mode,
            "endpoint_type": self.endpoint_type,
            "protocol_slot": self.protocol_slot,
            "profile_id": self.profile_id,
            "route_source": self.route_source,
        }


def _infer_profile_id_from_model(
    provider: str,
    channel_model_id: str,
    mode: str,
) -> Optional[str]:
    model_lower = (channel_model_id or "").lower()
    provider_lower = (provider or "").lower()
    for hint in MODEL_ID_PROFILE_HINTS:
        if hint.get("provider") and hint["provider"] != provider_lower:
            continue
        if hint["match"] in model_lower:
            return hint.get("modes", {}).get(mode)
    return None


def _legacy_determine_endpoint_type(
    category: str,
    params: Dict[str, Any],
    channel: Optional[Dict[str, Any]],
    channel_model_id: str,
    mode: str,
) -> str:
    """保留旧逻辑作为无 profile 时的兜底。"""
    if channel:
        from app.core.apiyi_image import is_apiyi_conversational_image_model
        from app.core.chat_image_protocol import chat_image_slot_for_mode

        prov = channel.get("channel_provider")
        if prov == "volcengine" and mode in (
            InvocationMode.TEXT_TO_VIDEO.value,
            InvocationMode.IMAGE_TO_VIDEO.value,
        ):
            return "video"
        if prov == "apiyi" and is_apiyi_conversational_image_model(channel_model_id):
            return "chat"

        endpoints = channel.get("endpoints", [])
        if any(ep.get("type") == "chat" for ep in endpoints):
            if category in ("text", "image"):
                return "chat"

    return mode_to_legacy_endpoint_type(mode, category)


def binding_supports_mode(binding: Dict[str, Any], mode: str, category: str) -> bool:
    supported = binding.get("supported_modes")
    if not supported:
        return mode in CATEGORY_DEFAULT_MODES.get(category, [mode])
    return mode in supported


async def resolve_route(
    category: str,
    params: Dict[str, Any],
    channel: Dict[str, Any],
    binding: Dict[str, Any],
) -> RouteContext:
    """
    解析完整路由上下文。
    优先级：binding.mode_profiles[mode] → binding.protocol_profile_id → model_id 推断 → legacy
    """
    mode = resolve_invocation_mode(category, params)
    channel_model_id = binding.get("channel_model_id", "")
    provider = channel.get("channel_provider", "")

    if not binding_supports_mode(binding, mode, category):
        logger.warning(
            f"绑定 {binding.get('channel_code')} 不支持模式 {mode}，仍将尝试 legacy 路由"
        )

    profile_service = get_protocol_profile_service()
    profile_id: Optional[str] = None
    route_source = "legacy"

    mode_profiles = binding.get("mode_profiles") or {}
    if isinstance(mode_profiles, dict) and mode in mode_profiles:
        profile_id = mode_profiles[mode]
        route_source = "binding"
    elif binding.get("protocol_profile_id"):
        profile_id = binding["protocol_profile_id"]
        route_source = "binding"

    if not profile_id:
        profile_id = _infer_profile_id_from_model(provider, channel_model_id, mode)
        if profile_id:
            route_source = "hint"

    profile: Optional[Dict[str, Any]] = None
    if profile_id:
        profile = await profile_service.get_by_profile_id(profile_id)
        if profile:
            endpoint_type = profile.get("endpoint_type") or mode_to_legacy_endpoint_type(mode, category)
            logger.info(
                f"[路由] mode={mode} profile={profile_id} "
                f"slot={profile.get('protocol_slot')} endpoint={endpoint_type} source={route_source}"
            )
            return RouteContext(
                invocation_mode=mode,
                endpoint_type=endpoint_type,
                protocol_slot=profile.get("protocol_slot", ""),
                profile_id=profile_id,
                profile=profile,
                route_source=route_source,
            )
        logger.warning(f"协议画像不存在: {profile_id}，回退 legacy")

    endpoint_type = _legacy_determine_endpoint_type(
        category, params, channel, channel_model_id, mode
    )
    # 尝试从内置按 endpoint_type 找 protocol_slot
    protocol_slot = ""
    for builtin in BUILTIN_PROFILE_BY_ID.values():
        if (
            builtin.get("invocation_mode") == mode
            and builtin.get("endpoint_type") == endpoint_type
            and (not builtin.get("provider") or builtin.get("provider") in (provider, "*"))
        ):
            protocol_slot = builtin.get("protocol_slot", "")
            break
    if not protocol_slot and endpoint_type == "chat" and mode in (
        InvocationMode.TEXT_TO_IMAGE.value,
        InvocationMode.IMAGE_TO_IMAGE.value,
    ):
        protocol_slot = chat_image_slot_for_mode(mode)

    logger.info(f"[路由] legacy mode={mode} endpoint={endpoint_type} slot={protocol_slot}")
    return RouteContext(
        invocation_mode=mode,
        endpoint_type=endpoint_type,
        protocol_slot=protocol_slot,
        profile_id=None,
        profile=None,
        route_source="legacy",
    )
