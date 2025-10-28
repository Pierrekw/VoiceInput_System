@echo off
chcp 65001 >nul
echo ========================================
echo FunASR CPU优化版 - 一键启动
echo ========================================
echo.

REM 设置FFmpeg路径
set "FFMPEG_PATH=%~dp0dependencies\ffmpeg-master-latest-win64-gpl-shared\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"

echo 🔍 检查环境...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python未找到，请先安装Python
    pause
    exit /b 1
)
echo ✅ Python环境正常

REM 检查模型文件
if not exist "%~dp0model\fun\model.pt" (
    echo WARNING: Model files not found
    echo Please copy model files to model\fun\ directory
    echo Required files:
    echo    - model.pt
    echo    - config.yaml
    echo    - tokens.json
    echo    - am.mvn
    echo.
    echo Press any key to continue basic test (import only)...
    pause >nul
)

echo.
echo Select run mode:
echo    1. Basic function test (no microphone needed)
echo    2. Voice recognition program (microphone required)
echo    3. Exit
echo.
set /p choice="Please choose (1-3): "

if "%choice%"=="1" goto basic_test
if "%choice%"=="2" goto voice_recognition
if "%choice%"=="3" goto end

echo Invalid choice, running basic test by default
goto basic_test

:basic_test
echo.
echo Running basic function test...
echo Testing FunASR import and model loading...
python test_cpu_basic.py
goto end

:voice_recognition
echo.
echo Starting voice recognition program...
echo Please ensure microphone is connected and working
echo.
python test_funasr_cpu.py
goto end

:end
echo.
echo ========================================
echo Program ended
echo ========================================
pause