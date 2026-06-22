from app.core.canvas_prompt import (
    append_attached_text_refs,
    build_ref_token,
    expand_prompt_refs,
    extract_ref_node_ids,
)


def test_build_ref_token():
    assert build_ref_token("cnode_abc") == "{{@node:cnode_abc}}"


def test_expand_prompt_refs():
    stored = f"请根据{build_ref_token('cnode_1')}生成"
    out = expand_prompt_refs(stored, {"cnode_1": "赛博朋克街景描述"})
    assert out == "请根据赛博朋克街景描述生成"


def test_extract_ref_node_ids():
    text = f"a{build_ref_token('x')}b{build_ref_token('y')}"
    assert extract_ref_node_ids(text) == ["x", "y"]


def test_append_attached_text_refs_skips_cited():
    stored = f"依据{build_ref_token('a')}扩写"
    out = append_attached_text_refs(
        expand_prompt_refs(stored, {"a": "已有片段", "b": "未引用片段"}),
        {"a": "已有片段", "b": "未引用片段"},
        ["a"],
    )
    assert out.endswith("未引用片段")
    assert "未引用片段" in out
    assert out.count("已有片段") == 1
