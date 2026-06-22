"""内置协议画像种子 — 无 DB 配置时也可路由。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.chat_image_protocol import (
    OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
    OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
)
from app.core.invocation_mode import InvocationMode


def _p(
    profile_id: str,
    name: str,
    *,
    provider: str,
    protocol_slot: str,
    invocation_mode: str,
    endpoint_type: str,
    path: str,
    builder: str | None = None,
    parser: str | None = None,
    size_strategy: str | None = None,
    forbidden_fields: List[str] | None = None,
    method: str = "POST",
    content_type: str = "application/json",
    description: str = "",
) -> Dict[str, Any]:
    return {
        "profile_id": profile_id,
        "name": name,
        "provider": provider,
        "protocol_slot": protocol_slot,
        "invocation_mode": invocation_mode,
        "endpoint_type": endpoint_type,
        "http": {
            "path": path,
            "method": method,
            "content_type": content_type,
        },
        "request": {
            "builder": builder,
            "forbidden_fields": forbidden_fields or [],
            "size_strategy": size_strategy,
            "body_params": None,
            "extra": {},
        },
        "response": {
            "parser": parser,
            "extract_path": None,
            "extra": {},
        },
        "description": description,
        "status": "active",
        "is_builtin": True,
    }


BUILTIN_PROTOCOL_PROFILES: List[Dict[str, Any]] = [
    # —— APIYI gpt-image-2-all（对话式）——
    _p(
        "apiyi.gpt-image-2-all.text_to_image",
        "APIYI gpt-image-2-all 对话式文生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
        invocation_mode=InvocationMode.TEXT_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="Chat Completions 纯文本 messages → 文生图，画幅写入 prompt",
    ),
    _p(
        "apiyi.gpt-image-2-all.image_to_image",
        "APIYI gpt-image-2-all 对话式图生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
        invocation_mode=InvocationMode.IMAGE_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="user 消息含 image_url；多轮改图须把上轮输出 URL 放入新一轮 user",
    ),
    # —— APIYI gpt-image-2-vip（对话式主推）——
    _p(
        "apiyi.gpt-image-2-vip.text_to_image",
        "APIYI gpt-image-2-vip 对话式文生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
        invocation_mode=InvocationMode.TEXT_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="Chat Completions 对话式文生图，VIP 尺寸写入 prompt",
    ),
    _p(
        "apiyi.gpt-image-2-vip.image_to_image",
        "APIYI gpt-image-2-vip 对话式图生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
        invocation_mode=InvocationMode.IMAGE_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="user 消息含 image_url；多轮改图须把上轮输出 URL 放入新一轮 user",
    ),
    _p(
        "apiyi.gpt-image-2-vip.generations.text_to_image",
        "APIYI gpt-image-2-vip 文生图（Images API）",
        provider="apiyi",
        protocol_slot="openai.images.generations",
        invocation_mode=InvocationMode.TEXT_TO_IMAGE.value,
        endpoint_type="image",
        path="images/generations",
        builder="apiyi_vip_generations",
        parser="openai_images",
        size_strategy="api_field",
        forbidden_fields=["quality", "n", "aspect_ratio"],
        description="兼容官转：/v1/images/generations",
    ),
    _p(
        "apiyi.gpt-image-2-vip.edits.image_to_image",
        "APIYI gpt-image-2-vip 图生图（Images API）",
        provider="apiyi",
        protocol_slot="openai.images.edits",
        invocation_mode=InvocationMode.IMAGE_TO_IMAGE.value,
        endpoint_type="image_edits",
        path="images/edits",
        builder="weelink_default",
        parser="openai_images",
        size_strategy="api_field",
        forbidden_fields=["quality", "n", "aspect_ratio"],
        content_type="multipart/form-data",
        description="兼容官转：/v1/images/edits multipart",
    ),
    # —— APIYI Gemini / Nano Banana（对话式 chat/completions）——
    _p(
        "apiyi.gemini.chat.text_to_image",
        "APIYI Gemini/Banana 对话式文生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
        invocation_mode=InvocationMode.TEXT_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="gemini-2.5-flash-image / gemini-3-pro-image 等 Nano Banana 系列",
    ),
    _p(
        "apiyi.gemini.chat.image_to_image",
        "APIYI Gemini/Banana 对话式图生图",
        provider="apiyi",
        protocol_slot=OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
        invocation_mode=InvocationMode.IMAGE_TO_IMAGE.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="apiyi_chat_image",
        parser="markdown_image",
        size_strategy="prompt_hint",
        description="user 消息含 image_url；多轮改图须带上轮输出 URL",
    ),
    # —— Weelinking 图片（OpenAI 兼容）——
    _p(
        "weelinking.openai-image.text_to_image",
        "Weelinking 文生图",
        provider="weelinking",
        protocol_slot="openai.images.generations",
        invocation_mode=InvocationMode.TEXT_TO_IMAGE.value,
        endpoint_type="image",
        path="images/generations",
        builder="weelink_default",
        parser="weelink_default",
        size_strategy="api_field",
    ),
    _p(
        "weelinking.openai-image.image_to_image",
        "Weelinking 图生图",
        provider="weelinking",
        protocol_slot="openai.images.edits",
        invocation_mode=InvocationMode.IMAGE_TO_IMAGE.value,
        endpoint_type="image_edits",
        path="images/edits",
        builder="weelink_default",
        parser="weelink_default",
        size_strategy="api_field",
        content_type="multipart/form-data",
    ),
    # —— 文本对话 ——
    _p(
        "openai.chat.text_chat",
        "OpenAI Chat 生文",
        provider="*",
        protocol_slot="openai.chat.completions",
        invocation_mode=InvocationMode.TEXT_CHAT.value,
        endpoint_type="chat",
        path="chat/completions",
        builder="weelink_default",
        parser="weelink_default",
    ),
    # —— 火山视频（多模态 content[]：文/图/视频/音频）——
    _p(
        "volcengine.video.text_to_video",
        "火山 多模态视频（纯文/混合）",
        provider="volcengine",
        protocol_slot="volcengine.video.multimodal",
        invocation_mode=InvocationMode.TEXT_TO_VIDEO.value,
        endpoint_type="video",
        path="contents/generations/tasks",
        builder="volcengine_video_multimodal",
        parser="weelink_default",
        description="content[] 支持 text / image_url / video_url / audio_url，同一端点",
    ),
    _p(
        "volcengine.video.image_to_video",
        "火山 多模态视频（含参考素材）",
        provider="volcengine",
        protocol_slot="volcengine.video.multimodal",
        invocation_mode=InvocationMode.IMAGE_TO_VIDEO.value,
        endpoint_type="video",
        path="contents/generations/tasks",
        builder="volcengine_video_multimodal",
        parser="weelink_default",
        description="与文生视频共用端点；参考图/视频/音频写入 content[]",
    ),
]

BUILTIN_PROFILE_BY_ID: Dict[str, Dict[str, Any]] = {
    p["profile_id"]: p for p in BUILTIN_PROTOCOL_PROFILES
}

# channel_model_id 子串 → 各 mode 的默认 profile_id（binding 未配置 mode_profiles 时推断）
MODEL_ID_PROFILE_HINTS: List[Dict[str, Any]] = [
    {
        "match": "gpt-image-2-all",
        "provider": "apiyi",
        "modes": {
            InvocationMode.TEXT_TO_IMAGE.value: "apiyi.gpt-image-2-all.text_to_image",
            InvocationMode.IMAGE_TO_IMAGE.value: "apiyi.gpt-image-2-all.image_to_image",
        },
    },
    {
        "match": "gpt-image-2-vip",
        "provider": "apiyi",
        "modes": {
            InvocationMode.TEXT_TO_IMAGE.value: "apiyi.gpt-image-2-vip.text_to_image",
            InvocationMode.IMAGE_TO_IMAGE.value: "apiyi.gpt-image-2-vip.image_to_image",
        },
    },
    {
        "match": "gemini",
        "provider": "apiyi",
        "modes": {
            InvocationMode.TEXT_TO_IMAGE.value: "apiyi.gemini.chat.text_to_image",
            InvocationMode.IMAGE_TO_IMAGE.value: "apiyi.gemini.chat.image_to_image",
        },
    },
    {
        "match": "banana",
        "provider": "apiyi",
        "modes": {
            InvocationMode.TEXT_TO_IMAGE.value: "apiyi.gemini.chat.text_to_image",
            InvocationMode.IMAGE_TO_IMAGE.value: "apiyi.gemini.chat.image_to_image",
        },
    },
    {
        "match": "gpt-image-2",
        "provider": "weelinking",
        "modes": {
            InvocationMode.TEXT_TO_IMAGE.value: "weelinking.openai-image.text_to_image",
            InvocationMode.IMAGE_TO_IMAGE.value: "weelinking.openai-image.image_to_image",
        },
    },
    {
        "match": "seedance",
        "provider": "volcengine",
        "modes": {
            InvocationMode.TEXT_TO_VIDEO.value: "volcengine.video.text_to_video",
            InvocationMode.IMAGE_TO_VIDEO.value: "volcengine.video.image_to_video",
        },
    },
    {
        "match": "seedancer",
        "provider": "volcengine",
        "modes": {
            InvocationMode.TEXT_TO_VIDEO.value: "volcengine.video.text_to_video",
            InvocationMode.IMAGE_TO_VIDEO.value: "volcengine.video.image_to_video",
        },
    },
]
