@echo off
chcp 65001 >nul
echo ===================================
echo   Fmt this Shit 启动中...
echo ===================================
echo.

REM 1. 检查 Python 虚拟环境
if not exist .venv (
    echo [1/5] 创建 Python 虚拟环境...
    python -m venv .venv
) else (
    echo [1/5] Python 虚拟环境已存在
)

REM 2. 激活虚拟环境并安装依赖
echo [2/5] 检查 Python 依赖...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt

REM 3. 检查 Pandoc
if not exist pandoc\pandoc.exe (
    echo [3/5] 警告: 未找到 pandoc.exe
    echo       请从 https://pandoc.org/installing.html 下载 Windows 便携版
    echo       解压到项目的 pandoc/ 目录
    echo.
    pause
    exit
) else (
    echo [3/5] Pandoc 已就绪
)

REM 4. 检查 mermaid-cli
if not exist node_modules\.bin\mmdc.cmd (
    echo [4/5] 安装 mermaid-cli...
    call npm install @mermaid-js/mermaid-cli
) else (
    echo [4/5] mermaid-cli 已就绪
)

REM 5. 启动 Flask 服务
echo [5/5] 启动 Flask 服务...
echo.
echo ===================================
echo   服务地址: http://localhost:5678
echo   按 Ctrl+C 停止服务
echo ===================================
echo.

timeout /t 2 >nul
start http://localhost:5678
.venv\Scripts\python backend/app.py

pause
