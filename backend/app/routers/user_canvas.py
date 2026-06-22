from fastapi import APIRouter, Body, UploadFile, File, Form
from app.core.response import success, error, paginated
from app.schemas.canvas import (
    CanvasProjectCreate,
    CanvasProjectUpdate,
    CanvasNodeCreate,
    CanvasNodeUpdate,
    CanvasEdgeCreate,
    CanvasBatchSync,
    CanvasNodeRun,
    CanvasNodeDuplicate,
)
from app.services.canvas_service import get_canvas_service
from app.services.storage_service import get_storage_service
from app.services.asset_service import get_asset_service
from app.core.logging_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/canvas", tags=["用户-无限画布"])


@router.post("/projects")
async def create_project(data: CanvasProjectCreate):
    project = await get_canvas_service().create_project(data.title, data.user_id)
    return success(project)


@router.get("/projects/workspace-default")
async def get_workspace_default_project(user_id: str = None):
    """创作工作台固定画布：每用户一个 project_id，不变。"""
    project = await get_canvas_service().get_or_create_workspace_default(user_id)
    return success(project)


@router.get("/projects")
async def list_projects(user_id: str = None, page: int = 1, page_size: int = 50):
    items, total = await get_canvas_service().list_projects(user_id, page, page_size)
    return paginated(items, total, page, page_size)


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await get_canvas_service().get_project(project_id)
    if not project:
        return error("not_found", "项目不存在")
    return success(project)


@router.put("/projects/{project_id}")
async def update_project(project_id: str, data: CanvasProjectUpdate):
    updates = data.model_dump(exclude_none=True)
    project = await get_canvas_service().update_project(project_id, updates)
    if not project:
        return error("not_found", "项目不存在")
    return success(project)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    ok = await get_canvas_service().delete_project(project_id)
    if not ok:
        return error("not_found", "项目不存在")
    return success({"deleted": True})


@router.post("/projects/{project_id}/nodes")
async def create_node(project_id: str, data: CanvasNodeCreate):
    node = await get_canvas_service().create_node(project_id, data.model_dump())
    if not node:
        return error("not_found", "项目不存在")
    return success(node)


@router.put("/projects/{project_id}/nodes/{node_id}")
async def update_node(project_id: str, node_id: str, data: CanvasNodeUpdate):
    updates = data.model_dump(exclude_unset=True)
    node = await get_canvas_service().update_node(project_id, node_id, updates)
    if not node:
        return error("not_found", "节点不存在")
    return success(node)


@router.delete("/projects/{project_id}/nodes/{node_id}")
async def delete_node(project_id: str, node_id: str):
    ok = await get_canvas_service().delete_node(project_id, node_id)
    if not ok:
        return error("not_found", "节点不存在")
    return success({"deleted": True})


@router.post("/projects/{project_id}/nodes/{node_id}/duplicate")
async def duplicate_node(
    project_id: str,
    node_id: str,
    data: CanvasNodeDuplicate = Body(default=CanvasNodeDuplicate()),
):
    position = data.position.model_dump() if data.position else None
    node = await get_canvas_service().duplicate_node(project_id, node_id, position)
    if not node:
        return error("not_found", "节点不存在")
    return success(node)


@router.post("/projects/{project_id}/edges")
async def create_edge(project_id: str, data: CanvasEdgeCreate):
    edge = await get_canvas_service().create_edge(project_id, data.model_dump())
    if not edge:
        return error("validation_error", "无法创建连接")
    return success(edge)


@router.delete("/projects/{project_id}/edges/{edge_id}")
async def delete_edge(project_id: str, edge_id: str):
    ok = await get_canvas_service().delete_edge(project_id, edge_id)
    if not ok:
        return error("not_found", "连接不存在")
    return success({"deleted": True})


@router.put("/projects/{project_id}/sync")
async def batch_sync(project_id: str, data: CanvasBatchSync):
    project = await get_canvas_service().batch_sync(project_id, data.model_dump(exclude_none=True))
    if not project:
        return error("not_found", "项目不存在")
    return success(project)


@router.get("/projects/{project_id}/runs")
async def list_project_runs(project_id: str, page: int = 1, page_size: int = 30):
    svc = get_canvas_service()
    if not await svc.projects.find_one({"project_id": project_id}, {"_id": 1}):
        return error("not_found", "项目不存在")
    items, total = await svc.list_project_runs(project_id, page, page_size)
    return paginated(items, total, page, page_size)


@router.get("/projects/{project_id}/runs/{task_id}")
async def get_project_run(project_id: str, task_id: str):
    run = await get_canvas_service().get_project_run(project_id, task_id)
    if not run:
        return error("not_found", "运行记录不存在")
    return success(run)


@router.post("/projects/{project_id}/nodes/{node_id}/run")
async def run_node(project_id: str, node_id: str, data: CanvasNodeRun = Body(default=CanvasNodeRun())):
    override = data.config_override.model_dump(exclude_none=True) if data.config_override else None
    result = await get_canvas_service().run_node(
        project_id,
        node_id,
        user_id=data.user_id,
        session_id=data.session_id,
        config_override=override,
    )
    if result.get("success"):
        return success(result)
    return error(result.get("error_code", "internal_error"), result.get("error_message", "运行失败"))


@router.post("/projects/{project_id}/nodes/{node_id}/ack-stale")
async def ack_stale(project_id: str, node_id: str):
    node = await get_canvas_service().acknowledge_stale(project_id, node_id)
    if not node:
        return error("not_found", "节点不存在")
    return success(node)


@router.post("/projects/{project_id}/upload-resource")
async def upload_resource(
    project_id: str,
    file: UploadFile = File(...),
    resource_type: str = Form("image"),
    x: float = Form(0),
    y: float = Form(0),
):
    """上传图片/视频并创建资源节点"""
    project = await get_canvas_service().get_project(project_id)
    if not project:
        return error("not_found", "项目不存在")

    content = await file.read()
    if not content:
        return error("validation_error", "文件为空")

    is_video = resource_type == "video" or (file.content_type or "").startswith("video/")
    max_size = 100 * 1024 * 1024 if is_video else 20 * 1024 * 1024
    if len(content) > max_size:
        return error("file_too_large", f"文件不能超过 {max_size // (1024 * 1024)}MB")

    storage = get_storage_service()
    if not storage.enabled:
        return error("service_unavailable", "存储服务未配置")

    category = "video" if is_video else "image"
    try:
        url, file_path = await storage.upload_file(content, file.filename or "asset.bin", category, file.content_type or "")
    except Exception as e:
        logger.error(f"画布资源上传失败: {e}")
        return error("internal_error", str(e))

    cdn_urls = storage.get_all_cdn_urls(file_path) if file_path else [url]

    await get_asset_service().create(
        file_name=file.filename or "upload",
        file_path=file_path,
        url=url,
        cdn_urls=cdn_urls,
        file_size=len(content),
        content_type=file.content_type or ("video/mp4" if is_video else "image/png"),
        category=category,
        source_type="upload",
    )

    node = await get_canvas_service().create_node(project_id, {
        "node_type": "resource",
        "title": file.filename or ("视频资源" if is_video else "图片资源"),
        "position": {"x": x, "y": y},
        "config": {
            "resource_url": url,
            "resource_type": category,
            "resource_name": file.filename,
        },
    })
    return success(node)
