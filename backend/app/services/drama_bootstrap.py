"""短剧 Agent 启动引导：索引 + 可选内置 Skill。"""
from __future__ import annotations

from app.core.logging_config import get_logger
from app.services.drama_knowledge_service import get_drama_knowledge_service
from app.services.drama_skill_service import get_drama_skill_service
from app.services.drama_style_service import get_drama_style_service
from app.services.drama_project_service import get_drama_project_service
from app.services.drama_agent_thread_service import get_drama_agent_thread_service
from app.services.kv_service import get_kv_service

logger = get_logger()


async def bootstrap_drama_module(seed_skills: bool = True) -> dict:
    """应用启动时创建索引；风格库以 MongoDB（风格广场）为唯一数据源。"""
    await get_kv_service().ensure_indexes()
    await get_drama_project_service().ensure_indexes()
    await get_drama_style_service().ensure_indexes()
    await get_drama_knowledge_service().ensure_indexes()
    await get_drama_skill_service().ensure_indexes()

    cat_count = await get_drama_knowledge_service().ensure_categories_seeded()
    try:
        from app.services.knowledge_vector_service import get_knowledge_vector_service

        vec_svc = get_knowledge_vector_service()
        vec_count = await vec_svc.collection.count_documents({})
        if vec_count == 0:
            reindexed = await get_drama_knowledge_service().reindex_vectors(status="published")
            logger.info(f"知识库向量首次建索引: {reindexed} 条")
    except Exception as e:
        logger.warning(f"知识库向量索引初始化跳过: {e}")
    skill_count = 0
    if seed_skills:
        skill_count = await get_drama_skill_service().ensure_builtin_skills_seeded()

    try:
        await get_drama_agent_thread_service().ensure_indexes()
    except Exception as e:
        logger.warning(f"短剧 Agent 线程索引创建失败（不影响 Skill 种子）: {e}")

    protocol_count = await get_drama_style_service().ensure_model_protocol_complete()

    logger.info(
        f"短剧模块 bootstrap: categories={cat_count} skills={skill_count} "
        f"model_protocol={protocol_count}"
    )
    return {
        "knowledge_categories": cat_count,
        "skills_seeded": skill_count,
        "model_protocol_updated": protocol_count,
    }
