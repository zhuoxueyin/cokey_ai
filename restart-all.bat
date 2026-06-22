@echo off
chcp 65001 >nul
title 可米幻工坊 - Restart All
cd /d "%~dp0"

echo ========================================
echo   可米幻工坊 - Restart All Services
echo ========================================
echo.

echo [STEP 1/3] 停止所有服务...
call stop-all.bat
timeout /t 2 /nobreak >nul

echo [STEP 2/3] 等待端口释放...
timeout /t 3 /nobreak >nul

echo [STEP 3/3] 启动所有服务...
call start-all.bat

exit
