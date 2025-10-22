@echo off
title FunASR FFmpeg依赖打包工具
color 0D

echo.
echo ==============================================
echo 📦 FunASR FFmpeg依赖打包工具
echo ==============================================
echo 📁 将FFmpeg依赖打包到现有程序目录
echo 🎯 目标: 将onnx_deps\ffmpeg-master-latest-win64-gpl-shared复制到打包结果中
echo.

:: 检查FFmpeg源目录
echo 🔍 检查FFmpeg依赖目录...
set ffmpeg_source=..\onnx_deps\ffmpeg-master-latest-win64-gpl-shared

if not exist "%ffmpeg_source%" (
    echo ❌ 未找到FFmpeg依赖目录: %ffmpeg_source%
    echo 📍 请确保FFmpeg已下载到正确位置
    pause
    exit /b 1
)

echo ✅ 找到FFmpeg依赖目录

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
echo   📁 复制: %ffmpeg_source%\bin → %target_dir%\ffmpeg\bin
echo   📁 复制: %ffmpeg_source%\lib → %target_dir%\ffmpeg\lib
echo   📄 创建: FFmpeg环境配置脚本
echo   📄 更新: 启动脚本 (添加FFmpeg路径)
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
echo 📦 开始复制FFmpeg依赖...
echo ==============================================
echo.

:: 创建ffmpeg目录
echo 📁 创建FFmpeg目录...
if not exist "%target_dir%\ffmpeg" mkdir "%target_dir%\ffmpeg"

:: 复制bin目录
echo 📁 复制FFmpeg可执行文件...
if exist "%ffmpeg_source%\bin" (
    xcopy /s /i /y "%ffmpeg_source%\bin" "%target_dir%\ffmpeg\bin\" >nul
    if %errorlevel% equ 0 (
        echo ✅ FFmpeg可执行文件复制完成
    ) else (
        echo ❌ FFmpeg可执行文件复制失败
    )
) else (
    echo ⚠️  未找到bin目录，跳过
)

:: 复制lib目录
echo 📁 复制FFmpeg库文件...
if exist "%ffmpeg_source%\lib" (
    xcopy /s /i /y "%ffmpeg_source%\lib" "%target_dir%\ffmpeg\lib\" >nul
    if %errorlevel% equ 0 (
        echo ✅ FFmpeg库文件复制完成
    ) else (
        echo ❌ FFmpeg库文件复制失败
    )
) else (
    echo ⚠️  未找到lib目录，跳过
)

:: 复制其他重要文件
echo 📄 复制FFmpeg配置文件...
if exist "%ffmpeg_source%\LICENSE.txt" (
    copy /y "%ffmpeg_source%\LICENSE.txt" "%target_dir%\ffmpeg\" >nul
    echo ✅ FFmpeg许可证复制完成
)

if exist "%ffmpeg_source%\README.txt" (
    copy /y "%ffmpeg_source%\README.txt" "%target_dir%\ffmpeg\" >nul
    echo ✅ FFmpeg说明文档复制完成
)

:: 创建FFmpeg环境配置脚本
echo.
echo 📄 创建FFmpeg环境配置脚本...
echo @echo off > "%target_dir%\setup_ffmpeg.bat"
echo :: FunASR FFmpeg环境配置 >> "%target_dir%\setup_ffmpeg.bat"
echo :: 自动配置FFmpeg环境变量 >> "%target_dir%\setup_ffmpeg.bat"
echo. >> "%target_dir%\setup_ffmpeg.bat"
echo :: 设置FFmpeg路径 >> "%target_dir%\setup_ffmpeg.bat"
echo set FFMPEG_HOME=%%~dp0ffmpeg >> "%target_dir%\setup_ffmpeg.bat"
echo set PATH=%%FFMPEG_HOME%%\bin;%%PATH%% >> "%target_dir%\setup_ffmpeg.bat"
echo. >> "%target_dir%\setup_ffmpeg.bat"
echo :: 验证FFmpeg >> "%target_dir%\setup_ffmpeg.bat"
echo ffmpeg -version ^>nul 2^>^&1 >> "%target_dir%\setup_ffmpeg.bat"
echo if %%errorlevel%% equ 0 ( >> "%target_dir%\setup_ffmpeg.bat"
echo     echo ✅ FFmpeg环境配置成功 >> "%target_dir%\setup_ffmpeg.bat"
echo     echo 📍 FFmpeg版本: >> "%target_dir%\setup_ffmpeg.bat"
echo     ffmpeg -version ^| findstr "ffmpeg version" >> "%target_dir%\setup_ffmpeg.bat"
echo ) else ( >> "%target_dir%\setup_ffmpeg.bat"
echo     echo ❌ FFmpeg环境配置失败 >> "%target_dir%\setup_ffmpeg.bat"
echo ) >> "%target_dir%\setup_ffmpeg.bat"
echo pause >> "%target_dir%\setup_ffmpeg.bat"

echo ✅ FFmpeg环境配置脚本创建完成

:: 更新启动脚本
echo.
echo 📄 更新启动脚本...
:: 查找现有的启动脚本
if exist "%target_dir%\start_gui.bat" (
    echo 📄 更新GUI启动脚本...
    :: 备份原文件
    copy /y "%target_dir%\start_gui.bat" "%target_dir%\start_gui_backup.bat" >nul
    
    :: 创建新启动脚本
    echo @echo off > "%target_dir%\start_gui.bat"
echo :: FunASR语音输入系统 - GUI版 (含FFmpeg) >> "%target_dir%\start_gui.bat"
echo title FunASR语音输入系统 - GUI版 >> "%target_dir%\start_gui.bat"
echo color 0A >> "%target_dir%\start_gui.bat"
echo. >> "%target_dir%\start_gui.bat"
echo :: 配置FFmpeg环境 >> "%target_dir%\start_gui.bat"
echo set PATH=%%~dp0ffmpeg\bin;%%PATH%% >> "%target_dir%\start_gui.bat"
echo. >> "%target_dir%\start_gui.bat"
echo :: 启动主程序 >> "%target_dir%\start_gui.bat"
echo echo 🎤 正在启动FunASR语音输入系统... >> "%target_dir%\start_gui.bat"
echo echo 📍 工作目录: %%~dp0 >> "%target_dir%\start_gui.bat"
echo echo. >> "%target_dir%\start_gui.bat"
echo FunASR_VoiceInput_GUI.exe %%* >> "%target_dir%\start_gui.bat"
    echo ✅ GUI启动脚本更新完成
)

if exist "%target_dir%\start_minimal.bat" (
    echo 📄 更新精简版启动脚本...
    :: 备份原文件
    copy /y "%target_dir%\start_minimal.bat" "%target_dir%\start_minimal_backup.bat" >nul
    
    :: 创建新启动脚本
    echo @echo off > "%target_dir%\start_minimal.bat"
echo :: FunASR语音输入系统 - 精简版 (含FFmpeg) >> "%target_dir%\start_minimal.bat"
echo title FunASR语音输入系统 - 精简版 >> "%target_dir%\start_minimal.bat"
echo color 0B >> "%target_dir%\start_minimal.bat"
echo. >> "%target_dir%\start_minimal.bat"
echo :: 配置FFmpeg环境 >> "%target_dir%\start_minimal.bat"
echo set PATH=%%~dp0ffmpeg\bin;%%PATH%% >> "%target_dir%\start_minimal.bat"
echo. >> "%target_dir%\start_minimal.bat"
echo :: 启动主程序 >> "%target_dir%\start_minimal.bat"
echo echo 🎤 正在启动FunASR精简版... >> "%target_dir%\start_minimal.bat"
echo echo 📍 工作目录: %%~dp0 >> "%target_dir%\start_minimal.bat"
echo echo. >> "%target_dir%\start_minimal.bat"
echo FunASR_VoiceInput_GUI_Minimal.exe %%* >> "%target_dir%\start_minimal.bat"
    echo ✅ 精简版启动脚本更新完成
)

:: 统计文件大小
echo.
echo 📊 统计FFmpeg文件大小...
echo FFmpeg依赖总大小:
if exist "%target_dir%\ffmpeg" (
    dir /s "%target_dir%\ffmpeg" | findstr "个文件"
)

:: 创建FFmpeg说明文件
echo.
echo 📄 创建FFmpeg说明文件...
echo # FFmpeg依赖说明 > "%target_dir%\ffmpeg_included.txt"
echo. >> "%target_dir%\ffmpeg_included.txt"
echo ## 📦 已包含的FFmpeg组件 >> "%target_dir%\ffmpeg_included.txt"
echo. >> "%target_dir%\ffmpeg_included.txt"
echo - ✅ ffmpeg.exe - 视频/音频处理工具 >> "%target_dir%\ffmpeg_included.txt"
echo - ✅ ffplay.exe - 媒体播放器 >> "%target_dir%\ffmpeg_included.txt"
echo - ✅ ffprobe.exe - 媒体信息查看工具 >> "%target_dir%\ffmpeg_included.txt"
echo - ✅ 相关DLL库文件 >> "%target_dir%\ffmpeg_included.txt"
echo. >> "%target_dir%\ffmpeg_included.txt"
echo ## 🔧 使用说明 >> "%target_dir%\ffmpeg_included.txt"
echo. >> "%target_dir%\ffmpeg_included.txt"
echo 1. 运行程序时会自动配置FFmpeg环境 >> "%target_dir%\ffmpeg_included.txt"
echo 2. 如需手动测试，可运行: setup_ffmpeg.bat >> "%target_dir%\ffmpeg_included.txt"
echo 3. 启动脚本已自动包含FFmpeg路径 >> "%target_dir%\ffmpeg_included.txt"
echo. >> "%target_dir%\ffmpeg_included.txt"
echo ## 📄 许可证 >> "%target_dir%\ffmpeg_included.txt"
echo FFmpeg遵循LGPL/GPL许可证，详见ffmpeg\LICENSE.txt >> "%target_dir%\ffmpeg_included.txt"

echo ✅ FFmpeg说明文件创建完成

:: 显示结果
echo.
echo ==============================================
echo 🎉 FFmpeg依赖打包完成！
echo ==============================================
echo.
echo 📁 目标目录: %target_dir%
echo 📦 包含FFmpeg组件:
echo   ✅ ffmpeg.exe - 音视频处理
echo   ✅ ffplay.exe - 媒体播放
echo   ✅ ffprobe.exe - 媒体信息
echo   ✅ 相关DLL库文件
echo   ✅ 环境配置脚本
echo   ✅ 许可证文件
echo.
echo 🚀 现在程序已具备完整的音视频处理能力！
echo 📖 使用说明: 查看目标目录中的ffmpeg_included.txt
echo.

:: 询问是否打开目录
echo.
set /p open_dir=是否打开目标目录? (y/n): 
if "%open_dir%"=="y" (
    explorer "%target_dir%"
)

pause