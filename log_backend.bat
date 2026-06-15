@echo off
chcp 65001 >nul
title AIGC Platform - Backend Log
cd /d "%~dp0"

echo ========================================
echo   AIGC Platform - Backend Log (tail)
echo ========================================
echo.

python "%~dp0launcher.py" log backend

echo.
echo.
echo ========================================
echo   Full log: .runtime\backend.log
echo ========================================
echo.
pause
