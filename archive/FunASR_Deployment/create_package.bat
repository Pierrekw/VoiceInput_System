@echo off
chcp 65001 >nul
echo ========================================
echo 创建FunASR部署包
echo ========================================
echo.

REM 检查是否存在7z
where 7z >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 未找到7z压缩工具
    echo 请先安装7-Zip: https://www.7-zip.org/
    pause
    exit /b 1
)

REM 获取当前日期作为版本号
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "VERSION=%YYYY%%MM%%DD%"

REM 创建部署包
echo 📦 正在创建部署包...
set "PACKAGE_NAME=FunASR_CPU_Deployment_v%VERSION%"

7z a -tzip "%PACKAGE_NAME%.zip" * -x!create_package.bat -x!*.zip

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ 部署包创建成功！
    echo 📁 文件名: %PACKAGE_NAME%.zip
    echo 📏 文件大小:
    dir "%PACKAGE_NAME%.zip" | findstr "%PACKAGE_NAME%.zip"
    echo.
    echo 📋 使用说明：
    echo 1. 将 %PACKAGE_NAME%.zip 复制到目标电脑
    echo 2. 解压缩到任意文件夹
    echo 3. 运行 setup_windows.bat (Windows) 或 setup_linux.sh (Linux)
    echo 4. 复制模型文件到 model\fun\ 目录
    echo 5. 运行 test_cpu_basic.py 测试安装
    echo.
) else (
    echo ❌ 创建部署包失败！
)

pause