@echo off
echo ========================================
echo Voice Input 项目复制脚本
echo ========================================
echo.

set "SOURCE_DIR=%~dp0"
set "DEST_DIR=%1"

if "%DEST_DIR%"=="" (
    echo 使用方法: %0 [目标目录]
    echo 例如: %0 D:\Voice_Input_Backup
    pause
    exit /b 1
)

echo 源目录: %SOURCE_DIR%
echo 目标目录: %DEST_DIR%
echo.

if not exist "%DEST_DIR%" (
    echo 创建目标目录: %DEST_DIR%
    mkdir "%DEST_DIR%"
)

echo 开始复制文件...
echo.

:: 复制核心程序文件
echo [1/8] 复制核心程序文件...
copy "%SOURCE_DIR%voice_gui.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%main_f.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%config.yaml" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%config_loader.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%voice_correction_dict.txt" "%DEST_DIR%\" >nul
echo ✓ 核心程序文件复制完成

:: 复制核心模块
echo [2/8] 复制核心模块...
copy "%SOURCE_DIR%excel_utils.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%funasr_voice_tenvad.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%text_processor.py" "%DEST_DIR%\" >nul
echo ✓ 核心模块复制完成

:: 复制依赖配置
echo [3/8] 复制依赖配置...
copy "%SOURCE_DIR%requirements.txt" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%pyproject.toml" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%setup.py" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%.python-version" "%DEST_DIR%\" >nul
echo ✓ 依赖配置复制完成

:: 复制项目文档
echo [4/8] 复制项目文档...
copy "%SOURCE_DIR%README.md" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%LICENSE" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%DEPLOYMENT_CHECKLIST.md" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%INSTALLATION_GUIDE.md" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%COPY_SCRIPT.bat" "%DEST_DIR%\" >nul
echo ✓ 项目文档复制完成

:: 复制配置文件
echo [5/8] 复制配置文件...
copy "%SOURCE_DIR%config_bak.yaml" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%mypy.ini" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%pytest.ini" "%DEST_DIR%\" >nul
copy "%SOURCE_DIR%.pre-commit-config.yaml" "%DEST_DIR%\" >nul
echo ✓ 配置文件复制完成

:: 复制工具模块
echo [6/8] 复制工具模块...
if exist "%DEST_DIR%utils" rmdir /s /q "%DEST_DIR%utils"
xcopy "%SOURCE_DIR%utils" "%DEST_DIR%utils\" /E /I /H >nul
echo ✓ 工具模块复制完成

:: 复制Excel模板
echo [7/8] 复制Excel模板...
if exist "%DEST_DIR%reports" rmdir /s /q "%DEST_DIR%reports"
xcopy "%SOURCE_DIR%reports" "%DEST_DIR%reports\" /E /I /H >nul
echo ✓ Excel模板复制完成

:: 复制模型文件 (最耗时的部分)
echo [8/8] 复制模型文件 (这可能需要几分钟)...
if exist "%DEST_DIR%model" rmdir /s /q "%DEST_DIR%model"
xcopy "%SOURCE_DIR%model" "%DEST_DIR%model\" /E /I /H >nul
echo ✓ 模型文件复制完成

:: 创建必要目录
echo.
echo 创建运行时目录...
mkdir "%DEST_DIR%logs" 2>nul
mkdir "%DEST_DIR%outputs" 2>nul
mkdir "%DEST_DIR%debug" 2>nul
mkdir "%DEST_DIR%archive" 2>nul
mkdir "%DEST_DIR%backup" 2>nul
echo ✓ 目录创建完成

:: 创建__init__.py文件
echo 创建包初始化文件...
echo. > "%DEST_DIR%\__init__.py"
echo. > "%DEST_DIR%\utils\__init__.py" 2>nul
echo ✓ 包初始化文件创建完成

:: 显示复制结果
echo.
echo ========================================
echo 复制完成！
echo ========================================
echo.
echo 目标目录: %DEST_DIR%
echo 复制的文件大小:
dir "%DEST_DIR%" /s | find "个文件"
echo.
echo 下一步操作:
echo 1. 在目标机器上安装Python 3.11+
echo 2. 安装uv: pip install uv
echo 3. 在目标目录运行: uv sync
echo 4. 运行程序: python voice_gui.py
echo.
echo 详细说明请查看:
echo - INSTALLATION_GUIDE.md (安装指南)
echo - DEPLOYMENT_CHECKLIST.md (部署清单)
echo.
pause