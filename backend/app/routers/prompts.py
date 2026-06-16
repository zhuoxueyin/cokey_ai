from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
from app.services.prompt_service import get_prompt_service

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# 延迟获取服务实例，避免模块导入时 MongoDB 未初始化
def get_service():
    return get_prompt_service()

@router.post("/", summary="创建提示词")
async def create_prompt(data: Dict[str, Any]):
    required_fields = ["name", "content"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise HTTPException(status_code=400, detail=f"缺少必填字段: {', '.join(missing)}")
    
    prompt = await get_service().create(data)
    return {"success": True, "data": prompt}

@router.get("/", summary="获取提示词列表")
async def list_prompts(
    category: Optional[str] = Query(None, description="分类: text, image, video"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    result = await get_service().list(category=category, page=page, page_size=page_size)
    return {"success": True, "data": result}

@router.get("/{prompt_id}", summary="获取提示词详情")
async def get_prompt(prompt_id: str):
    prompt = await get_service().get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "data": prompt}

@router.put("/{prompt_id}", summary="更新提示词")
async def update_prompt(prompt_id: str, data: Dict[str, Any]):
    prompt = await get_service().update(prompt_id, data)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "data": prompt}

@router.delete("/{prompt_id}", summary="删除提示词")
async def delete_prompt(prompt_id: str):
    success = await get_service().delete(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "message": "删除成功"}

@router.post("/{prompt_id}/publish", summary="发布当前版本")
async def publish_prompt(prompt_id: str):
    prompt = await get_service().publish(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "data": prompt, "message": f"已发布版本 v{prompt['version']}"}

@router.post("/{prompt_id}/rollback", summary="回滚到指定版本")
async def rollback_prompt(prompt_id: str, data: Dict[str, int]):
    version = data.get("version")
    if version is None:
        raise HTTPException(status_code=400, detail="缺少版本号")
    
    prompt = await get_service().rollback(prompt_id, version)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词或版本不存在")
    return {"success": True, "data": prompt, "message": f"已回滚到版本 v{version}"}

@router.get("/{prompt_id}/versions", summary="获取版本列表")
async def get_prompt_versions(prompt_id: str):
    versions = await get_service().get_versions(prompt_id)
    return {"success": True, "data": versions}

@router.get("/published/list", summary="获取所有已发布的提示词（用于任务选择）")
async def get_published_prompts():
    prompts = await get_service().get_published_prompts()
    return {"success": True, "data": prompts}

@router.get("/{prompt_id}/published/content", summary="获取已发布版本的内容（任务执行时使用）")
async def get_published_content(prompt_id: str):
    content = await get_service().get_published_content(prompt_id)
    if content is None:
        raise HTTPException(status_code=404, detail="提示词未发布或不存在")
    return {"success": True, "data": {"prompt_id": prompt_id, "content": content}}