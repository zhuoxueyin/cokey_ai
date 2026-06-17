from fastapi import APIRouter, Depends, Body
from app.core.response import success, error
from app.services.user_service import get_user_service
from app.services.auth_service import get_auth_service
from app.core.middleware import AuthMiddleware

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/profile")
async def get_profile(auth_info: dict = Depends(AuthMiddleware)):
    """获取当前用户信息"""
    try:
        user_service = get_user_service()
        user = await user_service.get_by_id(auth_info["user_id"])
        if not user:
            return error("not_found", "用户不存在")
        
        # 移除敏感字段
        user.pop("password", None)
        return success({
            "userId": user["_id"],
            "username": user["username"],
            "nickname": user.get("nickname", user["username"]),
            "avatar_url": user.get("avatar_url", ""),
            "status": user.get("status", 1),
        })
    except Exception as e:
        return error("internal_error", str(e))


@router.put("/profile")
async def update_profile(body: dict = Body(...), auth_info: dict = Depends(AuthMiddleware)):
    """更新当前用户资料"""
    nickname = body.get("nickname")
    avatar_url = body.get("avatar_url")

    if nickname is None and avatar_url is None:
        return error("validation_error", "请提供要更新的字段")

    try:
        user_service = get_user_service()
        user = await user_service.update_profile(
            auth_info["user_id"],
            nickname=nickname,
            avatar_url=avatar_url,
        )
        return success({
            "userId": user["_id"],
            "username": user["username"],
            "nickname": user.get("nickname", user["username"]),
            "avatar_url": user.get("avatar_url", ""),
            "status": user.get("status", 1),
        }, message="资料更新成功")
    except ValueError as e:
        return error("validation_error", str(e))


@router.put("/pwd")
async def update_password(body: dict = Body(...), auth_info: dict = Depends(AuthMiddleware)):
    """修改密码"""
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    
    if not old_password or not new_password:
        return error("validation_error", "旧密码和新密码不能为空")
    
    try:
        user_service = get_user_service()
        auth_service = get_auth_service()
        
        # 获取用户信息
        user = await user_service.get_by_id(auth_info["user_id"])
        if not user:
            return error("not_found", "用户不存在")
        
        # 验证旧密码
        if not await user_service.verify_password(old_password, user["password"]):
            return error("validation_error", "旧密码不正确")
        
        # 更新密码
        await user_service.update_password(auth_info["user_id"], new_password)
        
        # 将当前Token加入黑名单（强制下线）
        await auth_service.logout(auth_info["token"])
        
        return success({}, message="密码修改成功，请重新登录")
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        return error("internal_error", str(e))