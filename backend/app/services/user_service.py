from typing import Optional, Dict, Any
from datetime import datetime
from pymongo import collection
from app.core.database import get_db
import bcrypt
import re


class UserService:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["users"]
        # 确保索引存在
        self.collection.create_index("username", unique=True)

    async def create(self, username: str, password: str, nickname: str = None) -> Dict[str, Any]:
        """创建用户（注册）"""
        # 校验用户名格式：4-20位字母数字
        if not re.match(r'^[a-zA-Z0-9]{4,20}$', username):
            raise ValueError("用户名必须是4-20位字母或数字")
        
        # 校验密码格式：8-32位含大小写+数字
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,32}$', password):
            raise ValueError("密码必须是8-32位，包含大小写字母和数字")
        
        # 检查用户名是否已存在
        existing = await self.collection.find_one({"username": username})
        if existing:
            raise ValueError("用户名已存在")
        
        # BCrypt加密密码（BCrypt限制密码长度最多72字节）
        password_bytes = password[:72].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        now = datetime.utcnow()
        user = {
            "username": username,
            "password": hashed_password,
            "nickname": nickname or username,
            "status": 1,  # 1=正常, 0=禁用
            "createAt": now,
            "lastLogin": now
        }
        
        result = await self.collection.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user

    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名查询用户"""
        user = await self.collection.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID查询用户"""
        from bson.objectid import ObjectId
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception:
            return None

    async def update_last_login(self, user_id: str):
        """更新最后登录时间"""
        from bson.objectid import ObjectId
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"lastLogin": datetime.utcnow()}}
        )

    async def update_password(self, user_id: str, new_password: str):
        """更新密码"""
        # 校验新密码格式
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,32}$', new_password):
            raise ValueError("密码必须是8-32位，包含大小写字母和数字")
        
        password_bytes = new_password[:72].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        from bson.objectid import ObjectId
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed_password}}
        )

    async def update_status(self, user_id: str, status: int):
        """更新账号状态"""
        from bson.objectid import ObjectId
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": status}}
        )

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        password_bytes = plain_password[:72].encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_user_service() -> UserService:
    return UserService()