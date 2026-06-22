"""统一风格上下文单元测试。"""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.drama.style_context import (
    format_character_style_guide,
    resolve_style_context,
)


@pytest.mark.asyncio
async def test_resolve_style_context_skip_when_unbound():
    ctx = await resolve_style_context(None)
    assert ctx["trace"]["status"] == "skip"
    assert ctx["character_style_guide"] == ""
    assert ctx["style_analysis"]["render_class"] == "live_action"


@pytest.mark.asyncio
async def test_resolve_style_context_character_stage():
    style_doc = {
        "style_id": "retro_sci_fi",
        "name": "复古科幻",
        "render_class": "illustration_2d",
        "style_description_md": "## 复古科幻\n赛博朋克色调",
        "model_prompts": {
            "style_summary_zh": "复古科幻插画",
            "character_suffix_en": "retro sci-fi illustration",
            "image_negative_en": "blurry",
        },
        "visual": {"color_palette": ["青", "紫"]},
    }
    with patch(
        "app.services.drama_style_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=style_doc)),
    ):
        ctx = await resolve_style_context("retro_sci_fi", stage="character")

    assert ctx["trace"]["status"] == "ok"
    assert "retro sci-fi illustration" in ctx["style_analysis"]["character_suffix_en"]
    assert "style_analysis" in ctx["trace"]["detail"]
    assert "ReAct" in ctx["character_style_guide"]
    assert "style_analysis" in ctx["character_style_guide"]
    assert ctx["prompt_block"].startswith("视觉风格（全对话锁定）")


def test_format_character_style_guide():
    guide = format_character_style_guide({"render_class": "live_action", "trait_tags": []})
    assert "style_analysis" in guide
    assert "ReAct" in guide
