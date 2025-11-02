@echo off
REM ================================================================================
REM VoiceInput System - Nuitka打包脚本 (Windows)
REM ================================================================================

setlocal EnableDelayedExpansion

echo ========================================
echo VoiceInput System - Nuitka打包
echo ========================================
echo.

REM 检查Python环境
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    exit /b 1
)

echo [信息] 当前Python版本:
python --version

REM 检查Nuitka
where nuitka3 >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 安装Nuitka...
    pip install nuitka==1.9.2
    if !errorlevel! neq 0 (
        echo [错误] Nuitka安装失败
        exit /b 1
    )
) else (
    echo [信息] Nuitka已安装
)

REM 安装依赖
echo.
echo [步骤 1/4] 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    exit /b 1
)

REM 安装Nuitka特定依赖
echo.
echo [步骤 2/4] 安装Nuitka插件依赖...
pip install ordered-set zstandard
pip install --upgrade nuitka

REM 创建构建目录
echo.
echo [步骤 3/4] 创建构建目录...
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM 清理之前的构建
if exist "VoiceInput_System.exe" del /q "VoiceInput_System.exe"
if exist "VoiceInput_System.dist" rmdir /s /q "VoiceInput_System.dist" 2>nul

REM 检查主程序文件
if not exist "funasr_voice_combined.py" (
    echo [错误] 未找到主程序文件 funasr_voice_combined.py
    exit /b 1
)

REM 执行Nuitka打包
echo.
echo [步骤 4/4] 执行Nuitka打包...
echo [信息] 这可能需要较长时间，请耐心等待...
echo.

nuitka3 ^
    --onefile ^
    --standalone ^
    --enable-plugin=pytorch ^
    --enable-plugin=numpy ^
    --enable-cc=yes ^
    --cache-dir=.nuitka-cache ^
    --optimize-level=3 ^
    --output-dir=build ^
    --output-filename=VoiceInput_System.exe ^
    --include-data-dir=model/fun=model/fun ^
    --include-data-dir=onnx_deps=onnx_deps ^
    --include-data-dir=config=config ^
    --include-data-file=voice_correction_dict.txt=voice_correction_dict.txt ^
    funasr_voice_combined.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ 打包成功！
    echo ========================================
    echo.
    echo 输出文件:
    if exist "build\VoiceInput_System.exe" (
        echo   - 可执行文件: build\VoiceInput_System.exe
        dir "build\VoiceInput_System.exe" | find "VoiceInput_System.exe"
    )
    if exist "build\VoiceInput_System.dist" (
        echo   - 独立目录: build\VoiceInput_System.dist\
        dir /s "build\VoiceInput_System.dist" | find "个文件"
    )
    echo.
    echo 使用说明:
    echo 1. 将model/fun和onnx_deps文件夹复制到程序目录
    echo 2. 确保config.yaml中的路径配置正确
    echo 3. 双击运行VoiceInput_System.exe
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ 打包失败
    echo ========================================
    echo 请检查错误信息并重试
    echo.
    exit /b 1
)

endlocal
pause
