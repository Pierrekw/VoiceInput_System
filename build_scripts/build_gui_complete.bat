@echo off
title FunASR GUI完整版打包工具
color 0A

echo.
echo ==============================================
echo 🎨 FunASR GUI完整版打包工具
echo ==============================================
echo 📦 包含: GUI界面 + 模型文件 + FFmpeg依赖
echo 📁 输出: 独立exe + model目录 + ffmpeg目录
echo.

:: 检查基础环境
echo 🔍 检查环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

:: 检查Nuitka
python -c "import nuitka" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 正在安装Nuitka...
    python -m pip install nuitka ordered-set
)

echo ✅ 环境检查通过

:: 检查必要文件
echo 🔍 检查必要文件...
if not exist "..\main_f.py" (
    echo ❌ 未找到主程序文件 main_f.py
    pause
    exit /b 1
)

if not exist "..\model\fun" (
    echo ⚠️  未找到model/fun目录，确认是否需要包含模型文件？
    set /p include_model=是否包含模型文件? (y/n): 
) else (
    set include_model=y
)

if not exist "..\onnx_deps\ffmpeg-master-latest-win64-gpl-shared" (
    echo ⚠️  未找到FFmpeg依赖目录
    echo 📍 期望路径: ..\onnx_deps\ffmpeg-master-latest-win64-gpl-shared
    pause
    exit /b 1
)

echo ✅ 文件检查完成

:: 清理旧文件
echo.
echo 🧹 清理旧文件...
cd ..
if exist build_gui rmdir /s /q build_gui
if exist __pycache__ rmdir /s /q __pycache__
cd build_scripts

:: 开始打包
echo.
echo ==============================================
echo 🚀 开始打包GUI完整版...
echo ==============================================
echo.

:: 设置输出目录
set OUTPUT_DIR=..\build_gui
set APP_NAME=FunASR_VoiceInput_GUI

:: 基础打包命令
echo 📦 步骤1: 编译主程序...
python -m nuitka ..\main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --enable-plugin=numpy ^
    --enable-plugin=torch ^
    --include-package=funasr ^
    --include-package=modelscope ^
    --include-package-data=funasr ^
    --include-package-data=modelscope ^
    --include-data-dir=../config=./config ^
    --include-data-file=../config.yaml=./config.yaml ^
    --include-data-file=../voice_correction_dict.txt=./voice_correction_dict.txt ^
    --output-dir=%OUTPUT_DIR% ^
    --output-filename=%APP_NAME% ^
    --windows-disable-console ^
    --windows-icon-from-ico=../icon.ico ^
    --jobs=8 ^
    --lto=yes ^
    --assume-yes-for-downloads

if %errorlevel% neq 0 (
    echo ❌ 主程序编译失败
    pause
    exit /b 1
)

echo ✅ 主程序编译完成

:: 复制模型文件
echo.
echo 📦 步骤2: 复制模型文件...
if "%include_model%"=="y" (
    if exist "..\model\fun" (
        echo 📁 复制FunASR模型...
        xcopy /s /i /y "..\model\fun" "%OUTPUT_DIR%\%APP_NAME%.dist\model\fun\" >nul
        
        if exist "..\model\vad" (
            echo 📁 复制VAD模型...
            xcopy /s /i /y "..\model\vad" "%OUTPUT_DIR%\%APP_NAME%.dist\model\vad\" >nul
        )
        
        if exist "..\model\punc" (
            echo 📁 复制标点模型...
            xcopy /s /i /y "..\model\punc" "%OUTPUT_DIR%\%APP_NAME%.dist\model\punc\" >nul
        )
        
        echo ✅ 模型文件复制完成
    ) else (
        echo ⚠️  模型目录不存在，跳过模型文件复制
    )
) else (
    echo ⏭️  跳过模型文件复制
)

:: 复制FFmpeg依赖
echo.
echo 📦 步骤3: 复制FFmpeg依赖...
echo 📁 复制FFmpeg库文件...

:: 创建ffmpeg目录
mkdir "%OUTPUT_DIR%\%APP_NAME%.dist\ffmpeg" >nul 2>&1

:: 复制FFmpeg可执行文件和库
xcopy /s /i /y "..\onnx_deps\ffmpeg-master-latest-win64-gpl-shared\bin" "%OUTPUT_DIR%\%APP_NAME%.dist\ffmpeg\bin\" >nul
xcopy /s /i /y "..\onnx_deps\ffmpeg-master-latest-win64-gpl-shared\lib" "%OUTPUT_DIR%\%APP_NAME%.dist\ffmpeg\lib\" >nul

:: 创建FFmpeg环境配置脚本
echo 📄 创建FFmpeg环境配置...
echo @echo off > "%OUTPUT_DIR%\%APP_NAME%.dist\setup_ffmpeg.bat"
echo :: FunASR FFmpeg环境配置 >> "%OUTPUT_DIR%\%APP_NAME%.dist\setup_ffmpeg.bat"
echo set PATH=%%~dp0ffmpeg\bin;%%PATH%% >> "%OUTPUT_DIR%\%APP_NAME%.dist\setup_ffmpeg.bat"
echo echo ✅ FFmpeg环境已配置 >> "%OUTPUT_DIR%\%APP_NAME%.dist\setup_ffmpeg.bat"

echo ✅ FFmpeg依赖复制完成

:: 创建启动脚本
echo.
echo 📄 步骤4: 创建启动脚本...
echo @echo off > "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo :: FunASR GUI启动脚本 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo title FunASR语音输入系统 - GUI版 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo color 0A >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo :: 配置FFmpeg环境 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo set PATH=%%~dp0ffmpeg\bin;%%PATH%% >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo :: 启动主程序 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo echo 🎤 正在启动FunASR语音输入系统... >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo echo 📍 工作目录: %%~dp0 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"
echo %APP_NAME%.exe %%* >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat"

echo ✅ 启动脚本创建完成

:: 创建README文件
echo.
echo 📄 步骤5: 创建使用说明...
echo # FunASR语音输入系统 - GUI完整版 > "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo ## 🚀 快速开始 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 1️⃣ 双击运行: start_gui.bat >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 2️⃣ 或者直接运行: %APP_NAME%.exe >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 📁 目录结构: >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - %APP_NAME%.exe          # 主程序 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - start_gui.bat          # 启动脚本 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - model/                 # 模型文件目录 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - ffmpeg/                # FFmpeg依赖 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - config/                # 配置文件 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo ⚙️  命令行参数: >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   --help                  # 显示帮助 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   --gui                   # 启动GUI界面 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   --mode=fast             # 快速识别模式 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   --duration=60           # 设置识别时长 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 🔧 系统要求: >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - Windows 10/11 (64位) >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - 内存: 4GB以上 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - 存储: 2GB以上可用空间 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"

echo ✅ 使用说明创建完成

:: 显示打包结果
echo.
echo ==============================================
echo 🎉 GUI完整版打包完成！
echo ==============================================
echo.
echo 📁 输出目录: %OUTPUT_DIR%\%APP_NAME%.dist\
echo 🎯 主程序: %OUTPUT_DIR%\%APP_NAME%.dist\%APP_NAME%.exe
echo 🚀 启动脚本: %OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat
echo 📖 使用说明: %OUTPUT_DIR%\%APP_NAME%.dist\README.txt
echo.
echo 📦 包含内容:
echo   ✅ GUI界面 (无控制台窗口)
echo   ✅ 语音识别模型 (如存在)
echo   ✅ FFmpeg音频处理库
echo   ✅ 配置文件和纠错词典
echo   ✅ 一键启动脚本
echo.

:: 文件大小统计
if exist "%OUTPUT_DIR%\%APP_NAME%.dist" (
    echo 📊 文件大小统计:
    dir /s "%OUTPUT_DIR%\%APP_NAME%.dist" | findstr "个文件"
    echo.
)

echo 🧪 测试建议:
echo   1️⃣ 双击运行: %OUTPUT_DIR%\%APP_NAME%.dist\start_gui.bat
echo   2️⃣ 或者直接运行: %OUTPUT_DIR%\%APP_NAME%.dist\%APP_NAME%.exe
echo   3️⃣ 命令行测试: %OUTPUT_DIR%\%APP_NAME%.dist\%APP_NAME%.exe --help
echo.
echo 📋 更多帮助: 查看 nuitka_build_guide.md
echo ==============================================

:: 询问是否打开目录
echo.
set /p open_dir=是否打开输出目录? (y/n): 
if "%open_dir%"=="y" (
    explorer "%OUTPUT_DIR%\%APP_NAME%.dist"
)

pause