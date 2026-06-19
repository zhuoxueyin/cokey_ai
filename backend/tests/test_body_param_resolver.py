"""body_param_resolver 单元测试。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.body_param_resolver import (
    build_body_from_params,
    normalize_body_param,
)
from app.core.config_engine import ConfigEngine


def test_normalize_legacy_dynamic():
    n = normalize_body_param({"key": "prompt", "value_type": "dynamic", "value": ""})
    assert n["source"] == "task_param"
    assert n["param"] == "prompt"


def test_normalize_legacy_fixed():
    n = normalize_body_param({"key": "stream", "value_type": "fixed", "value": "false"})
    assert n["source"] == "literal"
    assert n["literal"] == "false"


def test_normalize_legacy_misconfigured_model():
    n = normalize_body_param({
        "key": "model",
        "value_type": "dynamic",
        "value": "doubao-seedance-2-0-260128",
    })
    assert n["source"] == "task_param"
    assert n["param"] == "doubao-seedance-2-0-260128"


def test_build_new_format():
    body = build_body_from_params(
        [
            {"key": "model", "source": "builtin", "builtin": "channel_model_id"},
            {"key": "prompt", "source": "task_param", "param": "prompt"},
            {"key": "stream", "source": "literal", "literal": "false"},
        ],
        {"prompt": "hello"},
        model_id="ep-123",
    )
    assert body["model"] == "ep-123"
    assert body["prompt"] == "hello"
    assert body["stream"] is False


def test_config_engine_legacy_compat():
    body = ConfigEngine.build_request_body(
        endpoint_config={
            "body_params": [
                {"key": "model", "source": "builtin", "builtin": "channel_model_id"},
                {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
            ]
        },
        params={"prompt": "cat"},
        model_id="ep-vip",
        channel_code="c1",
        trace_id="t1",
    )
    assert body["model"] == "ep-vip"
    assert body["prompt"] == "cat"


if __name__ == "__main__":
    test_normalize_legacy_dynamic()
    test_normalize_legacy_fixed()
    test_normalize_legacy_misconfigured_model()
    test_build_new_format()
    test_config_engine_legacy_compat()
    print("ok")
