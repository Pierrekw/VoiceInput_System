@echo off
REM ================================================================================
REM VoiceInput System - Nuitka Build Script (Windows)
REM ================================================================================

setlocal EnableDelayedExpansion

echo ========================================
echo VoiceInput System - Nuitka Build
echo ========================================
echo.

REM Check Python environment
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found, please install Python and add to PATH
    exit /b 1
)

echo [INFO] Current Python version:
python --version

REM Check Nuitka
where nuitka3 >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Nuitka...
    pip install nuitka==1.9.2
    if !errorlevel! neq 0 (
        echo [ERROR] Nuitka installation failed
        exit /b 1
    )
) else (
    echo [INFO] Nuitka is installed
)

REM Install dependencies
echo.
echo [STEP 1/4] Installing dependencies...
pip install -r requirements-nuitka.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed
    exit /b 1
)

REM Install Nuitka specific dependencies
echo.
echo [STEP 2/4] Installing Nuitka plugins...
pip install ordered-set zstandard
pip install --upgrade nuitka

REM Create build directories
echo.
echo [STEP 3/4] Creating build directories...
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Clean previous build
if exist "VoiceInput_System.exe" del /q "VoiceInput_System.exe"
if exist "VoiceInput_System.dist" rmdir /s /q "VoiceInput_System.dist" 2>nul

REM Check main program file
if not exist "funasr_voice_combined.py" (
    echo [ERROR] Main program file not found: funasr_voice_combined.py
    exit /b 1
)

REM Execute Nuitka build
echo.
echo [STEP 4/4] Executing Nuitka build...
echo [INFO] This may take a long time, please wait...
echo.

nuitka3 --onefile --standalone --enable-plugin=pytorch --enable-plugin=numpy --enable-cc=yes --cache-dir=.nuitka-cache --optimize-level=3 --output-dir=build --output-filename=VoiceInput_System.exe --include-data-dir=model/fun=model/fun --include-data-dir=onnx_deps=onnx_deps --include-data-dir=config=config --include-data-file=voice_correction_dict.txt=voice_correction_dict.txt funasr_voice_combined.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Output files:
    if exist "build\VoiceInput_System.exe" (
        echo   - Executable: build\VoiceInput_System.exe
        dir "build\VoiceInput_System.exe" | find "VoiceInput_System.exe"
    )
    if exist "build\VoiceInput_System.dist" (
        echo   - Standalone directory: build\VoiceInput_System.dist\
        dir /s "build\VoiceInput_System.dist" | find "File(s)"
    )
    echo.
    echo Usage:
    echo 1. Copy model/fun and onnx_deps folders to program directory
    echo 2. Ensure config.yaml paths are correct
    echo 3. Run VoiceInput_System.exe
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    echo Please check error messages and try again
    echo.
    exit /b 1
)

endlocal
pause
