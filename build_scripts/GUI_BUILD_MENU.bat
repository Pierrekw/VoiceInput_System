@echo off
title FunASR GUI打包工具菜单
color 0F

:menu
echo.
echo ==============================================
echo 🎨 FunASR GUI打包工具菜单
echo ==============================================
echo.
echo 📦 打包选项:
echo.
echo [1] 🚀 完整版打包 (GUI + 模型 + FFmpeg)
echo [2] ⚡ 精简版打包 (仅GUI + 必需依赖)
echo [3] 📁 单独添加模型文件到现有打包
echo [4] 🎬 单独添加FFmpeg到现有打包
echo [5] 🧪 快速测试打包 (最小依赖)
echo [6] 📋 查看打包说明
echo [7] 🧹 清理打包结果
echo [0] ❌ 退出
echo.
echo ==============================================

set /p choice=请选择操作 (0-7): 

if "%choice%"=="1" goto build_complete
if "%choice%"=="2" goto build_minimal
if "%choice%"=="3" goto add_models
if "%choice%"=="4" goto add_ffmpeg
if "%choice%"=="5" goto quick_test
if "%choice%"=="6" goto show_help
if "%choice%"=="7" goto cleanup
if "%choice%"=="0" goto exit

echo.
echo ❌ 无效选择，请重新输入
pause
goto menu

:build_complete
echo.
echo 🚀 开始完整版打包...
call build_gui_complete.bat
goto menu

:build_minimal
echo.
echo ⚡ 开始精简版打包...
call build_gui_minimal.bat
goto menu

:add_models
echo.
echo 📁 添加模型文件到现有打包...
call package_with_models.bat
goto menu

:add_ffmpeg
echo.
echo 🎬 添加FFmpeg到现有打包...
call package_with_ffmpeg.bat
goto menu

:quick_test
echo.
echo 🧪 开始快速测试打包...
call quick_build.bat
goto menu

:show_help
echo.
echo 📋 打包说明:
echo.
echo 🎯 打包目标: GUI界面 + 模型文件 + FFmpeg依赖
echo.
echo 📦 打包模式对比:
echo   [完整版] 包含所有组件，适合发布
echo   [精简版] 仅GUI和基础依赖，适合开发测试
echo   [快速测试] 最小依赖，快速验证功能
echo.
echo 🗂️  输出结构:
echo   FunASR_VoiceInput_GUI.exe     # 主程序 (GUI界面)
echo   model/                        # 语音识别模型
echo   ffmpeg/                       # 音视频处理库
echo   start_gui.bat                # 一键启动脚本
echo   README.txt                   # 使用说明
echo.
echo ⚠️  注意事项:
echo   - 确保已安装Python和Nuitka
echo   - 模型文件需提前下载到 model/fun 目录
echo   - FFmpeg依赖需位于 onnx_deps\ffmpeg-master-latest-win64-gpl-shared
echo   - 完整版打包时间较长，请耐心等待
echo.
pause
goto menu

:cleanup
echo.
echo 🧹 清理打包结果...
echo.
echo 即将清理以下目录:
echo   - build_gui\
echo   - build_gui_minimal\
echo   - build_quick\
echo   - build_custom\
echo   - build_* (其他打包结果)
echo.
set /p confirm=确认清理? (y/n): 
if "%confirm%"=="y" (
    echo.
    echo 🗑️  正在清理...
    cd ..
    if exist build_gui rmdir /s /q build_gui
    if exist build_gui_minimal rmdir /s /q build_gui_minimal
    if exist build_quick rmdir /s /q build_quick
    if exist build_custom rmdir /s /q build_custom
    if exist build_* rmdir /s /q build_*
    if exist __pycache__ rmdir /s /q __pycache__
    cd build_scripts
    echo ✅ 清理完成！
) else (
    echo ❌ 清理已取消
)
pause
goto menu

:exit
echo.
echo 👋 感谢使用FunASR打包工具！
echo 📋 详细说明请查看: nuitka_build_guide.md
echo.
pause
exit /b 0