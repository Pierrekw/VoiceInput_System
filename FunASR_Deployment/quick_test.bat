@echo off
echo FunASR Quick Test
echo ==================
echo.

REM Set FFmpeg path
set "FFMPEG_PATH=%~dp0dependencies\ffmpeg-master-latest-win64-gpl-shared\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"

echo Testing Python...
python --version
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo.
echo Testing FFmpeg...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo FFmpeg: OK
) else (
    echo FFmpeg: NOT FOUND (but program can still work)
)

echo.
echo Testing FunASR import...
python -c "import funasr; print('FunASR:', funasr.__version__)"
if %ERRORLEVEL% neq 0 (
    echo ERROR: FunASR not installed
    echo Run: pip install funasr
    pause
    exit /b 1
)

echo.
echo Running basic test...
python test_cpu_basic.py

echo.
echo Test completed!
pause