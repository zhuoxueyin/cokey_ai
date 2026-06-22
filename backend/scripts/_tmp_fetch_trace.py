"""Temporary: fetch trace log by ID."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, get_collection, init_mongodb

TRACE = sys.argv[1] if len(sys.argv) > 1 else "trace_bc9166e45332494c97320c04aae8a562"


async def main() -> None:
    await init_mongodb()
    col = get_collection("trace_logs")
    doc = await col.find_one({"trace_id": TRACE})
    if not doc:
        doc = await col.find_one({"log_id": TRACE})
    if doc:
        doc.pop("_id", None)
        print(json.dumps(doc, default=str, ensure_ascii=False, indent=2))
    else:
        print("NOT_FOUND")
    await close_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
