@echo off
chcp 65001 >nul
title AIGC Frontend - Port 3001
echo ========================================
echo   AIGC Platform - Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] First launch: installing dependencies (this may take a few minutes)...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Please ensure Node.js is installed.
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting frontend on http://localhost:3001
echo.
call npm run dev

echo.
echo [INFO] Frontend stopped.
pause
