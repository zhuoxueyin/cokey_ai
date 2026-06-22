import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["PYTHONPATH"] = BACKEND_DIR

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    port = settings.app_port
    print("=" * 50)
    print("  可米幻工坊 - Backend Server")
    print(f"  API Base   : http://localhost:{port}/api")
    print(f"  Health     : http://localhost:{port}/api/health")
    print(f"  API Docs   : http://localhost:{port}/docs")
    print("=" * 50)
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=port,
        log_level="info",
        reload=False,
        timeout_keep_alive=1800,  # 保持连接超时（秒）- 支持视频生成的长轮询（30分钟）
    )
