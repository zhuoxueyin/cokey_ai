@echo off
chcp 65001 >nul
title 可米幻工坊 - Stop All
cd /d "%~dp0"

echo ========================================
echo   可米幻工坊 - Stopping all services...
echo ========================================
echo.

python "%~dp0launcher.py" stop

echo.
timeout /t 5 /nobreak >nul
