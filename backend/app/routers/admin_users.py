from fastapi import APIRouter, Depends, Path
from app.core.response import success, error
from app.services.user_service import get_user_service
from app.core.middleware import AuthMiddleware

router = APIRouter(prefix="/admin/user", tags=["管理-用户管理"])


@router.put("/status/{user_id}")
async def update_user_status(
    user_id: str = Path(...),
    status: int = 1,
    auth_info: dict = Depends(AuthMiddleware)
):
    """更新用户状态（启用/禁用）"""
    # 简单的管理员权限校验（实际项目中应使用角色系统）
    # 这里假设第一个注册的用户为管理员
    if auth_info["user_id"] != "admin":
        return error("forbidden", "无管理员权限")
    
    try:
        user_service = get_user_service()
        await user_service.update_status(user_id, status)
        return success({}, message="状态更新成功")
    except Exception as e:
        return error("internal_error", str(e))