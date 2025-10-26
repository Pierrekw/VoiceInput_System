@echo off
title FunASR Nuitka打包工具 - Windows版本
color 0A

echo.
echo ==============================================
echo 🚀 FunASR Nuitka打包工具
echo ==============================================
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

:: 检查Nuitka
python -c "import nuitka" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 正在安装Nuitka...
    python -m pip install nuitka ordered-set
)

echo ✅ Nuitka环境检查通过

:: 清理旧文件
echo.
echo 🧹 清理旧文件...
if exist build (
    echo 删除旧build目录...
    rmdir /s /q build
)
if exist build_modules (
    echo 删除旧build_modules目录...
    rmdir /s /q build_modules
)
if exist __pycache__ (
    echo 删除__pycache__...
    rmdir /s /q __pycache__
)
if exist .pytest_cache (
    echo 删除.pytest_cache...
    rmdir /s /q .pytest_cache
)
if exist .mypy_cache (
    echo 删除.mypy_cache...
    rmdir /s /q .mypy_cache
)

:: 选择打包模式
echo.
echo ==============================================
echo 📋 选择打包模式:
echo ==============================================
echo 1️⃣ 快速测试打包 (推荐初次尝试)
echo 2️⃣ 标准优化打包 (推荐日常使用)
echo 3️⃣ 高级优化打包 (文件最小化)
echo 4️⃣ 分模块打包 (解决大文件问题)
echo 5️⃣ 自定义打包 (高级用户)
echo.
set /p choice=请选择模式 (1-5): 

if "%choice%"=="1" goto :fast_build
if "%choice%"=="2" goto :standard_build
if "%choice%"=="3" goto :advanced_build
if "%choice%"=="4" goto :module_build
if "%choice%"=="5" goto :custom_build

echo ❌ 无效选择，默认使用快速打包
goto :fast_build

:fast_build
echo.
echo 🚀 开始快速测试打包...
echo 模式说明: 基础功能，快速编译，适合测试
echo.

python -m nuitka main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --enable-plugin=numpy ^
    --enable-plugin=torch ^
    --output-dir=build ^
    --output-filename=FunASR_VoiceInput_Test ^
    --jobs=4

goto :finish

:standard_build
echo.
echo 🚀 开始标准优化打包...
echo 模式说明: 平衡性能和文件大小，推荐日常使用
echo.

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
    --output-filename=FunASR_VoiceInput ^
    --windows-disable-console ^
    --jobs=8 ^
    --lto=yes ^
    --assume-yes-for-downloads

goto :finish

:advanced_build
echo.
echo 🚀 开始高级优化打包...
echo 模式说明: 文件最小化，最长编译时间
echo.

:: 检查UPX
where upx >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 发现UPX压缩工具
    set UPX_FLAG=--upx-binary=upx.exe
) else (
    echo ⚠️ 未找到UPX，文件大小可能较大
    set UPX_FLAG=
)

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
    --output-filename=FunASR_VoiceInput ^
    --windows-disable-console ^
    --jobs=8 ^
    --lto=yes ^
    --clang ^
    --assume-yes-for-downloads ^
    --remove-output ^
    --no-pyi-file ^
    %UPX_FLAG%

goto :finish

:module_build
echo.
echo 🚀 开始分模块打包...
echo 模式说明: 先编译核心模块，再编译主程序，解决大文件问题
echo.

echo 📦 第一步: 编译核心模块...
python -m nuitka funasr_voice_module.py ^
    --module ^
    --enable-plugin=numpy ^
    --enable-plugin=torch ^
    --include-package=funasr ^
    --include-package-data=funasr ^
    --output-dir=build_modules

echo 📦 第二步: 编译主程序...
python -m nuitka main_f.py ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --module-interaction=build_modules/funasr_voice_module.py ^
    --include-data-dir=config=./config ^
    --include-data-dir=model=./model ^
    --include-data-file=config.yaml=./config.yaml ^
    --include-data-file=voice_correction_dict.txt=./voice_correction_dict.txt ^
    --output-dir=build ^
    --output-filename=FunASR_VoiceInput ^
    --windows-disable-console ^
    --jobs=8 ^
    --lto=yes

goto :finish

:custom_build
echo.
echo 🛠️ 自定义打包模式
echo 请编辑 build_nuitka_custom.bat 文件来设置自定义参数
echo.
if exist build_scripts\build_nuitka_custom.bat (
    echo ✅ 运行自定义配置...
    call build_scripts\build_nuitka_custom.bat
) else (
    echo ❌ 未找到自定义配置文件
    echo 正在创建模板...
    echo @echo off > build_scripts\build_nuitka_custom.bat
    echo :: 在此添加您的自定义Nuitka参数 >> build_scripts\build_nuitka_custom.bat
    echo :: 示例: >> build_scripts\build_nuitka_custom.bat
    echo python -m nuitka main_f.py --standalone --enable-plugin=pyside6 >> build_scripts\build_nuitka_custom.bat
)
pause
goto :menu

:finish
echo.
echo ==============================================
if %errorlevel% equ 0 (
    echo ✅ 打包完成！
    echo 📁 输出目录: build\FunASR_VoiceInput.dist\
    echo 🚀 可执行文件: build\FunASR_VoiceInput.dist\FunASR_VoiceInput.exe
    echo.
    echo 🧪 测试命令:
    echo cd build\FunASR_VoiceInput.dist
    echo FunASR_VoiceInput.exe --help
) else (
    echo ❌ 打包失败，请检查错误信息
    echo 📋 查看 nuitka_build_guide.md 获取帮助
)
echo ==============================================

:menu
echo.
echo 📋 其他选项:
echo 1️⃣ 查看打包结果
echo 2️⃣ 测试打包程序
echo 3️⃣ 清理构建文件
echo 4️⃣ 退出
echo.
set /p next_choice=请选择操作 (1-4): 

if "%next_choice%"=="1" (
    if exist build\FunASR_VoiceInput.dist (
        echo 📁 打开打包结果目录...
        explorer build\FunASR_VoiceInput.dist
    ) else (
        echo ❌ 打包结果目录不存在
    )
    goto :menu
)

if "%next_choice%"=="2" (
    if exist build\FunASR_VoiceInput.dist\FunASR_VoiceInput.exe (
        echo 🧪 运行测试...
        cd build\FunASR_VoiceInput.dist
        FunASR_VoiceInput.exe --help
        cd ..\..
    ) else (
        echo ❌ 可执行文件不存在
    )
    goto :menu
)

if "%next_choice%"=="3" (
    echo 🧹 清理构建文件...
    if exist build rmdir /s /q build
    if exist build_modules rmdir /s /q build_modules
    echo ✅ 清理完成
    goto :menu
)

if "%next_choice%"=="4" (
    echo 👋 感谢使用FunASR打包工具！
    pause
    exit /b 0
)

goto :menu