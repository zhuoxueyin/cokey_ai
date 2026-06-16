import os
os.environ['PYTHONPATH'] = '.'

import asyncio
from app.core.database import init_mongodb
from app.services.gateway_service import get_model_gateway

async def test_gateway():
    await init_mongodb()
    
    gateway = get_model_gateway()
    
    print("=== 测试 gpt-5.5 文本生成 ===")
    result = await gateway.execute(
        model_code="gpt-5.5",
        category="text",
        params={"prompt": "你好，这是一个测试"}
    )
    
    print("结果:", result)
    print("success:", result.get("success"))
    if "error_message" in result:
        print("错误信息:", result.get("error_message"))

if __name__ == "__main__":
    asyncio.run(test_gateway())
