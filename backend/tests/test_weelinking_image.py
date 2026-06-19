"""Weelinking GPT Image 2 请求体规范化测试"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.weelinking_image import normalize_weelinking_gpt_image_body, sanitize_image_prompt


def test_demo_payload_defaults():
    body = normalize_weelinking_gpt_image_body(
        {
            "model": "gpt-image-2",
            "prompt": "hello",
            "size": "1024x1024",
            "n": 1,
        },
        {"aspect_ratio": "9:16", "resolution": "1k"},
    )
    assert body["quality"] == "auto"
    assert body["output_format"] == "png"
    assert body["background"] == "auto"
    assert body["size"] == "1024x1024"
    assert "resolution" not in body
    assert "aspect_ratio" not in body


def test_864_maps_to_demo_size():
    body = normalize_weelinking_gpt_image_body(
        {
            "model": "gpt-image-2",
            "prompt": "test",
            "size": "864x1536",
            "n": 1,
        },
        {"aspect_ratio": "9:16"},
    )
    assert body["size"] == "1024x1536"


def test_sanitize_prompt():
    raw = "```text\n角色=悟空\n```\n\n**标题**\n真实提示词"
    cleaned = sanitize_image_prompt(raw)
    assert "```" not in cleaned
    assert "**" not in cleaned
    assert "真实提示词" in cleaned


def test_edits_official_defaults():
    body = normalize_weelinking_gpt_image_body(
        {
            "model": "gpt-image-2",
            "prompt": "test",
            "size": "1536x1024",
            "n": 1,
            "quality": "auto",
            "background": "auto",
        },
        {"trace_id": "trace_abc"},
        endpoint="image_edits",
    )
    assert body["quality"] == "high"
    assert body["response_format"] == "url"
    assert body["background"] == "opaque"
    assert body["output_format"] == "png"
    assert body["output_compression"] == 90
    assert body.get("user") == "trace_abc"
    assert "n" not in body


if __name__ == "__main__":
    test_demo_payload_defaults()
    test_864_maps_to_demo_size()
    test_sanitize_prompt()
    test_edits_official_defaults()
    print("weelinking_image tests passed")
