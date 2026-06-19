"""ConfigEngine model 字段兜底。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_engine import ConfigEngine


def test_body_params_injects_model_when_missing():
    body = ConfigEngine.build_request_body(
        endpoint_config={
            "body_params": [
                {"key": "messages", "value_type": "dynamic", "value": "messages"},
            ]
        },
        params={"prompt": "a cat"},
        model_id="gpt-image-2-vip",
        channel_code="apiyi_1",
        trace_id="t1",
    )
    assert body.get("model") == "gpt-image-2-vip"
    assert "messages" in body


def test_body_params_model_key_uses_model_id_fallback():
    body = ConfigEngine.build_request_body(
        endpoint_config={
            "body_params": [
                {"key": "model", "value_type": "dynamic", "value": "channel_model_id"},
                {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
            ]
        },
        params={"prompt": "hello"},
        model_id="gpt-image-2-vip",
        channel_code="apiyi_1",
        trace_id="t1",
    )
    assert body.get("model") == "gpt-image-2-vip"


if __name__ == "__main__":
    test_body_params_injects_model_when_missing()
    test_body_params_model_key_uses_model_id_fallback()
    print("ok")
