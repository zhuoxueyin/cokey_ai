@echo off
chcp 65001 >nul
title AIGC Platform - Stop All
cd /d "%~dp0"

echo ========================================
echo   AIGC Platform - Stopping all services...
echo ========================================
echo.

python "%~dp0launcher.py" stop

echo.
timeout /t 5 /nobreak >nul
