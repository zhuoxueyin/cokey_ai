"""验证 images/edits 端点 multipart/form-data 构建逻辑"""
import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_engine import ConfigEngine

# 模拟 weelink_image 的 image_edits 端点配置
endpoint_config = {
    "type": "image_edits",
    "endpoint": "images/edits",
    "method": "POST",
    "content_type": "multipart/form-data",
    "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
        {"key": "images[]", "value_type": "image", "value": "images"},
        {"key": "n", "value_type": "dynamic", "value": "n"},
        {"key": "size", "value_type": "dynamic", "value": "size"},
        {"key": "quality", "value_type": "dynamic", "value": "quality"},
    ],
}

# 模拟业务层传入参数
params = {
    "prompt": "将图1的商品放入图2的场景中，保持光影真实",
    "images": [
        "https://cdn.jsdmirror.com/gh/example/repo@main/assets/product.png",
        "https://cdn.jsdmirror.com/gh/example/repo@main/assets/scene.png",
    ],
    "size": "1536x1024",
    "quality": "high",
    "n": 1,
}

body = ConfigEngine.build_request_body(
    endpoint_config=endpoint_config,
    params=params,
    model_id="gpt-image-2",
    channel_code="weelink_image",
    trace_id="test-image-edits"
)

print("=" * 60)
print("images/edits 端点请求体构建结果")
print("=" * 60)
print(f"\nbody_type: {endpoint_config['content_type']}")
print(f"body keys: {list(body.keys())}")
print(f"\n完整 body:")
print(json.dumps(body, ensure_ascii=False, indent=2))

# 验证
print("\n" + "=" * 60)
print("关键验证")
print("=" * 60)

checks = [
    ("model 字段", "model" in body and body["model"] == "gpt-image-2"),
    ("prompt 字段", "prompt" in body and body["prompt"] == "将图1的商品放入图2的场景中，保持光影真实"),
    ("images[] 字段", "images[]" in body and isinstance(body["images[]"], list)),
    ("images[] 含2张图", isinstance(body.get("images[]"), list) and len(body["images[]"]) == 2),
    ("size 字段", "size" in body and body["size"] == "1536x1024"),
    ("quality 字段", "quality" in body and body["quality"] == "high"),
    ("n 字段", "n" in body and body["n"] == 1),
]

all_pass = True
for check_name, result in checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {check_name}")
    if not result:
        all_pass = False

if all_pass:
    print("\n[SUCCESS] images/edits 端点配置和构建逻辑正确！")
    print("\n后续 multipart/form-data 发送流程：")
    print("1. body 中的 images[] 会被识别为图片字段")
    print("2. CDN URL 会被下载为图片字节")
    print("3. 文本字段（model/prompt/size/quality/n）作为普通 form-data 文本")
    print("4. 图片字段（images[]）作为 form-data 文件上传")
    print("5. 最终发送请求到 images/edits 端点")
else:
    print("\n[ERROR] 部分验证失败，请检查配置")
