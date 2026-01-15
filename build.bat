@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===================================
echo   Fmt this Shit 便携包打包工具
echo ===================================
echo.

REM 获取版本号
set VERSION=%1
if "%VERSION%"=="" (
    set VERSION=1.0.0
)

echo 版本号: %VERSION%
echo.

REM 设置变量
set PROJECT_NAME=fmt-this-shit
set PACKAGE_NAME=%PROJECT_NAME%-portable-%VERSION%
set TEMP_DIR=%TEMP%\%PACKAGE_NAME%
set OUTPUT_DIR=%CD%\dist
set OUTPUT_FILE=%OUTPUT_DIR%\%PACKAGE_NAME%.zip

REM 清理旧文件
echo [1/6] 清理旧打包文件...
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
if exist "%OUTPUT_FILE%" del "%OUTPUT_FILE%"

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 创建临时目录
echo [2/6] 创建临时目录...
mkdir "%TEMP_DIR%"

REM 复制项目文件
echo [3/6] 复制项目文件...
xcopy /E /I /Y backend "%TEMP_DIR%\backend\" >nul
xcopy /E /I /Y frontend "%TEMP_DIR%\frontend\" >nul
xcopy /E /I /Y /EXCLUDE:build_exclude.txt docs "%TEMP_DIR%\docs\" 2>nul
copy /Y start.bat "%TEMP_DIR%\" >nul
copy /Y requirements.txt "%TEMP_DIR%\" >nul
copy /Y package.json "%TEMP_DIR%\" >nul
copy /Y README.md "%TEMP_DIR%\" >nul
copy /Y README.zh-CN.md "%TEMP_DIR%\" >nul
copy /Y LICENSE "%TEMP_DIR%\" >nul

REM 复制运行环境
echo [4/6] 复制运行环境...
if exist ".venv" (
    xcopy /E /I /Y .venv "%TEMP_DIR%\.venv\" >nul
    echo   - Python 虚拟环境已复制
) else (
    echo   - 警告: .venv 不存在，跳过
)

if exist "node_modules" (
    xcopy /E /I /Y node_modules "%TEMP_DIR%\node_modules\" >nul
    echo   - npm 依赖已复制
) else (
    echo   - 警告: node_modules 不存在，跳过
)

if exist "pandoc" (
    xcopy /E /I /Y pandoc "%TEMP_DIR%\pandoc\" >nul
    echo   - Pandoc 已复制
) else (
    echo   - 警告: pandoc 不存在，跳过
)

REM 清理不需要的文件
echo [5/6] 清理临时文件...
if exist "%TEMP_DIR%\backend\temp" rd /s /q "%TEMP_DIR%\backend\temp"
if exist "%TEMP_DIR%\backend\__pycache__" rd /s /q "%TEMP_DIR%\backend\__pycache__"
for /d /r "%TEMP_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r "%TEMP_DIR%" %%f in (*.pyc) do @del "%%f" 2>nul
for /r "%TEMP_DIR%" %%f in (*.pyo) do @del "%%f" 2>nul
for /r "%TEMP_DIR%" %%f in (*.log) do @del "%%f" 2>nul

REM 打包
echo [6/6] 打包中...
powershell -Command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%OUTPUT_FILE%' -Force"

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    goto :end
)

REM 清理临时目录
rd /s /q "%TEMP_DIR%"

echo.
echo ===================================
echo   ✅ 打包完成！
echo ===================================
echo.
echo 📦 输出文件: %OUTPUT_FILE%
for %%A in ("%OUTPUT_FILE%") do echo 📊 文件大小: %%~zA 字节
echo.

:end
pause
