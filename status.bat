@echo off
chcp 65001 >nul
title AIGC Platform - Status
cd /d "%~dp0"

echo ========================================
echo   AIGC Platform - Service Status
echo ========================================
echo.

python "%~dp0launcher.py" status

echo.
echo ========================================
echo   Backend log:  .runtime\backend.log
echo   Frontend log: .runtime\frontend.log
echo ========================================
echo.
pause
