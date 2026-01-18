@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===================================
echo   Fmt this Shit EXE 打包工具
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
set PACKAGE_NAME=fmt-this-shit-exe-%VERSION%
set OUTPUT_DIR=%CD%\dist

REM 清理旧的构建
echo [1/5] 清理旧的构建文件...
if exist "build" rd /s /q "build"
if exist "dist\fmt-this-shit.exe" del "dist\fmt-this-shit.exe"
if exist "dist\%PACKAGE_NAME%" rd /s /q "dist\%PACKAGE_NAME%"

REM 使用 PyInstaller 打包
echo [2/5] 使用 PyInstaller 打包...
.venv\Scripts\pyinstaller --clean fmt-this-shit.spec

if errorlevel 1 (
    echo.
    echo ❌ PyInstaller 打包失败！
    goto :end
)

REM 创建发布包目录
echo [3/5] 创建发布包目录...
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%"

REM 复制 exe
move dist\fmt-this-shit.exe "%OUTPUT_DIR%\%PACKAGE_NAME%\fmt-this-shit.exe" >nul
echo   - exe 已复制

REM 复制 Pandoc
if exist "pandoc" (
    xcopy /E /I /Y pandoc "%OUTPUT_DIR%\%PACKAGE_NAME%\pandoc" >nul
    echo   - Pandoc 已复制
) else (
    echo   - 警告: pandoc 不存在
)

REM 复制 node_modules (仅 mermaid-cli)
if exist "node_modules\.bin\mmdc.cmd" (
    xcopy /E /I /Y node_modules "%OUTPUT_DIR%\%PACKAGE_NAME%\node_modules" >nul
    echo   - mermaid-cli 已复制
) else (
    echo   - 警告: mermaid-cli 不存在
)

REM 复制 README
copy /Y README.md "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul
copy /Y README.zh-CN.md "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul
echo   - README 已复制

REM 打包成 zip
echo [4/5] 打包成 zip...
powershell -Command "Compress-Archive -Path '%OUTPUT_DIR%\%PACKAGE_NAME%\*' -DestinationPath '%OUTPUT_DIR%\%PACKAGE_NAME%.zip' -Force"

if errorlevel 1 (
    echo.
    echo ❌ ZIP 打包失败！
    goto :end
)

REM 清理临时目录
echo [5/5] 清理临时目录...
rd /s /q "%OUTPUT_DIR%\%PACKAGE_NAME%"

echo.
echo ===================================
echo   ✅ 打包完成！
echo ===================================
echo.
echo 📦 输出文件: %OUTPUT_DIR%\%PACKAGE_NAME%.zip
for %%A in ("%OUTPUT_DIR%\%PACKAGE_NAME%.zip") do echo 📊 文件大小: %%~zA 字节
echo.
echo 📝 使用说明：
echo    1. 解压 zip 文件
echo    2. 双击 fmt-this-shit.exe 启动
echo    3. 浏览器会自动打开 http://localhost:5678
echo.

:end
pause
