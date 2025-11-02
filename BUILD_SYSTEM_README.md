# VoiceInput Build System - README

## Overview

This directory contains the complete build system for packaging VoiceInput into standalone executables using Nuitka (alternative to PyInstaller).

## Why Nuitka?

| Feature | PyInstaller | Nuitka |
|---------|-------------|--------|
| Startup Speed | Slow | **Fast** |
| Memory Usage | High | **Low** |
| File Size | Large | **Medium** |
| ML Model Support | Poor | **Excellent** |
| Performance | Average | **Superior** |

## Quick Start

### Windows
```cmd
pip install -r requirements-nuitka.txt
build_nuitka.bat
```

### Linux
```bash
pip3 install -r requirements-nuitka.txt
chmod +x build_nuitka_simple.sh
./build_nuitka_simple.sh
```

## File Structure

```
Build System/
├── Build Scripts/
│   ├── build_nuitka.bat         # Windows build
│   ├── build_nuitka_simple.sh   # Linux build
│   └── build_nuitka.sh          # Detailed Linux build
│
├── Configuration/
│   ├── config.yaml              # App config (with external paths)
│   ├── nuitka.ini              # Nuitka config
│   └── requirements-nuitka.txt # Python dependencies
│
├── Documentation/
│   ├── BUILD_INSTRUCTIONS.md    # Quick start
│   ├── BUILD_SYSTEM_README.md   # This file
│   ├── NUITKA_PACKAGING_GUIDE.md # Complete guide
│   └── QUICK_START_NUITKA.md    # Quick reference
│
└── Testing/
    ├── test_packaged_app.py     # Post-build verification
    └── verify_build_files.py    # Verify build system files
```

## Configuration

### External Model Paths (config.yaml)
```yaml
model:
  external_paths:
    enabled: true
    funasr_model_path: model/fun   # FunASR models
    onnx_deps_path: onnx_deps      # ONNX dependencies
```

### Nuitka Options (nuitka.ini)
```
[main]
onefile=True              # Single executable
enable-plugin=pytorch     # PyTorch support
enable-plugin=numpy       # NumPy support
include-data-dir=model/fun=model/fun
include-data-dir=onnx_deps=onnx_deps
```

## Build Output

After successful build:
```
build/
├── VoiceInput_System.exe      # Windows
├── VoiceInput_System          # Linux
└── VoiceInput_System.dist/    # Standalone directory
```

## Required Directories

For the executable to work, ensure these directories exist:
```
Program Directory/
├── VoiceInput_System.exe       # Main program
├── model/fun/                  # FunASR model files
├── onnx_deps/                  # ONNX dependencies
├── config.yaml                 # Configuration file
└── voice_correction_dict.txt   # Voice dictionary
```

## Testing

Verify the build with:
```bash
python test_packaged_app.py
```

This will check:
- Configuration file
- Model files
- Executable file
- Basic functionality

## Troubleshooting

### Build Errors

**Memory Error**
- Close other programs
- Increase virtual memory
- Use `--low-memory` flag

**Module Not Found**
- Verify all dependencies in requirements-nuitka.txt
- Reinstall: `pip install -r requirements-nuitka.txt`

**Model Files Missing**
- Ensure model/fun directory exists
- Check config.yaml paths
- Verify file permissions

### Runtime Errors

**ONNX Runtime**
- Verify onnx_deps/ffmpeg is present
- Check system PATH variable
- Install Microsoft Visual C++ Redistributable

**PyTorch**
- Use CPU-only version:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## Advanced Usage

### Debug Mode
```bash
nuitka3 --debug=all main.py
```

### Custom Data
```bash
--include-data-dir=your_data=your_data
```

### Optimization
```bash
--optimize-level=3
--enable-cc=yes
```

## Documentation

| Document | Purpose |
|----------|---------|
| BUILD_INSTRUCTIONS.md | Quick start guide |
| NUITKA_PACKAGING_GUIDE.md | Complete technical guide |
| QUICK_START_NUITKA.md | Command reference |
| BUILD_SYSTEM_README.md | This file - system overview |

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB+ available
- **Disk**: 2GB+ free space
- **Time**: 10-20 minutes (first build)

## Performance Tips

1. **Use SSD**: Faster I/O during compilation
2. **Close Other Apps**: Free up RAM
3. **Cache**: Nuitka caches compilation results
4. **Onefile vs Standalone**:
   - Onefile: Larger, easier distribution
   - Standalone: Smaller, requires directory

## Support

For issues:
1. Check build logs in `build/` directory
2. Review cache info in `.nuitka-cache/`
3. Verify dependency versions
4. See NUITKA_PACKAGING_GUIDE.md#troubleshooting

## Version History

- **v2.8** (2025-11-02): Initial Nuitka build system
  - External model path support
  - Windows/Linux automated builds
  - Complete documentation
  - Test automation

## License

Same as main VoiceInput project.

---

**Last Updated**: 2025-11-02  
**Maintained by**: VoiceInput Development Team
