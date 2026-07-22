@echo off
chcp 65001 >nul
title 建筑材料数据库 MaterialDB

echo ======================================
echo   建筑材料数据库 MaterialDB 启动脚本
echo ======================================
echo.

cd /d "%~dp0"

:: 检查 Python
python --version 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 检查依赖…
pip show flask qrcode >nul 2>&1
if errorlevel 1 (
    echo     安装 Flask 和 qrcode…
    pip install flask qrcode pillow -q
)

:: 初始化数据库
echo [2/3] 初始化数据库…
python init_db.py
if errorlevel 1 (
    echo [错误] 数据库初始化失败
    pause
    exit /b 1
)

:: 启动 API 服务
echo [3/3] 启动 API 服务…
echo.
echo 访问地址: http://localhost:5188
echo 按 Ctrl+C 停止服务
echo.
python api_server.py

pause
