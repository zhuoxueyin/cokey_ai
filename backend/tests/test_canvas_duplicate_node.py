"""画布节点复制：图片节点只复制生图参数，不继承任务与结果。"""

from app.services.canvas_service import CanvasService


def _svc() -> CanvasService:
    return CanvasService.__new__(CanvasService)


def test_image_duplicate_clears_runtime_and_keeps_config():
    source = {
        "node_type": "image",
        "config": {
            "prompt": "赛博朋克少女",
            "model_code": "gpt-image-2-all",
            "params": {"size": "1024x1024", "n": 2},
            "style_preset_id": "style_abc",
            "output_image_index": 2,
            "width": 360,
            "height": 400,
        },
        "result": {"images": [{"url": "https://cdn.example.com/a.png"}]},
        "result_version": 3,
        "task_id": "task_old123",
        "status": "success",
        "error_message": None,
        "input_stale": True,
        "upstream_snapshot": {"img1": "https://cdn.example.com/ref.png"},
    }
    svc = _svc()
    runtime = svc._duplicate_runtime_fields(source)
    config = svc._duplicate_config(source)
    assert runtime["result"] is None
    assert runtime["result_version"] == 0
    assert runtime["task_id"] is None
    assert runtime["status"] == "idle"
    assert runtime["error_message"] is None
    assert runtime["input_stale"] is False
    assert runtime["upstream_snapshot"] == {}
    assert config["prompt"] == "赛博朋克少女"
    assert config["output_image_index"] == 0
    assert "width" not in config
    assert "height" not in config


def test_non_image_duplicate_preserves_runtime():
    source = {
        "node_type": "text",
        "result": {"text": "hello"},
        "result_version": 1,
        "task_id": "task_text1",
        "status": "success",
        "upstream_snapshot": {"txt1": "upstream"},
    }
    runtime = _svc()._duplicate_runtime_fields(source)
    assert runtime["result"] == {"text": "hello"}
    assert runtime["task_id"] == "task_text1"
    assert runtime["status"] == "success"


def test_image_duplicate_running_status_resets_to_idle():
    source = {
        "node_type": "image",
        "status": "running",
        "task_id": "task_running",
        "config": {"prompt": "test"},
    }
    runtime = _svc()._duplicate_runtime_fields(source)
    assert runtime["status"] == "idle"
    assert runtime["task_id"] is None
