"""角色队列与主链路阶段推进。"""
from app.core.drama.agent_creation_pipeline import (
    analyze_creation_intent,
    next_pipeline_stage,
)
from app.core.drama.agent_character_roster import (
    format_character_roster_block,
    sync_roster_from_messages,
)


def test_pipeline_advance_enter_next_link_from_character():
    intent = analyze_creation_intent("进入主链路下一环", "character")
    assert intent.intent_type == "stage_switch"
    assert intent.target_stage == "scene"
    assert next_pipeline_stage("character") == "scene"


def test_pipeline_advance_enter_next_stage():
    intent = analyze_creation_intent("进入下一阶段", "character")
    assert intent.intent_type == "stage_switch"
    assert intent.target_stage == "scene"


def test_roster_sync_order_and_progress():
    messages = [
        {"role": "user", "content": "三位角色：白小檀、卡与、纸面新郎"},
        {
            "role": "assistant",
            "content": "### 角色设计 · 白小檀\n宏观设计表…\n```look-prompt\n白小檀…\n```",
        },
        {"role": "user", "content": "给卡与出定妆图"},
    ]
    state = sync_roster_from_messages(messages, {})
    assert state["character_roster"][:3] == ["白小檀", "卡与", "纸面新郎"]
    assert state["character_progress"]["白小檀"]["character_design"]
    assert state["character_progress"]["白小檀"]["look_design"]

    block = format_character_roster_block(state, active_name="卡与", substep="look_design")
    assert "卡与" in block
    assert "顺序队列" in block
    assert "禁止" in block
