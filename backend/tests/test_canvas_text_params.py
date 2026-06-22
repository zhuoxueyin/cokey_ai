"""画布文本节点 params 与创作流 /tasks/generate 对齐"""

from app.core.canvas_prompt import build_ref_token, expand_prompt_refs, image_url_from_source_node
from app.services.canvas_service import CanvasService


def _svc() -> CanvasService:
    return CanvasService.__new__(CanvasService)


def test_text_prompt_appends_unreferenced_upstream_text():
    params = _svc()._build_run_params(
        "text",
        {"prompt": "写一首诗", "params": {}},
        {"texts": ["上游背景设定"], "images": [], "videos": []},
        {"txt1": "上游背景设定"},
        [],
    )
    assert params["prompt"] == "写一首诗\n\n上游背景设定"


def test_text_node_passes_upstream_images_like_workspace():
    url = "https://cdn.jsdmirror.com/gh/u/r/a.png"
    params = _svc()._build_run_params(
        "text",
        {"prompt": "描述这张图", "params": {}},
        {"texts": [], "images": [url], "videos": []},
        {},
        [url],
    )
    assert params["prompt"] == "描述这张图"
    assert params["images"] == [url]


def test_at_image_ref_expands_without_placeholder():
    token = build_ref_token("img1")
    stored = f"请分析{token}的内容"
    out = expand_prompt_refs(stored, {"img1": ""})
    assert out == "请分析的内容"
    assert "[参考图" not in out


def test_image_url_from_resource_node():
    url = "https://cdn.jsdmirror.com/gh/u/r/x.png"
    node = {
        "node_type": "resource",
        "config": {"resource_url": url, "resource_type": "image"},
    }
    assert image_url_from_source_node(node) == url


def test_image_node_passes_connected_refs_without_at():
    url = "https://cdn.jsdmirror.com/gh/u/r/ref.png"
    params = _svc()._build_run_params(
        "image",
        {"prompt": "生成类似风格", "params": {}},
        {"texts": [], "images": [url], "videos": []},
        {},
        [url],
    )
    assert params["prompt"] == "生成类似风格"
    assert params["images"] == [url]
