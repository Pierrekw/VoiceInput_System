# FunASR CPU优化版本 - 部署包

## 📋 概述
这是一个专为集成显卡和低配置电脑优化的FunASR语音识别部署包，适合只有Python环境的用户快速部署测试。

## 🎯 适用场景
- 集成显卡电脑
- 低配置办公电脑
- 无GPU服务器环境
- CPU推理优化需求

## 📁 文件说明
```
FunASR_Deployment/
├── 📋 说明文档
│   ├── README.md              # 本说明文档
│   ├── deployment_guide.md    # 详细部署指南
│   ├── QUICKSTART.txt         # 快速开始指南
│   ├── ONNX_OPTIONAL.md       # ONNX可选优化方案
│   ├── TROUBLESHOOTING.md     # 故障排除指南
│   ├── PORTABLE_GUIDE.md      # 便携版使用指南
│   ├── TEST_REPORT.md         # 实际测试报告
│   └── PACKAGE_INFO.txt       # 部署包信息
│
├── 🔧 安装脚本
│   ├── setup_windows.bat      # Windows标准安装
│   ├── setup_linux.sh         # Linux标准安装
│   ├── setup_portable.bat     # Windows便携环境设置
│   ├── setup_portable.sh      # Linux便携环境设置
│   ├── start_funasr.bat       # Windows一键启动
│   ├── download_deps_simple.bat # FFmpeg依赖下载
│   ├── optional_onnx_deps.bat # ONNX依赖下载（可选）
│   └── optional_build_onnx.bat # ONNX编译脚本（可选）
│
├── 🧪 测试程序
│   ├── test_cpu_basic.py      # 基础功能测试
│   ├── test_funasr_cpu.py     # CPU优化语音识别
│   └── test_download_script.bat # 下载脚本测试
│
├── 📂 依赖库
│   └── dependencies/ffmpeg-master-latest-win64-gpl-shared/
│       └── bin/ffmpeg.exe     # FFmpeg可执行文件
│
└── 📁 模型目录
    └── model/fun/             # 模型文件目录
```

## 🚀 快速开始

### Windows用户

#### 选项1: 便携模式（无需管理员权限）- 推荐
1. **一键启动**
   ```
   start_funasr.bat
   ```
   选择运行模式即可开始使用

2. **手动设置环境**
   ```
   setup_portable.bat
   python test_funasr_cpu.py
   ```

#### 选项2: 标准模式（需要管理员权限）
1. **运行安装脚本**
   ```
   setup_windows.bat
   ```

2. **复制模型文件**
   - 将 `model\fun\` 文件夹复制到当前目录
   - 确保包含以下文件：
     - `model.pt`
     - `config.yaml`
     - `tokens.json`
     - `am.mvn`
     - `configuration.json`

3. **测试安装**
   ```bash
   python test_cpu_basic.py
   ```

4. **运行语音识别**
   ```bash
   python test_funasr_cpu.py
   ```

### Linux用户
1. **运行安装脚本**
   ```bash
   chmod +x setup_linux.sh
   ./setup_linux.sh
   ```

2. **复制模型文件**
   ```bash
   # 将模型文件夹复制到当前目录
   cp -r /path/to/model/fun ./
   ```

3. **测试安装**
   ```bash
   python3 test_cpu_basic.py
   ```

4. **运行语音识别**
   ```bash
   python3 test_funasr_cpu.py
   ```

## 💻 系统要求

### 最低配置
- **操作系统**: Windows 10/11 或 Linux (Ubuntu 18.04+)
- **Python**: 3.8 或更高版本
- **内存**: 4GB RAM
- **存储**: 2GB可用空间（模型文件）

### 推荐配置
- **CPU**: 四核2.5GHz+
- **内存**: 8GB RAM+
- **存储**: SSD硬盘

## 🔧 安装的依赖包
- **torch** (CPU版本): PyTorch深度学习框架
- **funasr**: 语音识别核心库
- **pyaudio**: 音频处理
- **numpy**: 数值计算
- **psutil**: 系统信息（可选）

## ❓ 常见问题

### Windows相关问题

**Q: Python未找到**
```
A: 请确保Python已正确安装并添加到系统PATH
   下载地址: https://www.python.org/downloads/
   安装时勾选 "Add Python to PATH"
```

**Q: PyAudio安装失败**
```
A: 需要安装Microsoft Visual C++ Build Tools
   下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**Q: 麦克风无法使用**
```
A: 检查Windows隐私设置
   设置 → 隐私 → 麦克风 → 允许应用访问麦克风
```

### Linux相关问题

**Q: PyAudio安装失败**
```
A: 需要安装portaudio开发库
   Ubuntu/Debian: sudo apt install portaudio19-dev python3-dev
   CentOS/RHEL: sudo yum install portaudio-devel python3-devel
```

**Q: 音频权限问题**
```
A: 将用户添加到audio组
   sudo usermod -a -G audio $USER
   然后重启系统
```

## 📊 性能优化建议

### CPU优化
1. **关闭不必要的程序**释放内存
2. **使用SSD硬盘**提高模型加载速度
3. **调整chunk_size**参数平衡延迟和准确性
4. **设置合适的能量阈值**减少误识别

### 参数调优
```python
# 在test_funasr_cpu.py中调整这些参数
speech_energy_threshold = 0.02   # 能量阈值
min_speech_duration = 0.4        # 最小语音时长
min_silence_duration = 0.8       # 静音时长
```

## 📞 技术支持

如果遇到问题：
1. 首先运行 `test_cpu_basic.py` 检查基础功能
2. 查看错误日志信息
3. 参考本文档的常见问题部分
4. 确认模型文件完整性

## 🔄 更新说明

- **v1.0**: 初始版本，支持CPU优化
- 专门针对集成显卡环境优化
- 包含完整的部署脚本和文档

---
*本部署包专门为低配置电脑优化，提供稳定的CPU推理性能。*