"""
验证 weelink_text 渠道 messages 字段构建逻辑测试
运行方式: cd backend && python -m tests.test_weelink_messages
"""
import json
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config_engine import ConfigEngine

def test_chat_endpoint_with_prompt_and_images():
    """测试 chat 端点：业务参数只有 prompt 和 images，应自动构建 messages 字段"""
    endpoint_config = {
        "type": "chat",
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
        "prompt": "这是一个测试提示词，描述图片内容",
        "images": [
            "https://cdn.jsdmirror.com/gh/example/repo@main/assets/image1.jpg",
        ],
    }
    model_id = "gpt-5.5"

    body = ConfigEngine.build_request_body(
        endpoint_config=endpoint_config,
        params=params,
        model_id=model_id,
        channel_code="weelink_text",
        trace_id="test-trace-001"
    )

    print("===== 测试 1: chat 端点 + prompt+images =====")
    print(f"body: {json.dumps(body, ensure_ascii=False, indent=2)}")

    # 验证字段
    assert "model" in body, "❌ body 中缺少 model 字段"
    assert body["model"] == "gpt-5.5", f"❌ model 值错误: {body['model']}"
    assert "messages" in body, "❌ body 中缺少 messages 字段"
    assert isinstance(body["messages"], list), "❌ messages 应为数组"
    assert len(body["messages"]) > 0, "❌ messages 数组为空"

    first_msg = body["messages"][0]
    assert first_msg["role"] == "user", f"❌ role 应为 user: {first_msg.get('role')}"

    content = first_msg["content"]
    assert isinstance(content, list), "❌ 有图片时 content 应为多模态数组"
    content_types = [item.get("type") for item in content]
    assert "text" in content_types, "❌ content 中缺少 text 类型项"
    assert "image_url" in content_types, "❌ content 中缺少 image_url 类型项"

    # 检查 stream 字段
    assert body.get("stream") is True, f"❌ stream 应为 True"

    print("✅ 测试 1 通过\n")


def test_chat_endpoint_with_only_prompt():
    """测试 chat 端点：业务参数只有 prompt，应构建纯文本 messages"""
    endpoint_config = {
        "type": "chat",
        "endpoint": "chat/completions",
        "content_type": "application/json",
        "body_params": [
            {"key": "model", "value_type": "dynamic", "value": "model"},
            {"key": "messages", "value_type": "dynamic", "value": "messages"},
            {"key": "stream", "value_type": "fixed", "value": "True"},
        ],
    }

    params = {
        "prompt": "纯文本对话提示词",
    }
    model_id = "gpt-5.5"

    body = ConfigEngine.build_request_body(
        endpoint_config=endpoint_config,
        params=params,
        model_id=model_id,
        channel_code="weelink_text",
        trace_id="test-trace-002"
    )

    print("===== 测试 2: chat 端点 + 仅 prompt =====")
    print(f"body: {json.dumps(body, ensure_ascii=False, indent=2)}")

    assert "messages" in body, "❌ body 中缺少 messages 字段"
    first_msg = body["messages"][0]
    content = first_msg["content"]
    assert isinstance(content, str), "❌ 纯文本时 content 应为字符串"
    assert "纯文本对话提示词" in content, f"❌ content 值错误: {content}"

    print("✅ 测试 2 通过\n")


def test_text_endpoint_also_use_messages():
    """测试 text 端点走 chat/completions，应正确构建 messages"""
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
            "https://cdn.jsdmirror.com/gh/example/repo@main/img2.png"
        ],
        "temperature": 0.8,
        "max_tokens": 1000,
    }
    model_id = "text-model"

    body = ConfigEngine.build_request_body(
        endpoint_config=endpoint_config,
        params=params,
        model_id=model_id,
        channel_code="weelink_text",
        trace_id="test-trace-003"
    )

    print("===== 测试 3: text 端点走 chat/completions + prompt+images+temperature =====")
    print(f"body: {json.dumps(body, ensure_ascii=False, indent=2)}")

    assert "messages" in body, "❌ body 中缺少 messages 字段"
    assert "temperature" in body and body["temperature"] == 0.8, "❌ temperature 取值错误"

    content = body["messages"][0]["content"]
    assert isinstance(content, list), "❌ 有图片时 content 应为多模态数组"
    image_items = [item for item in content if item.get("type") == "image_url"]
    assert len(image_items) == 2, f"❌ 应为 2 张图片，实际 {len(image_items)}"

    print("✅ 测试 3 通过\n")


def test_user_scenario_reproduction():
    """复现用户原始场景：{prompt, images} + text 类别"""
    # 模拟用户提供的原始请求场景
    endpoint_config = {
        "type": "chat",
        "endpoint": "chat/completions",
        "content_type": "application/json",
        "body_params": [
            {"key": "model", "value_type": "dynamic", "value": "model"},
            {"key": "messages", "value_type": "dynamic", "value": "messages"},
            {"key": "stream", "value_type": "fixed", "value": "True"},
        ],
    }

    # 模拟用户实际传入 params
    params = {
        "prompt": "根据参考图中不同角色，生成一条角色逐一出场带球盘带...",
        "images": ["https://cdn.jsdmirror.com/gh/zhuoxueyin/cokey_ai@main/assets/images/20260617/d4b8da3d.jpeg"],
    }
    model_id = "gpt-5.5"

    body = ConfigEngine.build_request_body(
        endpoint_config=endpoint_config,
        params=params,
        model_id=model_id,
        channel_code="weelink_text",
        trace_id="test-user-scenario"
    )

    print("===== 测试 4: 复现用户原始请求场景 =====")
    print(f"构建后的 body: {json.dumps(body, ensure_ascii=False, indent=2)}")

    # 关键断言：body 中必须有 messages 字段
    assert "messages" in body, "❌ body 中缺少 messages 字段（用户问题的核心！）"
    assert len(body) > 1, "❌ body 字段数量不足"

    print("✅ 测试 4 通过\n")


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("\n")
    print("=======================================")
    print("   weelink_text 渠道 messages 构建测试  ")
    print("=======================================")
    print("\n")

    all_passed = True
    try:
        test_chat_endpoint_with_prompt_and_images()
        test_chat_endpoint_with_only_prompt()
        test_text_endpoint_also_use_messages()
        test_user_scenario_reproduction()
    except AssertionError as e:
        print(f"\n[ERROR] 测试失败: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n[ERROR] 意外错误: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    if all_passed:
        print("\n[SUCCESS] 所有测试通过！messages 字段构建成功。\n")
    else:
        print("\n[WARN] 部分测试失败，请检查代码修复\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
