from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.core.utils import generate_canvas_edge_id, generate_canvas_node_id, generate_project_id
from app.services.gateway_service import get_model_gateway
from app.services.model_service import get_model_service
from app.services.task_service import get_task_service
from app.services.trace_log_service import get_trace_log_service

logger = get_logger()

NODE_TYPE_CATEGORY = {
    "text": "text",
    "image": "image",
    "video": "video",
}


class CanvasService:
    def __init__(self):
        self.projects = get_collection("canvas_projects")
        self.nodes = get_collection("canvas_nodes")
        self.edges = get_collection("canvas_edges")

    # ── Project ──────────────────────────────────────────────

    async def create_project(
        self,
        title: str,
        user_id: Optional[str] = None,
        *,
        agent_thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        project_id = generate_project_id()
        doc = {
            "project_id": project_id,
            "user_id": user_id,
            "title": title or "未命名项目",
            "viewport": {"x": 0, "y": 0, "zoom": 1},
            "agent_thread_id": agent_thread_id,
            "source_agent_thread_id": agent_thread_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.projects.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return self._project_response(doc)

    async def get_or_create_workspace_default(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """每个用户固定一个「创作工作台」默认画布，ID 不变（KV 映射 + Mongo 项目）。"""
        from app.services.kv_service import get_kv_service

        uid = (user_id or "default_user").strip() or "default_user"
        kv_key = f"workspace_default:{uid}"
        kv = get_kv_service()
        cached_id = await kv.get("canvas", kv_key)
        if cached_id:
            doc = await self.projects.find_one({"project_id": cached_id})
            if doc:
                if doc.get("user_id") not in (uid, None, "", "default_user"):
                    await self.projects.update_one(
                        {"project_id": cached_id},
                        {"$set": {"user_id": uid, "updated_at": datetime.utcnow()}},
                    )
                    doc = await self.projects.find_one({"project_id": cached_id})
                return self._project_response(doc)

        project = await self.create_project("我的创作画布", uid)
        pid = project["project_id"]
        await self.projects.update_one(
            {"project_id": pid},
            {"$set": {"is_workspace_default": True, "updated_at": datetime.utcnow()}},
        )
        await kv.set("canvas", kv_key, pid)
        doc = await self.projects.find_one({"project_id": pid})
        logger.info(f"创建用户默认创作画布 user={uid} project={pid}")
        return self._project_response(doc)

    async def list_projects(self, user_id: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        query: Dict[str, Any] = {}
        if user_id and user_id != "default_user":
            # 当前用户 + 未绑定 + 创建时未登录的 default_user 历史项目
            query["$or"] = [
                {"user_id": user_id},
                {"user_id": None},
                {"user_id": ""},
                {"user_id": {"$exists": False}},
                {"user_id": "default_user"},
            ]
        total = await self.projects.count_documents(query)
        skip = (page - 1) * page_size
        cursor = self.projects.find(query).sort("updated_at", -1).skip(skip).limit(page_size)
        items = [self._project_response(doc) async for doc in cursor]
        return items, total

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.projects.find_one({"project_id": project_id})
        if not doc:
            return None
        project = self._project_response(doc)
        project["nodes"] = await self.list_nodes(project_id)
        project["edges"] = await self.list_edges(project_id)
        return project

    async def get_project_by_agent_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """按创作助手 thread_id 反查已绑定的画布（agent_thread_id / source_agent_thread_id）。"""
        tid = (thread_id or "").strip()
        if not tid:
            return None
        doc = await self.projects.find_one(
            {
                "$or": [
                    {"agent_thread_id": tid},
                    {"source_agent_thread_id": tid},
                ]
            },
            sort=[("updated_at", -1)],
        )
        return self._project_response(doc) if doc else None

    async def bind_agent_thread(self, project_id: str, thread_id: str) -> Optional[Dict[str, Any]]:
        """画布 ↔ 创作助手双向绑定：写入 agent_thread_id / source_agent_thread_id。"""
        pid = (project_id or "").strip()
        tid = (thread_id or "").strip()
        if not pid or not tid:
            raise ValueError("画布与创作助手 ID 不能为空")
        doc = await self.projects.find_one({"project_id": pid})
        if not doc:
            raise ValueError("画布项目不存在")
        existing_tid = (doc.get("agent_thread_id") or "").strip()
        if existing_tid and existing_tid != tid:
            raise ValueError("该画布已绑定其他创作助手")
        other = await self.projects.find_one(
            {
                "agent_thread_id": tid,
                "project_id": {"$ne": pid},
            }
        )
        if other:
            raise ValueError("该创作助手已绑定其他画布")
        now = datetime.utcnow()
        await self.projects.update_one(
            {"project_id": pid},
            {
                "$set": {
                    "agent_thread_id": tid,
                    "source_agent_thread_id": tid,
                    "updated_at": now,
                }
            },
        )
        updated = await self.projects.find_one({"project_id": pid})
        return self._project_response(updated) if updated else None

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {}
        if "title" in updates and updates["title"] is not None:
            allowed["title"] = updates["title"]
        if "viewport" in updates and updates["viewport"] is not None:
            allowed["viewport"] = updates["viewport"]
        if "user_id" in updates and updates["user_id"] is not None:
            allowed["user_id"] = updates["user_id"]
        if not allowed:
            return await self.get_project(project_id)
        allowed["updated_at"] = datetime.utcnow()
        result = await self.projects.update_one({"project_id": project_id}, {"$set": allowed})
        if result.matched_count == 0:
            return None
        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> bool:
        await self.nodes.delete_many({"project_id": project_id})
        await self.edges.delete_many({"project_id": project_id})
        result = await self.projects.delete_one({"project_id": project_id})
        return result.deleted_count > 0

    # ── Node ───────────────────────────────────────────────────

    async def create_node(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not await self.projects.find_one({"project_id": project_id}):
            return None
        now = datetime.utcnow()
        node_type = data["node_type"]
        title = data.get("title") or self._default_node_title(node_type)
        doc = {
            "node_id": generate_canvas_node_id(),
            "project_id": project_id,
            "node_type": node_type,
            "title": title,
            "position": data.get("position") or {"x": 0, "y": 0},
            "parent_id": data.get("parent_id"),
            "config": data.get("config") or {},
            "result": None,
            "result_version": 0,
            "task_id": None,
            "status": "idle" if node_type != "resource" else "success",
            "error_message": None,
            "input_stale": False,
            "upstream_snapshot": {},
            "created_at": now,
            "updated_at": now,
        }
        if node_type == "resource":
            cfg = doc["config"]
            if cfg.get("resource_url"):
                doc["result"] = self._resource_result(cfg)
                doc["result_version"] = 1
        result = await self.nodes.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": now}})
        return self._node_response(doc)

    async def list_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        cursor = self.nodes.find({"project_id": project_id}).sort("created_at", 1)
        rows: List[Dict[str, Any]] = []
        async for doc in cursor:
            if doc.get("status") == "running":
                await self._reconcile_node_run_status(project_id, doc["node_id"])
                doc = await self.nodes.find_one({"project_id": project_id, "node_id": doc["node_id"]}) or doc
            rows.append(self._node_response(doc))
        return rows

    async def get_node(self, project_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
        if not doc:
            return None
        await self._reconcile_node_run_status(project_id, node_id)
        doc = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
        return self._node_response(doc) if doc else None

    async def update_node(self, project_id: str, node_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed: Dict[str, Any] = {}
        nullable_keys = {"result", "error_message", "task_id"}
        for key in ("title", "position", "config", "status", "input_stale", "result", "parent_id", "task_id", "error_message", "result_version", "upstream_snapshot"):
            if key not in updates:
                continue
            if key == "parent_id":
                allowed["parent_id"] = updates["parent_id"]
                continue
            if updates[key] is not None or key in nullable_keys:
                allowed[key] = updates[key]
        if "config" in allowed:
            current = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
            if current:
                merged_cfg = {**(current.get("config") or {}), **allowed["config"]}
                for key in ("style_preset_id", "style_preset_name"):
                    if key in allowed["config"] and allowed["config"][key] is None:
                        merged_cfg.pop(key, None)
                allowed["config"] = merged_cfg
        if not allowed:
            return await self.get_node(project_id, node_id)
        allowed["updated_at"] = datetime.utcnow()
        result = await self.nodes.update_one(
            {"project_id": project_id, "node_id": node_id},
            {"$set": allowed},
        )
        if result.matched_count == 0:
            return None
        await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": datetime.utcnow()}})
        return await self.get_node(project_id, node_id)

    async def delete_node(self, project_id: str, node_id: str) -> bool:
        await self.edges.delete_many({
            "project_id": project_id,
            "$or": [{"source_node_id": node_id}, {"target_node_id": node_id}],
        })
        result = await self.nodes.delete_one({"project_id": project_id, "node_id": node_id})
        if result.deleted_count:
            await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": datetime.utcnow()}})
        return result.deleted_count > 0

    @staticmethod
    def _duplicate_config(source: Dict[str, Any]) -> Dict[str, Any]:
        config = deepcopy(source.get("config") or {})
        if source.get("node_type") == "image":
            config["output_image_index"] = 0
            if not config.get("user_resized"):
                config.pop("width", None)
                config.pop("height", None)
        return config

    @staticmethod
    def _duplicate_runtime_fields(source: Dict[str, Any]) -> Dict[str, Any]:
        """图片节点复制时只保留 config 生图参数，不继承运行态与结果。"""
        if source.get("node_type") == "image":
            return {
                "result": None,
                "result_version": 0,
                "task_id": None,
                "status": "idle",
                "error_message": None,
                "input_stale": False,
                "upstream_snapshot": {},
            }
        return {
            "result": deepcopy(source.get("result")) if source.get("result") else None,
            "result_version": source.get("result_version") or 0,
            "task_id": source.get("task_id"),
            "status": source.get("status") or "idle",
            "error_message": source.get("error_message"),
            "input_stale": source.get("input_stale", False),
            "upstream_snapshot": deepcopy(source.get("upstream_snapshot") or {}),
        }

    async def duplicate_node(
        self,
        project_id: str,
        node_id: str,
        position: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        source = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
        if not source:
            return None
        now = datetime.utcnow()
        pos = source.get("position") or {"x": 0, "y": 0}
        title = source.get("title") or self._default_node_title(source.get("node_type", "text"))
        if position is not None:
            new_pos = {"x": float(position.get("x", 0)), "y": float(position.get("y", 0))}
        else:
            new_pos = {"x": pos.get("x", 0) + 40, "y": pos.get("y", 0) + 40}
        doc = {
            "node_id": generate_canvas_node_id(),
            "project_id": project_id,
            "node_type": source["node_type"],
            "title": f"{title} (副本)",
            "position": new_pos,
            "config": self._duplicate_config(source),
            **self._duplicate_runtime_fields(source),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.nodes.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": now}})
        return self._node_response(doc)

    # ── Edge ───────────────────────────────────────────────────

    async def create_edge(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        source_id = data["source_node_id"]
        target_id = data["target_node_id"]
        if source_id == target_id:
            return None
        source = await self.nodes.find_one({"project_id": project_id, "node_id": source_id})
        target = await self.nodes.find_one({"project_id": project_id, "node_id": target_id})
        if not source or not target:
            return None
        if source.get("node_type") == "group" or target.get("node_type") == "group":
            return None
        existing = await self.edges.find_one({
            "project_id": project_id,
            "source_node_id": source_id,
            "target_node_id": target_id,
        })
        if existing:
            return self._edge_response(existing)
        now = datetime.utcnow()
        doc = {
            "edge_id": generate_canvas_edge_id(),
            "project_id": project_id,
            "source_node_id": source_id,
            "target_node_id": target_id,
            "source_handle": data.get("source_handle") or "output",
            "target_handle": data.get("target_handle") or "input",
            "created_at": now,
        }
        result = await self.edges.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        await self._refresh_target_input_state(project_id, target_id)
        await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": now}})
        return self._edge_response(doc)

    async def list_edges(self, project_id: str) -> List[Dict[str, Any]]:
        cursor = self.edges.find({"project_id": project_id}).sort("created_at", 1)
        return [self._edge_response(doc) async for doc in cursor]

    async def delete_edge(self, project_id: str, edge_id: str) -> bool:
        edge = await self.edges.find_one({"project_id": project_id, "edge_id": edge_id})
        if not edge:
            return False
        result = await self.edges.delete_one({"project_id": project_id, "edge_id": edge_id})
        if result.deleted_count:
            await self._refresh_target_input_state(project_id, edge["target_node_id"])
            await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": datetime.utcnow()}})
        return result.deleted_count > 0

    async def batch_sync(self, project_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not await self.projects.find_one({"project_id": project_id}):
            return None
        if payload.get("viewport"):
            await self.update_project(project_id, {"viewport": payload["viewport"]})
        for node in payload.get("nodes") or []:
            node_id = node.get("node_id")
            if not node_id:
                continue
            updates = {}
            if "position" in node:
                updates["position"] = node["position"]
            if "title" in node:
                updates["title"] = node["title"]
            if "parent_id" in node:
                updates["parent_id"] = node["parent_id"]
            if updates:
                await self.update_node(project_id, node_id, updates)
        return await self.get_project(project_id)

    # ── Run node ───────────────────────────────────────────────

    async def run_node(
        self,
        project_id: str,
        node_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        node = await self.get_node(project_id, node_id)
        if not node:
            return {"success": False, "error_code": "not_found", "error_message": "节点不存在"}
        if node["node_type"] == "resource":
            return {"success": False, "error_code": "validation_error", "error_message": "资源节点无需运行"}
        if node["node_type"] == "group":
            return {"success": False, "error_code": "validation_error", "error_message": "分组框不可运行"}
        if node["node_type"] == "title":
            return {"success": False, "error_code": "validation_error", "error_message": "标题节点不可运行"}

        config = deepcopy(node.get("config") or {})
        if config_override:
            for key, val in config_override.items():
                if val is not None:
                    config[key] = val

        model_code = config.get("model_code")
        if not model_code:
            return {"success": False, "error_code": "validation_error", "error_message": "请先选择模型"}

        category = NODE_TYPE_CATEGORY.get(node["node_type"])
        if not category:
            return {"success": False, "error_code": "validation_error", "error_message": "不支持的节点类型"}

        model = await get_model_service().get_by_code(model_code)
        if not model:
            return {"success": False, "error_code": "model_not_found", "error_message": f"模型不存在: {model_code}"}
        if model.get("status") != "online":
            return {"success": False, "error_code": "model_offline", "error_message": "模型已下架"}

        upstream_inputs, snapshot = await self._collect_upstream_inputs(project_id, node_id)
        ref_contents = await self._collect_ref_contents(project_id, node_id)
        ref_ids = self._extract_prompt_ref_ids(config)
        ref_image_urls = await self._collect_ref_image_urls(project_id, node_id, ref_ids)
        params = self._build_run_params(
            node["node_type"], config, upstream_inputs, ref_contents, ref_image_urls
        )
        if node["node_type"] in ("image", "video"):
            from app.core.canvas_style_prompt import apply_canvas_style_preset

            params = await apply_canvas_style_preset(
                params,
                style_preset_id=config.get("style_preset_id"),
                node_type=node["node_type"],
            )

        if category == "image":
            from app.core.image_size_spec import normalize_image_size

            bindings = [b for b in (model.get("channel_bindings") or []) if b.get("status", "active") == "active"]
            bindings.sort(key=lambda b: b.get("priority", 1), reverse=True)
            channel_model_id = bindings[0].get("channel_model_id", "") if bindings else ""
            normalized, size_err = normalize_image_size(params, model_code, channel_model_id)
            if size_err:
                return {"success": False, "error_code": "validation_error", "error_message": size_err}
            params = normalized

        if category in ("image", "video"):
            await self._mirror_params_images_to_cdn(params, trace_hint=f"canvas:{project_id}:{node_id}")

        if category in ("image", "video", "text"):
            from app.core.cdn import validate_reference_images
            try:
                validate_reference_images(params)
            except ValueError as ve:
                return {"success": False, "error_code": "validation_error", "error_message": str(ve)}

        if node.get("status") == "running":
            await self._reconcile_node_run_status(project_id, node_id)
            node = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
            if not node:
                return {"success": False, "error_code": "not_found", "error_message": "节点不存在"}

        latest_task = await self._get_latest_canvas_task(project_id, node_id)
        if latest_task and latest_task.get("status") == "processing":
            return {
                "success": False,
                "error_code": "validation_error",
                "error_message": "节点正在生成中，请稍候",
            }

        task = await get_task_service().create(
            model_code=model_code,
            category=category,
            params=params,
            session_id=session_id,
            user_id=user_id,
            canvas_project_id=project_id,
            canvas_node_id=node_id,
            canvas_node_title=node.get("title"),
            canvas_node_type=node.get("node_type"),
        )

        await self.nodes.update_one(
            {"project_id": project_id, "node_id": node_id},
            {
                "$set": {
                    "status": "running",
                    "error_message": None,
                    "task_id": task["task_id"],
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        trace_svc = get_trace_log_service()
        await trace_svc.ensure_log(
            task["trace_id"],
            task_id=task["task_id"],
            model_code=model_code,
            category=category,
            user_id=user_id,
            session_id=session_id,
        )
        await trace_svc.append_step(task["trace_id"], "canvas_node_run", {
            "project_id": project_id,
            "node_id": node_id,
            "upstream_snapshot": snapshot,
        })
        await get_task_service().update_status(task["task_id"], "processing")

        gateway = get_model_gateway()
        result = await gateway.execute(
            model_code=model_code,
            category=category,
            params=params,
            trace_id=task.get("trace_id"),
            task_id=task["task_id"],
        )

        if result.get("success"):
            result_data = result.get("data") or {}
            if node["node_type"] == "image":
                result_data = await self._mirror_result_images_to_cdn(
                    result_data, task.get("trace_id", "")
                )
            new_version = (node.get("result_version") or 0) + 1
            if node["node_type"] == "image":
                imgs = result_data.get("images") or []
                if imgs:
                    idx = int(config.get("output_image_index") or 0)
                    config["output_image_index"] = max(0, min(idx, len(imgs) - 1))
                else:
                    config["output_image_index"] = 0
            await get_task_service().update_status(
                task["task_id"], "success",
                result=result_data,
                channel_code=result.get("channel_code"),
                duration_ms=result.get("duration_ms"),
                channel_request=result.get("channel_request"),
                channel_response=result.get("channel_response"),
                external_task_id=result.get("external_task_id"),
            )
            await trace_svc.finalize(task["trace_id"], "success", duration_ms=result.get("duration_ms"))
            try:
                from app.services.asset_service import register_generated_assets_from_result

                await register_generated_assets_from_result(
                    result_data,
                    task_id=task["task_id"],
                    category=category,
                    trace_id=task.get("trace_id", ""),
                )
            except Exception as e:
                logger.warning(f"画布生成资源入库失败 project={project_id} node={node_id}: {e}")
            await self.nodes.update_one(
                {"project_id": project_id, "node_id": node_id},
                {"$set": {
                    "status": "success",
                    "result": result_data,
                    "result_version": new_version,
                    "task_id": task["task_id"],
                    "config": config,
                    "upstream_snapshot": snapshot,
                    "input_stale": False,
                    "error_message": None,
                    "updated_at": datetime.utcnow(),
                }},
            )
            await self._mark_downstream_stale(project_id, node_id, new_version)
            await self.projects.update_one({"project_id": project_id}, {"$set": {"updated_at": datetime.utcnow()}})
            updated = await self.get_node(project_id, node_id)
            return {"success": True, "node": updated, "task_id": task["task_id"]}

        err_msg = result.get("error_message", "生成失败")
        await get_task_service().update_status(task["task_id"], "failed", error_message=err_msg)
        await trace_svc.finalize(task["trace_id"], "failed", error_message=err_msg)
        await self.nodes.update_one(
            {"project_id": project_id, "node_id": node_id},
            {"$set": {"status": "failed", "error_message": err_msg, "task_id": task["task_id"], "updated_at": datetime.utcnow()}},
        )
        return {"success": False, "error_code": result.get("error_code", "internal_error"), "error_message": err_msg}

    async def acknowledge_stale(self, project_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        node = await self.get_node(project_id, node_id)
        if not node:
            return None
        _, snapshot = await self._collect_upstream_inputs(project_id, node_id)
        await self.nodes.update_one(
            {"project_id": project_id, "node_id": node_id},
            {"$set": {"input_stale": False, "upstream_snapshot": snapshot, "updated_at": datetime.utcnow()}},
        )
        return await self.get_node(project_id, node_id)

    # ── Run history ────────────────────────────────────────────

    async def _project_run_task_ids_from_traces(self, project_id: str) -> List[str]:
        trace_col = get_trace_log_service().collection
        cursor = trace_col.find(
            {"steps": {"$elemMatch": {"step": "canvas_node_run", "data.project_id": project_id}}},
            {"task_id": 1},
        )
        ids: List[str] = []
        seen = set()
        async for doc in cursor:
            tid = doc.get("task_id")
            if tid and tid not in seen:
                seen.add(tid)
                ids.append(tid)
        return ids

    def _project_runs_query(
        self,
        project_id: str,
        legacy_task_ids: List[str],
        *,
        agent_thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        clauses: List[Dict[str, Any]] = [{"canvas_project_id": project_id}]
        if agent_thread_id:
            clauses.append({"agent_thread_id": agent_thread_id, "source": "agent_chat"})
        if legacy_task_ids:
            clauses.append({"task_id": {"$in": legacy_task_ids}})
        if len(clauses) == 1:
            return clauses[0]
        return {"$or": clauses}

    async def _enrich_run_row(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task.get("canvas_node_id")
        node_title = task.get("canvas_node_title")
        node_type = task.get("canvas_node_type")
        if node_id and (not node_title or not node_type):
            node = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
            if node:
                node_title = node_title or node.get("title")
                node_type = node_type or node.get("node_type")
        if not node_id:
            trace_col = get_trace_log_service().collection
            log = await trace_col.find_one({"task_id": task.get("task_id")})
            if log:
                for step in reversed(log.get("steps") or []):
                    if step.get("step") == "canvas_node_run":
                        data = step.get("data") or {}
                        if data.get("project_id") == project_id:
                            node_id = data.get("node_id") or node_id
                            break
                if node_id and not node_title:
                    node = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
                    if node:
                        node_title = node.get("title")
                        node_type = node_type or node.get("node_type")
        return {
            "task_id": task["task_id"],
            "trace_id": task.get("trace_id"),
            "project_id": project_id,
            "canvas_project_id": task.get("canvas_project_id") or project_id,
            "node_id": node_id,
            "canvas_node_id": node_id,
            "node_title": node_title or ("创作助手对话" if node_type == "agent_chat" else "未命名节点"),
            "node_type": node_type,
            "canvas_node_type": node_type,
            "model_code": task.get("model_code"),
            "channel_code": task.get("channel_code"),
            "external_task_id": task.get("external_task_id"),
            "category": task.get("category"),
            "status": task.get("status"),
            "params_summary": task.get("params_summary"),
            "error_message": task.get("error_message"),
            "duration_ms": task.get("duration_ms"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }

    async def list_project_runs(
        self, project_id: str, page: int = 1, page_size: int = 30
    ) -> Tuple[List[Dict[str, Any]], int]:
        project = await self.projects.find_one({"project_id": project_id}, {"agent_thread_id": 1})
        agent_thread_id = (project or {}).get("agent_thread_id")
        legacy_ids = await self._project_run_task_ids_from_traces(project_id)
        query = self._project_runs_query(project_id, legacy_ids, agent_thread_id=agent_thread_id)
        task_col = get_task_service().collection
        total = await task_col.count_documents(query)
        skip = (page - 1) * page_size
        cursor = task_col.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        rows = []
        async for doc in cursor:
            task = get_task_service()._to_response(doc)
            rows.append(await self._enrich_run_row(project_id, task))
        return rows, total

    async def get_project_run(self, project_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        task = await get_task_service().get_by_id(task_id)
        if not task:
            return None
        if task.get("canvas_project_id") == project_id:
            return await self._enrich_run_row(project_id, task) | {
                "result": task.get("result"),
                "params": task.get("params"),
                "channel_code": task.get("channel_code"),
                "external_task_id": task.get("external_task_id"),
                "channel_request": task.get("channel_request"),
                "channel_response": task.get("channel_response"),
            }
        project = await self.projects.find_one({"project_id": project_id}, {"agent_thread_id": 1})
        agent_thread_id = (project or {}).get("agent_thread_id")
        if (
            agent_thread_id
            and task.get("agent_thread_id") == agent_thread_id
            and task.get("source") == "agent_chat"
        ):
            return await self._enrich_run_row(project_id, task) | {
                "result": task.get("result"),
                "params": task.get("params"),
                "channel_code": task.get("channel_code"),
                "external_task_id": task.get("external_task_id"),
                "channel_request": task.get("channel_request"),
                "channel_response": task.get("channel_response"),
            }
        legacy_ids = await self._project_run_task_ids_from_traces(project_id)
        if task_id not in legacy_ids:
            return None
        return await self._enrich_run_row(project_id, task) | {
            "result": task.get("result"),
            "params": task.get("params"),
            "channel_code": task.get("channel_code"),
            "external_task_id": task.get("external_task_id"),
            "channel_request": task.get("channel_request"),
            "channel_response": task.get("channel_response"),
        }

    async def task_belongs_to_project(self, project_id: str, task_id: str) -> bool:
        run = await self.get_project_run(project_id, task_id)
        return run is not None

    # ── Helpers ────────────────────────────────────────────────

    async def _get_latest_canvas_task(self, project_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        return await get_task_service().collection.find_one(
            {"canvas_project_id": project_id, "canvas_node_id": node_id},
            sort=[("created_at", -1)],
        )

    async def _reconcile_node_run_status(self, project_id: str, node_id: str) -> None:
        """任务已成功/失败但节点仍停留在 running 时自动对齐（如并发二次运行）。"""
        doc = await self.nodes.find_one({"project_id": project_id, "node_id": node_id})
        if not doc or doc.get("status") != "running":
            return
        latest = await self._get_latest_canvas_task(project_id, node_id)
        if not latest:
            return
        task_status = latest.get("status")
        if task_status == "processing":
            return
        now = datetime.utcnow()
        task_id = latest.get("task_id")
        if task_status == "success":
            result_data = latest.get("result") or doc.get("result")
            new_version = int(doc.get("result_version") or 0)
            if result_data and result_data != doc.get("result"):
                new_version += 1
            await self.nodes.update_one(
                {"project_id": project_id, "node_id": node_id},
                {
                    "$set": {
                        "status": "success",
                        "result": result_data,
                        "result_version": new_version,
                        "task_id": task_id,
                        "error_message": None,
                        "updated_at": now,
                    }
                },
            )
        elif task_status == "failed":
            await self.nodes.update_one(
                {"project_id": project_id, "node_id": node_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": latest.get("error_message") or "生成失败",
                        "task_id": task_id,
                        "updated_at": now,
                    }
                },
            )

    async def _mirror_params_images_to_cdn(self, params: Dict[str, Any], trace_hint: str = "") -> None:
        """上游生成图常为外部 URL，运行前镜像到 CDN 以满足 validate_reference_images。"""
        from app.adapters.weelinking import _ensure_cdn_url
        from app.core.cdn import extract_url_from_image_item, is_cdn_url

        raw = params.get("images")
        if raw is None:
            raw = params.get("image")
        if not raw:
            return
        items = raw if isinstance(raw, list) else [raw]
        out: List[str] = []
        for item in items:
            url = extract_url_from_image_item(item)
            if not url:
                continue
            if is_cdn_url(url):
                out.append(url)
            else:
                out.append(await _ensure_cdn_url(url, trace_hint))
        if out:
            params["images"] = out
            params.pop("image", None)

    async def _mirror_result_images_to_cdn(
        self, result_data: Dict[str, Any], trace_id: str = ""
    ) -> Dict[str, Any]:
        """生图结果落库前镜像到 CDN，便于下游节点直接引用。"""
        from app.adapters.weelinking import _ensure_cdn_url
        from app.core.cdn import extract_url_from_image_item, is_cdn_url

        imgs = result_data.get("images") or []
        if not imgs:
            return result_data
        mirrored: List[Dict[str, Any]] = []
        for img in imgs:
            url = extract_url_from_image_item(img)
            if not url:
                continue
            cdn = url if is_cdn_url(url) else await _ensure_cdn_url(url, trace_id)
            if isinstance(img, dict):
                mirrored.append({**img, "url": cdn, "cdn_url": cdn})
            else:
                mirrored.append({"url": cdn, "cdn_url": cdn})
        return {**result_data, "images": mirrored}

    async def _collect_upstream_inputs(self, project_id: str, node_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        edges = await self.edges.find({"project_id": project_id, "target_node_id": node_id}).to_list(length=100)
        texts: List[str] = []
        images: List[str] = []
        videos: List[str] = []
        snapshot: Dict[str, Any] = {}

        for edge in edges:
            source = await self.nodes.find_one({"project_id": project_id, "node_id": edge["source_node_id"]})
            if not source:
                continue
            snapshot[source["node_id"]] = {
                "result_version": source.get("result_version") or 0,
                "node_type": source.get("node_type"),
            }
            src_type = source.get("node_type")
            result = source.get("result") or {}
            cfg = source.get("config") or {}

            if src_type == "resource":
                url = cfg.get("resource_url")
                rtype = cfg.get("resource_type") or "image"
                if url:
                    if rtype == "video":
                        videos.append(url)
                    else:
                        images.append(url)
            elif src_type == "text":
                text_val = result.get("text") or cfg.get("content")
                if text_val:
                    texts.append(str(text_val))
            elif src_type == "image":
                imgs = result.get("images") or []
                if imgs:
                    idx = int(cfg.get("output_image_index") or 0)
                    idx = max(0, min(idx, len(imgs) - 1))
                    img = imgs[idx]
                    url = img.get("url") if isinstance(img, dict) else str(img)
                    if url:
                        images.append(url)
            elif src_type == "video":
                for vid in result.get("videos") or []:
                    url = vid.get("url") if isinstance(vid, dict) else str(vid)
                    if url:
                        videos.append(url)

        return {"texts": texts, "images": images, "videos": videos}, snapshot

    async def _collect_ref_contents(self, project_id: str, node_id: str) -> Dict[str, str]:
        from app.core.canvas_prompt import image_url_from_source_node, text_from_source_node

        edges = await self.edges.find({"project_id": project_id, "target_node_id": node_id}).to_list(length=100)
        contents: Dict[str, str] = {}
        for edge in edges:
            source = await self.nodes.find_one({"project_id": project_id, "node_id": edge["source_node_id"]})
            if not source:
                continue
            src_type = source.get("node_type")
            if src_type == "text":
                text = text_from_source_node(source)
                if text:
                    contents[source["node_id"]] = text
            elif src_type in ("image", "resource") and image_url_from_source_node(source):
                # @ 引用图片时占位符替换为空，实际 URL 走 params.images
                contents[source["node_id"]] = ""
        return contents

    def _extract_prompt_ref_ids(self, config: Dict[str, Any]) -> List[str]:
        from app.core.canvas_prompt import extract_ref_node_ids

        return extract_ref_node_ids((config.get("prompt") or "").strip())

    async def _collect_ref_image_urls(
        self,
        project_id: str,
        node_id: str,
        ref_ids: Optional[List[str]] = None,
    ) -> List[str]:
        from app.core.canvas_prompt import image_url_from_source_node

        urls: List[str] = []
        seen: set[str] = set()

        def add(url: Optional[str]) -> None:
            if not url or url in seen:
                return
            seen.add(url)
            urls.append(url)

        edges = await self.edges.find({"project_id": project_id, "target_node_id": node_id}).to_list(length=100)
        for edge in edges:
            source = await self.nodes.find_one({"project_id": project_id, "node_id": edge["source_node_id"]})
            if not source:
                continue
            add(image_url_from_source_node(source))

        if ref_ids:
            for ref_id in ref_ids:
                source = await self.nodes.find_one({"project_id": project_id, "node_id": ref_id})
                if source:
                    add(image_url_from_source_node(source))
        return urls

    def _build_run_params(
        self,
        node_type: str,
        config: Dict[str, Any],
        upstream: Dict[str, Any],
        ref_contents: Optional[Dict[str, str]] = None,
        ref_image_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        from app.core.canvas_prompt import (
            append_attached_text_refs,
            expand_prompt_refs,
            extract_ref_node_ids,
        )

        params = deepcopy(config.get("params") or {})
        raw_prompt = (config.get("prompt") or "").strip()
        ref_ids = extract_ref_node_ids(raw_prompt)
        if ref_ids:
            prompt = expand_prompt_refs(raw_prompt, ref_contents or {})
        else:
            prompt = raw_prompt
        prompt = append_attached_text_refs(
            (prompt or "").strip(),
            ref_contents or {},
            ref_ids,
        ).strip()
        if prompt:
            params["prompt"] = prompt

        def merge_image_urls(*sources: Optional[List[str]]) -> List[str]:
            images: List[str] = []
            for src in sources:
                for url in src or []:
                    if url and url not in images:
                        images.append(url)
            return images

        if node_type == "text":
            images = merge_image_urls(ref_image_urls, upstream.get("images"))
            if images:
                params["images"] = images

        if node_type in ("image", "video"):
            images = merge_image_urls(ref_image_urls, upstream.get("images"))
            existing_images = params.get("images") or params.get("image")
            if isinstance(existing_images, str):
                if existing_images not in images:
                    images.insert(0, existing_images)
            elif isinstance(existing_images, list):
                for url in existing_images:
                    if url and url not in images:
                        images.append(url)
            if images:
                params["images"] = images

        videos = list(upstream.get("videos") or [])
        existing_videos = params.get("videos")
        if isinstance(existing_videos, list):
            videos.extend(existing_videos)
        if videos:
            params["videos"] = videos
            if node_type == "video" and videos and "first_frame_image" not in params:
                params["first_frame_image"] = videos[0]

        return params

    async def _refresh_target_input_state(self, project_id: str, target_node_id: str) -> None:
        target = await self.nodes.find_one({"project_id": project_id, "node_id": target_node_id})
        if not target or target.get("node_type") == "resource":
            return
        _, snapshot = await self._collect_upstream_inputs(project_id, target_node_id)
        await self.nodes.update_one(
            {"project_id": project_id, "node_id": target_node_id},
            {"$set": {"upstream_snapshot": snapshot, "updated_at": datetime.utcnow()}},
        )

    async def _mark_downstream_stale(self, project_id: str, source_node_id: str, new_version: int) -> None:
        edges = await self.edges.find({"project_id": project_id, "source_node_id": source_node_id}).to_list(length=200)
        for edge in edges:
            target_id = edge["target_node_id"]
            target = await self.nodes.find_one({"project_id": project_id, "node_id": target_id})
            if not target:
                continue
            prev = target.get("upstream_snapshot") or {}
            prev_entry = prev.get(source_node_id) or {}
            if prev_entry.get("result_version") != new_version:
                await self.nodes.update_one(
                    {"project_id": project_id, "node_id": target_id},
                    {"$set": {"input_stale": True, "updated_at": datetime.utcnow()}},
                )

    def _is_snapshot_stale(self, prev: Dict[str, Any], current: Dict[str, Any]) -> bool:
        for node_id, snap in current.items():
            prev_ver = (prev.get(node_id) or {}).get("result_version", 0)
            if snap.get("result_version", 0) != prev_ver:
                return True
        return False

    def _resource_result(self, config: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get("resource_url")
        rtype = config.get("resource_type") or "image"
        if rtype == "video":
            return {"type": "video", "videos": [{"url": url}], "count": 1}
        return {"type": "image", "images": [{"url": url}], "count": 1}

    def _default_node_title(self, node_type: str) -> str:
        labels = {"resource": "资源", "text": "文本节点", "image": "图片节点", "video": "视频节点", "group": "分组", "title": "标题"}
        return labels.get(node_type, "节点")

    def _project_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "project_id": doc["project_id"],
            "user_id": doc.get("user_id"),
            "title": doc.get("title"),
            "viewport": doc.get("viewport") or {"x": 0, "y": 0, "zoom": 1},
            "is_workspace_default": bool(doc.get("is_workspace_default")),
            "agent_thread_id": doc.get("agent_thread_id"),
            "source_agent_thread_id": doc.get("source_agent_thread_id"),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _node_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "node_id": doc["node_id"],
            "project_id": doc["project_id"],
            "node_type": doc["node_type"],
            "title": doc.get("title"),
            "position": doc.get("position") or {"x": 0, "y": 0},
            "parent_id": doc.get("parent_id"),
            "config": doc.get("config") or {},
            "result": doc.get("result"),
            "result_version": doc.get("result_version") or 0,
            "task_id": doc.get("task_id"),
            "status": doc.get("status") or "idle",
            "error_message": doc.get("error_message"),
            "input_stale": doc.get("input_stale", False),
            "upstream_snapshot": doc.get("upstream_snapshot") or {},
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _edge_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "edge_id": doc["edge_id"],
            "project_id": doc["project_id"],
            "source_node_id": doc["source_node_id"],
            "target_node_id": doc["target_node_id"],
            "source_handle": doc.get("source_handle") or "output",
            "target_handle": doc.get("target_handle") or "input",
            "created_at": doc["created_at"],
        }


_canvas_service = None


def get_canvas_service() -> CanvasService:
    global _canvas_service
    if _canvas_service is None:
        _canvas_service = CanvasService()
    return _canvas_service
