"""批量写入风格广场全部 preset 的 style_description_md（并同步 model_prompts / visual）。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import (
    SKIP_STYLE_IDS,
    get_style_description_md,
)
from app.services.drama_style_service import get_drama_style_service


async def upsert_all(*, dry_run: bool = False) -> list[dict]:
    await init_mongodb()
    svc = get_drama_style_service()
    results: list[dict] = []

    items, total = await svc.list(page=1, page_size=500, status="published")
    if total > len(items):
        items, _ = await svc.list(page=1, page_size=total, status="published")

    for doc in items:
        style_id = doc["style_id"]
        name = doc.get("name") or style_id
        render_class = doc.get("render_class") or "live_action"
        tags = doc.get("genre_tags") or []

        if style_id in SKIP_STYLE_IDS:
            results.append(
                {"style_id": style_id, "name": name, "action": "skipped", "reason": "已有优质描述"}
            )
            continue

        md = get_style_description_md(style_id, name, render_class, tags)
        if not md:
            results.append(
                {"style_id": style_id, "name": name, "action": "missing", "reason": "catalog 无内容"}
            )
            continue

        if dry_run:
            results.append({"style_id": style_id, "name": name, "action": "dry_run", "md_len": len(md)})
            continue

        updated = await svc.update(style_id, {"style_description_md": md})
        if not updated:
            results.append({"style_id": style_id, "name": name, "action": "not_found"})
            continue

        try:
            await svc.publish(style_id)
            status = "published"
        except ValueError as e:
            status = f"updated_draft: {e}"

        mp = updated.get("model_prompts") or {}
        results.append(
            {
                "style_id": style_id,
                "name": name,
                "action": "updated",
                "status": status,
                "md_len": len(md),
                "has_image_prompt": bool(mp.get("image_positive_en")),
            }
        )

    await close_mongodb()
    return results


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    results = asyncio.run(upsert_all(dry_run=dry_run))
    updated = sum(1 for r in results if r.get("action") == "updated")
    skipped = sum(1 for r in results if r.get("action") == "skipped")
    missing = sum(1 for r in results if r.get("action") == "missing")
    print(f"total={len(results)} updated={updated} skipped={skipped} missing={missing} dry_run={dry_run}")
    for r in results:
        if r.get("action") in ("missing", "not_found"):
            print(f"  [!] {r['style_id']} · {r.get('reason', r['action'])}")
        elif r.get("action") == "updated":
            print(f"  [ok] {r['style_id']} · {r['name']} ({r.get('md_len')} chars)")


if __name__ == "__main__":
    main()
