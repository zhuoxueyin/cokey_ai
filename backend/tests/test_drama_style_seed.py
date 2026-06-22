"""StyleSpec 默认骨架生成。"""
from app.core.drama.style_spec_defaults import RenderClass, build_style_spec_document


def test_build_style_spec_has_model_prompts():
    spec = build_style_spec_document(
        {
            "style_id": "demo_style",
            "name": "演示风格",
            "render_class": "live_action",
            "genre_tags": ["测试"],
        }
    )
    assert spec["spec_version"] == "1.0"
    assert spec["style_id"] == "demo_style"
    assert spec["origin"] == "manual"
    assert spec["model_prompts"]["style_summary_en"]
    assert spec["model_prompts"]["image_positive_en"]
    assert spec["status"] == "draft"


def test_render_class_values():
    allowed: set[RenderClass] = {"live_action", "illustration_2d", "render_3d"}
    for rc in allowed:
        spec = build_style_spec_document(
            {"style_id": f"s_{rc}", "name": "x", "render_class": rc, "genre_tags": []}
        )
        assert spec["render_class"] == rc


def test_build_style_spec_uses_custom_cover():
    spec = build_style_spec_document(
        {
            "style_id": "with_cover",
            "name": "封面测试",
            "render_class": "illustration_2d",
            "genre_tags": [],
            "cover_url": "https://cdn.example.com/cover.png",
        }
    )
    assert spec["reference_images"][0]["url"] == "https://cdn.example.com/cover.png"
