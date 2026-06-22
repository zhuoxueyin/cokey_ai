from fastapi import APIRouter, Query, Body
from typing import Optional

from app.core.logging_config import get_logger
from app.core.response import success, paginated, error
from app.schemas.drama import (
    StylePresetCreate,
    StylePresetUpdate,
    KnowledgeEntryCreate,
    KnowledgeEntryUpdate,
    KnowledgeImportRequest,
    FeishuPreviewRequest,
    KnowledgeCategoryCreate,
    KnowledgeCategoryUpdate,
    SkillCreate,
    SkillUpdate,
    SkillImportRepoRequest,
    SkillReimportRepoRequest,
    SkillRollbackRequest,
    KVSetRequest,
)
from app.services.drama_style_service import get_drama_style_service
from app.services.drama_knowledge_service import get_drama_knowledge_service
from app.services.drama_skill_service import get_drama_skill_service
from app.services.kv_service import get_kv_service

logger = get_logger()

router = APIRouter(prefix="/admin/drama", tags=["管理-短剧Agent"])


# ── 风格库 ──

@router.get("/styles")
async def list_styles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    render_class: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    items, total = await get_drama_style_service().list(
        page=page,
        page_size=page_size,
        render_class=render_class,
        status=status,
        keyword=keyword,
    )
    return paginated(items, total, page, page_size)


@router.post("/styles")
async def create_style(data: StylePresetCreate):
    try:
        doc = await get_drama_style_service().create(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.get("/styles/{style_id}")
async def get_style(style_id: str):
    doc = await get_drama_style_service().get_by_style_id(style_id)
    if not doc:
        return error("not_found", "风格不存在")
    return success(doc)


@router.put("/styles/{style_id}")
async def update_style(style_id: str, data: StylePresetUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    doc = await get_drama_style_service().update(style_id, update_dict)
    if not doc:
        return error("not_found", "风格不存在")
    return success(doc)


@router.post("/styles/{style_id}/publish")
async def publish_style(style_id: str):
    try:
        doc = await get_drama_style_service().publish(style_id)
    except ValueError as e:
        return error("validation_error", str(e))
    if not doc:
        return error("not_found", "风格不存在")
    return success(doc)


@router.delete("/styles/{style_id}")
async def delete_style(style_id: str):
    try:
        ok = await get_drama_style_service().soft_delete(style_id, allow_seed=True)
    except ValueError as e:
        return error("validation_error", str(e))
    if not ok:
        return error("not_found", "风格不存在")
    return success({"deleted": True})


# ── 知识库 ──

@router.get("/knowledge/stages")
async def list_knowledge_stages():
    from app.core.drama.knowledge_stage import CREATION_STAGES

    return success(CREATION_STAGES)


@router.get("/knowledge/categories")
async def list_knowledge_categories():
    return success(await get_drama_knowledge_service().list_categories())


@router.get("/knowledge/tags")
async def list_knowledge_tags(limit: int = Query(200, ge=1, le=500)):
    return success(await get_drama_knowledge_service().list_tags(limit=limit))


@router.post("/knowledge/categories")
async def create_knowledge_category(data: KnowledgeCategoryCreate):
    try:
        doc = await get_drama_knowledge_service().create_category(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.put("/knowledge/categories/{code}")
async def update_knowledge_category(code: str, data: KnowledgeCategoryUpdate):
    try:
        doc = await get_drama_knowledge_service().update_category(
            code, data.model_dump(exclude_unset=True)
        )
        if not doc:
            return error("not_found", "分类不存在")
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.delete("/knowledge/categories/{code}")
async def delete_knowledge_category(code: str):
    try:
        ok = await get_drama_knowledge_service().delete_category(code)
        if not ok:
            return error("not_found", "分类不存在")
        return success({"deleted": True})
    except ValueError as e:
        return error("validation_error", str(e))


@router.get("/knowledge")
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    items, total = await get_drama_knowledge_service().list(
        page=page,
        page_size=page_size,
        category=category,
        domain=domain,
        status=status,
        keyword=keyword,
    )
    return paginated(items, total, page, page_size)


@router.post("/knowledge")
async def create_knowledge(data: KnowledgeEntryCreate):
    try:
        doc = await get_drama_knowledge_service().create(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.post("/knowledge/preview-feishu")
async def preview_feishu_url(data: FeishuPreviewRequest):
    try:
        result = await get_drama_knowledge_service().preview_feishu(data.url)
        return success(result)
    except ValueError as e:
        return error("validation_error", str(e))


@router.post("/knowledge/import")
async def import_knowledge(data: KnowledgeImportRequest):
    try:
        doc = await get_drama_knowledge_service().import_entry(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.get("/knowledge/entry/{entry_id}")
async def get_knowledge(entry_id: str):
    doc = await get_drama_knowledge_service().get_by_entry_id(entry_id)
    if not doc:
        return error("not_found", "知识条目不存在")
    return success(doc)


@router.put("/knowledge/entry/{entry_id}")
async def update_knowledge(entry_id: str, data: KnowledgeEntryUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    doc = await get_drama_knowledge_service().update(entry_id, update_dict)
    if not doc:
        return error("not_found", "知识条目不存在")
    return success(doc)


@router.post("/knowledge/entry/{entry_id}/publish")
async def publish_knowledge(entry_id: str):
    doc = await get_drama_knowledge_service().publish(entry_id)
    if not doc:
        return error("not_found", "知识条目不存在")
    return success(doc)


@router.delete("/knowledge/entry/{entry_id}")
async def delete_knowledge(entry_id: str):
    ok = await get_drama_knowledge_service().soft_delete(entry_id)
    if not ok:
        return error("not_found", "知识条目不存在")
    return success({"deleted": True})


@router.get("/knowledge/search")
async def search_knowledge(
    q: str = Query(""),
    category: Optional[str] = Query(None),
    stage: Optional[str] = Query(None, description="创作阶段，按分类 applicable_stages 过滤"),
    top_k: int = Query(6, ge=1, le=20),
):
    items = await get_drama_knowledge_service().search(
        query=q, category=category, stage=stage, top_k=top_k
    )
    return success(items)


@router.post("/knowledge/reindex-vectors")
async def reindex_knowledge_vectors():
    try:
        count = await get_drama_knowledge_service().reindex_vectors(status="published")
        return success({"reindexed": count})
    except Exception as e:
        return error("internal_error", str(e))


# ── Skill ──

@router.get("/skills")
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    stage: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
):
    items, total = await get_drama_skill_service().list(
        page=page, page_size=page_size, stage=stage, status=status, source=source
    )
    return paginated(items, total, page, page_size)


@router.post("/skills")
async def create_skill(data: SkillCreate):
    try:
        doc = await get_drama_skill_service().create(data.model_dump())
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.post("/skills/seed-builtin")
async def seed_builtin_skills():
    """补种缺失的内置 Skill（如 skill.character），不影响已发布的同名 Skill。"""
    inserted = await get_drama_skill_service().ensure_builtin_skills_seeded()
    return success({"inserted": inserted})


@router.get("/skills/repo-catalog")
async def list_repo_skill_catalog():
    items = await get_drama_skill_service().list_repo_catalog()
    return success(items)


@router.get("/skills/repo-folders")
async def list_repo_skill_folders():
    folders = await get_drama_skill_service().list_repo_folders()
    return success(folders)


@router.get("/skills/repo-preview")
async def preview_repo_skill(folder: str = Query(..., description="skills/ 子目录名")):
    try:
        data = await get_drama_skill_service().preview_repo_skill(folder)
        return success(data)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("preview_repo_skill failed folder=%s", folder)
        return error("internal_error", f"预览失败: {e}")


@router.get("/skills/content-template")
async def get_skill_content_template(
    skill_name: str = Query("技能名称"),
    skill_id: str = Query("skill.example"),
    author: str = Query("xxx"),
    tag: str = Query("标签"),
):
    text = await get_drama_skill_service().get_content_template(
        skill_name=skill_name,
        skill_id=skill_id,
        author=author,
        tag=tag,
    )
    return success({"markdown": text})


@router.post("/skills/import-repo")
async def import_skill_from_repo(data: SkillImportRepoRequest):
    try:
        doc = await get_drama_skill_service().import_from_repo(
            data.folder,
            stage=data.stage,
            publish=data.publish,
            target_skill_id=data.target_skill_id,
        )
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("import_skill_from_repo failed folder=%s", data.folder)
        return error("internal_error", f"导入失败: {e}")


@router.get("/skills/{skill_doc_id}")
async def get_skill(skill_doc_id: str):
    doc = await get_drama_skill_service().get_by_id(skill_doc_id)
    if not doc:
        return error("not_found", "Skill 不存在")
    return success(doc)


@router.put("/skills/{skill_doc_id}")
async def update_skill(skill_doc_id: str, data: SkillUpdate):
    try:
        doc = await get_drama_skill_service().update(skill_doc_id, data.model_dump(exclude_none=True))
    except ValueError as e:
        return error("validation_error", str(e))
    if not doc:
        return error("not_found", "Skill 不存在")
    return success(doc)


@router.post("/skills/{skill_doc_id}/publish")
async def publish_skill(skill_doc_id: str):
    doc = await get_drama_skill_service().publish(skill_doc_id)
    if not doc:
        return error("not_found", "Skill 不存在")
    return success(doc)


@router.get("/skills/{skill_doc_id}/publish-compare")
async def compare_skill_before_publish(skill_doc_id: str):
    try:
        data = await get_drama_skill_service().get_publish_compare(skill_doc_id)
        return success(data)
    except ValueError as e:
        return error("validation_error", str(e))


@router.get("/skills/by-code/{skill_code}/versions")
async def list_skill_versions(skill_code: str):
    items = await get_drama_skill_service().list_versions(skill_code)
    return success(items)


@router.post("/skills/by-code/{skill_code}/rollback")
async def rollback_skill(skill_code: str, data: SkillRollbackRequest):
    try:
        doc = await get_drama_skill_service().rollback(skill_code, data.version_num)
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))


@router.post("/skills/{skill_doc_id}/reimport-repo")
async def reimport_skill_from_repo(skill_doc_id: str, data: SkillReimportRepoRequest = Body(...)):
    try:
        doc = await get_drama_skill_service().reimport_from_repo(
            skill_doc_id,
            folder=data.folder,
            publish=data.publish,
        )
        return success(doc)
    except ValueError as e:
        return error("validation_error", str(e))
    except Exception as e:
        logger.exception("reimport_skill_from_repo failed id=%s", skill_doc_id)
        return error("internal_error", f"重新导入失败: {e}")


@router.delete("/skills/{skill_doc_id}")
async def delete_skill(skill_doc_id: str):
    ok = await get_drama_skill_service().soft_delete(skill_doc_id)
    if not ok:
        return error("not_found", "Skill 不存在")
    return success({"deleted": True})


# ── MongoDB KV（内部/调试） ──

@router.get("/kv/{namespace}/{key}")
async def kv_get(namespace: str, key: str):
    val = await get_kv_service().get(namespace, key)
    if val is None:
        return error("not_found", "键不存在")
    return success({"namespace": namespace, "key": key, "value": val})


@router.put("/kv")
async def kv_set(data: KVSetRequest):
    result = await get_kv_service().set(
        data.namespace, data.key, data.value, ttl_seconds=data.ttl_seconds
    )
    return success(result)


@router.delete("/kv/{namespace}/{key}")
async def kv_delete(namespace: str, key: str):
    ok = await get_kv_service().delete(namespace, key)
    if not ok:
        return error("not_found", "键不存在")
    return success({"deleted": True})
