@echo off
chcp 65001 >nul
title 可米幻工坊 - Status
cd /d "%~dp0"

echo ========================================
echo   可米幻工坊 - Service Status
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
