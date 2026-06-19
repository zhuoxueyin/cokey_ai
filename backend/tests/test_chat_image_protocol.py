"""对话式生图协议槽位单元测试。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.chat_image_protocol import (
    OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE,
    OPENAI_CHAT_IMAGE_LEGACY,
    OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE,
    chat_image_slot_for_mode,
    is_openai_chat_image_slot,
    normalize_chat_image_protocol_slot,
)


def test_slot_for_mode():
    assert chat_image_slot_for_mode("text_to_image") == OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE
    assert chat_image_slot_for_mode("image_to_image") == OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE


def test_normalize_legacy():
    assert (
        normalize_chat_image_protocol_slot(OPENAI_CHAT_IMAGE_LEGACY, "text_to_image")
        == OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE
    )
    assert (
        normalize_chat_image_protocol_slot(OPENAI_CHAT_IMAGE_LEGACY, "image_to_image")
        == OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE
    )


def test_is_openai_chat_image_slot():
    assert is_openai_chat_image_slot(OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE)
    assert is_openai_chat_image_slot(OPENAI_CHAT_IMAGE_LEGACY)
    assert not is_openai_chat_image_slot("openai.images.generations")
