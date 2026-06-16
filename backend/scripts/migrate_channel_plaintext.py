"""
一次性数据迁移脚本：把 channels 表中 auth_config 的加密值解密后写回明文。
运行方式：cd backend && python scripts/migrate_channel_plaintext.py
仅需运行一次。
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_mongodb, get_db
from app.core.config import settings
from app.core.security import decrypt_string


def _looks_like_encrypted(value: str) -> bool:
    """
    判断是否是 Fernet 加密值（base64 编码）
    heuristics：非空字符串 + 能成功解密 + 解密后 != 原值
    """
    if not value or not isinstance(value, str):
        return False
    try:
        plain = decrypt_string(value, settings.encryption_key)
        return plain and plain != value
    except Exception:
        return False


def _try_decrypt(value: str) -> (bool, str):
    """返回 (是否是加密值, 解密后的值或原值)"""
    if not _looks_like_encrypted(value):
        return False, value
    try:
        plain = decrypt_string(value, settings.encryption_key)
        return True, plain
    except Exception:
        return False, value


async def main():
    await init_mongodb()
    db = get_db()
    channels_col = db["channels"]

    total = await channels_col.count_documents({})
    print(f"Total channels in DB: {total}")
    print("=" * 70)

    updated_count = 0
    unchanged_count = 0

    async for doc in channels_col.find({}):
        channel_code = doc.get("channel_code", "?")
        auth_config = doc.get("auth_config", {})

        print(f"\n[{channel_code}] {doc.get('channel_name', '')}")

        new_auth_config = {}
        doc_changed = False
        for key, value in auth_config.items():
            is_encrypted, plain_value = _try_decrypt(value)
            if is_encrypted:
                print(f"  - {key}: ENCRYPTED -> 解密后 ...{plain_value[-6:]} (len={len(plain_value)})")
                new_auth_config[key] = plain_value
                doc_changed = True
            else:
                display = (value[:12] + "...") if isinstance(value, str) and len(value) > 12 else str(value)
                print(f"  - {key}: PLAIN -> {display}")
                new_auth_config[key] = value

        if doc_changed:
            result = await channels_col.update_one(
                {"_id": doc["_id"]},
                {"$set": {"auth_config": new_auth_config}}
            )
            if result.modified_count > 0:
                print(f"  -> UPDATE OK")
                updated_count += 1
            else:
                print(f"  -> UPDATE FAILED (modified_count=0)")
        else:
            unchanged_count += 1
            print(f"  -> NO CHANGE")

    print("\n" + "=" * 70)
    print(f"Done. Updated={updated_count}, Unchanged={unchanged_count}, Total={total}")


if __name__ == "__main__":
    asyncio.run(main())
