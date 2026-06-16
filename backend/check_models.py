import os
os.environ['PYTHONPATH'] = '.'

from app.core.config import settings
import motor.motor_asyncio
import asyncio

async def check():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    col = db['models']
    async for doc in col.find():
        print("=== " + doc.get('model_code', 'unknown') + " ===")
        print("model_name:", doc.get('model_name'))
        print("category:", doc.get('category'))
        print("status:", doc.get('status'))
        print("channel_bindings:", doc.get('channel_bindings', []))
        print()

asyncio.run(check())
