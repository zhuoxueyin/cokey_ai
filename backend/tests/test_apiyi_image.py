"""APIYI gpt-image-2-all / gpt-image-2-vip 对话式提示词与 body"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.apiyi_image import (
    build_apiyi_aspect_hint,
    build_apiyi_chat_image_body,
    enrich_prompt_with_count_hint,
    enrich_prompt_with_size_hint,
    resolve_image_count,
)


def test_16_9_hint():
    hint = build_apiyi_aspect_hint(
        {"size": "1536x1024", "aspect_ratio": "16:9", "resolution": "1k"},
        "gpt-image-2-all",
    )
    assert hint == "横版 16:9 电影画幅"


def test_prompt_prepend():
    text = enrich_prompt_with_size_hint(
        "黄昏时的海边老灯塔，写实风格",
        {"aspect_ratio": "16:9", "resolution": "1k"},
        "gpt-image-2-all",
    )
    assert text.startswith("横版 16:9 电影画幅，")
    assert "海边老灯塔" in text


def test_body_no_size_field():
    body = build_apiyi_chat_image_body(
        {
            "prompt": "一只猫",
            "size": "1024x1536",
            "aspect_ratio": "9:16",
            "resolution": "2k",
        },
        "gpt-image-2-all",
    )
    assert "size" not in body
    content = body["messages"][0]["content"]
    assert isinstance(content, str)
    assert "竖版 9:16" in content
    assert "高清" in content
    assert "1024x1536" not in content


def test_skip_duplicate_ratio_in_prompt():
    text = enrich_prompt_with_size_hint(
        "横版 16:9 赛博朋克街景",
        {"aspect_ratio": "16:9"},
        "gpt-image-2-all",
    )
    assert text == "横版 16:9 赛博朋克街景"


def test_vip_chat_body_pixel_size_in_prompt():
    from app.core.apiyi_image import enrich_prompt_for_apiyi_chat

    text = enrich_prompt_for_apiyi_chat(
        "黄昏海边灯塔",
        {"aspect_ratio": "16:9", "resolution": "1k"},
        "gpt-image-2-vip",
    )
    assert "1280x720" in text
    assert "灯塔" in text

    body = build_apiyi_chat_image_body(
        {
            "prompt": "一只猫",
            "aspect_ratio": "16:9",
            "resolution": "1k",
        },
        "gpt-image-2-vip",
    )
    assert body["model"] == "gpt-image-2-vip"
    assert "size" not in body
    content = body["messages"][0]["content"]
    assert isinstance(content, str)
    assert "1280x720" in content


def test_vip_chat_image_to_image_multimodal():
    body = build_apiyi_chat_image_body(
        {
            "prompt": "改成水彩风",
            "images": ["https://cdn.example.com/a.png"],
        },
        "gpt-image-2-vip",
    )
    content = body["messages"][0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == "https://cdn.example.com/a.png"


def test_resolve_image_count():
    assert resolve_image_count({"n": 2}) == 2
    assert resolve_image_count({"count": 3}) == 3
    assert resolve_image_count({"n": 99}) == 4
    assert resolve_image_count({}) == 1


def test_count_hint_in_chat_body():
    body = build_apiyi_chat_image_body(
        {"prompt": "一只猫", "n": 2, "aspect_ratio": "1:1"},
        "gpt-image-2-all",
    )
    content = body["messages"][0]["content"]
    assert isinstance(content, str)
    assert "2张" in content
    assert "一只猫" in content


def test_count_hint_skips_duplicate():
    text = enrich_prompt_with_count_hint("请生成2张不同风格的猫", {"n": 2})
    assert text == "请生成2张不同风格的猫"


if __name__ == "__main__":
    test_16_9_hint()
    test_prompt_prepend()
    test_body_no_size_field()
    test_skip_duplicate_ratio_in_prompt()
    print("ok")
