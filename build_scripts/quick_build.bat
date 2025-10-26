@echo off
title FunASR快速打包
color 0A

echo.
echo ==============================================
echo ⚡ FunASR快速打包模式
echo ==============================================
echo.

:: 快速打包，适合测试和开发
echo 🚀 开始快速打包...
echo ⚠️  注意：此模式文件较大，性能一般，仅适合测试使用
echo.

:: 清理旧文件
if exist build rmdir /s /q build

:: 基础打包
python -m nuitka main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --enable-plugin=numpy ^
    --enable-plugin=torch ^
    --output-dir=build ^
    --output-filename=FunASR_VoiceInput_Quick ^
    --jobs=4

echo.
echo ✅ 快速打包完成！
echo 📁 输出目录: build\FunASR_VoiceInput_Quick.dist\
echo 🧪 测试命令: cd build\FunASR_VoiceInput_Quick.dist && FunASR_VoiceInput_Quick.exe --help
pause