from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_collection
from app.core.logging_config import get_logger

logger = get_logger()

class PromptService:
    def __init__(self):
        self.collection = get_collection("prompts")
        self.versions_collection = get_collection("prompt_versions")
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建提示词"""
        prompt = {
            "name": data["name"],
            "content": data["content"],
            "category": data.get("category", "text"),  # text, image, video
            "tags": data.get("tags", []),
            "description": data.get("description", ""),
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "version": 1,
            "published_version": None,
            "status": "draft",  # draft: 未发布, published: 已发布
        }
        result = await self.collection.insert_one(prompt)
        prompt["_id"] = str(result.inserted_id)
        
        # 创建初始版本记录
        await self._create_version(str(result.inserted_id), prompt["version"], data["content"])
        
        logger.info(f"创建提示词成功: {prompt['name']}")
        return prompt
    
    async def update(self, prompt_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新提示词（自动创建新版本）"""
        prompt = await self.collection.find_one({"_id": ObjectId(prompt_id)})
        if not prompt:
            return None
        
        # 检查内容是否变化
        content_changed = data.get("content") is not None and data["content"] != prompt["content"]
        
        update_data: Dict[str, Any] = {
            "updated_at": datetime.now(),
        }
        
        if "name" in data:
            update_data["name"] = data["name"]
        if "category" in data:
            update_data["category"] = data["category"]
        if "tags" in data:
            update_data["tags"] = data["tags"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "content" in data:
            update_data["content"] = data["content"]
            if content_changed:
                update_data["version"] = prompt["version"] + 1
                # 内容变化后状态变为未发布
                update_data["status"] = "draft"
        
        result = await self.collection.update_one(
            {"_id": ObjectId(prompt_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0 and content_changed:
            # 创建新版本记录
            await self._create_version(prompt_id, update_data["version"], data["content"])
        
        logger.info(f"更新提示词成功: {prompt_id}")
        return await self.get_by_id(prompt_id)
    
    async def delete(self, prompt_id: str) -> bool:
        """删除提示词（软删除）"""
        result = await self.collection.update_one(
            {"_id": ObjectId(prompt_id)},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    
    async def get_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取提示词"""
        prompt = await self.collection.find_one({"_id": ObjectId(prompt_id), "is_active": True})
        if prompt:
            prompt["_id"] = str(prompt["_id"])
        return prompt
    
    async def list(self, category: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """分页获取提示词列表"""
        query = {"is_active": True}
        if category:
            query["category"] = category
        
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("updated_at", -1).skip((page - 1) * page_size).limit(page_size)
        
        prompts = []
        async for prompt in cursor:
            prompt["_id"] = str(prompt["_id"])
            prompts.append(prompt)
        
        return {
            "data": prompts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def publish(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """发布当前版本"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        await self.collection.update_one(
            {"_id": ObjectId(prompt_id)},
            {"$set": {"published_version": prompt["version"], "status": "published", "updated_at": datetime.now()}}
        )
        
        logger.info(f"发布提示词版本: {prompt_id} v{prompt['version']}")
        return await self.get_by_id(prompt_id)
    
    async def get_published_content(self, prompt_id: str) -> Optional[str]:
        """获取已发布版本的内容（任务执行时使用）"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        # 如果没有发布版本，返回空
        if prompt.get("published_version") is None:
            return None
        
        # 获取发布版本的内容
        version = await self.versions_collection.find_one({
            "prompt_id": prompt_id,
            "version": prompt["published_version"]
        })
        
        return version["content"] if version else None
    
    async def get_published_prompts(self) -> List[Dict[str, Any]]:
        """获取所有已发布的提示词（用于任务选择）"""
        cursor = self.collection.find({
            "is_active": True,
            "status": "published",
            "published_version": {"$ne": None}
        }).sort("updated_at", -1)
        
        prompts = []
        async for prompt in cursor:
            prompt["_id"] = str(prompt["_id"])
            prompts.append(prompt)
        
        return prompts
    
    async def rollback(self, prompt_id: str, target_version: int) -> Optional[Dict[str, Any]]:
        """回滚到指定版本"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        # 获取目标版本的内容
        version = await self.versions_collection.find_one({
            "prompt_id": prompt_id,
            "version": target_version
        })
        
        if not version:
            return None
        
        # 更新提示词内容到目标版本
        new_version = prompt["version"] + 1
        await self.collection.update_one(
            {"_id": ObjectId(prompt_id)},
            {
                "$set": {
                    "content": version["content"],
                    "version": new_version,
                    "updated_at": datetime.now()
                }
            }
        )
        
        # 创建新版本记录（记录回滚操作）
        await self._create_version(prompt_id, new_version, version["content"], f"rollback_from_v{prompt['version']}")
        
        logger.info(f"回滚提示词: {prompt_id} from v{prompt['version']} to v{target_version}")
        return await self.get_by_id(prompt_id)
    
    async def get_versions(self, prompt_id: str) -> List[Dict[str, Any]]:
        """获取提示词的所有版本"""
        cursor = self.versions_collection.find({"prompt_id": prompt_id}).sort("version", -1)
        versions = []
        async for version in cursor:
            version["_id"] = str(version["_id"])
            versions.append(version)
        return versions
    
    async def _create_version(self, prompt_id: str, version: int, content: str, comment: str = "") -> None:
        """创建版本记录"""
        await self.versions_collection.insert_one({
            "prompt_id": prompt_id,
            "version": version,
            "content": content,
            "comment": comment,
            "created_at": datetime.now()
        })

_prompt_service = None

def get_prompt_service() -> PromptService:
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service