@echo off
chcp 65001 >nul
title 可米幻工坊 - Frontend Log
cd /d "%~dp0"

echo ========================================
echo   可米幻工坊 - Frontend Log (tail)
echo ========================================
echo.

python "%~dp0launcher.py" log frontend

echo.
echo.
echo ========================================
echo   Full log: .runtime\frontend.log
echo ========================================
echo.
pause
