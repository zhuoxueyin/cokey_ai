@echo off
chcp 65001 >nul
title AIGC Platform - Frontend Log
cd /d "%~dp0"

echo ========================================
echo   AIGC Platform - Frontend Log (tail)
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
