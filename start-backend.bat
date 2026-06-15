@echo off
chcp 65001 >nul
title AIGC Backend - Port 8000
echo ========================================
echo   AIGC Platform - Backend
echo ========================================
echo.

cd /d "%~dp0backend"

if not exist ".venv" (
    echo [INFO] First launch: creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Please ensure Python is installed.
        pause
        exit /b 1
    )
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

if not exist ".venv\Lib\site-packages\fastapi" (
    echo [INFO] First launch: installing dependencies (this may take a few minutes)...
    pip install -r requirements.txt
)

if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env
    echo [INFO] Please edit backend\.env and fill in your config if needed.
)

echo.
echo [INFO] Starting backend on http://localhost:8000
echo [INFO] API docs: http://localhost:8000/docs
echo.
python run_server.py

echo.
echo [INFO] Backend stopped.
pause
