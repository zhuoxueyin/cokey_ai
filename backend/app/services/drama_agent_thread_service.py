"""超级智能体线程与消息持久化。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger

logger = get_logger()


class DramaAgentThreadService:
    THREADS = "drama_agent_threads"
    MESSAGES = "drama_agent_messages"

    def __init__(self):
        self._threads = None
        self._messages = None

    @property
    def threads(self):
        if self._threads is None:
            from app.core.database import get_collection
            self._threads = get_collection(self.THREADS)
        return self._threads

    @property
    def messages(self):
        if self._messages is None:
            from app.core.database import get_collection
            self._messages = get_collection(self.MESSAGES)
        return self._messages

    async def _ensure_index(self, collection, keys, *, name: str, **kwargs) -> None:
        from pymongo.errors import OperationFailure

        try:
            await collection.create_index(keys, name=name, **kwargs)
        except OperationFailure as e:
            if e.code != 86:
                raise
            logger.warning(f"索引 {name} 规格冲突，尝试重建: {e.details.get('errmsg', e)}")
            try:
                await collection.drop_index(name)
            except Exception:
                pass
            legacy = f"{keys}_1" if isinstance(keys, str) else None
            if legacy:
                try:
                    await collection.drop_index(legacy)
                except Exception:
                    pass
            await collection.create_index(keys, name=name, **kwargs)

    async def ensure_indexes(self) -> None:
        await self._ensure_index(self.threads, "thread_id", name="uniq_thread_id", unique=True)
        await self._ensure_index(self.threads, "user_id", name="idx_thread_user_id")
        await self._ensure_index(self.threads, "project_id", name="idx_thread_project_id")
        await self._ensure_index(
            self.threads,
            "canvas_project_id",
            name="uniq_canvas_project_id_sparse",
            unique=True,
            sparse=True,
        )
        await self._ensure_index(
            self.messages,
            [("thread_id", 1), ("created_at", 1)],
            name="idx_thread_messages_created",
        )
        from app.core.database import get_collection
        canvas_projects = get_collection("canvas_projects")
        await self._ensure_index(
            canvas_projects,
            "agent_thread_id",
            name="uniq_agent_thread_id_sparse",
            unique=True,
            sparse=True,
        )

    def _ser(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        for f in ("created_at", "updated_at"):
            if doc.get(f):
                out[f] = doc[f].isoformat() + "Z"
        return out

    async def create_thread(self, data: Dict[str, Any]) -> Dict[str, Any]:
        canvas_id = data.get("canvas_project_id")
        if canvas_id:
            existing = await self.get_thread_by_canvas(canvas_id)
            if existing:
                return existing

        now = datetime.utcnow()
        thread_id = f"dat_{uuid.uuid4().hex[:16]}"
        doc = {
            "thread_id": thread_id,
            "project_id": data.get("project_id"),
            "user_id": data.get("user_id"),
            "canvas_project_id": data.get("canvas_project_id"),
            "agent_mode": data.get("agent_mode", "creative_short_drama"),
            "model_code": data.get("model_code"),
            "style_preset_id": data.get("style_preset_id"),
            "multi_episode": bool(data.get("multi_episode", False)),
            "stage": data.get("stage", "concept"),
            "title": data.get("title") or "未命名创作",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        r = await self.threads.insert_one(doc)
        doc["_id"] = r.inserted_id
        if canvas_id:
            from app.services.canvas_service import get_canvas_service

            await get_canvas_service().bind_agent_thread(str(canvas_id), thread_id)
        return self._ser(doc)

    async def get_thread(
        self,
        thread_id: str,
        *,
        resolve_canvas: bool = True,
    ) -> Optional[Dict[str, Any]]:
        doc = await self.threads.find_one({"thread_id": thread_id, "status": {"$ne": "deleted"}})
        if not doc:
            return None
        thread = self._ser(doc)
        if resolve_canvas:
            thread = await self._resolve_canvas_binding(thread)
        return thread

    async def _resolve_canvas_binding(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        """thread 无 canvas_project_id 时，按画布 agent_thread_id 反查并补全绑定。"""
        bound = (thread.get("canvas_project_id") or "").strip()
        if bound:
            return thread
        tid = (thread.get("thread_id") or "").strip()
        if not tid:
            return thread
        from app.services.canvas_service import get_canvas_service

        proj = await get_canvas_service().get_project_by_agent_thread(tid)
        if not proj:
            return thread
        pid = proj["project_id"]
        now = datetime.utcnow()
        await self.threads.update_one(
            {"thread_id": tid},
            {"$set": {"canvas_project_id": pid, "updated_at": now}},
        )
        thread["canvas_project_id"] = pid
        return thread

    async def get_thread_by_canvas(self, canvas_project_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.threads.find_one(
            {
                "canvas_project_id": canvas_project_id,
                "status": {"$ne": "deleted"},
            },
            sort=[("updated_at", -1)],
        )
        return self._ser(doc) if doc else None

    async def _enrich_thread(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        ser = self._ser(doc) if "_id" in doc else dict(doc)
        tid = ser["thread_id"]
        ser["message_count"] = await self.messages.count_documents({"thread_id": tid})
        last = await self.messages.find_one({"thread_id": tid}, sort=[("created_at", -1)])
        if last:
            ser["last_message_at"] = last["created_at"].isoformat() + "Z"
            ser["last_message_preview"] = (last.get("content") or "")[:120]
        return ser

    async def list_threads(
        self,
        *,
        user_id: Optional[str] = None,
        standalone_only: bool = False,
        canvas_project_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {"status": {"$ne": "deleted"}}
        if user_id:
            query["user_id"] = user_id
        if canvas_project_id:
            query["canvas_project_id"] = canvas_project_id
        elif standalone_only:
            query["$or"] = [
                {"canvas_project_id": None},
                {"canvas_project_id": ""},
                {"canvas_project_id": {"$exists": False}},
            ]

        total = await self.threads.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self.threads.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = [await self._enrich_thread(d) async for d in cursor]
        return items, total

    async def delete_thread(self, thread_id: str) -> bool:
        r = await self.threads.update_one(
            {"thread_id": thread_id, "status": {"$ne": "deleted"}},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}},
        )
        return r.modified_count > 0

    async def bind_canvas(self, thread_id: str, canvas_project_id: str) -> Dict[str, Any]:
        """外部助手 → 画布：建立 thread ↔ canvas 1:1 强绑定。"""
        from app.services.canvas_service import get_canvas_service

        thread = await self.get_thread(thread_id, resolve_canvas=False)
        if not thread:
            raise ValueError("创作助手对话不存在")

        bound = (thread.get("canvas_project_id") or "").strip()
        if bound:
            if bound == canvas_project_id:
                return thread
            raise ValueError("该创作助手已绑定其他画布，无法重复创建")

        other = await self.get_thread_by_canvas(canvas_project_id)
        if other and other.get("thread_id") != thread_id:
            raise ValueError("该画布已绑定其他创作助手")

        now = datetime.utcnow()
        await self.threads.update_one(
            {"thread_id": thread_id},
            {"$set": {"canvas_project_id": canvas_project_id, "updated_at": now}},
        )
        await get_canvas_service().bind_agent_thread(canvas_project_id, thread_id)
        thread["canvas_project_id"] = canvas_project_id
        return thread

    async def update_thread(self, thread_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_count = await self.messages.count_documents({"thread_id": thread_id})
        if msg_count > 0 and "agent_mode" in data:
            data = {k: v for k, v in data.items() if k != "agent_mode"}
        allowed = {k: data[k] for k in data if k in (
            "stage", "model_code", "style_preset_id", "agent_mode", "multi_episode",
            "title", "canvas_project_id", "project_id",
        )}
        if not allowed:
            return await self.get_thread(thread_id)
        allowed["updated_at"] = datetime.utcnow()
        await self.threads.update_one({"thread_id": thread_id}, {"$set": allowed})
        return await self.get_thread(thread_id)

    async def list_messages(
        self,
        thread_id: str,
        limit: int = 50,
        *,
        tail: bool = True,
    ) -> List[Dict[str, Any]]:
        """列出消息。默认返回最近 limit 条（tail），避免长对话只拿到最早消息。"""
        if limit < 1:
            return []
        if tail:
            cursor = (
                self.messages.find({"thread_id": thread_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            docs = [d async for d in cursor]
            docs.reverse()
            return [self._ser(d) for d in docs]
        cursor = self.messages.find({"thread_id": thread_id}).sort("created_at", 1).limit(limit)
        return [self._ser(d) async for d in cursor]

    async def append_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        *,
        refs: Optional[List[Dict[str, Any]]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "message_id": f"msg_{uuid.uuid4().hex[:16]}",
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "refs": refs or [],
            "meta": meta or {},
            "created_at": now,
        }
        r = await self.messages.insert_one(doc)
        doc["_id"] = r.inserted_id
        await self.threads.update_one({"thread_id": thread_id}, {"$set": {"updated_at": now}})
        return self._ser(doc)

    async def get_recent_for_prompt(self, thread_id: str, max_turns: int = 20) -> List[Tuple[str, str]]:
        msgs = await self.list_messages(thread_id, limit=max_turns)
        out: List[Tuple[str, str]] = []
        for m in msgs:
            if m["role"] not in ("user", "assistant"):
                continue
            content = m.get("content") or ""
            refs = m.get("refs") or []
            if m["role"] == "user" and refs:
                urls = [(r.get("url") or "").strip() for r in refs if (r.get("url") or "").strip()]
                if urls:
                    suffix = f"\n[附带 {len(urls)} 张引用参考图: {', '.join(urls[:6])}]"
                    content = f"{content}{suffix}"
            out.append((m["role"], content))
        return out


_svc: Optional[DramaAgentThreadService] = None


def get_drama_agent_thread_service() -> DramaAgentThreadService:
    global _svc
    if _svc is None:
        _svc = DramaAgentThreadService()
    return _svc
