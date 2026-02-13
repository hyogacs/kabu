@echo off
chcp 65001 >nul
echo ========================================
echo   kabu 股票监控系统 - 环境构建
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 创建 Python 虚拟环境...
cd /d %~dp0backend
if not exist venv (
    python -m venv venv
)

echo [2/4] 安装后端依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt
call deactivate

echo [3/4] 安装前端依赖...
cd /d %~dp0frontend
call npm install

echo [4/4] 构建前端...
call npm run build

echo.
echo ========================================
echo   构建完成！
echo   启动后端: start-backend.bat
echo   启动前端: start-frontend.bat
echo ========================================
pause
