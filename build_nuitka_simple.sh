#!/bin/bash
# VoiceInput System - Nuitka Build Script (Linux)

set -e

echo "========================================"
echo "VoiceInput System - Nuitka Build (Linux)"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[INFO] Python version: $PYTHON_VERSION"

# Install Nuitka if not exists
if ! command -v nuitka3 &> /dev/null; then
    echo "[INFO] Installing Nuitka..."
    pip3 install nuitka==1.9.2
fi

# Install dependencies
echo
echo "[STEP 1/3] Installing dependencies..."
pip3 install -r requirements-nuitka.txt

# Create directories
echo
echo "[STEP 2/3] Creating directories..."
mkdir -p build dist

# Clean previous build
rm -f VoiceInput_System
rm -rf build/VoiceInput_System.dist

# Check main file
if [ ! -f "funasr_voice_combined.py" ]; then
    echo "[ERROR] Main file not found: funasr_voice_combined.py"
    exit 1
fi

# Build with Nuitka
echo
echo "[STEP 3/3] Building with Nuitka..."
nuitka3 \
    --onefile \
    --standalone \
    --enable-plugin=pytorch \
    --enable-plugin=numpy \
    --cache-dir=.nuitka-cache \
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
    echo "BUILD SUCCESSFUL!"
    echo "========================================"
    echo
    if [ -f "build/VoiceInput_System" ]; then
        ls -lh build/VoiceInput_System
    fi
else
    echo
    echo "========================================"
    echo "BUILD FAILED"
    echo "========================================"
    exit 1
fi
