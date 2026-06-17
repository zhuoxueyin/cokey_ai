"""调试脚本：检查 build_request_body 中 temperature 和 max_tokens 字段提取"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_engine import ConfigEngine

# 模拟测试 3 场景
endpoint_config = {
    "type": "text",
    "endpoint": "chat/completions",
    "content_type": "application/json",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "temperature", "value_type": "dynamic", "value": "temperature"},
        {"key": "max_tokens", "value_type": "dynamic", "value": "max_tokens"},
        {"key": "stream", "value_type": "fixed", "value": "True"},
    ],
}

params = {
    "prompt": "根据参考图生成描述",
    "images": [
        "https://cdn.jsdmirror.com/gh/example/repo@main/img1.png",
    ],
    "temperature": 0.8,
    "max_tokens": 1000,
}

print("params:", params)
print("params.temperature:", params.get("temperature"))
print("params.max_tokens:", params.get("max_tokens"))

# 手动测试 _get_nested_field
val_temp = ConfigEngine._get_nested_field(params, "temperature")
val_tokens = ConfigEngine._get_nested_field(params, "max_tokens")
print("_get_nested_field temperature:", val_temp, "is not None:", val_temp is not None)
print("_get_nested_field max_tokens:", val_tokens, "is not None:", val_tokens is not None)

# 调用 build_request_body
body = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config,
    params=params,
    model_id="text-model",
    channel_code="weelink_text",
    trace_id="debug-001"
)

import json
print("\nbuild_request_body result:")
print(json.dumps(body, ensure_ascii=False, indent=2))
print("\nbody keys:", list(body.keys()))
print("has temperature:", "temperature" in body)
print("has max_tokens:", "max_tokens" in body)
