"""迁移渠道配置到新格式：
1. 将分类专用的 api_key 合并为单个 api_key
2. 添加 api_config 配置（路径和流式响应）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["aigc_platform"]

print("=== Migrating channel config ===")

channels = list(db.channels.find())
for ch in channels:
    channel_code = ch["channel_code"]
    print(f"\nProcessing channel: {channel_code}")
    
    updates = {}
    
    # 1. Migrate auth_config - merge multiple api_keys into one
    auth_config = ch.get("auth_config", {})
    
    # Prefer new api_key format
    if "api_key" not in auth_config or not auth_config["api_key"]:
        # Migrate from old format
        api_key = auth_config.get("text_api_key", "") or \
                  auth_config.get("image_api_key", "") or \
                  auth_config.get("video_api_key", "")
        
        if api_key and not api_key.startswith("your-"):
            updates["auth_config"] = {"api_key": api_key}
            print(f"  [OK] Migrated auth_config: using text_api_key")
        else:
            updates["auth_config"] = {"api_key": ""}
            print(f"  [OK] Migrated auth_config: empty")
    
    # 2. Add api_config
    if "api_config" not in ch:
        updates["api_config"] = {
            "text_path": "/chat/completions",
            "image_path": "/images/generations",
            "video_path": "/videos/generations",
            "text_stream": True,
        }
        print(f"  [OK] Added api_config")
    
    if updates:
        result = db.channels.update_one(
            {"_id": ch["_id"]},
            {"$set": updates}
        )
        if result.modified_count > 0:
            print(f"  [OK] Updated")
        else:
            print(f"  [FAIL] Update failed")
    else:
        print(f"  [SKIP] No changes needed")

print("\n=== Migration complete ===")

# Verify results
print("\n=== Verification ===")
for ch in db.channels.find():
    auth = ch.get("auth_config", {})
    api = ch.get("api_config", {})
    has_api_key = bool(auth.get("api_key", ""))
    has_api_config = bool(api)
    key_status = "OK" if has_api_key else "NONE"
    config_status = "OK" if has_api_config else "NONE"
    print(f"{ch['channel_code']}: api_key={key_status}, api_config={config_status}")