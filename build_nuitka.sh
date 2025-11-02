#!/bin/bash
# ================================================================================
# VoiceInput System - Nuitka打包脚本 (Linux)
# ================================================================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "VoiceInput System - Nuitka打包 (Linux)"
echo "========================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印信息
print_info() {
    echo -e "${GREEN}[信息]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

# 检查Python环境
print_info "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    print_error "未找到Python3，请安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_info "当前Python版本: $PYTHON_VERSION"

# 检查Nuitka
print_info "检查Nuitka..."
if ! command -v nuitka3 &> /dev/null; then
    print_info "安装Nuitka..."
    pip3 install nuitka==1.9.2
else
    print_info "Nuitka已安装"
fi

# 安装依赖
echo
print_info "步骤 1/4: 安装依赖包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "依赖安装失败"
    exit 1
fi

# 安装Nuitka特定依赖
echo
print_info "步骤 2/4: 安装Nuitka插件依赖..."
pip3 install ordered-set zstandard
pip3 install --upgrade nuitka

# 创建构建目录
echo
print_info "步骤 3/4: 创建构建目录..."
mkdir -p build
mkdir -p dist

# 清理之前的构建
rm -f VoiceInput_System
rm -rf build/VoiceInput_System.dist
rm -rf build/VoiceInput_System.bin

# 检查主程序文件
if [ ! -f "funasr_voice_combined.py" ]; then
    print_error "未找到主程序文件 funasr_voice_combined.py"
    exit 1
fi

# 执行Nuitka打包
echo
print_info "步骤 4/4: 执行Nuitka打包..."
print_info "这可能需要较长时间，请耐心等待..."
echo

nuitka3 \
    --onefile \
    --standalone \
    --enable-plugin=pytorch \
    --enable-plugin=numpy \
    --enable-cc=yes \
    --cache-dir=.nuitka-cache \
    --optimize-level=3 \
    --output-dir=build \
    --output-filename=VoiceInput_System \
    --include-data-dir=model/fun=model/fun \
    --include-data-dir=onnx_deps=onnx_deps \
    --include-data-dir=config=config \
    --include-data-file=voice_correction_dict.txt=voice_correction_dict.txt \
    funasr_voice_combined.py

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo -e "${GREEN}✅ 打包成功！${NC}"
    echo "========================================"
    echo
    echo "输出文件:"
    
    if [ -f "build/VoiceInput_System" ]; then
        print_info "可执行文件: build/VoiceInput_System"
        ls -lh build/VoiceInput_System
    fi
    
    if [ -d "build/VoiceInput_System.dist" ]; then
        print_info "独立目录: build/VoiceInput_System.dist/"
        du -sh build/VoiceInput_System.dist
    fi
    
    echo
    echo "使用说明:"
    echo "1. 将model/fun和onnx_deps文件夹复制到程序目录"
    echo "2. 确保config.yaml中的路径配置正确"
    echo "3. 运行: ./build/VoiceInput_System"
    echo
else
    echo
    echo "========================================"
    echo -e "${RED}❌ 打包失败${NC}"
    echo "========================================"
    echo "请检查错误信息并重试"
    echo
    exit 1
fi
