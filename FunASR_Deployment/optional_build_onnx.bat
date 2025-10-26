@echo off
echo ========================================
echo 编译FunASR ONNX Runtime版本
echo ========================================

REM 设置环境变量
set ONNXRUNTIME_DIR=F:\onnx_deps\onnxruntime-win-x64-1.16.3
set FFMPEG_DIR=F:\onnx_deps\ffmpeg-master-latest-win64-gpl-shared
set FUNASR_ROOT=F:\04_AI\01_Workplace\FunASR
set BUILD_DIR=%FUNASR_ROOT%\runtime\onnxruntime\build

echo.
echo 检查依赖库是否存在...
if not exist "%ONNXRUNTIME_DIR%" (
    echo 错误：找不到 ONNX Runtime 目录 %ONNXRUNTIME_DIR%
    echo 请先运行 download_onnx_deps.bat 下载依赖库
    pause
    exit /b 1
)

if not exist "%FFMPEG_DIR%" (
    echo 错误：找不到 FFmpeg 目录 %FFMPEG_DIR%
    echo 请先运行 download_onnx_deps.bat 下载依赖库
    pause
    exit /b 1
)

if not exist "%FUNASR_ROOT%" (
    echo 错误：找不到 FunASR 目录 %FUNASR_ROOT%
    pause
    exit /b 1
)

echo.
echo 创建构建目录...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo.
echo 进入构建目录...
cd /d "%BUILD_DIR%"

echo.
echo 配置CMake...
cmake ../ ^
    -D CMAKE_BUILD_TYPE=Release ^
    -D ONNXRUNTIME_DIR=%ONNXRUNTIME_DIR% ^
    -D FFMPEG_DIR=%FFMPEG_DIR%

if %ERRORLEVEL% neq 0 (
    echo.
    echo CMake配置失败！请检查：
    echo 1. 是否安装了Visual Studio 2019或更高版本
    echo 2. 是否安装了CMake
    echo 3. 是否下载了正确的依赖库
    pause
    exit /b 1
)

echo.
echo 开始编译...
echo 注意：首次编译可能需要较长时间，请耐心等待...
msbuild FunASROnnx.sln /p:Configuration=Release /m

if %ERRORLEVEL% neq 0 (
    echo.
    echo 编译失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo 编译成功！
echo 可执行文件位置: %BUILD_DIR%\bin\Release\
echo ========================================
pause