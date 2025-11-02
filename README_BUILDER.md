# VoiceInput - Nuitka Builder

🚀 **一键打包VoiceInput为独立可执行文件**

## ⚡ 快速开始

### Windows
```cmd
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

## 📦 输出

构建完成后，在 `build/` 目录中找到：
- **Windows**: `VoiceInput_System.exe`
- **Linux**: `VoiceInput_System`

## 📁 必要文件

确保这些目录存在：
- `model/fun/` - FunASR模型
- `onnx_deps/` - ONNX依赖
- `config.yaml` - 配置文件

## 📚 文档

- [BUILD_SYSTEM_README.md](BUILD_SYSTEM_README.md) - 完整说明
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) - 快速指南
- [NUITKA_PACKAGING_GUIDE.md](NUITKA_PACKAGING_GUIDE.md) - 详细指南

## ✅ 验证

```bash
python test_packaged_app.py
```

## 🔧 配置

修改 `config.yaml` 中的模型路径：
```yaml
model:
  external_paths:
    enabled: true
    funasr_model_path: model/fun
    onnx_deps_path: onnx_deps
```

---

**支持**: 完整替代PyInstaller，性能更优，模型支持更好
