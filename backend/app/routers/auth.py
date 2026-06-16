from fastapi import APIRouter, Depends, HTTPException, Body, Header
from app.core.response import success, error
from app.services.user_service import get_user_service
from app.services.auth_service import get_auth_service
from app.core.middleware import AuthMiddleware
from typing import Optional

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(body: dict = Body(...)):
    """用户注册"""
    username = body.get("username")
    password = body.get("password")
    nickname = body.get("nickname")
    
    if not username or not password:
        return error("validation_error", "用户名和密码不能为空")
    
    try:
        user_service = get_user_service()
        user = await user_service.create(username, password, nickname)
        return success({
            "userId": user["_id"],
            "username": user["username"],
            "nickname": user["nickname"]
        }, message="注册成功")
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        return error("internal_error", str(e))


@router.post("/login")
async def login(body: dict = Body(...)):
    """用户登录"""
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        return error("validation_error", "用户名和密码不能为空")
    
    try:
        user_service = get_user_service()
        auth_service = get_auth_service()
        
        # 查询用户
        user = await user_service.get_by_username(username)
        if not user:
            return error("auth_error", "账号或密码错误")
        
        # 检查状态
        if user.get("status") != 1:
            return error("forbidden", "账号已被禁用")
        
        # 验证密码
        if not await user_service.verify_password(password, user["password"]):
            return error("auth_error", "账号或密码错误")
        
        # 更新登录时间
        await user_service.update_last_login(user["_id"])
        
        # 生成令牌
        token = await auth_service.create_token(user["_id"], user["username"])
        
        return success({
            "token": token,
            "user": {
                "userId": user["_id"],
                "username": user["username"],
                "nickname": user["nickname"],
                "status": user["status"]
            }
        }, message="登录成功")
    except Exception as e:
        return error("internal_error", str(e))


@router.post("/logout")
async def logout(auth_info: dict = Depends(AuthMiddleware)):
    """用户登出"""
    try:
        auth_service = get_auth_service()
        # 获取原始Token（不带Bearer前缀）
        await auth_service.logout(auth_info["token"])
        return success({}, message="登出成功")
    except Exception as e:
        return error("internal_error", str(e))