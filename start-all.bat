@echo off
chcp 65001 >nul
echo ========================================
echo   AIGC 创作平台 - 一键启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] 启动后端服务 (新窗口)...
start "AIGC Backend" cmd /k "start-backend.bat"

echo [INFO] 等待后端启动...
timeout /t 10 /nobreak >nul

echo [INFO] 启动前端服务 (新窗口)...
start "AIGC Frontend" cmd /k "start-frontend.bat"

echo.
echo [完成] 服务已启动！
echo   - 后端 API:  http://localhost:8000
echo   - 前端界面:  http://localhost:3000
echo   - API文档:   http://localhost:8000/docs
echo.
pause
