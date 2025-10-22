@echo off
title FunASR GUI精简版打包工具
color 0B

echo.
echo ==============================================
echo 🎨 FunASR GUI精简版打包工具
echo ==============================================
echo 📦 包含: GUI界面 + 必需依赖
echo 📁 输出: 精简exe + 最小依赖
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

echo ✅ 文件检查完成

:: 清理旧文件
echo.
echo 🧹 清理旧文件...
cd ..
if exist build_gui_minimal rmdir /s /q build_gui_minimal
if exist __pycache__ rmdir /s /q __pycache__
cd build_scripts

:: 开始打包
echo.
echo ==============================================
echo 🚀 开始打包GUI精简版...
echo ==============================================
echo.

:: 设置输出目录
set OUTPUT_DIR=..\build_gui_minimal
set APP_NAME=FunASR_VoiceInput_GUI_Minimal

:: 精简打包命令
echo 📦 编译主程序...
python -m nuitka ..\main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --include-package=funasr ^
    --include-package=modelscope ^
    --include-package-data=funasr ^
    --include-package-data=modelscope ^
    --include-data-file=../config.yaml=./config.yaml ^
    --include-data-file=../voice_correction_dict.txt=./voice_correction_dict.txt ^
    --output-dir=%OUTPUT_DIR% ^
    --output-filename=%APP_NAME% ^
    --windows-disable-console ^
    --jobs=4 ^
    --lto=yes ^
    --assume-yes-for-downloads

if %errorlevel% neq 0 (
    echo ❌ 主程序编译失败
    pause
    exit /b 1
)

echo ✅ 主程序编译完成

:: 创建启动脚本
echo.
echo 📄 创建启动脚本...
echo @echo off > "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo :: FunASR GUI精简版启动脚本 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo title FunASR语音输入系统 - 精简版 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo color 0B >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo :: 启动主程序 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo echo 🎤 正在启动FunASR精简版... >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo echo 📍 工作目录: %%~dp0 >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"
echo %APP_NAME%.exe %%* >> "%OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat"

echo ✅ 启动脚本创建完成

:: 创建README文件
echo.
echo 📄 创建使用说明...
echo # FunASR语音输入系统 - GUI精简版 > "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo ## 🚀 快速开始 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 1️⃣ 双击运行: start_minimal.bat >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 2️⃣ 或者直接运行: %APP_NAME%.exe >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo 📁 目录结构: >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - %APP_NAME%.exe          # 主程序 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - start_minimal.bat      # 启动脚本 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - config.yaml            # 配置文件 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo   - voice_correction_dict.txt # 纠错词典 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo. >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo ⚠️  注意: 精简版不包含模型文件和FFmpeg >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"
echo    如需完整功能，请使用完整版打包 >> "%OUTPUT_DIR%\%APP_NAME%.dist\README.txt"

echo ✅ 使用说明创建完成

:: 显示打包结果
echo.
echo ==============================================
echo 🎉 GUI精简版打包完成！
echo ==============================================
echo.
echo 📁 输出目录: %OUTPUT_DIR%\%APP_NAME%.dist\
echo 🎯 主程序: %OUTPUT_DIR%\%APP_NAME%.dist\%APP_NAME%.exe
echo 🚀 启动脚本: %OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat
echo 📖 使用说明: %OUTPUT_DIR%\%APP_NAME%.dist\README.txt
echo.
echo 📦 包含内容:
echo   ✅ GUI界面 (无控制台窗口)
echo   ✅ 基础语音识别功能
echo   ✅ 配置文件和纠错词典
echo   ❌ 不包含模型文件 (需单独下载)
echo   ❌ 不包含FFmpeg (需单独安装)
echo.
echo 💡 建议用途:
echo   - 快速测试GUI界面
echo   - 开发调试使用
echo   - 模型文件单独管理的场景
echo.
echo 🧪 测试建议:
echo   双击运行: %OUTPUT_DIR%\%APP_NAME%.dist\start_minimal.bat
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