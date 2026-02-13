@echo off
chcp 65001 >nul
echo ========================================
echo   kabu 前端开发服务启动中...
echo ========================================
echo.

cd /d %~dp0frontend

echo 前端地址: http://localhost:5173
echo 按 Ctrl+C 停止服务
echo.

call npm run dev
