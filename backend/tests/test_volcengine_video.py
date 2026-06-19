from app.core.volcengine_video import (
    VOLCENGINE_VIDEO_MULTIMODAL_SLOT,
    is_volcengine_video_endpoint,
    is_volcengine_video_slot,
    normalize_volcengine_video_slot,
)


def test_normalize_legacy_slot():
    assert normalize_volcengine_video_slot("volcengine.video.task") == VOLCENGINE_VIDEO_MULTIMODAL_SLOT
    assert is_volcengine_video_slot("volcengine.video.multimodal")


def test_is_volcengine_video_endpoint_by_slot():
    assert is_volcengine_video_endpoint({
        "type": "chat",
        "protocol_slot": "volcengine.video.multimodal",
        "endpoint": "contents/generations/tasks",
    })


def test_is_volcengine_video_endpoint_by_type():
    assert is_volcengine_video_endpoint({"type": "video", "endpoint": "x"})
    assert is_volcengine_video_endpoint({"type": "video_image", "endpoint": "x"})


def test_finalize_volcengine_video_body_fills_empty_config_engine_output():
    from app.adapters.volcengine import VolcengineAdapter

    adapter = VolcengineAdapter({"channel_code": "volcengine_video", "base_url": "https://x"}, "t1")
    channel_params = adapter._build_video_body({
        "prompt": "test prompt",
        "images": ["https://cdn.jsdmirror.com/gh/example/a.png"],
        "ratio": "16:9",
        "duration": 15,
        "audio": True,
        "watermark": False,
    })
    body = adapter._finalize_volcengine_video_body({}, channel_params, "ep-test-endpoint")
    assert body["model"] == "ep-test-endpoint"
    assert body["content"]
    assert body["content"][0]["type"] == "text"
    assert body["ratio"] == "16:9"
    assert body["duration"] == 15

