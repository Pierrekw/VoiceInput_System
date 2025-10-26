# FunASR CPU优化版本 - 详细部署指南

## 📋 目录
1. [准备工作](#准备工作)
2. [Windows部署](#windows部署)
3. [Linux部署](#linux部署)
4. [模型配置](#模型配置)
5. [功能测试](#功能测试)
6. [性能调优](#性能调优)
7. [故障排除](#故障排除)

## 🛠️ 准备工作

### 1. 系统要求检查
```bash
# Windows
python --version

# Linux
python3 --version
```

确保Python版本为3.8或更高。

### 2. 下载部署包
将整个`FunASR_Deployment`文件夹复制到目标电脑。

### 3. 准备模型文件
从原始环境复制以下文件到部署目录：
```
model/
└── fun/
    ├── model.pt              # 模型权重文件
    ├── config.yaml           # 模型配置
    ├── tokens.json           # 词汇表
    ├── am.mvn               # 音频归一化参数
    └── configuration.json   # 模型元信息
```

## 🪟 Windows部署

### 步骤1: 检查Python环境
1. 打开命令提示符(CMD)或PowerShell
2. 检查Python版本：
   ```cmd
   python --version
   ```
3. 如果提示未找到命令，请重新安装Python并确保勾选"Add Python to PATH"

### 步骤2: 运行自动安装脚本
1. 双击`setup_windows.bat`文件
2. 等待安装完成，期间会自动安装所需依赖包
3. 如果出现权限提示，选择"是"

### 步骤3: 验证安装
```cmd
python test_cpu_basic.py
```

### 步骤4: 测试语音识别
```cmd
python test_funasr_cpu.py
```

## 🐧 Linux部署

### 步骤1: 检查Python环境
```bash
python3 --version
```

### 步骤2: 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install portaudio19-dev python3-dev

# CentOS/RHEL/Fedora
sudo yum install portaudio-devel python3-devel
# 或 (较新版本)
sudo dnf install portaudio-devel python3-devel
```

### 步骤3: 运行安装脚本
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

### 步骤4: 设置音频权限
```bash
# 将当前用户添加到audio组
sudo usermod -a -G audio $USER
# 重启系统使权限生效
```

### 步骤5: 验证安装
```bash
python3 test_cpu_basic.py
```

### 步骤6: 测试语音识别
```bash
python3 test_funasr_cpu.py
```

## 📁 模型配置

### 模型文件结构
确保`model/fun/`目录包含以下文件：
```
model/fun/
├── model.pt              # 必需 - 模型权重
├── config.yaml           # 必需 - 模型配置
├── tokens.json           # 必需 - 词汇表
├── am.mvn               # 必需 - 音频归一化参数
└── configuration.json   # 可选 - 模型元信息
```

### 模型路径配置
如果需要修改模型路径，编辑`test_funasr_cpu.py`：
```python
# 找到这一行
model_path = "f:\\04_AI\\01_Workplace\\Voice_Input\\model\\fun"

# 修改为
model_path = "model\\fun"  # 相对路径
# 或
model_path = "/absolute/path/to/model/fun"  # Linux绝对路径
```

## 🧪 功能测试

### 基础功能测试
```bash
# Windows
python test_cpu_basic.py

# Linux
python3 test_cpu_basic.py
```

这个测试会：
- ✅ 检查所有依赖包是否正确安装
- ✅ 测试模型加载
- ✅ 验证基本识别功能
- ✅ 检查CPU优化状态

### 完整语音识别测试
```bash
# Windows
python test_funasr_cpu.py

# Linux
python3 test_funasr_cpu.py
```

测试前确保：
1. 麦克风已连接并工作正常
2. 系统音频权限已授予
3. 环境相对安静

## ⚡ 性能调优

### CPU优化参数
在`test_funasr_cpu.py`中调整以下参数：

```python
# 语音活动检测参数
speech_energy_threshold = 0.02   # 能量阈值：0.01-0.05
min_speech_duration = 0.4        # 最小语音时长：0.2-1.0秒
min_silence_duration = 0.8       # 静音时长：0.5-2.0秒

# 音频处理参数
chunk_size = 8000               # 音频块大小：4000-16000
sample_rate = 16000             # 采样率：固定16000
```

### 内存优化
```python
# 减少内存占用的方法
chunk_size = 4000               # 使用较小的音频块
# 在程序结束时添加
import gc
gc.collect()                    # 手动垃圾回收
```

### 速度优化
```python
# 提高响应速度
min_silence_duration = 0.6      # 减少静音等待时间
min_speech_duration = 0.3       # 减少最小语音时长
```

## 🔧 故障排除

### 常见错误及解决方案

#### 1. Python相关问题
**错误**: `python: command not found`
```bash
# Windows: 重新安装Python，确保勾选Add to PATH
# Linux: 安装Python
sudo apt install python3 python3-pip
```

**错误**: `ModuleNotFoundError: No module named 'xxx'`
```bash
# 重新运行安装脚本
./setup_windows.bat  # Windows
./setup_linux.sh     # Linux

# 或手动安装
pip install 模块名
```

#### 2. PyAudio问题
**Windows错误**: `Microsoft Visual C++ 14.0 is required`
- 解决方案：安装Visual Studio Build Tools
- 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Linux错误**: `portaudio.h: No such file or directory`
```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-dev

# CentOS/RHEL
sudo yum install portaudio-devel python3-devel
```

#### 3. 音频设备问题
**错误**: `Invalid number of channels`
```python
# 检查音频设备
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(i, p.get_device_info_by_index(i)['name'])
```

**Linux权限问题**:
```bash
# 检查音频设备权限
ls -l /dev/snd/*

# 添加用户到audio组
sudo usermod -a -G audio $USER
# 重启系统
```

#### 4. 模型加载问题
**错误**: `No such file or directory: model.pt`
- 确保模型文件完整复制
- 检查文件路径是否正确
- 确认文件权限（Linux: `chmod -R 755 model/`）

**错误**: `RuntimeError: CUDA out of memory`
- 这是正常的，我们使用CPU版本
- 确保没有其他GPU程序在运行

#### 5. 识别效果问题
**问题**: 识别结果不准确
```python
# 调整能量阈值
speech_energy_threshold = 0.015  # 降低阈值增加灵敏度

# 调整语音时长要求
min_speech_duration = 0.3        # 减少最小语音时长
```

**问题**: 误识别过多
```python
# 提高能量阈值
speech_energy_threshold = 0.025  # 提高阈值减少误触发

# 增加最小语音时长
min_speech_duration = 0.5        # 要求更长的语音
```

### 日志分析
启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看日志输出中的关键信息：
- 模型加载时间
- 音频能量值
- 语音段检测
- 识别结果

## 📊 性能基准

### 预期性能指标
- **模型加载时间**: 2-5秒
- **实时识别延迟**: 0.5-1秒
- **内存占用**: 1-2GB
- **CPU使用率**: 20-50%（取决于硬件）

### 性能测试命令
```bash
# 运行性能测试
python test_cpu_basic.py
```

查看输出中的性能统计信息。

## 📞 获取帮助

如果问题仍未解决：
1. 检查本文档的故障排除部分
2. 运行基础测试确定问题范围
3. 查看详细错误日志
4. 确认系统环境符合要求

---
*本指南涵盖了从安装到使用的完整流程，如需进一步协助请参考各步骤的详细说明。*