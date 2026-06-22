"""用户 @ 引用资源格式化。"""
from app.core.drama.agent_user_refs import (
    build_user_refs_trace_step,
    extract_ref_image_urls,
    format_user_refs_for_prompt,
)


def test_format_user_refs_for_prompt_empty():
    assert format_user_refs_for_prompt(None) == "（无）"
    assert format_user_refs_for_prompt([]) == "（无）"


def test_format_user_refs_for_prompt_with_urls():
    text = format_user_refs_for_prompt(
        [{"type": "asset", "id": "a1", "url": "https://cdn.jsdmirror.com/gh/x/y.png"}]
    )
    assert "参考图 1" in text
    assert "cdn.jsdmirror.com" in text


def test_extract_ref_image_urls_filters_invalid():
    urls = extract_ref_image_urls(
        [
            {"url": "https://cdn.jsdmirror.com/gh/a/b.png"},
            {"url": "https://evil.example.com/x.png"},
            {"url": ""},
        ]
    )
    assert urls == ["https://cdn.jsdmirror.com/gh/a/b.png"]


def test_build_user_refs_trace_step():
    step = build_user_refs_trace_step(
        [{"type": "asset", "url": "https://cdn.jsdmirror.com/gh/a/b.png"}]
    )
    assert step is not None
    assert step["title"] == "用户引用资源"
    assert step["status"] == "ok"
    assert "多模态" in step["summary"]
