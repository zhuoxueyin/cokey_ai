"""角色生图标准提示词模板单元测试。"""
from app.core.drama.character_prompt_template import (
    analyze_character_description,
    analyze_style_for_character,
    build_character_card_prompt_pack,
    build_character_design,
    build_character_prompt_pack,
    build_look_prompt_pack,
    export_template_document,
    format_character_session_guide,
)


def test_export_template_document():
    doc = export_template_document()
    assert doc["version"] == "4.2"
    assert doc["skill_code"] == "skill.character"
    assert len(doc["workflow_phases"]) == 3
    assert len(doc["card_section_order"]) == 11
    assert len(doc["look_section_order"]) == 8
    assert len(doc["card_dimensions"]) == 8


def test_analyze_style_for_character_empty():
    out = analyze_style_for_character(None)
    assert out["render_class"] == "live_action"
    assert out["character_suffix_en"] == ""


def test_analyze_style_for_character_from_doc():
    style = {
        "render_class": "illustration_2d",
        "name": "赛璐璐",
        "model_prompts": {
            "style_summary_zh": "日系赛璐璐",
            "character_suffix_en": "anime cel shading, clean lineart",
            "image_negative_en": "photorealistic, blurry",
        },
        "model_protocol": {"trait_tags": ["2D插画"]},
        "visual": {"color_palette": ["粉", "白"]},
    }
    out = analyze_style_for_character(style)
    assert out["render_class"] == "illustration_2d"
    assert "cel shading" in out["character_suffix_en"]
    assert out["trait_tags"] == ["2D插画"]


def test_build_character_design():
    design = build_character_design(
        name="小雪",
        role="主角",
        gender_zh="女",
        age_range_zh="18-22",
        identity_zh="转学生",
        personality_zh="外冷内热",
    )
    assert design["name"] == "小雪"
    assert design["gender_zh"] == "女"
    assert design["story_function_zh"] == "待补充"


def test_analyze_character_description_card_dimensions():
    char = analyze_character_description(
        name="小雪",
        role="主角",
        appearance_zh="银发双马尾",
        expression_zh="温柔浅笑, 惊讶",
        action_zh="单手撩发, 奔跑",
        costume_zh="校服",
        accessories_zh="蓝色丝带",
        tools_weapons_zh="无",
    )
    assert char["card_dimensions"]["expression_zh"] == "温柔浅笑, 惊讶"
    assert char["card_dimensions"]["action_zh"] == "单手撩发, 奔跑"
    assert char["character_design"]["name"] == "小雪"
    assert "小雪" in char["card_copy_zh"]


def test_build_look_prompt_pack_single_view():
    style = analyze_style_for_character(
        {"model_prompts": {"character_suffix_en": "anime style", "image_negative_en": "blurry"}}
    )
    design = build_character_design(name="小雪", gender_zh="女", age_range_zh="青年")
    look = {
        "appearance_zh": "银发双马尾",
        "costume_zh": "校服",
        "color_palette_zh": "蓝白",
        "line_art_zh": "细线勾边",
    }
    pack = build_look_prompt_pack(
        style,
        design,
        look,
        appearance_en="silver twin tails",
        costume_en="school uniform",
    )
    assert pack["aspect_ratio"] == "3:4"
    assert pack["image_count"] == 1
    assert "one view only" in pack["layout_en"]
    assert "plain solid color background" in pack["layout_en"]
    assert "turn-around" in pack["negative_en"]
    assert "complex environment" in pack["negative_en"]
    assert pack["positive_en"].endswith("anime style")


def test_build_character_card_prompt_pack_16_9():
    style = analyze_style_for_character(
        {
            "render_class": "illustration_2d",
            "model_prompts": {
                "character_suffix_en": "anime style",
                "image_negative_en": "blurry",
            },
        }
    )
    char = analyze_character_description(
        name="小雪",
        role="主角",
        appearance_zh="银发双马尾",
        expression_zh="gentle smile, surprised",
        action_zh="hand in hair, running",
        costume_zh="school uniform",
    )
    pack = build_character_card_prompt_pack(
        style,
        char,
        subject_en="young woman",
        appearance_en="silver twin tails",
        expression_en="gentle smile, surprised eyes",
        action_en="one hand touching hair, running pose",
        costume_en="school uniform, blue ribbon",
        accessories_en="hair ribbon",
        background_en="soft classroom light",
        style_tokens=["cel shading", "soft lighting"],
        locked_tokens=["silver twin tails", "blue ribbon"],
    )
    pp = pack["card_prompt_pack"]
    assert pp["aspect_ratio"] == "16:9"
    assert pp["image_count"] == 1
    assert "16:9" in pp["layout_en"]
    assert "multiple facial expressions" in pp["layout_en"]
    positive = pp["positive_en"]
    assert positive.index("young woman") < positive.index("silver twin tails")
    assert positive.index("gentle smile") < positive.index("school uniform")
    assert positive.endswith("anime style")
    assert "not 16:9" in pp["negative_en"]
    assert pack["locked_tokens"] == ["silver twin tails", "blue ribbon"]
    assert pack["look_prompt_pack"]["image_count"] == 1
    assert pack["character_design"]["name"] == "小雪"


def test_build_character_prompt_pack_alias():
    style = analyze_style_for_character({"model_prompts": {"character_suffix_en": "anime style"}})
    char = analyze_character_description(name="A", appearance_zh="test")
    pack = build_character_prompt_pack(style, char, subject_en="hero")
    assert pack["prompt_pack"] == pack["card_prompt_pack"]


def test_format_character_session_guide_has_intent_routing():
    guide = format_character_session_guide(
        {"render_class": "illustration_2d", "style_summary_zh": "测试风格"},
        ref_image_count=1,
        ref_urls=["https://example.com/ref.png"],
    )
    assert "意图识别（先判再做）" in guide
    assert "默认单轮只交付当前意图阶段" in guide
    assert "纯色/干净背景" in guide
