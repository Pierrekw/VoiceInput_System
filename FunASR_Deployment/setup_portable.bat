@echo off
chcp 65001 >nul
echo ========================================
echo FunASR 便携版环境设置
echo ========================================
echo.
echo 此脚本为无管理员权限用户设计
echo 将FFmpeg路径临时添加到当前会话
echo.

REM 设置FFmpeg路径
set "FFMPEG_PATH=%~dp0dependencies\ffmpeg-master-latest-win64-gpl-shared\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"

echo ✅ FFmpeg路径已设置:
echo    %FFMPEG_PATH%
echo.
echo 🔍 测试FFmpeg...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ FFmpeg可用
    for /f "tokens=3" %%i in ('ffmpeg -version ^| findstr "ffmpeg version"') do echo    版本: %%i
) else (
    echo ❌ FFmpeg不可用
    echo 💡 请检查dependencies目录是否包含ffmpeg文件
)

echo.
echo ========================================
echo 📋 使用说明
echo ========================================
echo.
echo 🎯 环境已配置完成，可以运行FunASR程序：
echo.
echo 基础测试:
echo    python test_cpu_basic.py
echo.
echo 语音识别:
echo    python test_funasr_cpu.py
echo.
echo ⚠️  重要提醒:
echo    - 此设置仅在当前命令行窗口有效
echo    - 关闭窗口后需要重新运行此脚本
echo    - 如需永久设置，请联系管理员添加系统PATH
echo.

echo 🚀 现在可以运行FunASR程序了！
echo.

REM 如果有参数，直接运行指定的程序
if not "%~1"=="" (
    echo 🔄 正在运行: %*
    %*
)

pause