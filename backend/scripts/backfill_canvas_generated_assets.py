"""将历史画布节点成功生图/生视频结果补写入 assets 集合（source_type=generated）。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, get_collection, init_mongodb
from app.services.asset_service import register_generated_assets_from_result


async def backfill(*, dry_run: bool = False) -> dict:
    await init_mongodb()
    nodes = get_collection("canvas_nodes")
    cursor = nodes.find(
        {
            "node_type": {"$in": ["image", "video"]},
            "status": "success",
            "result": {"$exists": True, "$ne": None},
        },
        {"node_id": 1, "project_id": 1, "node_type": 1, "result": 1, "task_id": 1},
    )

    scanned = 0
    registered = 0
    skipped = 0

    async for node in cursor:
        scanned += 1
        result = node.get("result") or {}
        task_id = node.get("task_id") or f"canvas_{node.get('project_id')}_{node.get('node_id')}"
        category = "video" if node.get("node_type") == "video" else "image"

        imgs = result.get("images") or []
        vids = result.get("videos") or []
        if not imgs and not vids:
            skipped += 1
            continue

        if dry_run:
            registered += len(imgs) + len(vids)
            continue

        count = await register_generated_assets_from_result(
            result,
            task_id=task_id,
            category=category,
            skip_existing=True,
        )
        if count:
            registered += count
        else:
            skipped += 1

    await close_mongodb()
    return {"scanned": scanned, "registered": registered, "skipped": skipped, "dry_run": dry_run}


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    stats = asyncio.run(backfill(dry_run=dry_run))
    print(
        f"scanned={stats['scanned']} registered={stats['registered']} "
        f"skipped={stats['skipped']} dry_run={stats['dry_run']}"
    )


if __name__ == "__main__":
    main()
