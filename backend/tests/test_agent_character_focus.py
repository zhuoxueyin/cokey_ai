"""活跃角色锁定与子步骤解析。"""
from app.core.drama.agent_character_focus import (
    extract_character_from_assistant,
    extract_character_substep,
    resolve_character_focus,
)
from app.core.drama.agent_creation_pipeline import (
    analyze_creation_intent,
    build_reply_guidance_block,
    suggest_next_options,
)


def test_extract_substep_look_and_card():
    assert extract_character_substep("定妆图设计 / 16:9 角色卡") == "look_design"
    assert extract_character_substep("16:9 角色卡") == "character_card"
    assert extract_character_substep("出定妆图") == "look_design"


def test_extract_character_from_assistant_next_options():
    assistant = """好的，纸面新郎宏观设计如下…

### 下一步可选
1. **确认纸面新郎角色设计**，我继续进入他的定妆图设计。
2. **更滑稽诡异一点**，加强纸偶丑角感。
"""
    assert extract_character_from_assistant(assistant) == "纸面新郎"


def test_resolve_focus_from_assistant_when_user_generic():
    assistant = """### 下一步可选
1. **确认纸面新郎角色设计**，我继续进入他的定妆图设计。
"""
    intent = analyze_creation_intent("定妆图设计 / 16:9 角色卡", "character")
    focus = resolve_character_focus(
        "定妆图设计 / 16:9 角色卡",
        stored={},
        recent_messages=[("assistant", assistant)],
        intent=intent,
    )
    assert focus.name == "纸面新郎"
    assert focus.substep == "look_design"
    assert focus.source == "assistant_guidance"


def test_resolve_focus_prefers_explicit_user_name():
    intent = analyze_creation_intent("给狐老太君出定妆图", "character")
    focus = resolve_character_focus(
        "给狐老太君出定妆图",
        stored={"active_character": "纸面新郎"},
        recent_messages=[],
        intent=intent,
    )
    assert focus.name == "狐老太君"
    assert focus.source == "user_explicit"


def test_resolve_focus_uses_stored_on_refine():
    intent = analyze_creation_intent("更阴冷压迫一点", "character")
    focus = resolve_character_focus(
        "更阴冷压迫一点",
        stored={"active_character": "纸面新郎", "character_substep": "look_design"},
        recent_messages=[],
        intent=intent,
    )
    assert focus.name == "纸面新郎"
    assert focus.source == "thread_context"


def test_build_reply_guidance_character_active_name():
    intent = analyze_creation_intent("定妆图设计", "character")
    intent.subject = "纸面新郎"
    intent.character_substep = "look_design"
    block = build_reply_guidance_block(
        stage="character",
        intent=intent,
        style_name="上美画风",
        subject="纸面新郎",
        user_message="定妆图设计 / 16:9 角色卡",
        character_substep="look_design",
    )
    assert "纸面新郎" in block
    assert "禁止" in block and "跳回" in block
    assert "look_design" in block or "定妆" in block


def test_suggest_next_from_assistant_not_first_user():
    assistant = "### 下一步可选\n1. **确认纸面新郎角色设计**，继续定妆。\n"
    options = suggest_next_options(
        "character",
        subject="",
        style_name="上美画风",
        character_substep="look_design",
        recent_assistant_messages=[assistant],
        recent_user_messages=["更滑稽一点", "定妆图设计"],
    )
    assert any("纸面新郎" in o for o in options)


def test_suggest_next_from_assistant_not_first_user():
    assistant = "### 下一步可选\n1. **确认纸面新郎角色设计**，继续定妆。\n"
    options = suggest_next_options(
        "character",
        subject="",
        style_name="上美画风",
        character_substep="look_design",
        recent_assistant_messages=[assistant],
        recent_user_messages=["更滑稽一点", "定妆图设计"],
    )
    assert any("纸面新郎" in o for o in options)
