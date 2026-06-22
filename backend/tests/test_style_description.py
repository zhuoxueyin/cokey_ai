"""风格描述 Markdown 解析与派生。"""
import pytest

from app.core.drama.style_description import (
    derive_from_sections,
    enrich_style_payload,
    legacy_doc_to_markdown,
    parse_style_description_md,
    style_description_template,
    validate_for_publish,
)


SAMPLE_MD = """# 测试风格

## 风格摘要

国风 3D 奇幻动画美学。

## 风格特点

柔和光影、水墨质感。

## 人物角色

delicate facial features, flowing robes

## 场景描述

misty mountains, ancient temples

## 色彩倾向

青绿, 金色, 墨色

## 代表作品

哪吒之魔童降世 (2019)
白蛇：缘起 (2019)

## 生图提示词参考

3D Chinese fantasy animation, cinematic lighting

## 生视频提示词参考

slow camera pan, ethereal atmosphere
"""


def test_template_has_required_sections():
    md = style_description_template("Demo")
    assert "## 风格摘要" in md
    assert "## 画风大类" in md
    assert "## 画师/工作室参考" in md
    assert "## 场景描述" in md
    assert "## 代表作品" in md
    assert "## 生视频提示词参考" in md
    assert md.startswith("# Demo")


def test_parse_sections():
    sections = parse_style_description_md(SAMPLE_MD)
    assert "国风 3D" in sections["summary"]
    assert "柔和光影" in sections["traits"]
    assert "delicate" in sections["characters"]
    assert "misty" in sections["scenes"]
    assert "青绿" in sections["colors"]
    assert "哪吒" in sections["references"]
    assert "cinematic" in sections["image_prompt"]
    assert "ethereal" in sections["video_prompt"]


def test_derive_model_prompts_and_visual():
    sections = parse_style_description_md(SAMPLE_MD)
    mp, visual = derive_from_sections(sections)
    assert "国风 3D" in mp["style_summary_zh"]
    assert "柔和光影" in mp["style_summary_zh"]
    assert mp["image_positive_en"].startswith("3D Chinese")
    assert mp["video_positive_en"].startswith("slow camera")
    assert mp["character_suffix_en"].startswith("delicate")
    assert visual["reference_films"][0].startswith("哪吒")
    assert "青绿" in visual["color_palette"]


V2_SAMPLE_MD = """# 上美画风

## 风格摘要

上美影经典二维动画美学。

## 画风大类

二维赛璐璐/国画意境融合

## 画师/工作室参考

上海美术电影制片厂、万籁鸣、特伟

## 年代质感

1960s–1980s 中国手绘动画

## 线条与轮廓控制

粗黑外轮廓，内线简炼

## 光影与色彩

平涂为主，明暗二层

## 配色搭配

矿物色、石青、朱砂

## 氛围气质

神话寓言、民间趣味

## 材质细节

水粉平涂、泥塑造型感

## 画质要求

赛璐璐干净，无3D

## 约束禁忌

禁止3D CG

## 人物角色

戏曲脸谱化造型

Shanghai Animation style character, thick outlines

## 场景描述

古庙山水云雾

misty mountains ink wash background

## 色彩倾向

石青, 朱砂, 墨黑

## 代表作品

天书奇谭 (1983)

## 生图提示词参考

Shanghai Animation Film Studio style, cel animation

## 生视频提示词参考

gentle 2D animation motion
"""


def test_parse_v2_sections_and_derive():
    sections = parse_style_description_md(V2_SAMPLE_MD)
    assert "万籁鸣" in sections["artist_refs"]
    assert "粗黑" in sections["line_control"]
    mp, _ = derive_from_sections(sections)
    assert "【画风大类】" in mp["style_summary_zh"]
    assert "Shanghai Animation" in mp["image_positive_en"]
    assert mp["character_suffix_en"].startswith("Shanghai")


def test_enrich_style_payload():
    out = enrich_style_payload({"name": "X", "style_description_md": SAMPLE_MD})
    assert out["style_description_md"].startswith("# 测试风格")
    assert out["model_prompts"]["image_positive_en"]
    assert out["visual"]["color_palette"]


def test_legacy_doc_to_markdown():
    doc = {
        "name": "Legacy",
        "model_prompts": {
            "style_summary_zh": "旧摘要",
            "image_positive_en": "old image prompt",
            "video_positive_en": "old video prompt",
        },
        "visual": {
            "reference_films": ["Film A"],
            "color_palette": ["red", "blue"],
        },
    }
    md = legacy_doc_to_markdown(doc)
    assert "## 风格摘要" in md
    assert "旧摘要" in md
    assert "Film A" in md
    assert "old image prompt" in md


def test_validate_for_publish_requires_sections():
    with pytest.raises(ValueError, match="风格摘要"):
        validate_for_publish({"style_description_md": "## 生图提示词参考\n\nx\n"})
    with pytest.raises(ValueError, match="生图提示词"):
        validate_for_publish({"style_description_md": "## 风格摘要\n\nok\n"})
    validate_for_publish(
        {
            "style_description_md": "## 风格摘要\n\nok\n\n## 生图提示词参考\n\nprompt\n",
        }
    )
