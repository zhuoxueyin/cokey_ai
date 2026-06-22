"""短剧 Skill 注册 CRUD（markdown 运营源）。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger

logger = get_logger()


class DramaSkillService:
    COLLECTION = "drama_skills"

    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            from app.core.database import get_collection
            self._collection = get_collection(self.COLLECTION)
        return self._collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            [("skill_code", 1), ("version", -1)],
            name="idx_skill_code_version",
        )
        await self.collection.create_index("status", name="idx_status")

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        for field in ("created_at", "updated_at", "published_at"):
            if doc.get(field):
                out[field] = doc[field].isoformat() + "Z"
        return out

    async def get_published(self, skill_code: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(
            {"skill_code": skill_code, "status": "published", "deleted_at": None},
            sort=[("version_num", -1)],
        )
        return self._serialize(doc) if doc else None

    async def get_latest_by_code(self, skill_code: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(
            {"skill_code": skill_code, "deleted_at": None},
            sort=[("version_num", -1)],
        )
        return self._serialize(doc) if doc else None

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            doc = await self.collection.find_one({"_id": ObjectId(doc_id), "deleted_at": None})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {"deleted_at": None}
        if stage:
            query["stage"] = stage
        if status:
            query["status"] = status
        if source:
            query["source"] = source

        pipeline = [
            {"$match": query},
            {"$sort": {"skill_code": 1, "version_num": -1}},
            {"$group": {"_id": "$skill_code", "doc": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$sort": {"skill_code": 1}},
        ]
        all_docs = [d async for d in self.collection.aggregate(pipeline)]
        total = len(all_docs)
        start = (page - 1) * page_size
        page_docs = all_docs[start : start + page_size]
        items = []
        for doc in page_docs:
            serialized = self._serialize(doc)
            items.append({**serialized, **self.compute_repo_sync_meta(serialized)})
        return items, total

    def compute_repo_sync_meta(
        self,
        doc: Dict[str, Any],
        *,
        repo_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """对比代码库 skills/ 与 Skill 库最新草稿，供列表展示同步 Tag。"""
        from app.core.drama.skill_spec import parse_frontmatter, resolve_repo_folder

        folder = resolve_repo_folder(doc.get("skill_code", ""), doc.get("repo_path"))
        if not folder:
            return {
                "repo_folder": None,
                "repo_available": False,
                "repo_has_changes": False,
                "repo_version": "",
            }

        payload = repo_payload
        if payload is None:
            try:
                from app.core.drama.skill_spec import load_repo_skill

                payload = load_repo_skill(folder)
            except (ValueError, OSError):
                return {
                    "repo_folder": folder,
                    "repo_available": False,
                    "repo_has_changes": False,
                    "repo_version": "",
                }

        unchanged = self._repo_payload_unchanged(doc, payload)
        meta, _ = parse_frontmatter(payload.get("skill_content_md") or "")
        return {
            "repo_folder": folder,
            "repo_available": True,
            "repo_has_changes": not unchanged,
            "repo_version": meta.get("version") or "",
        }

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.core.drama.skill_spec import enrich_skill_payload, validate_skill_content

        data = enrich_skill_payload(dict(data))
        content = data.get("skill_content_md") or data.get("system_markdown") or ""
        if content.strip():
            validate_skill_content(content, skill_code=data.get("skill_code"))

        now = datetime.utcnow()
        skill_code = data["skill_code"]
        latest = await self.collection.find_one(
            {"skill_code": skill_code},
            sort=[("version_num", -1)],
        )
        version_num = (latest.get("version_num", 0) + 1) if latest else 1

        doc = {
            "skill_id": f"sk_{uuid.uuid4().hex[:12]}",
            "skill_code": skill_code,
            "name": data["name"],
            "stage": data.get("stage", "init"),
            "source": data.get("source", "online"),
            "source_type": data.get("source_type", data.get("source", "online")),
            "repo_path": data.get("repo_path"),
            "source_ref": f"db:{skill_code}@v{version_num}",
            "immutable": False,
            "version": f"{version_num}.0.0",
            "version_num": version_num,
            "status": "draft",
            "skill_content_md": data.get("skill_content_md", ""),
            "skill_meta": data.get("skill_meta") or {},
            "script_files": data.get("script_files") or [],
            "system_markdown": data.get("system_markdown", ""),
            "user_markdown": data.get("user_markdown", ""),
            "output_schema_id": data.get("output_schema_id", ""),
            "required_memory": data.get("required_memory", []),
            "default_knowledge_tags": data.get("default_knowledge_tags", []),
            "model_hint": data.get("model_hint", {}),
            "description": data.get("description", ""),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._serialize(doc)

    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from app.core.drama.skill_spec import enrich_skill_payload, validate_skill_content

        existing = await self.get_by_id(doc_id)
        if not existing:
            return None
        if existing.get("immutable"):
            raise ValueError("内置 code 源 Skill 不可编辑正文")

        merged_input = {**existing, **data}
        if data.get("skill_content_md") is not None or data.get("system_markdown") is not None:
            merged_input = enrich_skill_payload(merged_input)
            content = merged_input.get("skill_content_md") or ""
            if content.strip():
                validate_skill_content(content, skill_code=existing["skill_code"])
            data = {**data, **{k: merged_input[k] for k in (
                "skill_content_md", "skill_meta", "system_markdown", "user_markdown", "name", "description"
            ) if k in merged_input}}

        from bson import ObjectId
        now = datetime.utcnow()
        new_doc = {**existing, **data, "id": None}
        for k in ("id", "created_at", "published_at"):
            new_doc.pop(k, None)
        new_doc["status"] = "draft"
        new_doc["version_num"] = existing.get("version_num", 1) + 1
        new_doc["version"] = f"{new_doc['version_num']}.0.0"
        new_doc["source_ref"] = f"db:{existing['skill_code']}@v{new_doc['version_num']}"
        new_doc["updated_at"] = now
        new_doc["created_at"] = now
        new_doc["deleted_at"] = None
        new_doc.pop("_id", None)

        result = await self.collection.insert_one(new_doc)
        new_doc["_id"] = result.inserted_id
        return self._serialize(new_doc)

    async def publish(self, doc_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            return None
        now = datetime.utcnow()
        await self.collection.update_many(
            {"skill_code": doc["skill_code"], "status": "published"},
            {"$set": {"status": "archived", "updated_at": now}},
        )
        await self.collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "published", "published_at": now, "updated_at": now}},
        )
        return await self.get_by_id(doc_id)

    async def soft_delete(self, doc_id: str) -> bool:
        from bson import ObjectId
        result = await self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"deleted_at": datetime.utcnow(), "status": "archived"}},
        )
        return result.modified_count > 0

    async def list_repo_folders(self) -> List[str]:
        from app.core.drama.skill_spec import scan_repo_skill_folders

        return [item["folder"] for item in scan_repo_skill_folders()]

    async def preview_repo_skill(self, folder: str) -> Dict[str, Any]:
        from app.core.drama.skill_spec import parse_frontmatter, repo_skills_root, validate_skill_content

        base = repo_skills_root()
        skill_dir = base / folder
        skill_md = skill_dir / "SKILL.md"
        scripts_dir = skill_dir / "scripts"

        if not skill_dir.is_dir():
            raise ValueError(f"目录不存在: {folder}")
        if not skill_md.is_file():
            raise ValueError(f"缺少 SKILL.md: {folder}")
        if not scripts_dir.is_dir():
            raise ValueError(f"缺少 scripts/ 目录: {folder}")

        content = skill_md.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(content)
        script_files = sorted(
            p.name for p in scripts_dir.iterdir() if p.is_file() and not p.name.startswith(".")
        )

        valid = True
        validation_error: Optional[str] = None
        try:
            validate_skill_content(content)
        except ValueError as e:
            valid = False
            validation_error = str(e)

        skill_code = meta.get("skill_id") or folder
        latest = await self.get_latest_by_code(skill_code)
        pub = await self.get_published(skill_code)

        return {
            "folder": folder,
            "path": str(skill_dir.relative_to(base.parent)),
            "skill_id": skill_code,
            "skill_name": meta.get("skill_name") or folder,
            "version": meta.get("version", ""),
            "tag": meta.get("tag", ""),
            "author": meta.get("author", ""),
            "update_time": meta.get("update_time", ""),
            "script_files": script_files,
            "skill_content_md": content.strip(),
            "valid": valid,
            "validation_error": validation_error,
            "registered": bool(pub),
            "published_version": pub.get("version") if pub else None,
            "target_skill_id": latest.get("id") if latest else None,
            "latest_status": latest.get("status") if latest else None,
        }

    async def list_repo_catalog(self) -> List[Dict[str, Any]]:
        from app.core.drama.skill_spec import scan_repo_skill_folders

        items = scan_repo_skill_folders()
        for item in items:
            code = item.get("skill_id") or ""
            pub = await self.get_published(code) if code else None
            latest = await self.get_latest_by_code(code) if code else None
            item["registered"] = bool(pub)
            if pub:
                item["published_version"] = pub.get("version")
            if latest:
                item["target_skill_id"] = latest.get("id")
                item["latest_status"] = latest.get("status")
        return items

    def _infer_stage_for_skill(self, payload: Dict[str, Any], stage: str) -> str:
        if stage != "production":
            return stage
        from app.core.drama.skill_registry import STAGE_SKILL_MAP

        inferred = next(
            (s for s, code in STAGE_SKILL_MAP.items() if code == payload.get("skill_code")),
            None,
        )
        return inferred or stage

    @staticmethod
    def _normalize_skill_content(text: str) -> str:
        return (text or "").strip().replace("\r\n", "\n")

    def _repo_payload_unchanged(self, existing: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        old = self._normalize_skill_content(
            existing.get("skill_content_md") or existing.get("system_markdown") or ""
        )
        new = self._normalize_skill_content(payload.get("skill_content_md") or "")
        if old != new:
            return False
        old_scripts = sorted(existing.get("script_files") or [])
        new_scripts = sorted(payload.get("script_files") or [])
        return old_scripts == new_scripts

    async def _repo_sync_state(
        self, existing: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """代码库 vs 草稿 vs 线上 同步状态（用于 unchanged 时的提示与发布引导）。"""
        from app.core.drama.skill_spec import parse_frontmatter

        unchanged = self._repo_payload_unchanged(existing, payload)
        published = await self.get_published(existing["skill_code"])
        repo_meta, _ = parse_frontmatter(payload.get("skill_content_md") or "")
        repo_version = repo_meta.get("version") or ""

        published_version = published.get("version") if published else None
        published_norm = self._normalize_skill_content(
            (published or {}).get("skill_content_md") or (published or {}).get("system_markdown") or ""
        )
        draft_norm = self._normalize_skill_content(
            existing.get("skill_content_md") or existing.get("system_markdown") or ""
        )
        repo_norm = self._normalize_skill_content(payload.get("skill_content_md") or "")

        draft_differs_from_published = published is None or draft_norm != published_norm
        # 草稿已与代码库一致，但线上仍是旧版 → 引导发布
        needs_publish = unchanged and draft_differs_from_published and draft_norm == repo_norm

        return {
            "unchanged": unchanged,
            "needs_publish": bool(needs_publish),
            "repo_version": repo_version,
            "published_version": published_version,
            "draft_version": existing.get("version"),
            "draft_status": existing.get("status"),
        }

    async def _apply_repo_to_skill(
        self,
        doc_id: str,
        payload: Dict[str, Any],
        *,
        folder: str,
        stage: str,
        publish: bool,
    ) -> Dict[str, Any]:
        existing = await self.get_by_id(doc_id)
        if not existing:
            raise ValueError("Skill 不存在")
        if payload["skill_code"] != existing["skill_code"]:
            raise ValueError(
                f"代码库 skill_id ({payload['skill_code']}) 与当前 Skill ({existing['skill_code']}) 不一致"
            )

        if self._repo_payload_unchanged(existing, payload):
            sync = await self._repo_sync_state(existing, payload)
            if publish and sync["needs_publish"]:
                doc = await self.publish(existing["id"]) or existing
                return {**doc, "unchanged": True, "action": "published", **sync}
            if publish and not sync["needs_publish"]:
                return {**existing, "unchanged": True, "action": "already_published", **sync}
            return {**existing, **sync}

        resolved_stage = self._infer_stage_for_skill(payload, stage)
        if resolved_stage == "production" and existing.get("stage"):
            resolved_stage = existing["stage"]

        update_data = {
            "name": payload["name"],
            "stage": resolved_stage,
            "skill_content_md": payload["skill_content_md"],
            "script_files": payload.get("script_files") or [],
            "description": payload.get("description", ""),
            "source": "repo",
            "source_type": "repo",
            "repo_path": folder,
        }
        doc = await self.update(doc_id, update_data)
        if not doc:
            raise ValueError("Skill 更新失败")
        if publish:
            doc = await self.publish(doc["id"]) or doc
        return {**doc, "unchanged": False}

    async def import_from_repo(
        self,
        folder: str,
        *,
        stage: str = "production",
        publish: bool = False,
        target_skill_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from app.core.drama.skill_spec import load_repo_skill

        payload = load_repo_skill(folder)
        payload["stage"] = self._infer_stage_for_skill(payload, stage)

        if target_skill_id:
            return await self._apply_repo_to_skill(
                target_skill_id,
                payload,
                folder=folder,
                stage=payload["stage"],
                publish=publish,
            )

        latest = await self.get_latest_by_code(payload["skill_code"])
        if latest:
            return await self._apply_repo_to_skill(
                latest["id"],
                payload,
                folder=folder,
                stage=payload["stage"],
                publish=publish,
            )

        doc = await self.create({**payload, "repo_path": folder})
        if publish:
            doc = await self.publish(doc["id"]) or doc
        return {**doc, "unchanged": False}

    async def reimport_from_repo(
        self,
        doc_id: str,
        *,
        folder: Optional[str] = None,
        publish: bool = False,
    ) -> Dict[str, Any]:
        from app.core.drama.skill_spec import load_repo_skill

        existing = await self.get_by_id(doc_id)
        if not existing:
            raise ValueError("Skill 不存在")

        from app.core.drama.skill_spec import resolve_repo_folder

        repo_folder = folder or resolve_repo_folder(
            existing.get("skill_code", ""),
            existing.get("repo_path"),
        )
        if not repo_folder:
            raise ValueError("未绑定代码库目录，请指定 folder 或在 skills/ 下建立对应目录")

        payload = load_repo_skill(repo_folder)
        return await self._apply_repo_to_skill(
            doc_id,
            payload,
            folder=repo_folder,
            stage=existing.get("stage", "production"),
            publish=publish,
        )

    async def list_versions(self, skill_code: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"skill_code": skill_code, "deleted_at": None},
        ).sort("version_num", -1)
        return [self._serialize(doc) async for doc in cursor]

    async def rollback(self, skill_code: str, target_version_num: int) -> Dict[str, Any]:
        """将线上版本回滚到指定历史版本（直接重新发布该版本文档）。"""
        from bson import ObjectId

        target = await self.collection.find_one(
            {
                "skill_code": skill_code,
                "version_num": target_version_num,
                "deleted_at": None,
            }
        )
        if not target:
            raise ValueError(f"版本 v{target_version_num} 不存在")

        published = await self.get_published(skill_code)
        if published and published.get("version_num") == target_version_num:
            return published

        now = datetime.utcnow()
        await self.collection.update_many(
            {"skill_code": skill_code, "status": "published"},
            {"$set": {"status": "archived", "updated_at": now}},
        )
        await self.collection.update_one(
            {"_id": ObjectId(target["_id"])},
            {"$set": {"status": "published", "published_at": now, "updated_at": now}},
        )
        logger.info(
            "回滚 Skill %s 到 v%s（原线上 v%s）",
            skill_code,
            target_version_num,
            (published or {}).get("version_num"),
        )
        return self._serialize(target)

    async def get_publish_compare(self, doc_id: str) -> Dict[str, Any]:
        from app.core.drama.skill_diff import compare_skill_texts

        draft = await self.get_by_id(doc_id)
        if not draft:
            raise ValueError("Skill 不存在")

        published = await self.get_published(draft["skill_code"])
        draft_content = draft.get("skill_content_md") or draft.get("system_markdown") or ""
        published_content = ""
        if published:
            published_content = published.get("skill_content_md") or published.get("system_markdown") or ""

        diff = compare_skill_texts(
            published_content,
            draft_content,
            from_label=f"线上 {published.get('version')}" if published else "线上（无）",
            to_label=f"草稿 {draft.get('version')}",
        )
        return {
            "skill_code": draft["skill_code"],
            "draft_id": draft["id"],
            "draft_version": draft.get("version"),
            "draft_status": draft.get("status"),
            "published_id": published.get("id") if published else None,
            "published_version": published.get("version") if published else None,
            "has_published": bool(published),
            "draft_content": draft_content,
            "published_content": published_content,
            **diff,
        }

    async def get_content_template(self, **kwargs) -> str:
        from app.core.drama.skill_spec import skill_spec_template

        return skill_spec_template(**kwargs)

    async def ensure_builtin_skills_seeded(self) -> int:
        """内置 markdown 种子 Skill（intake / concept / character / scene / storyboard / production）。"""
        from app.core.drama.skill_spec import load_repo_skill

        def _load_repo_seed(
            folder: str,
            *,
            stage: str,
            description: str = "",
            output_schema_id: str = "",
            default_knowledge_tags: Optional[List[str]] = None,
            user_markdown: str = "",
        ) -> Dict[str, Any]:
            try:
                seed = load_repo_skill(folder)
                seed["stage"] = stage
                if description:
                    seed["description"] = description
                if output_schema_id:
                    seed["output_schema_id"] = output_schema_id
                if default_knowledge_tags:
                    seed["default_knowledge_tags"] = default_knowledge_tags
                if user_markdown:
                    seed["user_markdown"] = user_markdown
                return seed
            except (ValueError, OSError) as e:
                logger.warning("%s repo load failed, skip seed: %s", folder, e)
                return {}

        intake_seed = _load_repo_seed(
            "skill_intake",
            stage="init",
            description="结构化立项问诊 → 项目 Brief JSON",
            output_schema_id="schemas/project_brief.v2.json",
            default_knowledge_tags=["short_drama", "brief", "intake"],
            user_markdown=(
                "## 用户输入\n{{message}}\n\n"
                "## 已有项目字段（可选）\n{{project}}\n\n"
                "请严格按 SKILL 四步执行：intake_analysis → brief → next_questions → status。"
                "先输出 JSON，再附 Markdown 摘要；一次最多追问 3 项。"
            ),
        )
        concept_seed = _load_repo_seed(
            "skill_concept",
            stage="concept",
            description="3~5 故事方向比选 + 六维评分 + 推荐",
            output_schema_id="schemas/story_directions.v2.json",
            default_knowledge_tags=["short_drama", "genre", "concept"],
                user_markdown=(
                    "## 项目 Brief\n{{project}}\n\n"
                    "## 绑定风格（可选）\n{{style}}\n\n"
                    "## 用户本轮要求\n{{message}}\n\n"
                    "请按 SKILL 子步骤执行：3A 风格包九项 → 3B 选定深化 → 3C 定稿方向+剧本大纲。"
                    "引用 Tool 知识做创意融合；禁止 JSON。"
                ),
        )
        character_seed = _load_repo_seed(
            "skill_character",
            stage="character",
            description="三步流水线：角色设计 → 定妆图（单视角）→ 角色卡（16:9）",
            output_schema_id="schemas/character_card.v2.json",
            default_knowledge_tags=["anime", "aigc", "character_design"],
            user_markdown=(
                "## 绑定风格（风格准备）\n{{style}}\n\n"
                "## 角色描述 / 剧本\n{{message}}\n\n"
                "## 项目（可选）\n{{project}}\n\n"
                "请严格按 SKILL 执行：风格准备 → 三步设定 Markdown → "
                "look-prompt / card-prompt（主力生图 prompt）→ character-image-tasks JSON（尺寸与负向）。"
            ),
        )
        scene_seed = _load_repo_seed(
            "skill_scene",
            stage="scene",
            description="前置收集剧本与角色 → 知识融合 → 风格准备 → 场景清单 → 场景卡 → scene-prompt",
            output_schema_id="schemas/scene_card.v2.json",
            default_knowledge_tags=["composition", "color", "lighting", "blocking", "short_drama"],
            user_markdown=(
                "## 绑定风格（风格准备）\n{{style}}\n\n"
                "## 剧本 / 场次\n{{message}}\n\n"
                "## 项目与角色（可选）\n{{project}}\n\n"
                "请严格按 SKILL 执行：前置收集 → 知识融合 → 风格准备 → 场景清单 → "
                "单场景 scene_design + scene_card → 场景 locked 后输出 scene-prompt + scene-grid-prompt "
                "→ scene-image-tasks（scene_master 一键生图 + scene_grid_6 六宫格多角度）。"
            ),
        )

        storyboard_seed = _load_repo_seed(
            "skill_storyboard",
            stage="storyboard",
            description="剧本+角色+场景+风格 → 知识融合 → 分镜规划 → 镜头表 Shot[]",
            output_schema_id="schemas/shot_list.v2.json",
            default_knowledge_tags=[
                "shot_size",
                "camera_movement",
                "film_grammar",
                "platform",
                "ai_video",
            ],
            user_markdown=(
                "## 绑定风格（camera_defaults / 画幅）\n{{style}}\n\n"
                "## 剧本 / 拆镜范围\n{{message}}\n\n"
                "## 项目 · 角色 · 场景（可选）\n{{project}}\n\n"
                "请严格按 SKILL 执行：前置收集 → 知识融合 → 分镜规划 → "
                "Markdown 镜头表（镜号/时长/景别/运镜/画面描述）→ 用户确认后 status=confirmed；"
                "仅当用户要求关键帧出图时输出 shot-prompt + shot-image-tasks。"
            ),
        )
        production_seed = _load_repo_seed(
            "skill_production",
            stage="production",
            description="反拖沓子步骤：章节×格号 → image/video prompt → production-tasks 一键出图出视频",
            output_schema_id="schemas/production_grid.v2.json",
            default_knowledge_tags=[
                "ai_video",
                "shot_size",
                "camera_movement",
                "platform",
                "lighting",
                "color",
            ],
            user_markdown=(
                "## 绑定风格\n{{style}}\n\n"
                "## 生产需求 / 当前格位\n{{message}}\n\n"
                "## 项目 · 剧本 · 场景 · 分镜（可选）\n{{project}}\n\n"
                "请严格按 SKILL 子步骤：P0 盘点 → P1 章节规划（时长+格数）→ P2 单格生产包 "
                "（image-prompt + video-prompt + production-tasks）。每轮只一步，禁止拖沓重复。"
            ),
        )

        seeds = [
            s
            for s in (
                intake_seed,
                concept_seed,
                character_seed,
                scene_seed,
                storyboard_seed,
                production_seed,
            )
            if s.get("skill_code")
        ]
        inserted = 0
        for seed in seeds:
            if await self.get_published(seed["skill_code"]):
                continue
            doc = await self.create(seed)
            await self.publish(doc["id"])
            inserted += 1
        return inserted


_drama_skill_service: Optional[DramaSkillService] = None


def get_drama_skill_service() -> DramaSkillService:
    global _drama_skill_service
    if _drama_skill_service is None:
        _drama_skill_service = DramaSkillService()
    return _drama_skill_service
