@echo off
title FunASR Nuitka自定义打包配置
echo.
echo ==============================================
echo 🛠️ FunASR Nuitka自定义打包配置
echo ==============================================
echo.

:: 在此添加您的自定义Nuitka参数
:: 示例配置，请根据需要进行修改

:: 基础参数
echo 📋 使用自定义配置打包...

python -m nuitka main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --enable-plugin=numpy ^
    --enable-plugin=torch ^
    --include-package=funasr ^
    --include-package=modelscope ^
    --include-package-data=funasr ^
    --include-package-data=modelscope ^
    --include-data-dir=config=./config ^
    --include-data-dir=model=./model ^
    --include-data-file=config.yaml=./config.yaml ^
    --include-data-file=voice_correction_dict.txt=./voice_correction_dict.txt ^
    --output-dir=build ^
    --output-filename=FunASR_VoiceInput_Custom ^
    --windows-disable-console ^
    --jobs=4 ^
    --lto=yes ^
    --assume-yes-for-downloads

:: 可选参数 (根据需要取消注释)
:: --windows-icon-from-ico=icon.ico ^
:: --upx-binary=upx.exe ^
:: --clang ^
:: --remove-output ^
:: --no-pyi-file ^
:: --debug ^
:: --execute

echo.
echo ✅ 自定义打包完成！
echo 📁 输出目录: build\FunASR_VoiceInput_Custom.dist\
pause