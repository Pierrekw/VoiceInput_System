# VoiceInput - Nuitka快速开始指南

## 🚀 一键打包

### Windows用户
```bash
# 1. 安装依赖
pip install -r requirements-nuitka.txt

# 2. 一键构建
build_nuitka.bat

# 3. 测试输出
python test_packaged_app.py
```

### Linux用户
```bash
# 1. 安装依赖
pip3 install -r requirements-nuitka.txt

# 2. 一键构建
chmod +x build_nuitka.sh
./build_nuitka.sh

# 3. 测试输出
python3 test_packaged_app.py
```

## 📦 输出文件

构建完成后，您将在 `build/` 目录中找到：

```
build/
├── VoiceInput_System.exe       # Windows可执行文件
├── VoiceInput_System           # Linux可执行文件
└── VoiceInput_System.dist/     # 独立目录 (可选)
```

## 📁 必要目录

确保这些目录与可执行文件在同一位置：

```
程序目录/
├── VoiceInput_System.exe       # 主程序
├── model/fun/                  # FunASR模型目录
├── onnx_deps/                  # ONNX依赖目录
├── config.yaml                 # 配置文件
└── voice_correction_dict.txt   # 词典文件
```

## ⚙️ 配置调整

如需修改模型路径，编辑 `config.yaml`：

```yaml
model:
  external_paths:
    enabled: true
    funasr_model_path: model/fun      # 修改为你的模型路径
    onnx_deps_path: onnx_deps         # 修改为你的依赖路径
```

## ✅ 验证成功

运行 `python test_packaged_app.py` 检查：

```
====================================
VoiceInput System - 打包后测试
====================================

📋 检查配置文件...
✅ 文件存在: config.yaml

🤖 检查模型文件...
✅ 文件存在: model/fun
✅ 文件存在: onnx_deps

📦 检查可执行文件...
📁 找到可执行文件: build/VoiceInput_System.exe
📊 文件大小: XX.XX MB

🧪 测试可执行文件基本功能...
✅ 可执行文件启动成功

====================================
测试结果汇总
配置文件................ ✅ 通过
模型文件................ ✅ 通过
可执行文件.............. ✅ 通过
功能测试................ ✅ 通过

总计: 4/4 项测试通过

🎉 所有测试通过！打包成功！
```

## 🐛 常见问题

**Q: 编译失败，提示内存不足**
A: 关闭其他程序，或增加虚拟内存

**Q: 找不到模型文件**
A: 确保 `model/fun` 目录存在且包含模型文件

**Q: ONNX runtime错误**
A: 检查 `onnx_deps` 目录和FFmpeg路径

**Q: PyTorch导入失败**
A: 使用官方CPU版本：
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 📚 完整文档

详细说明请参考：
- `NUITKA_PACKAGING_GUIDE.md` - 完整打包指南
- `NUITKA_PACKAGING_GUIDE.md#常见问题解决` - 问题排查

---

**版本**: v2.8  
**更新时间**: 2025-11-02
