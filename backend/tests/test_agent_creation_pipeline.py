"""创作主链路 · 意图识别 · 下一步引导。"""
from app.core.drama.agent_creation_pipeline import (
    analyze_creation_intent,
    build_reply_guidance_block,
    extract_subject,
    infer_stage_from_message,
    suggest_next_options,
)


def test_extract_subject_shen_yansheng():
    msg = "我计划给沈砚生设计角色图 按流程引导我下"
    assert extract_subject(msg) == "沈砚生"


def test_infer_character_from_production():
    msg = "我计划给沈砚生设计角色图 按流程引导我下"
    assert infer_stage_from_message(msg, "production") == "character"


def test_refine_intent_stays_on_character():
    intent = analyze_creation_intent("更滑稽一点，加强天书奇谭喜感", "character")
    assert intent.intent_type == "refine"
    assert intent.target_stage == "character"
    assert "滑稽" in intent.refinement_hint or intent.refinement_hint


def test_production_signal_does_not_leave_character():
    assert infer_stage_from_message("开始出图", "character") is None


def test_build_reply_guidance_block_concept_enforces_readable_brainstorm():
    intent = analyze_creation_intent("我要做一个重生复仇题材", "concept")
    block = build_reply_guidance_block(
        stage="concept",
        intent=intent,
        style_name="上美风格",
        subject="女主",
        mode_name="创意短剧",
        user_message="我要做一个重生复仇题材",
    )
    assert "禁止 JSON" in block or "禁止" in block
    assert "重生复仇" in block
    assert "创意短剧" in block
    assert "风格包" in block or "3A" in block
    assert "定稿方向" in block or "剧本大纲" in block


def test_suggest_next_character_includes_subject():
    intent = analyze_creation_intent("给沈砚生设计角色", "character")
    options = suggest_next_options("character", intent=intent, subject="沈砚生", style_name="上美画风")
    assert len(options) >= 3
    assert any("沈砚生" in o for o in options)
    assert any("滑稽" in o or "清秀" in o for o in options)


def test_stage_switch_guidance_mentions_scene():
    intent = analyze_creation_intent("进入主链路下一环", "character")
    block = build_reply_guidance_block(
        stage="character",
        intent=intent,
        style_name="上美画风",
        user_message="进入主链路下一环",
    )
    assert "阶段切换" in block
    assert "场景" in block
