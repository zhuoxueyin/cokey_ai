"""知识库轻量化向量存储与检索（Mongo + 本地 Hash Embedding，无外部向量库依赖）。"""
from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger

logger = get_logger()

EMBEDDING_MODEL = "hash-v1"
EMBEDDING_DIMS = 384
MAX_EMBED_CHARS = 12000


def _tokenize_for_embed(text: str) -> List[str]:
    raw = (text or "").strip().lower()
    if not raw:
        return []
    tokens: List[str] = []
    for m in re.finditer(r"[a-z0-9_]{2,}", raw):
        tokens.append(m.group(0))
    for m in re.finditer(r"[\u4e00-\u9fff]{1,8}", raw):
        seg = m.group(0)
        tokens.append(seg)
        if len(seg) >= 3:
            for i in range(len(seg) - 1):
                tokens.append(seg[i:i + 2])
    return tokens


def embed_text(text: str, dims: int = EMBEDDING_DIMS) -> List[float]:
    """确定性 Hash Embedding（轻量、无模型依赖）。"""
    vec = [0.0] * dims
    tokens = _tokenize_for_embed(text[:MAX_EMBED_CHARS])
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        h = int(digest, 16)
        idx = h % dims
        sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def build_entry_embed_text(doc: Dict[str, Any]) -> str:
    parts = [
        str(doc.get("title") or ""),
        " ".join(str(t) for t in (doc.get("tags") or [])),
        str(doc.get("summary") or ""),
        str(doc.get("content_markdown") or "")[:8000],
    ]
    return "\n".join(p for p in parts if p.strip())


class KnowledgeVectorService:
    COLLECTION = "drama_knowledge_vectors"

    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            from app.core.database import get_collection
            self._collection = get_collection(self.COLLECTION)
        return self._collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("entry_id", unique=True, name="uniq_entry_id")
        await self.collection.create_index("category", name="idx_category")
        await self.collection.create_index("status", name="idx_status")

    async def upsert_entry_vector(self, doc: Dict[str, Any]) -> None:
        entry_id = str(doc.get("entry_id") or "")
        if not entry_id:
            return
        text = build_entry_embed_text(doc)
        vector = embed_text(text)
        now = datetime.utcnow()
        await self.collection.update_one(
            {"entry_id": entry_id},
            {
                "$set": {
                    "entry_id": entry_id,
                    "category": doc.get("category"),
                    "status": doc.get("status"),
                    "model": EMBEDDING_MODEL,
                    "dims": EMBEDDING_DIMS,
                    "vector": vector,
                    "updated_at": now,
                }
            },
            upsert=True,
        )

    async def delete_entry_vector(self, entry_id: str) -> None:
        await self.collection.delete_one({"entry_id": entry_id})

    async def search_similar(
        self,
        query: str,
        *,
        categories: Optional[List[str]] = None,
        status: str = "published",
        top_k: int = 20,
    ) -> List[Tuple[float, str]]:
        """返回 (similarity, entry_id) 列表。"""
        query_vec = embed_text(query)
        mongo_query: Dict[str, Any] = {"status": status}
        cat_list = [c for c in (categories or []) if c]
        if cat_list:
            mongo_query["category"] = {"$in": cat_list}

        scored: List[Tuple[float, str]] = []
        cursor = self.collection.find(mongo_query, {"entry_id": 1, "vector": 1})
        async for row in cursor:
            vec = row.get("vector") or []
            sim = cosine_similarity(query_vec, vec)
            if sim > 0:
                scored.append((sim, str(row.get("entry_id"))))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    async def reindex_all(self, entries: List[Dict[str, Any]]) -> int:
        count = 0
        for doc in entries:
            if doc.get("deleted_at"):
                await self.delete_entry_vector(str(doc.get("entry_id")))
                continue
            await self.upsert_entry_vector(doc)
            count += 1
        return count


_vector_service: Optional[KnowledgeVectorService] = None


def get_knowledge_vector_service() -> KnowledgeVectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = KnowledgeVectorService()
    return _vector_service
