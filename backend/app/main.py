from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.core.database import init_mongodb
from app.core.logging_config import get_logger
from app.core.redis_client import init_redis

from app.routers import health, assets, prompts
from app.routers import admin_channels, admin_models, admin_tasks, admin_trace_logs, admin_users, admin_protocol_profiles
from app.routers import user_models, user_tasks, user_sessions, user_upload, auth, user, user_canvas, user_download

logger = get_logger()

app = FastAPI(
    title="AIGC创作平台 API",
    description="通用AIGC创作平台后端服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api"

app.include_router(health.router, prefix=api_prefix)
app.include_router(admin_channels.router, prefix=api_prefix)
app.include_router(admin_protocol_profiles.router, prefix=api_prefix)
app.include_router(admin_models.router, prefix=api_prefix)
app.include_router(admin_tasks.router, prefix=api_prefix)
app.include_router(admin_trace_logs.router, prefix=api_prefix)
app.include_router(user_models.router, prefix=api_prefix)
app.include_router(user_tasks.router, prefix=api_prefix)
app.include_router(user_sessions.router, prefix=api_prefix)
app.include_router(user_upload.router, prefix=api_prefix)
app.include_router(assets.router, prefix=api_prefix)
app.include_router(prompts.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(user.router, prefix=api_prefix)
app.include_router(user_canvas.router, prefix=api_prefix)
app.include_router(user_download.router, prefix=api_prefix)
app.include_router(admin_users.router, prefix=api_prefix)


@app.on_event("startup")
async def startup_event():
    logger.info("应用启动中...")
    try:
        await init_mongodb()
        logger.info("MongoDB 初始化完成")
        from app.services.protocol_profile_service import get_protocol_profile_service
        await get_protocol_profile_service().ensure_builtin_seeded()
    except Exception as e:
        logger.error(f"MongoDB 初始化失败: {e}")

    try:
        await init_redis()
        logger.info("Redis 初始化完成")
    except Exception as e:
        logger.warning(f"Redis 初始化失败（可选依赖）: {e}")

    logger.info(f"应用启动完成 - {settings.app_name} v1.0.0")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用关闭中...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        timeout_keep_alive=120,  # 保持连接超时（秒）
    )
