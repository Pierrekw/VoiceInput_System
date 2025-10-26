#!/bin/bash

echo "========================================"
echo "FunASR 便携版环境设置 (Linux)"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FFMPEG_PATH="$SCRIPT_DIR/dependencies/ffmpeg-master-latest-win64-gpl-shared/bin"

# 设置FFmpeg路径（如果有Linux版本的ffmpeg）
if [ -d "$SCRIPT_DIR/dependencies/ffmpeg-linux" ]; then
    FFMPEG_PATH="$SCRIPT_DIR/dependencies/ffmpeg-linux/bin"
fi

export PATH="$FFMPEG_PATH:$PATH"

echo "✅ FFmpeg路径已设置:"
echo "   $FFMPEG_PATH"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3可用: $(python3 --version)"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ Python可用: $(python --version)"
    PYTHON_CMD="python"
else
    echo "❌ Python未找到，请先安装Python"
    exit 1
fi

echo ""
echo "========================================"
echo "📋 使用说明"
echo "========================================"
echo ""
echo "🎯 环境已配置完成，可以运行FunASR程序："
echo ""
echo "基础测试:"
echo "   $PYTHON_CMD test_cpu_basic.py"
echo ""
echo "语音识别:"
echo "   $PYTHON_CMD test_funasr_cpu.py"
echo ""
echo "⚠️  重要提醒:"
echo "   - 此设置仅在当前终端会话有效"
echo "   - 关闭终端后需要重新运行此脚本"
echo ""

echo "🚀 现在可以运行FunASR程序了！"
echo ""

# 如果有参数，直接运行指定的程序
if [ $# -gt 0 ]; then
    echo "🔄 正在运行: $*"
    "$@"
fi