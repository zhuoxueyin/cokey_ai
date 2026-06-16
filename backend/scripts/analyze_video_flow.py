"""分析视频生成链路及第一次接口返回结果"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_mongodb
from app.services.channel_service import get_channel_service
from app.services.model_service import get_model_service


async def main():
    await init_mongodb()
    channel_svc = get_channel_service()
    model_svc = get_model_service()
    
    print("=" * 70)
    print("视频生成完整链路分析")
    print("=" * 70)
    
    print("\n1. 配置检查")
    print("-" * 70)
    
    # 检查火山引擎渠道配置
    channel = await channel_svc.get_by_code("volcengine_video")
    if channel:
        api_config = channel.get("api_config", {})
        print(f"渠道: {channel.get('channel_name')} ({channel.get('channel_code')})")
        print(f"状态: {channel.get('status')}")
        print(f"Base URL: {channel.get('base_url')}")
        print(f"video_path: {api_config.get('video_path')}")
        print(f"完整视频接口: {channel.get('base_url')}{api_config.get('video_path', '')}")
    
    # 检查视频模型配置
    model = await model_svc.get_by_code("seedancer-video")
    if model:
        bindings = model.get("channel_bindings", [])
        print(f"\n模型: {model.get('model_name')} ({model.get('model_code')})")
        print(f"状态: {model.get('status')}")
        for b in bindings:
            print(f"渠道绑定: {b.get('channel_code')} -> {b.get('channel_model_id')}")
    
    print("\n" + "=" * 70)
    print("2. 视频生成链路")
    print("=" * 70)
    
    flow = [
        "1. 用户请求 /api/generate/video",
        "2. gateway_service.execute() - 验证参数、选择渠道",
        "3. 创建 VolcengineAdapter 适配器",
        "4. adapter.execute() - 主执行方法",
        "   ├── convert_params() - 转换参数格式",
        "   ├── call_api() - 调用渠道API",
        "   │   └── _call_video_async() - 异步视频生成",
        "   │       ├── 步骤1: POST /api/v3/contents/generations/tasks (创建任务)",
        "   │       └── 步骤2: GET /api/v3/contents/generations/tasks/{task_id} (轮询状态)",
        "   └── parse_result() - 解析响应",
        "5. 返回视频URL给用户"
    ]
    
    for step in flow:
        print(f"  {step}")
    
    print("\n" + "=" * 70)
    print("3. 第一次接口（创建任务）返回格式")
    print("=" * 70)
    
    print("""
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks

请求体:
{
    "model": "doubao-seed-2-0-mini",
    "content": [...],
    "generate_audio": false,
    "ratio": "16:9",
    "duration": 11,
    "watermark": false
}

成功响应（期望）:
{
    "task_id": "task-xxx-xxx-xxx",
    "status": "running"
}

如果响应中没有 task_id，会报错:
"创建任务失败：未返回 task_id"
""")
    
    print("\n" + "=" * 70)
    print("4. 当前问题分析")
    print("=" * 70)
    
    print("""
问题根源:
1. 之前 video_path 配置错误为 /api/v3/responses（文本接口）
   → 已修复为 /api/v3/contents/generations/tasks（视频接口）

2. 模型ID问题:
   - "doubao-seed-2-0-mini" - 不支持内容生成
   - 需要确认正确的火山引擎视频模型ID

3. 确保API Key有视频生成权限
""")


if __name__ == "__main__":
    asyncio.run(main())
