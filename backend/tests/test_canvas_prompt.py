from app.core.canvas_prompt import build_ref_token, expand_prompt_refs, extract_ref_node_ids


def test_build_ref_token():
    assert build_ref_token("cnode_abc") == "{{@node:cnode_abc}}"


def test_expand_prompt_refs():
    stored = f"请根据{build_ref_token('cnode_1')}生成"
    out = expand_prompt_refs(stored, {"cnode_1": "赛博朋克街景描述"})
    assert out == "请根据赛博朋克街景描述生成"


def test_extract_ref_node_ids():
    text = f"a{build_ref_token('x')}b{build_ref_token('y')}"
    assert extract_ref_node_ids(text) == ["x", "y"]
