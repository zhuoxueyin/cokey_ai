@echo off
chcp 65001 >nul
echo ========================================
echo   AIGC 创作平台 - 前端启动脚本
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] 安装依赖...
    npm install
)

echo.
echo [INFO] 启动前端开发服务器 (http://localhost:3000)...
npm run dev

pause
