import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["PYTHONPATH"] = BACKEND_DIR

import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("  AIGC Platform - Backend Server")
    print("  API Base   : http://localhost:8000/api")
    print("  Health     : http://localhost:8000/api/health")
    print("  API Docs   : http://localhost:8000/docs")
    print("=" * 50)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        timeout_keep_alive=1800,  # 保持连接超时（秒）- 支持视频生成的长轮询（30分钟）
    )
