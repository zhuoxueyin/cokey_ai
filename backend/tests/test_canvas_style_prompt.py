"""画布风格 prompt 合并单元测试。"""
from app.core.canvas_style_prompt import build_full_style_reference, merge_style_into_params


def test_merge_image_style_appends_positive_and_negative():
    style = {
        "style_id": "demo",
        "name": "Demo",
        "model_prompts": {
            "image_positive_en": "cinematic, low key lighting",
            "image_negative_en": "blurry, watermark",
        },
        "model_protocol": {
            "image": {"positive_en": "cinematic, low key lighting", "negative_en": "blurry, watermark"}
        },
    }
    out = merge_style_into_params(
        {"prompt": "a warrior in rain"},
        style_doc=style,
        node_type="image",
    )
    assert "a warrior in rain" in out["prompt"]
    assert "[Visual Style Reference]" in out["prompt"]
    assert "cinematic, low key lighting" in out["prompt"]
    assert out["negative_prompt"] == "blurry, watermark"


def test_merge_includes_full_style_description_md():
    style = {
        "style_id": "tianshu",
        "name": "天书奇谭",
        "render_class": "illustration_2d",
        "style_description_md": """# 天书奇谭

## 风格摘要
80年代国风手绘

## 生图提示词参考
clay sculpture, bold outline""",
        "model_prompts": {
            "image_positive_en": "clay sculpture, bold outline",
            "image_negative_en": "3d, cg",
        },
    }
    text, negative = build_full_style_reference(style, "image")
    assert "80年代国风手绘" in text
    assert "clay sculpture" in text
    assert negative == "3d, cg"

    out = merge_style_into_params({"prompt": "蛋生站在山顶"}, style_doc=style, node_type="image")
    assert "蛋生站在山顶" in out["prompt"]
    assert "80年代国风手绘" in out["prompt"]
    assert "clay sculpture" in out["prompt"]


def test_merge_video_style_only_positive_when_no_user_prompt():
    style = {
        "style_id": "v1",
        "name": "Cinematic",
        "model_prompts": {"video_positive_en": "slow pan, cinematic motion"},
    }
    out = merge_style_into_params({}, style_doc=style, node_type="video")
    assert "slow pan, cinematic motion" in out["prompt"]
    assert "[Visual Style Reference]" not in out["prompt"] or "Cinematic" in out["prompt"]


def test_merge_skips_when_no_style():
    out = merge_style_into_params({"prompt": "hello"}, style_doc=None, node_type="image")
    assert out["prompt"] == "hello"
    assert "negative_prompt" not in out
