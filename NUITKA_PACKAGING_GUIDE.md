# VoiceInput System - Nuitka打包指南

## 📋 概述

本指南说明如何使用Nuitka将VoiceInput系统打包为独立的可执行文件。

**为什么选择Nuitka？**
- ✅ 对PyTorch和机器学习模型支持更好
- ✅ 生成真正的本地可执行文件
- ✅ 性能优于PyInstaller
- ✅ 支持外部资源文件挂载
- ✅ 更小的内存占用

## 🛠️ 环境准备

### 系统要求
- **Python**: 3.8+
- **内存**: 至少4GB可用内存
- **磁盘空间**: 至少2GB（编译缓存）
- **时间**: 首次编译约10-20分钟

### 安装Nuitka
```bash
pip install nuitka==1.9.2
pip install ordered-set zstandard
```

## 🚀 快速开始

### Windows
```bash
# 1. 安装依赖
pip install -r requirements-nuitka.txt

# 2. 运行构建脚本
build_nuitka.bat
```

### Linux
```bash
# 1. 安装依赖
pip3 install -r requirements-nuitka.txt

# 2. 运行构建脚本
chmod +x build_nuitka.sh
./build_nuitka.sh
```

## 📁 目录结构

```
VoiceInput/
├── funasr_voice_combined.py    # 主程序
├── config.yaml                  # 配置文件
├── voice_correction_dict.txt   # 语音纠错词典
├── model/fun/                   # FunASR模型目录
│   ├── README.md
│   └── ... (模型文件)
├── onnx_deps/                   # ONNX依赖目录
│   ├── ffmpeg/
│   └── ... (依赖库)
├── build/                       # 构建输出目录
└── dist/                        # 发布目录
```

## ⚙️ 配置说明

### config.yaml模型路径配置
```yaml
model:
  external_paths:
    enabled: true
    funasr_model_path: model/fun
    onnx_deps_path: onnx_deps
  default_path: model/fun
  device: cpu
  funasr:
    path: model/fun
```

### Nuitka配置选项

#### onefile模式
```bash
nuitka3 --onefile main.py
```
- 生成单个可执行文件
- 体积较大但便于分发

#### standalone模式
```bash
nuitka3 --standalone main.py
```
- 生成独立目录
- 体积较小但有多个文件

## 🔧 高级配置

### 包含数据文件
```bash
--include-data-dir=model/fun=model/fun
--include-data-dir=onnx_deps=onnx_deps
--include-data-file=config.yaml=config.yaml
```

### 启用插件
```bash
--enable-plugin=pytorch
--enable-plugin=numpy
--enable-cc=yes
```

### 性能优化
```bash
--optimize-level=3          # 最高优化级别
--enable-btot=yes           # 后端优化
--cache-dir=.nuitka-cache   # 使用缓存
```

## 📦 打包流程详解

### 第一步：环境检查
- 验证Python版本
- 检查Nuitka是否安装
- 安装必要依赖

### 第二步：依赖安装
- 安装核心依赖包
- 安装Nuitka特定插件
- 验证关键库可用性

### 第三步：构建准备
- 创建build和dist目录
- 清理之前的构建结果
- 验证源文件完整性

### 第四步：执行编译
- 运行Nuitka编译
- 监控编译进度
- 处理编译错误

### 第五步：验证输出
- 检查可执行文件
- 验证资源文件
- 测试运行

## 🐛 常见问题解决

### 问题1：内存不足
**错误**: `MemoryError` during compilation
**解决**: 增加虚拟内存或关闭其他程序

### 问题2：找不到模型文件
**错误**: `FileNotFoundError: model/fun`
**解决**: 
1. 确保model/fun目录存在
2. 检查config.yaml路径配置
3. 使用绝对路径测试

### 问题3：ONNX依赖错误
**错误**: `ONNX runtime not found`
**解决**: 
1. 确保onnx_deps目录存在
2. 检查FFmpeg路径
3. 添加到系统PATH

### 问题4：PyTorch导入失败
**错误**: `ModuleNotFoundError: torch`
**解决**:
```bash
pip install --upgrade torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 📊 性能对比

| 指标 | PyInstaller | Nuitka |
|------|-------------|--------|
| 启动速度 | 慢 | 快 |
| 内存占用 | 高 | 低 |
| 文件体积 | 大 | 中等 |
| 加载速度 | 慢 | 快 |
| 兼容性 | 中 | 高 |

## 🎯 输出文件说明

### 可执行文件
- **Windows**: `VoiceInput_System.exe`
- **Linux**: `VoiceInput_System`

### 独立目录 (standalone模式)
```
VoiceInput_System.dist/
├── VoiceInput_System          # 主程序
├── _internal/                 # 依赖库
│   ├── model/fun/            # 模型文件
│   ├── onnx_deps/            # ONNX依赖
│   └── *.so/*.dll            # 动态库
```

## 🔄 更新和维护

### 模型更新
1. 替换`model/fun`目录内容
2. 更新版本号
3. 重新编译

### 配置更新
1. 修改`config.yaml`
2. 测试新配置
3. 重新编译（如需要）

## 📝 脚本定制

### 修改构建参数
编辑`build_nuitka.bat`或`build_nuitka.sh`:
```bash
# 启用调试模式
--debug=all

# 禁用优化（调试用）
--optimize-level=0

# 详细输出
--verbose
```

### 添加自定义数据
在构建脚本中添加:
```bash
--include-data-dir=your_data=your_data
--include-data-file=your_file.py=your_file.py
```

## ✅ 验证清单

打包完成后，请验证：
- [ ] 可执行文件可正常启动
- [ ] 模型文件可正常加载
- [ ] 语音识别功能正常
- [ ] 配置读取正确
- [ ] 资源文件完整
- [ ] 依赖库正确链接

## 📞 技术支持

如遇到问题：
1. 检查`build`目录中的编译日志
2. 查看`.nuitka-cache`中的缓存信息
3. 验证依赖版本兼容性
4. 参考[Nuitka官方文档](https://nuitka.net/)

---

**版本**: v2.8
**更新日期**: 2025-11-02
**维护者**: VoiceInput开发团队
