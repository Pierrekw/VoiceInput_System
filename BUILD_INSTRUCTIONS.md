# VoiceInput - Build Instructions

## Quick Start

### Windows
```bash
pip install -r requirements-nuitka.txt
build_nuitka.bat
python test_packaged_app.py
```

### Linux
```bash
pip3 install -r requirements-nuitka.txt
chmod +x build_nuitka_simple.sh
./build_nuitka_simple.sh
python3 test_packaged_app.py
```

## Output Files

After successful build, you will find:

```
build/
├── VoiceInput_System.exe      # Windows executable
├── VoiceInput_System          # Linux executable
└── VoiceInput_System.dist/    # Standalone directory
```

## Required Directories

Make sure these directories exist alongside the executable:

```
Program Directory/
├── VoiceInput_System.exe      # Main program
├── model/fun/                 # FunASR models
├── onnx_deps/                 # ONNX dependencies
├── config.yaml                # Configuration
└── voice_correction_dict.txt  # Dictionary
```

## Troubleshooting

**Q: Build fails with memory error**
A: Close other programs or increase virtual memory

**Q: Model files not found**
A: Ensure model/fun directory exists with model files

**Q: ONNX runtime error**
A: Check onnx_deps directory and FFmpeg path

**Q: PyTorch import fails**
A: Use official CPU version:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## Build Options

### Onefile Mode (Default)
Single executable file, easy to distribute
```bash
nuitka3 --onefile main.py
```

### Standalone Mode
Independent directory with all dependencies
```bash
nuitka3 --standalone main.py
```

## Verification

Run the test script to verify the build:
```bash
python test_packaged_app.py
```

Expected output:
```
====================================
VoiceInput System - Packaged Test
====================================

Configuration file............. ✅ Pass
Model files.................... ✅ Pass
Executable file................ ✅ Pass
Function test.................. ✅ Pass

Total: 4/4 tests passed

🎉 All tests passed! Build successful!
```

---

**Version**: v2.8  
**Updated**: 2025-11-02
