from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from app.core.database import get_db
from app.core.config import settings
from app.services.user_service import get_user_service
from bson.objectid import ObjectId


class AuthService:
    def __init__(self):
        self.db = get_db()
        self.token_blacklist = self.db["token_blacklist"]
        # 确保索引存在
        self.token_blacklist.create_index("token", unique=True)
        self.token_blacklist.create_index("expireAt", expireAfterSeconds=0)

    async def create_token(self, user_id: str, username: str) -> str:
        """生成JWT令牌"""
        expire = datetime.utcnow() + timedelta(minutes=30)
        payload = {
            "uid": user_id,
            "username": username,
            "iat": datetime.utcnow(),
            "exp": expire
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            # 先检查黑名单
            exists = await self.token_blacklist.find_one({"token": token})
            if exists:
                return None
            
            # 解析JWT
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("uid")
            username = payload.get("username")
            
            if not user_id or not username:
                return None
            
            # 检查用户状态
            user_service = get_user_service()
            user = await user_service.get_by_id(user_id)
            if not user or user.get("status") != 1:
                return None
            
            return {"user_id": user_id, "username": username, "user": user}
            
        except ExpiredSignatureError:
            return None
        except JWTError:
            return None

    async def blacklist_token(self, token: str, expire_at: datetime):
        """将令牌加入黑名单"""
        try:
            await self.token_blacklist.insert_one({
                "token": token,
                "expireAt": expire_at
            })
        except Exception:
            # 如果已存在则忽略
            pass

    async def logout(self, token: str):
        """登出，将令牌加入黑名单"""
        try:
            # 解析过期时间
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            expire_timestamp = payload.get("exp")
            if expire_timestamp:
                expire_at = datetime.fromtimestamp(expire_timestamp)
                await self.blacklist_token(token, expire_at)
        except Exception:
            pass


def get_auth_service() -> AuthService:
    return AuthService()