"""InvocationMode 与协议路由单元测试。"""
import asyncio

from app.core.invocation_mode import (
    InvocationMode,
    has_reference_images,
    resolve_invocation_mode,
    mode_to_legacy_endpoint_type,
)
from app.core.protocol_resolver import resolve_route, binding_supports_mode


def test_resolve_text_chat():
    assert resolve_invocation_mode("text", {"prompt": "hi"}) == InvocationMode.TEXT_CHAT.value


def test_resolve_text_to_image():
    assert resolve_invocation_mode("image", {"prompt": "a cat"}) == InvocationMode.TEXT_TO_IMAGE.value


def test_resolve_image_to_image():
    assert resolve_invocation_mode("image", {"prompt": "x", "images": ["https://cdn/a.png"]}) == (
        InvocationMode.IMAGE_TO_IMAGE.value
    )


def test_resolve_manual_override():
    params = {"prompt": "x", "invocation_mode": "text_to_image"}
    assert resolve_invocation_mode("image", params) == "text_to_image"


def test_has_reference_images():
    assert has_reference_images({"images": []}) is False
    assert has_reference_images({"images": ["u"]}) is True
    assert has_reference_images({"image": "https://x"}) is True


def test_mode_to_legacy_endpoint():
    assert mode_to_legacy_endpoint_type("text_to_image", "image") == "image"
    assert mode_to_legacy_endpoint_type("image_to_image", "image") == "image_edits"


def test_binding_supports_mode_default():
    binding = {"channel_code": "c1"}
    assert binding_supports_mode(binding, "text_to_image", "image") is True
    assert binding_supports_mode(binding, "text_chat", "image") is False


def test_binding_supports_mode_explicit():
    binding = {"supported_modes": ["text_to_image"]}
    assert binding_supports_mode(binding, "text_to_image", "image") is True
    assert binding_supports_mode(binding, "image_to_image", "image") is False


def test_resolve_route_apiyi_vip_text_to_image():
  async def _run():
        channel = {"channel_provider": "apiyi", "channel_code": "apiyi_1", "base_url": "https://x"}
        binding = {"channel_code": "apiyi_1", "channel_model_id": "gpt-image-2-vip", "priority": 20}
        ctx = await resolve_route("image", {"prompt": "cat"}, channel, binding)
        assert ctx.invocation_mode == "text_to_image"
        assert ctx.endpoint_type == "chat"
        assert ctx.profile_id == "apiyi.gpt-image-2-vip.text_to_image"
        assert ctx.protocol_slot == "openai.chat.image.text_to_image"

  asyncio.run(_run())


def test_resolve_route_apiyi_all_with_mode_profiles():
  async def _run():
        channel = {"channel_provider": "apiyi", "channel_code": "apiyi_1", "base_url": "https://x"}
        binding = {
            "channel_code": "apiyi_1",
            "channel_model_id": "gpt-image-2-all",
            "mode_profiles": {
                "text_to_image": "apiyi.gpt-image-2-all.text_to_image",
                "image_to_image": "apiyi.gpt-image-2-all.image_to_image",
            },
        }
        ctx = await resolve_route("image", {"prompt": "cat"}, channel, binding)
        assert ctx.endpoint_type == "chat"
        assert ctx.route_source == "binding"

        ctx2 = await resolve_route(
            "image", {"prompt": "edit", "images": ["https://cdn/a.png"]}, channel, binding
        )
        assert ctx2.invocation_mode == "image_to_image"
        assert ctx2.endpoint_type == "chat"

  asyncio.run(_run())


def test_resolve_route_apiyi_vip_image_to_image_chat_slot():
  async def _run():
        channel = {"channel_provider": "apiyi", "channel_code": "apiyi_1", "base_url": "https://x"}
        binding = {"channel_code": "apiyi_1", "channel_model_id": "gpt-image-2-vip", "priority": 20}
        ctx = await resolve_route(
            "image", {"prompt": "edit", "images": ["https://cdn/a.png"]}, channel, binding
        )
        assert ctx.invocation_mode == "image_to_image"
        assert ctx.endpoint_type == "chat"
        assert ctx.profile_id == "apiyi.gpt-image-2-vip.image_to_image"
        assert ctx.protocol_slot == "openai.chat.image.image_to_image"

  asyncio.run(_run())


def test_resolve_route_apiyi_vip_legacy_generations_profile():
  async def _run():
        channel = {"channel_provider": "apiyi", "channel_code": "apiyi_1", "base_url": "https://x"}
        binding = {
            "channel_code": "apiyi_1",
            "channel_model_id": "gpt-image-2-vip",
            "mode_profiles": {
                "text_to_image": "apiyi.gpt-image-2-vip.generations.text_to_image",
            },
        }
        ctx = await resolve_route("image", {"prompt": "cat"}, channel, binding)
        assert ctx.endpoint_type == "image"
        assert ctx.protocol_slot == "openai.images.generations"

  asyncio.run(_run())
