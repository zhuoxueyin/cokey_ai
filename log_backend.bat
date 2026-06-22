@echo off
chcp 65001 >nul
title 可米幻工坊 - Backend Log
cd /d "%~dp0"

echo ========================================
echo   可米幻工坊 - Backend Log (tail)
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
