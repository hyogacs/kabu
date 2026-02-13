@echo off
chcp 65001 >nul
echo ========================================
echo   kabu 后端服务启动中...
echo ========================================
echo.

cd /d %~dp0backend
call venv\Scripts\activate.bat

echo 后端地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
