"""OpenAI Chat Completions 对话式生图协议槽位。"""
from __future__ import annotations

OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE = "openai.chat.image.text_to_image"
OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE = "openai.chat.image.image_to_image"
OPENAI_CHAT_IMAGE_LEGACY = "openai.chat.image"

CHAT_IMAGE_PROTOCOL_SLOTS = frozenset(
    {
        OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
        OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
        OPENAI_CHAT_IMAGE_LEGACY,
    }
)


def chat_image_slot_for_mode(invocation_mode: str) -> str:
    if invocation_mode == "image_to_image":
        return OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE
    return OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE


def normalize_chat_image_protocol_slot(
    protocol_slot: str | None,
    invocation_mode: str | None = None,
) -> str:
    if not protocol_slot:
        return ""
    slot = protocol_slot.strip()
    if slot == OPENAI_CHAT_IMAGE_LEGACY:
        return chat_image_slot_for_mode(invocation_mode or "text_to_image")
    return slot


def is_openai_chat_image_slot(protocol_slot: str | None) -> bool:
    if not protocol_slot:
        return False
    return protocol_slot.strip() in CHAT_IMAGE_PROTOCOL_SLOTS
