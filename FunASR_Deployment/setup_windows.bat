@echo off
chcp 65001 >nul
echo ========================================
echo FunASR CPU优化版本 - Windows环境安装
echo ========================================
echo.
echo 此脚本将自动安装运行所需的所有依赖包
echo 适用于只有Python环境的Windows电脑
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.8或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo.
    echo 安装Python时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ 检测到Python环境
python --version

REM 升级pip
echo.
echo 🔄 正在升级pip...
python -m pip install --upgrade pip

REM 安装核心依赖包
echo.
echo 📦 安装核心依赖包...

echo   - 安装PyTorch (CPU版本，适合无显卡环境)...
python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu

echo   - 安装FunASR...
python -m pip install funasr

echo   - 安装PyAudio (音频处理)...
python -m pip install pyaudio

echo   - 安装其他依赖...
python -m pip install numpy psutil

REM 检查安装结果
echo.
echo 🔍 检查安装结果...

python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" 2>nul || echo "❌ PyTorch安装失败"
python -c "import funasr; print(f'✅ FunASR: {funasr.__version__}')" 2>nul || echo "❌ FunASR安装失败"
python -c "import pyaudio; print('✅ PyAudio: 安装成功')" 2>nul || echo "❌ PyAudio安装失败"
python -c "import numpy; print(f'✅ NumPy: {numpy.__version__}')" 2>nul || echo "❌ NumPy安装失败"

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 📋 下一步操作：
echo 1. 将模型文件夹 model\fun\ 复制到当前目录
echo 2. 运行基础测试：python test_cpu_basic.py
echo 3. 运行语音识别：python test_funasr_cpu.py
echo.
echo 💡 如果遇到问题：
echo   - PyAudio安装失败：需要安装Visual C++ Build Tools
echo   - 麦克风问题：检查系统音频权限设置
echo.
pause