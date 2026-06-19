"""APIYI gpt-image-2-vip 文生图 body 构建"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.apiyi_vip_image import (
    build_apiyi_vip_generations_body,
    is_apiyi_vip_image_model,
    normalize_vip_size,
)


def test_is_vip_model():
    assert is_apiyi_vip_image_model("gpt-image-2-vip")
    assert not is_apiyi_vip_image_model("gpt-image-2-all")


def test_size_16_9_2k():
    size = normalize_vip_size(
        {"size": "2048x1152", "aspect_ratio": "16:9", "resolution": "2k"},
        "gpt-image-2-vip",
    )
    assert size == "2048x1152"


def test_size_from_aspect_only():
    size = normalize_vip_size(
        {"aspect_ratio": "16:9", "resolution": "2k"},
        "gpt-image-2-vip",
    )
    assert size == "2048x1152"


def test_body_forbidden_fields():
    body = build_apiyi_vip_generations_body(
        {
            "prompt": "黄昏海边灯塔",
            "size": "2048x1152",
            "aspect_ratio": "16:9",
            "quality": "high",
            "n": 3,
        },
        "gpt-image-2-vip",
    )
    assert body["model"] == "gpt-image-2-vip"
    assert body["size"] == "2048x1152"
    assert body["response_format"] == "url"
    assert "quality" not in body
    assert "n" not in body
    assert "aspect_ratio" not in body
    assert "黄昏海边灯塔" in body["prompt"]


def test_platform_size_maps_to_vip():
    # 平台 16:9 1k 为 1536x1024，VIP 应映射到 1280x720
    size = normalize_vip_size(
        {"size": "1536x1024", "aspect_ratio": "16:9", "resolution": "1k"},
        "gpt-image-2-vip",
    )
    assert size == "1280x720"


def test_vip_edits_form_fields():
    from app.core.apiyi_vip_image import build_apiyi_vip_edits_form_fields, APIYI_VIP_EDITS_IMAGE_FIELD

    fields = build_apiyi_vip_edits_form_fields(
        {
            "prompt": "把图1放进图2",
            "size": "1536x1024",
            "aspect_ratio": "16:9",
            "resolution": "1k",
            "quality": "high",
            "n": 1,
            "background": "opaque",
        },
        "gpt-image-2-vip",
    )
    assert fields["model"] == "gpt-image-2-vip"
    assert fields["size"] == "1280x720"
    assert fields["response_format"] == "url"
    assert "quality" not in fields
    assert "n" not in fields
    assert "background" not in fields
    assert APIYI_VIP_EDITS_IMAGE_FIELD == "image"


if __name__ == "__main__":
    test_is_vip_model()
    test_size_16_9_2k()
    test_size_from_aspect_only()
    test_body_forbidden_fields()
    test_platform_size_maps_to_vip()
    test_vip_edits_form_fields()
    print("ok")
