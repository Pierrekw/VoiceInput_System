# VoiceInput - 轻量级构建指南

## 🎯 轻量级构建说明

轻量级构建是专门为**已有完整环境**的用户设计的快速构建方案。

## ⚡ 优势

- **快速安装**: 仅需10MB下载
- **跳过大型依赖**: 不重复安装torch、funasr等 (~1GB+)
- **相同构建效果**: 与完整构建100%一致
- **节省时间**: 依赖安装 < 1分钟

## 📋 系统要求

### 必须已安装
- Python 3.8+
- 完整依赖环境 (通过 `requirements-nuitka.txt` 安装过)

### 可选但推荐
- Visual Studio (Windows) 或 GCC (Linux) - 用于C编译优化

## 🚀 使用方法

### Windows
```cmd
# 如果Nuitka未安装，会自动安装轻量级依赖
build_nuitka_light.bat
```

### Linux/macOS
```bash
chmod +x build_nuitka_light.sh
./build_nuitka_light.sh
```

## 📦 依赖对比

### 完整构建 (requirements-nuitka.txt)
```
torch==2.3.1+cpu       (~200MB)
funasr==1.0.22         (~500MB)
onnxruntime>=1.12.0    (~50MB)
numpy>=1.21.0          (~50MB)
... (共 ~1GB+)
```

### 轻量级构建 (requirements-nuitka-light.txt)
```
nuitka==1.9.2          (~5MB)
ordered-set==4.1.0     (<1MB)
zstandard==0.21.0      (~5MB)
总计: ~10MB
```

## ❓ 何时使用

### 使用轻量级构建
✅ 您的项目已经安装了完整依赖  
✅ 之前使用过 `requirements-nuitka.txt`  
✅ 在开发环境中已经运行过VoiceInput  
✅ 只想快速重新构建可执行文件  

### 使用完整构建
❗ 首次设置构建环境  
❗ 依赖环境不完整或损坏  
❗ 不确定是否安装了所有依赖  
❗ 从零开始配置  

## 🔍 验证环境

检查是否可以使用轻量级构建：

```bash
# 检查Nuitka
where nuitka3  # Windows
which nuitka3  # Linux/macOS

# 检查关键依赖
python -c "import torch, funasr, onnxruntime; print('All dependencies OK')"
```

如果上述命令都成功，您可以使用轻量级构建！

## 📊 性能对比

| 指标 | 完整构建 | 轻量级构建 |
|------|---------|-----------|
| **依赖安装** | 5-20分钟 | < 1分钟 |
| **依赖大小** | ~1GB+ | ~10MB |
| **构建时间** | 10-20分钟 | 10-20分钟 |
| **构建结果** | ✅ 完全一致 | ✅ 完全一致 |

**注意**: 构建时间相同，因为只与代码复杂度有关，与依赖安装无关。

## 🐛 故障排除

### 错误: ModuleNotFoundError
**原因**: 缺少某些依赖  
**解决**: 使用完整构建
```cmd
pip install -r requirements-nuitka.txt
build_nuitka.bat
```

### 错误: nuitka3 not found
**原因**: Nuitka未安装  
**解决**: 轻量级脚本会自动安装，或手动安装：
```cmd
pip install nuitka==1.9.2 ordered-set zstandard
```

### 错误: C编译器未找到
**原因**: 缺少Visual Studio/GCC  
**解决**: 
- Windows: 安装 Visual Studio Build Tools
- Linux: 安装 build-essential

## 📞 支持

如遇问题：
1. 尝试完整构建：`pip install -r requirements-nuitka.txt`
2. 查看构建日志：`build/` 目录
3. 参考主文档：`BUILD_README.md`

---

**提示**: 轻量级构建是完整构建的快捷方式，效果完全相同！

**版本**: v2.8  
**更新时间**: 2025-11-02
