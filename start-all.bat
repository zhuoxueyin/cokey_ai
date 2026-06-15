@echo off
chcp 65001 >nul
title AIGC Platform - Start All
cd /d "%~dp0"

echo ========================================
echo   AIGC Platform - Starting all services...
echo ========================================
echo.

python "%~dp0launcher.py" start

if errorlevel 1 (
    echo.
    echo [ERROR] Service start failed. Please check the output above.
)

echo.
timeout /t 10 /nobreak >nul
