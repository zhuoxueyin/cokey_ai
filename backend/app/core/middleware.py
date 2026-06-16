from fastapi import HTTPException, Header, Depends
from app.services.auth_service import get_auth_service
from typing import Optional


async def AuthMiddleware(authorization: Optional[str] = Header(None)):
    """
    全局鉴权中间件
    从请求头提取Authorization，校验JWT令牌
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    # 提取Token（Bearer xxx格式）
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="令牌格式错误")
    
    token = parts[1]
    
    auth_service = get_auth_service()
    result = await auth_service.verify_token(token)
    
    if not result:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    
    # 返回认证信息，包含原始token用于登出
    return {
        "user_id": result["user_id"],
        "username": result["username"],
        "user": result["user"],
        "token": token  # 保存原始token用于后续登出操作
    }