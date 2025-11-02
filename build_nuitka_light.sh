#!/bin/bash
# ================================================================================
# VoiceInput System - Nuitka Light Build (Linux)
# Only install Nuitka dependencies, suitable for environments with existing setup
# ================================================================================

set -e

echo "========================================"
echo "VoiceInput System - Nuitka Light Build (Linux)"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[INFO] Python version: $PYTHON_VERSION"

# Check if Nuitka is already installed
if ! command -v nuitka3 &> /dev/null; then
    echo "[INFO] Installing Nuitka..."
    pip3 install nuitka==1.9.2 ordered-set zstandard
else
    echo "[INFO] Nuitka already installed"
fi

# Skip other dependencies (assume full environment is already set up)
echo
echo "[SKIP] Dependencies check skipped (using existing environment)"
echo "[INFO] Ensure these are already installed:"
echo "  - torch, torchaudio (PyTorch)"
echo "  - funasr (Voice Recognition)"
echo "  - onnxruntime (ONNX Runtime)"
echo "  - numpy, pandas (Data Processing)"
echo "  - openpyxl (Excel)"
echo "  - cn2an (Chinese Number)"
echo

# Create directories
echo "[STEP] Creating directories..."
mkdir -p build dist

# Clean previous build
rm -f VoiceInput_System
rm -rf build/VoiceInput_System.dist

# Check main file
if [ ! -f "funasr_voice_combined.py" ]; then
    echo "[ERROR] Main file not found: funasr_voice_combined.py"
    exit 1
fi

# Check required directories
if [ ! -d "model/fun" ]; then
    echo "[WARNING] Model directory not found: model/fun"
    echo "Please ensure model files are present before running"
fi

if [ ! -d "onnx_deps" ]; then
    echo "[WARNING] ONNX dependencies directory not found: onnx_deps"
    echo "Please ensure ONNX dependencies are present before running"
fi

# Build with Nuitka
echo
echo "[STEP] Building with Nuitka..."
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
    if [ -d "build/VoiceInput_System.dist" ]; then
        du -sh build/VoiceInput_System.dist
    fi
else
    echo
    echo "========================================"
    echo "BUILD FAILED"
    echo "========================================"
    echo "Please check error messages and try again"
    echo
    echo "Tip: If you see import errors, ensure all dependencies are installed:"
    echo "  pip3 install -r requirements-nuitka.txt"
    echo
    exit 1
fi
