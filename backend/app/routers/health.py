from fastapi import APIRouter
from app.core.response import success

router = APIRouter(prefix="", tags=["健康检查"])


@router.get("/health")
async def health_check():
    return success({"status": "ok", "service": "AIGC Platform API"})


@router.get("/")
async def root():
    return success({
        "name": "AIGC创作平台",
        "version": "1.0.0",
        "api_prefix": "/api"
    })
