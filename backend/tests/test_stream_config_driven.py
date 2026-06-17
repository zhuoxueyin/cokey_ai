"""
测试: stream 参数按配置严格传递（无自动注入）
- 场景 1: text 端点 body_params 包含 stream/fixed/True → body 应包含 stream=True
- 场景 2: text 端点 body_params 不包含 stream → body 不包含 stream（严格按配置）
- 场景 3: 模拟用户真实场景 - text 端点仅有 model/messages/max_tokens
- 场景 4: fixed 类型 True/true/TRUE 大小写各种格式解析
"""
import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_engine import ConfigEngine

print("=" * 70)
print("TEST 1: text 端点 body_params 包含 stream/fixed=True（正确配置）")
print("=" * 70)

endpoint_config_1 = {
    "type": "text",
    "endpoint": "chat/completions",
    "method": "POST",
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
    "prompt": "根据参考图中不同角色，生成角色出场带球盘带描述...",
    "images": ["https://cdn.jsdmirror.com/gh/zhuoxueyin/cokey_ai@main/assets/images/20260617/d4b8da3d.jpeg"],
    "temperature": 0.7,
    "max_tokens": 30000,
}

body_1 = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config_1,
    params=params,
    model_id="gpt-5.5",
    channel_code="weelink_text",
    trace_id="test-stream-001",
)

print(f"\nbody 字段: {list(body_1.keys())}")
print(f"body: {json.dumps(body_1, ensure_ascii=False, indent=2, default=str)}")
print(f"\n  ✓ model 存在: {body_1.get('model') == 'gpt-5.5'}")
print(f"  ✓ messages 存在: {'messages' in body_1}")
print(f"  ✓ temperature 存在: {body_1.get('temperature') == 0.7}")
print(f"  ✓ max_tokens 存在: {body_1.get('max_tokens') == 30000}")
print(f"  ✓ stream 存在: {body_1.get('stream') is True}")
print(f"  ✓ stream 类型: {type(body_1.get('stream'))}")

print("\n" + "=" * 70)
print("TEST 2: text 端点 body_params 不包含 stream（配置遗漏）- 严格按配置")
print("=" * 70)

endpoint_config_2 = {
    "type": "text",
    "endpoint": "chat/completions",
    "method": "POST",
    "content_type": "application/json",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "max_tokens", "value_type": "dynamic", "value": "max_tokens"},
        # 注意: 没有 stream 配置
    ],
}

body_2 = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config_2,
    params=params,
    model_id="gpt-5.5",
    channel_code="weelink_text",
    trace_id="test-stream-002",
)

print(f"\nbody 字段: {list(body_2.keys())}")
print(f"body: {json.dumps(body_2, ensure_ascii=False, indent=2, default=str)}")
print(f"\n  ✓ model 存在: {body_2.get('model') == 'gpt-5.5'}")
print(f"  ✓ messages 存在: {'messages' in body_2}")
print(f"  ✓ max_tokens 存在: {body_2.get('max_tokens') == 30000}")
print(f"  ✓ stream 不存在（严格按配置）: {'stream' not in body_2}")
print(f"  ⚠️  【此情况需补充配置：stream/fixed=True 或 stream=false】")

print("\n" + "=" * 70)
print("TEST 3: stream/fixed 各种值格式解析（True/true/TRUE/False/false/FALSE）")
print("=" * 70)

test_values = ["True", "true", "TRUE", "False", "false", "FALSE", "yes", "no", "1", "0", "3000"]
print()
for v in test_values:
    parsed = ConfigEngine._smart_parse_fixed_value(v)
    print(f"  _smart_parse_fixed_value('{v}') = {parsed!r}  (类型: {type(parsed).__name__})")

print("\n" + "=" * 70)
print("TEST 4: stream 设为 false（禁用流式）")
print("=" * 70)

endpoint_config_4 = {
    "type": "text",
    "endpoint": "chat/completions",
    "method": "POST",
    "content_type": "application/json",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "stream", "value_type": "fixed", "value": "false"},
    ],
}

body_4 = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config_4,
    params={"prompt": "hi"},
    model_id="gpt-5.5",
    channel_code="weelink_text",
    trace_id="test-stream-004",
)
print(f"\nbody: {json.dumps(body_4, ensure_ascii=False, indent=2, default=str)}")
print(f"  ✓ stream=False: {body_4.get('stream') is False}")

print("\n" + "=" * 70)
print("TEST 5: 完整端到端模拟 - 数据库配置缺失 stream 的修复方法")
print("=" * 70)
print("""
用户遇到的实际问题: endpoint_type=text，但 body 中没有 stream 字段

诊断路径:
1. 网关层: _determine_endpoint_type(category="text", params) → 返回 "text"
2. 适配器层: _get_endpoint_by_type("text") → 找到 channels.endpoints 中 type="text" 的端点
3. 构建请求体: ConfigEngine.build_request_body → 根据 endpoints.body_params 构建
4. 问题: 如果 endpoints.body_params 中没有 {"key": "stream", "value_type": "fixed", "value": "True"},
           则最终请求体中不会有 stream 字段（严格按配置）

修复方案: 【在渠道配置中补充 stream 参数】
渠道管理 → 编辑渠道 → 端点配置 → text 类型端点 → body_params → 添加:
  key=stream, value_type=fixed, value=True

正确的 endpoints.body_params 配置示例:
  [
    {"key": "model",        "value_type": "dynamic", "value": "model"},
    {"key": "messages",     "value_type": "dynamic", "value": "messages"},
    {"key": "temperature",  "value_type": "dynamic", "value": "temperature"},
    {"key": "max_tokens",   "value_type": "dynamic", "value": "max_tokens"},
    {"key": "stream",       "value_type": "fixed",   "value": "True"},   ← 必须有这一行
  ]

""")

print("=" * 70)
print("测试总结")
print("=" * 70)

checks = [
    ("TEST 1: body_params 中有 stream/fixed=True → body.stream=True",
     body_1.get('stream') is True),
    ("TEST 1: messages 智能构建", 'messages' in body_1),
    ("TEST 2: body_params 中无 stream → body 无 stream (严格按配置)",
     'stream' not in body_2),
    ("TEST 3: 'True'/'true'/'TRUE' 都解析为 True",
     ConfigEngine._smart_parse_fixed_value("True") is True
     and ConfigEngine._smart_parse_fixed_value("true") is True
     and ConfigEngine._smart_parse_fixed_value("TRUE") is True),
    ("TEST 3: 'False'/'false'/'FALSE' 都解析为 False",
     ConfigEngine._smart_parse_fixed_value("False") is False
     and ConfigEngine._smart_parse_fixed_value("false") is False
     and ConfigEngine._smart_parse_fixed_value("FALSE") is False),
    ("TEST 4: stream/fixed=false → body.stream=False",
     body_4.get('stream') is False),
]

all_pass = True
for name, result in checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"  {status} {name}")
    if not result:
        all_pass = False

if all_pass:
    print("\n✅ 全部测试通过！代码逻辑正确，stream 传递完全按配置驱动。")
    print("   只需在渠道端点配置中补充 stream 字段即可修复。")
else:
    print("\n⚠️ 部分测试失败，请检查代码逻辑。")
