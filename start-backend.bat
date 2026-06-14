@echo off
chcp 65001 >nul
echo ========================================
echo   AIGC 创作平台 - 后端启动脚本
echo ========================================
echo.

cd /d "%~dp0backend"

if not exist ".venv" (
    echo [INFO] 创建虚拟环境...
    python -m venv .venv
)

echo [INFO] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [INFO] 安装依赖...
pip install -r requirements.txt

if not exist ".env" (
    echo [INFO] 创建配置文件...
    copy .env.example .env
    echo [提示] 请编辑 .env 文件，填入正确的配置信息
)

echo.
echo [INFO] 初始化数据库种子数据...
python scripts/seed_data.py

echo.
echo [INFO] 启动后端服务 (http://localhost:8000)...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
