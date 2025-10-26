@echo off
chcp 65001 >nul
echo ========================================
echo 下载FunASR ONNX Runtime依赖库
echo ========================================
echo.

REM 设置下载目录
set DEPS_DIR=F:\onnx_deps
set DOWNLOAD_RETRY=3
set TIMEOUT=300

echo 📁 依赖库将下载到: %DEPS_DIR%

REM 创建下载目录
if not exist "%DEPS_DIR%" (
    echo 📂 创建下载目录...
    mkdir "%DEPS_DIR%"
)
cd /d "%DEPS_DIR%"

REM 检查PowerShell版本
echo 🔍 检查PowerShell环境...
powershell -Command "Write-Host 'PowerShell版本:' $PSVersionTable.PSVersion" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ PowerShell不可用，请检查系统环境
    pause
    exit /b 1
)
echo ✅ PowerShell环境正常

REM 函数：下载文件（带重试）
:download_file
set URL=%~1
set FILENAME=%~2
set DESC=%~3

echo.
echo 📥 正在下载 %DESC%...
echo    URL: %URL%
echo    文件: %FILENAME%

set /a RETRY_COUNT=0
:download_retry
set /a RETRY_COUNT+=1
echo    尝试第 %RETRY_COUNT% 次...

REM 删除部分下载的文件
if exist "%FILENAME%" del "%FILENAME%"

REM 使用多种方法下载
echo    方法1: PowerShell Invoke-WebRequest...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri '%URL%' -OutFile '%FILENAME%' -TimeoutSec %TIMEOUT%; Write-Host '下载成功' } catch { Write-Host 'PowerShell下载失败:' $_.Exception.Message; exit 1 } }"

if %ERRORLEVEL% equ 0 goto :download_success

if %RETRY_COUNT% geq %DOWNLOAD_RETRY% (
    echo ❌ 下载失败，已重试 %DOWNLOAD_RETRY% 次
    echo 💡 尝试备用下载方法...

    echo    方法2: curl 下载...
    curl -L -o "%FILENAME%" "%URL%" --connect-timeout 30 --max-time %TIMEOUT%
    if %ERRORLEVEL% equ 0 goto :download_success

    echo    方法3: PowerShell Invoke-RestMethod...
    powershell -Command "& {$ProgressPreference='SilentlyContinue'; try { [Net.WebRequest]::Create('%URL%').DownloadFile('%FILENAME%'); Write-Host 'WebRequest下载成功' } catch { Write-Host 'WebRequest下载失败:' $_.Exception.Message; exit 1 } }"
    if %ERRORLEVEL% equ 0 goto :download_success

    echo ❌ 所有下载方法都失败了
    goto :download_failed
)

echo ⚠️ 下载失败，正在重试...
goto :download_retry

:download_success
echo ✅ %DESC% 下载成功
REM 检查文件大小
for %%I in ("%FILENAME%") do (
    set /a FILE_SIZE=%%~zI/1024/1024
    echo    文件大小: %%~zI 字节 (%FILE_SIZE% MB)
)
if %FILE_SIZE% lss 10 (
    echo ⚠️ 文件大小异常小，可能下载不完整
    if %RETRY_COUNT% lss %DOWNLOAD_RETRY% (
        echo 正在重试下载...
        goto :download_retry
    )
)
goto :eof

:download_failed
echo ❌ %DESC% 下载彻底失败
echo 💡 请检查：
echo    1. 网络连接是否正常
echo    2. 防火墙是否阻止下载
echo    3. 磁盘空间是否充足
echo    4. URL是否可以访问（可尝试在浏览器中打开）
exit /b 1

REM 开始下载ONNX Runtime
call :download_file "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/onnxruntime-win-x64-1.16.3.zip" "onnxruntime-win-x64-1.16.3.zip" "ONNX Runtime 1.16.3"
if %ERRORLEVEL% neq 0 (
    echo ❌ ONNX Runtime下载失败，终止安装
    pause
    exit /b 1
)

REM 开始下载FFmpeg
call :download_file "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/dep_libs/ffmpeg-master-latest-win64-gpl-shared.zip" "ffmpeg-master-latest-win64-gpl-shared.zip" "FFmpeg 预编译库"
if %ERRORLEVEL% neq 0 (
    echo ❌ FFmpeg下载失败，终止安装
    pause
    exit /b 1
)

echo.
echo ========================================
echo 📦 开始解压文件...
echo ========================================

REM 函数：解压文件
:extract_file
set ZIPFILE=%~1
set TARGET_DIR=%~2
set DESC=%~3

echo 📂 正在解压 %DESC%...
echo    压缩包: %ZIPFILE%
echo    目标目录: %TARGET_DIR%

REM 检查压缩包是否存在
if not exist "%ZIPFILE%" (
    echo ❌ 压缩包不存在: %ZIPFILE%
    exit /b 1
)

REM 尝试多种解压方法
echo    方法1: PowerShell Expand-Archive...
powershell -Command "try { Expand-Archive -Path '%ZIPFILE%' -DestinationPath '%TARGET_DIR%' -Force; Write-Host 'PowerShell解压成功' } catch { Write-Host 'PowerShell解压失败:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% equ 0 (
    echo ✅ %DESC% 解压成功
    goto :extract_success
)

echo    方法2: 手动解压（如果PowerShell失败）...
echo 💡 请手动解压文件：
echo    1. 右键点击 %ZIPFILE%
echo    2. 选择 "全部解压缩..."
echo    3. 解压到当前目录
echo    4. 重新运行此脚本
pause
exit /b 1

:extract_success
goto :eof

REM 解压ONNX Runtime
call :extract_file "onnxruntime-win-x64-1.16.3.zip" "." "ONNX Runtime"
if %ERRORLEVEL% neq 0 (
    echo ❌ ONNX Runtime解压失败
    pause
    exit /b 1
)

REM 解压FFmpeg
call :extract_file "ffmpeg-master-latest-win64-gpl-shared.zip" "." "FFmpeg"
if %ERRORLEVEL% neq 0 (
    echo ❌ FFmpeg解压失败
    pause
    exit /b 1
)

echo.
echo 🧹 清理压缩文件...
if exist "onnxruntime-win-x64-1.16.3.zip" del "onnxruntime-win-x64-1.16.3.zip"
if exist "ffmpeg-master-latest-win64-gpl-shared.zip" del "ffmpeg-master-latest-win64-gpl-shared.zip"

echo.
echo ========================================
echo ✅ 下载和解压完成！
echo ========================================
echo.

REM 验证下载结果
echo 🔍 验证下载结果...

if exist "onnxruntime-win-x64-1.16.3" (
    echo ✅ ONNX Runtime: onnxruntime-win-x64-1.16.3
    dir "onnxruntime-win-x64-1.16.3" | findstr "个文件"
) else (
    echo ❌ ONNX Runtime 目录不存在
)

if exist "ffmpeg-master-latest-win64-gpl-shared" (
    echo ✅ FFmpeg: ffmpeg-master-latest-win64-gpl-shared
    dir "ffmpeg-master-latest-win64-gpl-shared" | findstr "个文件"
) else (
    echo ❌ FFmpeg 目录不存在
)

echo.
echo 📋 下载的文件位置:
echo    ONNX Runtime: %DEPS_DIR%\onnxruntime-win-x64-1.16.3
echo    FFmpeg: %DEPS_DIR%\ffmpeg-master-latest-win64-gpl-shared
echo.
echo 📝 下一步:
echo    运行 optional_build_onnx.bat 编译FunASR ONNX版本
echo.
pause