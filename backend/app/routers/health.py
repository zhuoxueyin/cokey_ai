from fastapi import APIRouter
from app.core.response import success
from app.core.config import settings
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="", tags=["健康检查"])


@router.get("/health")
async def health_check():
    storage = get_storage_service()
    sample_path = "assets/images/20260615/sample.png"
    all_urls = storage.get_all_cdn_urls(sample_path)
    weelink_key = (settings.weelink_api_key or "").strip()
    key_display = weelink_key[:10] + "..." if len(weelink_key) > 10 else (weelink_key or "(未设置)")

    return success({
        "status": "ok",
        "service": "AIGC Platform API",
        "storage": {
            "enabled": storage.enabled,
            "repo": storage.repo,
            "branch": storage.branch,
            "upload_path": f"{storage.repo}/assets/",
            "primary_cdn": all_urls[0],
            "fallback_cdns": all_urls[1:],
            "setup_guide": (
                "未启用时请：1) 编辑 backend/.env 填入 GITHUB_TOKEN "
                "2) 重启后端服务（launcher.py stop 然后 start）"
            ) if not storage.enabled else "存储服务已就绪"
        },
        "channel": {
            "weelink_api_key_env": key_display,
            "weelink_key_set": bool(weelink_key) and not weelink_key.startswith("your-")
        }
    })


@router.get("/")
async def root():
    return success({
        "name": "AIGC创作平台",
        "version": "1.0.0",
        "api_prefix": "/api"
    })
