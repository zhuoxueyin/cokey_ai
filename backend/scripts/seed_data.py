from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import asyncio

MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB = "aigc_platform"


async def seed_data():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]

    # 清理旧数据
    await db.channels.drop()
    await db.models.drop()

    # ========== 渠道配置 ==========
    channels = [
        {
            "channel_code": "weelink_text",
            "channel_name": "WeeLink 文本模型",
            "channel_type": "aggregator",
            "channel_provider": "weelinking",
            "base_url": "https://api.weelink.ai/v1",
            "auth_config": {
                "api_key": "your-weelink-api-key-here",
            },
            "api_config": {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "video_path": "/videos/generations",
                "text_stream": True,
            },
            "endpoints": [
                {
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
                },
                {
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
                },
            ],
            "retry_config": {"timeout": 60, "max_retries": 3, "retry_delay": 2},
            "rate_limit_config": {"requests_per_minute": 60},
            "status": "active",
            "description": "WeeLink聚合平台 - 文本模型接入",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "channel_code": "weelink_image",
            "channel_name": "WeeLink 图像模型",
            "channel_type": "aggregator",
            "channel_provider": "weelinking",
            "base_url": "https://api.weelink.ai/v1",
            "auth_config": {
                "api_key": "your-weelink-api-key-here",
            },
            "api_config": {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "image_edits_path": "/images/edits",
                "video_path": "/videos/generations",
                "text_stream": True,
            },
            "endpoints": [
                {
                    "type": "image",
                    "endpoint": "images/generations",
                    "method": "POST",
                    "content_type": "application/json",
                    "body_params": [
                        {"key": "model", "value_type": "dynamic", "value": "model"},
                        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
                        {"key": "n", "value_type": "dynamic", "value": "n"},
                        {"key": "size", "value_type": "dynamic", "value": "size"},
                        {"key": "quality", "value_type": "dynamic", "value": "quality"},
                    ],
                },
                {
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
                },
            ],
            "retry_config": {"timeout": 120, "max_retries": 3, "retry_delay": 2},
            "rate_limit_config": {"requests_per_minute": 30},
            "status": "active",
            "description": "WeeLink聚合平台 - 图像模型接入",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "channel_code": "weelink_video",
            "channel_name": "WeeLink 视频模型",
            "channel_type": "aggregator",
            "channel_provider": "weelinking",
            "base_url": "https://api.weelink.ai/v1",
            "auth_config": {
                "api_key": "your-weelink-api-key-here",
            },
            "api_config": {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "video_path": "/videos/generations",
                "text_stream": True,
            },
            "endpoints": [
                {
                    "type": "video",
                    "endpoint": "videos/generations",
                    "method": "POST",
                    "content_type": "application/json",
                    "body_params": [
                        {"key": "model", "value_type": "dynamic", "value": "model"},
                        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
                        {"key": "duration", "value_type": "dynamic", "value": "duration"},
                        {"key": "size", "value_type": "dynamic", "value": "size"},
                    ],
                },
                {
                    "type": "video_image",
                    "endpoint": "videos/generations",
                    "method": "POST",
                    "content_type": "application/json",
                    "body_params": [
                        {"key": "model", "value_type": "dynamic", "value": "model"},
                        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
                        {"key": "image", "value_type": "image", "value": "images"},
                        {"key": "duration", "value_type": "dynamic", "value": "duration"},
                        {"key": "size", "value_type": "dynamic", "value": "size"},
                    ],
                },
            ],
            "retry_config": {"timeout": 300, "max_retries": 2, "retry_delay": 5},
            "rate_limit_config": {"requests_per_minute": 10},
            "status": "active",
            "description": "WeeLink聚合平台 - 视频模型接入",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]

    await db.channels.insert_many(channels)
    print(f"已插入 {len(channels)} 个渠道配置")

    # ========== 模型配置 ==========
    models = [
        {
            "model_code": "gpt-3.5-turbo",
            "model_name": "GPT-3.5 Turbo",
            "category": "text",
            "cover": "",
            "description": "通用对话模型，适用于日常问答、文本创作、代码生成",
            "tags": ["通用", "对话", "快速"],
            "channel_bindings": [
                {"channel_code": "weelink_text", "channel_model_id": "gpt-3.5-turbo", "priority": 1, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "提示词", "field_type": "textarea", "required": True, "placeholder": "请输入您的问题或描述..."},
                    {"name": "temperature", "label": "温度", "field_type": "slider", "required": False, "default": 0.7, "min": 0, "max": 2, "step": 0.1, "help_text": "控制生成内容的随机性，0为确定性，2为最大随机性"},
                    {"name": "max_tokens", "label": "最大生成长度", "field_type": "number", "required": False, "default": 2000, "min": 1, "max": 16000, "step": 100},
                ]
            },
            "status": "online",
            "sort_order": 100,
            "is_default": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "model_code": "gpt-4o-mini",
            "model_name": "GPT-4o Mini",
            "category": "text",
            "cover": "",
            "description": "轻量级GPT-4o模型，速度快且性价比高",
            "tags": ["通用", "对话", "高质量"],
            "channel_bindings": [
                {"channel_code": "weelink_text", "channel_model_id": "gpt-4o-mini", "priority": 2, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "提示词", "field_type": "textarea", "required": True, "placeholder": "请输入您的问题或描述..."},
                    {"name": "temperature", "label": "温度", "field_type": "slider", "required": False, "default": 0.7, "min": 0, "max": 2, "step": 0.1},
                    {"name": "max_tokens", "label": "最大生成长度", "field_type": "number", "required": False, "default": 2000, "min": 1, "max": 32000, "step": 100},
                ]
            },
            "status": "online",
            "sort_order": 90,
            "is_default": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "model_code": "dall-e-3",
            "model_name": "DALL-E 3",
            "category": "image",
            "cover": "",
            "description": "高质量图像生成模型，擅长理解复杂的中文提示词",
            "tags": ["图像", "高质量", "中文友好"],
            "channel_bindings": [
                {"channel_code": "weelink_image", "channel_model_id": "dall-e-3", "priority": 1, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "正向提示词", "field_type": "textarea", "required": True, "placeholder": "描述您想要生成的图像..."},
                    {"name": "size", "label": "尺寸", "field_type": "select", "required": False, "default": "1024x1024",
                        "options": [
                            {"label": "1:1 (1024x1024)", "value": "1024x1024"},
                            {"label": "9:16 (1024x1792)", "value": "1024x1792"},
                            {"label": "16:9 (1792x1024)", "value": "1792x1024"},
                        ]
                    },
                    {"name": "quality", "label": "质量", "field_type": "select", "required": False, "default": "standard",
                        "options": [
                            {"label": "标准", "value": "standard"},
                            {"label": "高清", "value": "hd"},
                        ]
                    },
                    {"name": "n", "label": "生成数量", "field_type": "number", "required": False, "default": 1, "min": 1, "max": 4, "step": 1},
                ]
            },
            "status": "online",
            "sort_order": 100,
            "is_default": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "model_code": "sdxl-turbo",
            "model_name": "SDXL Turbo",
            "category": "image",
            "cover": "",
            "description": "Stable Diffusion XL Turbo - 极速图像生成，几秒出图",
            "tags": ["图像", "快速", "开源"],
            "channel_bindings": [
                {"channel_code": "weelink_image", "channel_model_id": "sdxl-turbo", "priority": 1, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "正向提示词", "field_type": "textarea", "required": True, "placeholder": "描述您想要生成的图像..."},
                    {"name": "negative_prompt", "label": "反向提示词", "field_type": "textarea", "required": False, "placeholder": "不想要的元素..."},
                    {"name": "width", "label": "宽度", "field_type": "number", "required": False, "default": 1024, "min": 512, "max": 2048, "step": 64},
                    {"name": "height", "label": "高度", "field_type": "number", "required": False, "default": 1024, "min": 512, "max": 2048, "step": 64},
                    {"name": "n", "label": "生成数量", "field_type": "number", "required": False, "default": 1, "min": 1, "max": 4, "step": 1},
                ]
            },
            "status": "online",
            "sort_order": 90,
            "is_default": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "model_code": "sora-video",
            "model_name": "Sora 视频生成",
            "category": "video",
            "cover": "",
            "description": "基于文本描述生成高质量视频内容",
            "tags": ["视频", "高质量", "文生视频"],
            "channel_bindings": [
                {"channel_code": "weelink_video", "channel_model_id": "sora-video", "priority": 1, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "提示词", "field_type": "textarea", "required": True, "placeholder": "描述您想要生成的视频内容..."},
                    {"name": "duration", "label": "时长(秒)", "field_type": "select", "required": False, "default": "5",
                        "options": [
                            {"label": "5秒", "value": "5"},
                            {"label": "10秒", "value": "10"},
                            {"label": "15秒", "value": "15"},
                        ]
                    },
                    {"name": "size", "label": "分辨率", "field_type": "select", "required": False, "default": "1080p",
                        "options": [
                            {"label": "720p", "value": "720p"},
                            {"label": "1080p", "value": "1080p"},
                            {"label": "4K", "value": "4k"},
                        ]
                    },
                ]
            },
            "status": "online",
            "sort_order": 100,
            "is_default": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "model_code": "runway-gen3",
            "model_name": "Runway Gen-3",
            "category": "video",
            "cover": "",
            "description": "Runway Gen-3 视频生成模型，支持图生视频、视频扩展",
            "tags": ["视频", "图生视频", "专业"],
            "channel_bindings": [
                {"channel_code": "weelink_video", "channel_model_id": "runway-gen3", "priority": 1, "status": "active"}
            ],
            "param_schema": {
                "fields": [
                    {"name": "prompt", "label": "提示词", "field_type": "textarea", "required": True, "placeholder": "描述您想要生成的视频内容..."},
                    {"name": "reference_image", "label": "参考图（可选）", "field_type": "image_upload", "required": False},
                    {"name": "duration", "label": "时长(秒)", "field_type": "select", "required": False, "default": "5",
                        "options": [
                            {"label": "4秒", "value": "4"},
                            {"label": "8秒", "value": "8"},
                            {"label": "10秒", "value": "10"},
                        ]
                    },
                    {"name": "size", "label": "分辨率", "field_type": "select", "required": False, "default": "1080p",
                        "options": [
                            {"label": "720p", "value": "720p"},
                            {"label": "1080p", "value": "1080p"},
                        ]
                    },
                ]
            },
            "status": "online",
            "sort_order": 90,
            "is_default": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]

    await db.models.insert_many(models)
    print(f"已插入 {len(models)} 个模型配置")
    print("\n初始化完成！")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
