@echo off
chcp 65001 >nul
echo ========================================
echo FunASR ONNX依赖库 - 简化下载脚本
echo ========================================
echo.

set DEPS_DIR=F:\onnx_deps
echo 📁 下载目录: %DEPS_DIR%

REM 创建目录
if not exist "%DEPS_DIR%" (
    mkdir "%DEPS_DIR%"
    echo ✅ 创建目录: %DEPS_DIR%
)

cd /d "%DEPS_DIR%"
echo 当前目录: %CD%

echo.
echo 🌐 测试网络连接...
ping -n 1 baidu.com >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ 网络连接正常
) else (
    echo ❌ 网络连接异常，请检查网络
    pause
    exit /b 1
)

echo.
echo 📥 开始下载依赖库...
echo.

REM 下载ONNX Runtime
echo [1/2] 下载 ONNX Runtime...
echo URL: https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/onnxruntime-win-x64-1.16.3.zip

REM 尝试多种下载方法
echo 方法1: 使用PowerShell下载...
powershell -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/onnxruntime-win-x64-1.16.3.zip' -OutFile 'onnxruntime-win-x64-1.16.3.zip'; Write-Host '下载成功' } catch { Write-Host '失败:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% equ 0 (
    echo ✅ ONNX Runtime 下载成功
) else (
    echo ❌ PowerShell下载失败，尝试其他方法...

    echo 方法2: 使用curl下载...
    if exist "C:\Windows\System32\curl.exe" (
        "C:\Windows\System32\curl.exe" -L -k -o "onnxruntime-win-x64-1.16.3.zip" "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/onnxruntime-win-x64-1.16.3.zip"
        if %ERRORLEVEL% equ 0 (
            echo ✅ curl 下载成功
        ) else (
            echo ❌ curl 下载也失败
        )
    ) else (
        echo ❌ curl 不可用
    )
)

REM 检查文件是否下载成功
if exist "onnxruntime-win-x64-1.16.3.zip" (
    for %%I in ("onnxruntime-win-x64-1.16.3.zip") do (
        set /a SIZE_MB=%%~zI/1024/1024
        echo 文件大小: !SIZE_MB! MB
    )
    if !SIZE_MB! lss 50 (
        echo ⚠️ 文件大小异常，可能下载不完整
    ) else (
        echo ✅ 文件大小正常
    )
) else (
    echo ❌ ONNX Runtime下载失败，请手动下载
    echo 手动下载地址: https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/onnxruntime-win-x64-1.16.3.zip
    echo 保存到: %DEPS_DIR%
    pause
    exit /b 1
)

echo.
echo [2/2] 下载 FFmpeg...
echo URL: https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/ffmpeg-master-latest-win64-gpl-shared.zip

echo 方法1: 使用PowerShell下载...
powershell -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/ffmpeg-master-latest-win64-gpl-shared.zip' -OutFile 'ffmpeg-master-latest-win64-gpl-shared.zip'; Write-Host '下载成功' } catch { Write-Host '失败:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% equ 0 (
    echo ✅ FFmpeg 下载成功
) else (
    echo ❌ PowerShell下载失败，尝试其他方法...

    echo 方法2: 使用curl下载...
    if exist "C:\Windows\System32\curl.exe" (
        "C:\Windows\System32\curl.exe" -L -k -o "ffmpeg-master-latest-win64-gpl-shared.zip" "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/ffmpeg-master-latest-win64-gpl-shared.zip"
        if %ERRORLEVEL% equ 0 (
            echo ✅ curl 下载成功
        ) else (
            echo ❌ curl 下载也失败
        )
    ) else (
        echo ❌ curl 不可用
    )
)

REM 检查FFmpeg文件
if exist "ffmpeg-master-latest-win64-gpl-shared.zip" (
    for %%I in ("ffmpeg-master-latest-win64-gpl-shared.zip") do (
        set /a SIZE_MB=%%~zI/1024/1024
        echo 文件大小: !SIZE_MB! MB
    )
    if !SIZE_MB! lss 20 (
        echo ⚠️ 文件大小异常，可能下载不完整
    ) else (
        echo ✅ 文件大小正常
    )
) else (
    echo ❌ FFmpeg下载失败，请手动下载
    echo 手动下载地址: https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/ffmpeg-master-latest-win64-gpl-shared.zip
    echo 保存到: %DEPS_DIR%
    pause
    exit /b 1
)

echo.
echo 📦 开始解压文件...

REM 解压ONNX Runtime
echo 解压 ONNX Runtime...
if exist "onnxruntime-win-x64-1.16.3.zip" (
    echo 使用PowerShell解压...
    powershell -Command "try { Expand-Archive -Path 'onnxruntime-win-x64-1.16.3.zip' -DestinationPath '.' -Force; Write-Host '解压成功' } catch { Write-Host '解压失败:' $_.Exception.Message; exit 1 }"

    if %ERRORLEVEL% equ 0 (
        echo ✅ ONNX Runtime 解压成功
        del "onnxruntime-win-x64-1.16.3.zip"
    ) else (
        echo ❌ 自动解压失败，请手动解压:
        echo 1. 右键点击 onnxruntime-win-x64-1.16.3.zip
        echo 2. 选择 "全部解压缩..."
        echo 3. 解压到当前目录
    )
) else (
    echo ❌ ONNX Runtime压缩包不存在
)

REM 解压FFmpeg
echo 解压 FFmpeg...
if exist "ffmpeg-master-latest-win64-gpl-shared.zip" (
    echo 使用PowerShell解压...
    powershell -Command "try { Expand-Archive -Path 'ffmpeg-master-latest-win64-gpl-shared.zip' -DestinationPath '.' -Force; Write-Host '解压成功' } catch { Write-Host '解压失败:' $_.Exception.Message; exit 1 }"

    if %ERRORLEVEL% equ 0 (
        echo ✅ FFmpeg 解压成功
        del "ffmpeg-master-latest-win64-gpl-shared.zip"
    ) else (
        echo ❌ 自动解压失败，请手动解压:
        echo 1. 右键点击 ffmpeg-master-latest-win64-gpl-shared.zip
        echo 2. 选择 "全部解压缩..."
        echo 3. 解压到当前目录
    )
) else (
    echo ❌ FFmpeg压缩包不存在
)

echo.
echo ========================================
echo 📋 下载完成检查
echo ========================================

if exist "onnxruntime-win-x64-1.16.3" (
    echo ✅ ONNX Runtime: onnxruntime-win-x64-1.16.3
) else (
    echo ❌ ONNX Runtime: 未找到
)

if exist "ffmpeg-master-latest-win64-gpl-shared" (
    echo ✅ FFmpeg: ffmpeg-master-latest-win64-gpl-shared
) else (
    echo ❌ FFmpeg: 未找到
)

echo.
echo 📁 文件位置: %DEPS_DIR%
echo 📝 下一步: 运行 optional_build_onnx.bat
echo.
pause