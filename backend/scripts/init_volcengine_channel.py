#!/usr/bin/env python3
"""
初始化火山引擎渠道和视频模型配置

使用方式:
cd backend && python scripts/init_volcengine_channel.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_mongodb
from app.services.channel_service import ChannelService
from app.services.model_service import ModelService


async def init_volcengine_channel():
    """初始化火山引擎渠道配置"""
    await init_mongodb()
    
    channel_service = ChannelService()
    model_service = ModelService()
    
    # ========== 创建火山引擎渠道 ==========
    channel_data = {
        "channel_code": "volcengine_video",
        "channel_name": "火山引擎视频",
        "channel_type": "volcengine",
        "base_url": "https://ark.cn-beijing.volces.com",
        "auth_config": {
            "api_key": "ark-ad5b7fc4-895e-4253-86d0-674c13b0f7af-eee56"
        },
        "api_config": {
            "text_path": "/api/v3/responses",
            "image_path": "/api/v3/responses",
            "video_path": "/api/v3/responses",
            "text_stream": False
        },
        "retry_config": {
            "timeout": 120,
            "max_retries": 2,
            "retry_delay": 3
        },
        "rate_limit_config": {
            "requests_per_minute": 30
        },
        "status": "active",
        "description": "火山引擎直连渠道，用于视频模型 seedancer"
    }
    
    # 检查渠道是否已存在
    existing_channel = await channel_service.get_by_code("volcengine_video")
    if existing_channel:
        print(f"渠道已存在，更新配置: volcengine_video")
        # 使用渠道的 id 更新（注意返回的是 id 而不是 _id）
        result = await channel_service.update(existing_channel["id"], channel_data)
    else:
        print(f"创建新渠道: volcengine_video")
        result = await channel_service.create(channel_data)
    
    if result:
        print(f"渠道配置结果: {result.get('channel_code')}")
    else:
        print("渠道更新失败")
    
    # ========== 创建视频模型 ==========
    model_data = {
        "model_code": "seedancer-video",
        "model_name": "Seedancer 视频模型",
        "category": "video",
        "model_type": "video",
        "description": "火山引擎 seedancer 视频生成模型，支持图文输入",
        "status": "online",
        "channel_bindings": [
            {
                "channel_code": "volcengine_video",
                "channel_model_id": "doubao-seed-2-0-mini",
                "priority": 10,
                "status": "active"
            }
        ],
        "default_params": {
            "max_tokens": 4096,
            "temperature": 0.7
        },
        "supported_categories": ["video", "text", "image"]
    }
    
    # 检查模型是否已存在
    existing_model = await model_service.get_by_code("seedancer-video")
    if existing_model:
        print(f"模型已存在，更新配置: seedancer-video")
        # 使用模型的 id 更新（注意返回的是 id 而不是 _id）
        result = await model_service.update(existing_model["id"], model_data)
    else:
        print(f"创建新模型: seedancer-video")
        result = await model_service.create(model_data)
    
    if result:
        print(f"模型配置结果: {result.get('model_code')}")
    else:
        print("模型更新失败")
    
    print("\n=== 初始化完成 ===")
    print("渠道: volcengine_video (火山引擎直连)")
    print("模型: seedancer-video (Seedancer 视频模型)")
    print("API Key: ark-ad5b7fc4-895e-4253-86d0-674c13b0f7af-eee56")


if __name__ == "__main__":
    asyncio.run(init_volcengine_channel())