"""将指定写实/电影类风格 profile 写入 Mongo（style_description_md + publish）。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import get_style_description_md
from app.services.drama_style_service import get_drama_style_service

TARGET_STYLE_IDS = [
    "horror_film",
    "retro_war_film",
    "absurdist_high_key_white",
    "american_retro_weird",
    "retro_cinematography",
    "teal_orange_cinematic",
    "industrial_film",
    "hk_90s_film",
    "tech_cinematic",
    "suspense_film",
    "american_retro_film_tv",
    "greek_mythology_film",
    "purple_tone_cinematic",
]


async def upsert_targets(*, dry_run: bool = False) -> list[dict]:
    await init_mongodb()
    svc = get_drama_style_service()
    results: list[dict] = []

    for style_id in TARGET_STYLE_IDS:
        doc = await svc.get_by_style_id(style_id)
        if not doc:
            results.append({"style_id": style_id, "action": "not_found"})
            continue
        name = doc.get("name") or style_id
        render_class = doc.get("render_class") or "live_action"
        tags = doc.get("genre_tags") or []
        md = get_style_description_md(style_id, name, render_class, tags)
        if not md:
            results.append({"style_id": style_id, "name": name, "action": "missing_profile"})
            continue
        if dry_run:
            results.append({"style_id": style_id, "name": name, "action": "dry_run", "md_len": len(md)})
            continue
        updated = await svc.update(style_id, {"style_description_md": md})
        if not updated:
            results.append({"style_id": style_id, "name": name, "action": "update_failed"})
            continue
        try:
            await svc.publish(style_id)
            status = "published"
        except ValueError as e:
            status = f"updated_draft: {e}"
        results.append(
            {
                "style_id": style_id,
                "name": name,
                "action": "updated",
                "status": status,
                "md_len": len(md),
            }
        )

    await close_mongodb()
    return results


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    results = asyncio.run(upsert_targets(dry_run=dry_run))
    for r in results:
        print(r)
    ok = sum(1 for r in results if r.get("action") == "updated")
    print(f"done: {ok}/{len(TARGET_STYLE_IDS)} updated dry_run={dry_run}")


if __name__ == "__main__":
    main()
