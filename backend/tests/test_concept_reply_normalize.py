"""创意脑暴回复清洗单元测试。"""
from app.services.drama_super_agent_service import _normalize_concept_reply


def test_normalize_concept_reply_strips_json_fence_and_blob():
    mixed = (
        "## 剧本草稿\n主角重生归来，先隐忍再翻盘。\n\n"
        "```json\n"
        '{"theme":"复仇","tone":"爽感"}\n'
        "```\n\n"
        '{\n  "ideas": ["豪门博弈", "身份反转"]\n}\n\n'
        "## 选题方向\n- 豪门恩怨线\n- 女性成长线"
    )
    cleaned = _normalize_concept_reply(mixed)
    assert "```json" not in cleaned
    assert '"ideas"' not in cleaned
    assert "## 剧本草稿" in cleaned
    assert "## 选题方向" in cleaned


def test_normalize_concept_reply_keeps_non_json_code_fence():
    text = "## 剧本草稿\n```\n第一幕：雨夜重逢\n```"
    assert _normalize_concept_reply(text) == text
