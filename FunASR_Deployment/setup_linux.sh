#!/bin/bash

echo "========================================"
echo "FunASR CPU优化版本 - Linux环境安装"
echo "========================================"
echo ""
echo "此脚本将自动安装运行所需的所有依赖包"
echo "适用于只有Python环境的Linux系统"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未检测到Python3"
    echo "请先安装Python 3.8或更高版本"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

echo "✅ 检测到Python环境"
python3 --version

# 升级pip
echo ""
echo "🔄 正在升级pip..."
python3 -m pip install --upgrade pip

# 安装系统依赖（音频支持）
echo ""
echo "📦 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    echo "   检测到apt包管理器，安装音频库..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-dev
elif command -v yum &> /dev/null; then
    echo "   检测到yum包管理器，安装音频库..."
    sudo yum install -y portaudio-devel python3-devel
elif command -v dnf &> /dev/null; then
    echo "   检测到dnf包管理器，安装音频库..."
    sudo dnf install -y portaudio-devel python3-devel
else
    echo "   ⚠️  未识别的包管理器，可能需要手动安装portaudio开发库"
fi

# 安装Python依赖包
echo ""
echo "📦 安装Python依赖包..."

echo "   - 安装PyTorch (CPU版本)..."
python3 -m pip install torch==2.3.1+cpu torchvision==0.18.1+cpu torchaudio==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu

echo "   - 安装FunASR..."
python3 -m pip install funasr

echo "   - 安装PyAudio (音频处理)..."
python3 -m pip install pyaudio

echo "   - 安装其他依赖..."
python3 -m pip install numpy psutil

# 检查安装结果
echo ""
echo "🔍 检查安装结果..."

python3 -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" 2>/dev/null || echo "❌ PyTorch安装失败"
python3 -c "import funasr; print(f'✅ FunASR: {funasr.__version__}')" 2>/dev/null || echo "❌ FunASR安装失败"
python3 -c "import pyaudio; print('✅ PyAudio: 安装成功')" 2>/dev/null || echo "❌ PyAudio安装失败"
python3 -c "import numpy; print(f'✅ NumPy: {numpy.__version__}')" 2>/dev/null || echo "❌ NumPy安装失败"

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "📋 下一步操作："
echo "1. 将模型文件夹 model/fun/ 复制到当前目录"
echo "2. 运行基础测试：python3 test_cpu_basic.py"
echo "3. 运行语音识别：python3 test_funasr_cpu.py"
echo ""
echo "💡 权限设置："
echo "   chmod +x test_funasr_cpu.py"
echo "   chmod +x test_cpu_basic.py"
echo ""
echo "🔊 音频问题："
echo "   - 确保用户在audio组中：sudo usermod -a -G audio $USER"
echo "   - 重启系统使组权限生效"
echo ""