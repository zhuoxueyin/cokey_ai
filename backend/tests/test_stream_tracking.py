"""
追踪 stream 参数从数据库配置到 API 请求体的完整流程
运行方式: cd backend && python -m tests.test_stream_tracking
"""
import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_engine import ConfigEngine

print("=" * 60)
print("测试 1: 标准 chat 端点配置（包含 stream 的 fixed 值）")
print("=" * 60)

# 模拟数据库中配置的 endpoint_config（weelink_text 的 chat 端点）
endpoint_config_1 = {
    "type": "chat",
    "endpoint": "chat/completions",
    "method": "POST",
    "content_type": "application/json",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "stream", "value_type": "fixed", "value": "True"},
    ],
}

# 业务层传入的参数（来自前端/用户）
params_1 = {
    "prompt": "你好，帮我写一个快速排序",
    "images": [],
    "temperature": 0.7,
    "max_tokens": 2000,
}

body_1 = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config_1,
    params=params_1,
    model_id="gpt-5.5",
    channel_code="weelink_text",
    trace_id="trace-test-001"
)

print("\n输入 body_params 配置:")
for bp in endpoint_config_1["body_params"]:
    print(f"  - {bp['key']}: {bp['value_type']}='{bp['value']}'")

print("\n输出请求体 body:")
print(json.dumps(body_1, ensure_ascii=False, indent=2))

# 验证
print("\n关键检查:")
print(f"  ✓ body 中包含 'stream' 字段: {'stream' in body_1}")
print(f"  ✓ stream 字段值: {body_1.get('stream')} (类型: {type(body_1.get('stream')).__name__})")
print(f"  ✓ body 中包含 'messages' 字段: {'messages' in body_1}")
print(f"  ✓ body 中包含 'model' 字段: {'model' in body_1}")

print("\n" + "=" * 60)
print("测试 2: text 端点配置（也包含 stream 的 fixed 值）")
print("=" * 60)

endpoint_config_2 = {
    "type": "text",
    "endpoint": "chat/completions",
    "content_type": "application/json",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "temperature", "value_type": "dynamic", "value": "temperature"},
        {"key": "max_tokens", "value_type": "dynamic", "value": "max_tokens"},
        {"key": "stream", "value_type": "fixed", "value": "true"},
    ],
}

params_2 = {
    "prompt": "用一句话解释什么是快速排序",
    "images": [],
    "temperature": 0.7,
    "max_tokens": 2000,
}

body_2 = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config_2,
    params=params_2,
    model_id="gpt-5.5",
    channel_code="weelink_text",
    trace_id="trace-test-002"
)

print("\n输入 body_params 配置:")
for bp in endpoint_config_2["body_params"]:
    print(f"  - {bp['key']}: {bp['value_type']}='{bp['value']}'")

print("\n输出请求体 body:")
print(json.dumps(body_2, ensure_ascii=False, indent=2))

print("\n关键检查:")
print(f"  ✓ body 中包含 'stream' 字段: {'stream' in body_2}")
print(f"  ✓ stream 字段值: {body_2.get('stream')} (类型: {type(body_2.get('stream')).__name__})")
print(f"  ✓ body 中包含 'temperature' 字段: {'temperature' in body_2}")
print(f"  ✓ body 中包含 'max_tokens' 字段: {'max_tokens' in body_2}")

print("\n" + "=" * 60)
print("测试 3: stream 的各种值格式（测试 _smart_parse_fixed_value）")
print("=" * 60)

test_cases = [
    "True", "true", "TRUE",
    "False", "false", "FALSE",
    "yes", "no",
    "1", "0",
    "3000",
    "1.5",
    "",
]

for test_val in test_cases:
    parsed = ConfigEngine._smart_parse_fixed_value(test_val)
    print(f"  '{test_val}' -> {parsed} (类型: {type(parsed).__name__})")

print("\n" + "=" * 60)
print("测试 4: 检查 _smart_parse_fixed_value 对 Python bool 的处理")
print("=" * 60)

# 用户可能直接在 JSON 中存了 true/false，而非字符串
test_bool_cases = [
    True, False, None, 1, 0, 3000,
]

for test_val in test_bool_cases:
    parsed = ConfigEngine._smart_parse_fixed_value(test_val)
    print(f"  {test_val!r} -> {parsed} (类型: {type(parsed).__name__})")

print("\n" + "=" * 60)
print("完整测试总结")
print("=" * 60)

all_pass = True
checks = [
    ("测试1 stream 存在", "stream" in body_1),
    ("测试1 stream 值正确", body_1.get("stream") is True),
    ("测试2 stream 存在", "stream" in body_2),
    ("测试2 stream 值正确", body_2.get("stream") is True),
    ("测试2 temperature 存在", "temperature" in body_2),
    ("测试2 max_tokens 存在", "max_tokens" in body_2),
]

for name, result in checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"  {status} {name}")
    if not result:
        all_pass = False

if all_pass:
    print("\n🎉 所有测试通过 - body_params 构建逻辑正确")
else:
    print("\n⚠️ 部分测试失败 - 需要检查问题")
