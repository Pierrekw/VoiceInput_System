@echo off
title FunASR 模型文件打包工具
color 0E

echo.
echo ==============================================
echo 📦 FunASR 模型文件打包工具
echo ==============================================
echo 📁 将模型文件打包到现有程序目录
echo 🎯 目标: 将model/fun目录复制到打包结果中
echo.

:: 检查源目录
echo 🔍 检查模型目录...
if not exist "..\model\fun" (
    echo ❌ 未找到模型目录: ..\model\fun
    echo 📍 请确保模型文件已下载到正确位置
    pause
    exit /b 1
)

echo ✅ 找到模型目录

:: 查找打包结果目录
echo.
echo 🔍 查找打包结果目录...
set found_dir=0

:: 检查完整版打包结果
if exist "..\build_gui\FunASR_VoiceInput_GUI.dist" (
    echo ✅ 找到完整版打包结果: build_gui\FunASR_VoiceInput_GUI.dist
    set target_dir=..\build_gui\FunASR_VoiceInput_GUI.dist
    set found_dir=1
)

:: 检查自定义打包结果
if exist "..\build_custom\FunASR_VoiceInput_Custom.dist" (
    echo ✅ 找到自定义打包结果: build_custom\FunASR_VoiceInput_Custom.dist
    set target_dir=..\build_custom\FunASR_VoiceInput_Custom.dist
    set found_dir=1
)

:: 检查快速打包结果
if exist "..\build_quick\FunASR_VoiceInput_Quick.dist" (
    echo ✅ 找到快速打包结果: build_quick\FunASR_VoiceInput_Quick.dist
    set target_dir=..\build_quick\FunASR_VoiceInput_Quick.dist
    set found_dir=1
)

if %found_dir% equ 0 (
    echo ❌ 未找到任何打包结果目录
    echo 📍 请先运行打包脚本生成exe文件
    pause
    exit /b 1
)

echo.
echo 🎯 目标目录: %target_dir%

:: 确认操作
echo.
echo ⚠️  即将执行以下操作:
echo   📁 复制: ..\model\fun → %target_dir%\model\fun
echo   📁 复制: ..\model\vad → %target_dir%\model\vad (如存在)
echo   📁 复制: ..\model\punc → %target_dir%\model\punc (如存在)
echo.
set /p confirm=确认执行? (y/n): 
if not "%confirm%"=="y" (
    echo ❌ 操作已取消
    pause
    exit /b 1
)

:: 开始复制
echo.
echo ==============================================
echo 📦 开始复制模型文件...
echo ==============================================
echo.

:: 复制FunASR模型
echo 📁 复制FunASR模型...
if not exist "%target_dir%\model" mkdir "%target_dir%\model"
xcopy /s /i /y "..\model\fun" "%target_dir%\model\fun\" >nul
if %errorlevel% equ 0 (
    echo ✅ FunASR模型复制完成
) else (
    echo ❌ FunASR模型复制失败
)

:: 复制VAD模型
echo 📁 复制VAD模型...
if exist "..\model\vad" (
    xcopy /s /i /y "..\model\vad" "%target_dir%\model\vad\" >nul
    if %errorlevel% equ 0 (
        echo ✅ VAD模型复制完成
    ) else (
        echo ❌ VAD模型复制失败
    )
) else (
    echo ⏭️  VAD模型不存在，跳过
)

:: 复制标点模型
echo 📁 复制标点模型...
if exist "..\model\punc" (
    xcopy /s /i /y "..\model\punc" "%target_dir%\model\punc\" >nul
    if %errorlevel% equ 0 (
        echo ✅ 标点模型复制完成
    ) else (
        echo ❌ 标点模型复制失败
    )
) else (
    echo ⏭️  标点模型不存在，跳过
)

:: 统计文件大小
echo.
echo 📊 统计模型文件大小...
echo FunASR模型大小:
if exist "%target_dir%\model\fun" (
    dir /s "%target_dir%\model\fun" | findstr "个文件"
)
if exist "%target_dir%\model\vad" (
    echo VAD模型大小:
    dir /s "%target_dir%\model\vad" | findstr "个文件"
)
if exist "%target_dir%\model\punc" (
    echo 标点模型大小:
    dir /s "%target_dir%\model\punc" | findstr "个文件"
)

:: 更新启动脚本
echo.
echo 📄 更新启动脚本...
echo :: FunASR语音输入系统 - 已包含模型 >> "%target_dir%\model_included.txt"
echo :: 模型文件已集成 >> "%target_dir%\model_included.txt"
echo :: 包含: FunASR模型, VAD模型, 标点模型 >> "%target_dir%\model_included.txt"

echo ✅ 启动脚本已更新

:: 显示结果
echo.
echo ==============================================
echo 🎉 模型文件打包完成！
echo ==============================================
echo.
echo 📁 目标目录: %target_dir%
echo 📦 包含模型:
echo   ✅ FunASR语音识别模型
echo   ✅ VAD语音活动检测模型 (如存在)
echo   ✅ 标点符号模型 (如存在)
echo.
echo 🚀 现在可以运行程序了！
echo 📖 使用说明: 查看目标目录中的README.txt
echo.

:: 询问是否打开目录
echo.
set /p open_dir=是否打开目标目录? (y/n): 
if "%open_dir%"=="y" (
    explorer "%target_dir%"
)

pause