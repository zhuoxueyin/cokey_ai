"""角色参考图风格融合单元测试。"""
from app.core.drama.character_ref_analysis import (
    merge_style_and_ref_analysis,
    normalize_ref_analysis,
)
from app.core.drama.character_prompt_template import (
    build_character_prompt_pack,
    analyze_style_for_character,
    analyze_character_description,
)


def test_merge_style_and_ref_analysis():
    style = analyze_style_for_character(
        {
            "render_class": "illustration_2d",
            "model_prompts": {
                "style_summary_en": "Shanghai Animation Studio style",
                "character_suffix_en": "classic Chinese animation",
                "image_negative_en": "3D render",
            },
            "model_protocol": {"trait_tags": ["2D插画"]},
        }
    )
    ref = normalize_ref_analysis(
        {
            "line_art_en": "calligraphic ink outlines",
            "color_palette_en": "vermillion and azure mineral pigments",
            "lighting_en": "flat illustrative lighting",
            "style_tokens_en": ["cel shading", "paper grain"],
            "notes_zh": "仅画风",
        }
    )
    fused = merge_style_and_ref_analysis(style, ref)
    assert "bound_style" in fused["sources"]
    assert "reference_images" in fused["sources"]
    assert "calligraphic" in fused["line_art_en"]
    assert fused["character_suffix_en"] == "classic Chinese animation"
    assert len(fused["style_tokens_en"]) >= 2


def test_build_prompt_pack_with_fused_style():
    style = analyze_style_for_character(
        {"model_prompts": {"character_suffix_en": "anime style", "image_negative_en": "blurry"}}
    )
    ref = normalize_ref_analysis({"lighting_en": "soft rim light", "style_tokens_en": ["cel shading"]})
    fused = merge_style_and_ref_analysis(style, ref)
    char = analyze_character_description(name="小雪", appearance_zh="银发", costume_zh="校服")
    pack = build_character_prompt_pack(
        style,
        char,
        ref_style_analysis=ref,
        fused_style=fused,
        subject_en="young woman",
        appearance_en="silver hair",
        costume_en="school uniform",
    )
    pos = pack["prompt_pack"]["positive_en"]
    assert "soft rim light" in pos or "cel shading" in pos
    assert pos.endswith("anime style")
    assert pack["fused_style"]["sources"]
