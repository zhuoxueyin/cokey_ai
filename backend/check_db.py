import os
os.environ['PYTHONPATH'] = '.'

from app.core.config import settings
import motor.motor_asyncio
import asyncio

async def check():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    col = db['channels']
    async for doc in col.find():
        print("=== " + doc['channel_code'] + " ===")
        auth = doc.get('auth_config', {})
        print("auth_config type:", type(auth))
        print("auth_config repr:", repr(auth)[:200])
        if isinstance(auth, dict):
            print("auth_config keys:", list(auth.keys()))
            if 'api_key' in auth:
                val = auth['api_key']
                print("api_key type:", type(val))
                if val and not val.startswith('your-'):
                    print("api_key: SET (len=" + str(len(val)) + ")")
                else:
                    print("api_key: NOT SET or PLACEHOLDER")
        print()

asyncio.run(check())
