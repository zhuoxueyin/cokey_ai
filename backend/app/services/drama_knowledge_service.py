"""短剧知识库 CRUD + Mongo 文本检索。"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.drama.knowledge_categories import KNOWLEDGE_CATEGORIES
from app.core.drama.knowledge_keyword import extract_keywords, score_entry_keywords
from app.core.drama.knowledge_stage import (
    category_applies_to_stage,
    normalize_stage,
    validate_applicable_stages,
)
from app.core.logging_config import get_logger

logger = get_logger()


class DramaKnowledgeService:
    COLLECTION = "drama_knowledge"
    CATEGORY_COLLECTION = "drama_knowledge_categories"
    SUPPRESSED_CATEGORIES_KV = "category_suppressed_codes"

    def __init__(self):
        self._collection = None
        self._cat_collection = None

    @property
    def collection(self):
        if self._collection is None:
            from app.core.database import get_collection
            self._collection = get_collection(self.COLLECTION)
        return self._collection

    @property
    def cat_collection(self):
        if self._cat_collection is None:
            from app.core.database import get_collection
            self._cat_collection = get_collection(self.CATEGORY_COLLECTION)
        return self._cat_collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("entry_id", unique=True, name="uniq_entry_id")
        await self.collection.create_index("category", name="idx_category")
        await self.collection.create_index("domain", name="idx_domain")
        await self.collection.create_index("status", name="idx_status")
        await self.collection.create_index(
            [("title", "text"), ("summary", "text"), ("content_markdown", "text"), ("tags", "text")],
            name="text_search",
        )
        await self.cat_collection.create_index("code", unique=True, name="uniq_category_code")
        from app.services.knowledge_vector_service import get_knowledge_vector_service

        await get_knowledge_vector_service().ensure_indexes()

    async def ensure_categories_seeded(self) -> int:
        inserted = 0
        now = datetime.utcnow()
        suppressed = await self._get_suppressed_category_codes()
        for cat in KNOWLEDGE_CATEGORIES:
            if cat["code"] in suppressed:
                continue
            existing = await self.cat_collection.find_one({"code": cat["code"]})
            if existing:
                # 同步内置分类的适用阶段等种子字段
                patch: Dict[str, Any] = {}
                if cat.get("applicable_stages") is not None:
                    patch["applicable_stages"] = cat.get("applicable_stages") or []
                if cat.get("description"):
                    patch["description"] = cat["description"]
                if patch:
                    patch["updated_at"] = now
                    await self.cat_collection.update_one({"code": cat["code"]}, {"$set": patch})
                continue
            doc = {**cat, "created_at": now}
            if "applicable_stages" not in doc:
                doc["applicable_stages"] = []
            await self.cat_collection.insert_one(doc)
            inserted += 1
        return inserted

    async def list_category_codes_for_stage(self, stage: str) -> List[str]:
        """返回当前创作阶段适用的分类 code 列表。"""
        stage_norm = normalize_stage(stage)
        await self.ensure_categories_seeded()
        codes: List[str] = []
        async for doc in self.cat_collection.find().sort("code", 1):
            if category_applies_to_stage(doc, stage_norm):
                codes.append(str(doc["code"]))
        return codes

    @staticmethod
    def _is_builtin_category_code(code: str) -> bool:
        return any(c["code"] == code for c in KNOWLEDGE_CATEGORIES)

    async def _get_suppressed_category_codes(self) -> set[str]:
        from app.services.kv_service import get_kv_service

        raw = await get_kv_service().get_json(
            "drama_knowledge",
            self.SUPPRESSED_CATEGORIES_KV,
            default=[],
        )
        if not isinstance(raw, list):
            return set()
        return {str(x).strip() for x in raw if str(x).strip()}

    async def _suppress_builtin_category(self, code: str) -> None:
        from app.services.kv_service import get_kv_service

        codes = sorted(await self._get_suppressed_category_codes() | {code})
        await get_kv_service().set_json("drama_knowledge", self.SUPPRESSED_CATEGORIES_KV, codes)

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        for field in ("created_at", "updated_at", "published_at"):
            if doc.get(field):
                out[field] = doc[field].isoformat() + "Z"
        return out

    def _serialize_category(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        for field in ("created_at", "updated_at"):
            if doc.get(field):
                out[field] = doc[field].isoformat() + "Z"
        return out

    @staticmethod
    def _normalize_category_code(code: str) -> str:
        normalized = (code or "").strip().lower().replace("-", "_")
        if not re.match(r"^[a-z][a-z0-9_]{0,47}$", normalized):
            raise ValueError("分类 code 须以小写字母开头，仅含字母、数字、下划线")
        return normalized

    async def _category_entry_counts(self) -> Dict[str, int]:
        pipeline = [
            {"$match": {"deleted_at": None}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        ]
        counts: Dict[str, int] = {}
        async for row in self.collection.aggregate(pipeline):
            key = row.get("_id")
            if key:
                counts[str(key)] = int(row.get("count") or 0)
        return counts

    async def list_categories(self) -> List[Dict[str, Any]]:
        await self.ensure_categories_seeded()
        counts = await self._category_entry_counts()
        cursor = self.cat_collection.find().sort("code", 1)
        items: List[Dict[str, Any]] = []
        async for doc in cursor:
            ser = self._serialize_category(doc)
            ser["entry_count"] = counts.get(ser["code"], 0)
            items.append(ser)
        return items

    async def get_category(self, code: str) -> Optional[Dict[str, Any]]:
        doc = await self.cat_collection.find_one({"code": code})
        if not doc:
            return None
        ser = self._serialize_category(doc)
        ser["entry_count"] = await self.collection.count_documents(
            {"category": code, "deleted_at": None}
        )
        return ser

    async def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        code = self._normalize_category_code(data["code"])
        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("请填写分类名称")
        existing = await self.cat_collection.find_one({"code": code})
        if existing:
            raise ValueError(f"分类 code 已存在: {code}")
        now = datetime.utcnow()
        doc = {
            "code": code,
            "name": name,
            "description": (data.get("description") or "").strip(),
            "applicable_stages": validate_applicable_stages(data.get("applicable_stages")),
            "builtin": False,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.cat_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        ser = self._serialize_category(doc)
        ser["entry_count"] = 0
        return ser

    async def update_category(self, code: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = await self.cat_collection.find_one({"code": code})
        if not doc:
            return None
        updates: Dict[str, Any] = {}
        if data.get("name") is not None:
            name = str(data["name"]).strip()
            if not name:
                raise ValueError("分类名称不能为空")
            updates["name"] = name
        if data.get("description") is not None:
            updates["description"] = str(data["description"]).strip()
        if data.get("applicable_stages") is not None:
            updates["applicable_stages"] = validate_applicable_stages(data.get("applicable_stages"))
        if not updates:
            return await self.get_category(code)
        updates["updated_at"] = datetime.utcnow()
        await self.cat_collection.update_one({"code": code}, {"$set": updates})
        return await self.get_category(code)

    async def delete_category(self, code: str) -> bool:
        doc = await self.cat_collection.find_one({"code": code})
        if not doc:
            return False
        entry_count = await self.collection.count_documents({"category": code, "deleted_at": None})
        if entry_count > 0:
            raise ValueError(f"该分类下仍有 {entry_count} 条知识，请先迁移或删除后再删分类")
        if self._is_builtin_category_code(code):
            await self._suppress_builtin_category(code)
        result = await self.cat_collection.delete_one({"code": code})
        return result.deleted_count > 0

    async def list_tags(self, *, limit: int = 200) -> List[str]:
        """已使用过的标签（去重、按频次排序），供前端选择器推荐。"""
        pipeline = [
            {"$match": {"deleted_at": None, "tags": {"$exists": True, "$ne": []}}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": max(1, min(limit, 500))},
        ]
        tags: List[str] = []
        async for row in self.collection.aggregate(pipeline):
            tag = (row.get("_id") or "").strip()
            if tag:
                tags.append(tag)
        return tags

    async def get_by_entry_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"entry_id": entry_id, "deleted_at": None})
        return self._serialize(doc) if doc else None

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {"deleted_at": None}
        if category:
            query["category"] = category
        if domain:
            query["domain"] = domain
        if status:
            query["status"] = status
        if keyword:
            query["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"summary": {"$regex": keyword, "$options": "i"}},
                {"entry_id": {"$regex": keyword, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort("entry_id", 1).skip(skip).limit(page_size)
        return [self._serialize(d) async for d in cursor], total

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        entry_id = data.get("entry_id") or f"kb.{uuid.uuid4().hex[:12]}"
        if await self.collection.find_one({"entry_id": entry_id}):
            raise ValueError(f"entry_id 已存在: {entry_id}")

        doc = {
            "entry_id": entry_id,
            "category": data["category"],
            "domain": data.get("domain", ""),
            "tags": data.get("tags", []),
            "title": data["title"],
            "summary": data.get("summary", ""),
            "content_markdown": data.get("content_markdown", ""),
            "when_to_use": data.get("when_to_use", []),
            "when_to_avoid": data.get("when_to_avoid", []),
            "prompt_tokens_en": data.get("prompt_tokens_en", []),
            "related_entries": data.get("related_entries", []),
            "source": data.get("source", {"type": "manual"}),
            "version": 1,
            "status": data.get("status", "draft"),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        ser = self._serialize(doc)
        await self._sync_entry_vector(doc)
        return ser

    async def update(self, entry_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"entry_id": entry_id, "deleted_at": None})
        if not doc:
            return None
        update_data = {**data, "updated_at": datetime.utcnow(), "version": doc.get("version", 1) + 1}
        await self.collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
        updated = await self.get_by_entry_id(entry_id)
        if updated:
            await self._sync_entry_vector(
                await self.collection.find_one({"entry_id": entry_id, "deleted_at": None}) or {}
            )
        return updated

    async def _try_fetch_feishu(self, url: str) -> Dict[str, Any]:
        import re
        import httpx

        url = (url or "").strip()
        if not url:
            raise ValueError("飞书链接不能为空")
        if "feishu.cn" not in url and "larksuite.com" not in url:
            raise ValueError("请输入有效的飞书文档链接（feishu.cn / larksuite.com）")

        result: Dict[str, Any] = {"status": "partial", "title": "", "content_markdown": ""}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 CokeyKnowledgeBot/1.0"})
            if resp.status_code >= 400:
                result["status"] = "needs_manual"
                result["message"] = f"无法自动拉取（HTTP {resp.status_code}），请粘贴正文到编辑器"
                return result

            text = resp.text or ""
            title_match = re.search(
                r'<meta\s+property="og:title"\s+content="([^"]+)"',
                text,
                re.I,
            ) or re.search(r"<title>([^<]+)</title>", text, re.I)
            if title_match:
                result["title"] = title_match.group(1).strip()

            if text.lstrip().startswith("#") or "##" in text[:500]:
                result["content_markdown"] = text[:50000]
                result["status"] = "ok"
            else:
                result["status"] = "needs_manual"
                result["message"] = "已记录飞书链接；私有文档需手动粘贴正文到编辑器"
        except Exception as e:
            result["status"] = "needs_manual"
            result["message"] = f"拉取失败：{e}，请手动粘贴正文"
        return result

    async def preview_feishu(self, url: str) -> Dict[str, Any]:
        return await self._try_fetch_feishu(url)

    async def import_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        source_type = data.get("source_type", "manual")
        content = data.get("content_markdown", "") or ""
        title = (data.get("title") or "").strip()
        summary = data.get("summary", "") or ""
        feishu_url = (data.get("feishu_url") or "").strip()
        filename = (data.get("filename") or "").strip()
        import_meta: Dict[str, Any] = {"type": source_type}

        if source_type == "feishu":
            if not feishu_url:
                raise ValueError("请填写飞书文档链接")
            fetched = await self._try_fetch_feishu(feishu_url)
            import_meta["url"] = feishu_url
            import_meta["fetch_status"] = fetched.get("status")
            if fetched.get("message"):
                import_meta["message"] = fetched["message"]
            if not title and fetched.get("title"):
                title = fetched["title"]
            if not content and fetched.get("content_markdown"):
                content = fetched["content_markdown"]
            if not title:
                title = "飞书文档导入"
        elif source_type == "file":
            if not content.strip():
                raise ValueError("文件内容为空")
            import_meta["filename"] = filename or "upload.md"
            if not title:
                title = (filename or "本地文档").rsplit(".", 1)[0]
        else:
            import_meta["type"] = "manual"

        if not title:
            raise ValueError("请填写标题")
        if not content.strip() and source_type != "feishu":
            raise ValueError("请填写正文内容")

        doc = await self.create(
            {
                "category": data["category"],
                "title": title,
                "summary": summary,
                "content_markdown": content,
                "tags": data.get("tags", []),
                "source": import_meta,
            }
        )
        if data.get("publish"):
            doc = await self.publish(doc["entry_id"]) or doc
        doc["import_hint"] = import_meta.get("message")
        return doc

    async def publish(self, entry_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        await self.collection.update_one(
            {"entry_id": entry_id},
            {"$set": {"status": "published", "published_at": now, "updated_at": now}},
        )
        doc = await self.get_by_entry_id(entry_id)
        if doc:
            raw = await self.collection.find_one({"entry_id": entry_id, "deleted_at": None})
            if raw:
                await self._sync_entry_vector(raw)
        return doc

    async def soft_delete(self, entry_id: str) -> bool:
        result = await self.collection.update_one(
            {"entry_id": entry_id},
            {"$set": {"deleted_at": datetime.utcnow(), "status": "archived"}},
        )
        if result.modified_count > 0:
            from app.services.knowledge_vector_service import get_knowledge_vector_service

            await get_knowledge_vector_service().delete_entry_vector(entry_id)
        return result.modified_count > 0

    async def _sync_entry_vector(self, doc: Dict[str, Any]) -> None:
        from app.services.knowledge_vector_service import get_knowledge_vector_service

        if not doc or doc.get("deleted_at"):
            if doc and doc.get("entry_id"):
                await get_knowledge_vector_service().delete_entry_vector(str(doc["entry_id"]))
            return
        if doc.get("status") != "published":
            await get_knowledge_vector_service().delete_entry_vector(str(doc.get("entry_id") or ""))
            return
        await get_knowledge_vector_service().upsert_entry_vector(doc)

    async def reindex_vectors(self, *, status: Optional[str] = "published") -> int:
        """全量重建向量索引（管理端维护）。"""
        from app.services.knowledge_vector_service import get_knowledge_vector_service

        query: Dict[str, Any] = {"deleted_at": None}
        if status:
            query["status"] = status
        entries = [d async for d in self.collection.find(query)]
        return await get_knowledge_vector_service().reindex_all(entries)

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        categories: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 6,
        status: str = "published",
        stage: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """混合检索：阶段类目过滤 + 关键词多维匹配 + 向量相似度。"""
        from app.services.knowledge_vector_service import get_knowledge_vector_service

        mongo_query: Dict[str, Any] = {"deleted_at": None, "status": status}
        cat_list = [c for c in (categories or []) if c]
        if not cat_list and stage:
            cat_list = await self.list_category_codes_for_stage(stage)
        if cat_list:
            mongo_query["category"] = {"$in": cat_list}
        elif category:
            mongo_query["category"] = category
        if domains:
            mongo_query["domain"] = {"$in": domains}

        q = (query or "").strip()
        keywords = extract_keywords(q, max_keywords=10) if q else []

        # 候选集：类目下已发布条目（上限 400，避免全表扫描过大）
        candidate_limit = max(top_k * 20, 80)
        cursor = self.collection.find(mongo_query).sort("updated_at", -1).limit(candidate_limit)
        candidates = [d async for d in cursor]

        if not candidates and cat_list:
            # 阶段类目无条目时，不按类目限制浏览最近更新
            fallback_query = {k: v for k, v in mongo_query.items() if k != "category"}
            cursor = self.collection.find(fallback_query).sort("updated_at", -1).limit(candidate_limit)
            candidates = [d async for d in cursor]

        if not candidates:
            return []

        if not q:
            results: List[Dict[str, Any]] = []
            for doc in candidates[:top_k]:
                ser = self._serialize(doc)
                ser["snippet"] = ser.get("summary") or ser.get("title", "")
                ser["match_keywords"] = []
                ser["match_score"] = 0.0
                results.append(ser)
            return results

        keyword_scores: Dict[str, float] = {}
        max_kw = 0.0
        for doc in candidates:
            kw_score = score_entry_keywords(doc, keywords)
            eid = str(doc["entry_id"])
            keyword_scores[eid] = kw_score
            if kw_score > max_kw:
                max_kw = kw_score

        vector_svc = get_knowledge_vector_service()
        vector_hits = await vector_svc.search_similar(
            q,
            categories=cat_list or None,
            status=status,
            top_k=max(top_k * 3, 24),
        )
        vector_scores: Dict[str, float] = {eid: sim for sim, eid in vector_hits}
        max_vec = max(vector_scores.values()) if vector_scores else 0.0

        tag_set = set(tags or [])
        combined: List[tuple[float, Dict[str, Any], List[str]]] = []
        for doc in candidates:
            eid = str(doc["entry_id"])
            kw_raw = keyword_scores.get(eid, 0.0)
            vec_raw = vector_scores.get(eid, 0.0)
            kw_norm = (kw_raw / max_kw) if max_kw > 0 else 0.0
            vec_norm = (vec_raw / max_vec) if max_vec > 0 else 0.0
            score = 0.55 * kw_norm + 0.45 * vec_norm

            doc_tags = set(doc.get("tags") or [])
            if tag_set:
                overlap = len(tag_set & doc_tags) / max(len(tag_set), 1)
                score += overlap * 0.15

            matched_kw = [k for k in keywords if score_entry_keywords(doc, [k]) > 0]
            combined.append((score, doc, matched_kw))

        combined.sort(key=lambda x: x[0], reverse=True)
        results: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for score, doc, matched_kw in combined:
            eid = str(doc["entry_id"])
            if eid in seen or score <= 0:
                continue
            seen.add(eid)
            ser = self._serialize(doc)
            ser["snippet"] = ser.get("summary") or ser.get("title", "")
            ser["match_score"] = round(score, 4)
            ser["match_keywords"] = matched_kw[:10]
            results.append(ser)
            if len(results) >= top_k:
                break

        if not results and keywords:
            # 关键词零命中时回退正则宽匹配
            regex_candidates = await self._regex_search_candidates(mongo_query, q, top_k * 3)
            for doc in regex_candidates:
                eid = str(doc["entry_id"])
                if eid in seen:
                    continue
                ser = self._serialize(doc)
                ser["snippet"] = ser.get("summary") or ser.get("title", "")
                ser["match_keywords"] = keywords[:10]
                ser["match_score"] = 0.1
                results.append(ser)
                if len(results) >= top_k:
                    break

        return results

    @staticmethod
    def _extract_search_terms(query: str) -> List[str]:
        """中英文混合查询拆词，供正则回退。"""
        text = (query or "").strip()
        if not text:
            return []
        parts = re.split(r"[\s,，。！？；;、：:/\\|（）()【】\[\]「」\"'<>]+", text)
        terms: List[str] = []
        for part in parts:
            chunk = part.strip()
            if len(chunk) >= 2:
                terms.append(chunk)
        if len(text) <= 80:
            terms.insert(0, text)
        # 中文长句再拆 2~4 字滑窗，提升「动画短片」类词条命中率
        if re.search(r"[\u4e00-\u9fff]", text):
            for m in re.finditer(r"[\u4e00-\u9fff]{2,6}", text):
                terms.append(m.group(0))
        return list(dict.fromkeys(terms))[:12]

    async def _regex_search_candidates(
        self,
        mongo_query: Dict[str, Any],
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        terms = self._extract_search_terms(query)
        if not terms:
            return []
        or_clauses: List[Dict[str, Any]] = []
        for term in terms:
            regex = re.compile(re.escape(term), re.I)
            or_clauses.extend(
                [
                    {"title": regex},
                    {"summary": regex},
                    {"content_markdown": regex},
                    {"tags": regex},
                    {"domain": regex},
                ]
            )
        cursor = self.collection.find({**mongo_query, "$or": or_clauses}).limit(limit)
        return [d async for d in cursor]


_drama_knowledge_service: Optional[DramaKnowledgeService] = None


def get_drama_knowledge_service() -> DramaKnowledgeService:
    global _drama_knowledge_service
    if _drama_knowledge_service is None:
        _drama_knowledge_service = DramaKnowledgeService()
    return _drama_knowledge_service
