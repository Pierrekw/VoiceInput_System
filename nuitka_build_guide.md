# 🚀 Nuitka打包指南 - FunASR语音输入系统

## 📋 打包前准备

### 1. 环境检查
```bash
# 检查Python版本 (推荐3.8-3.11)
python --version

# 检查pip版本
python -m pip --version

# 升级pip
python -m pip install --upgrade pip
```

### 2. 安装Nuitka
```bash
# 安装Nuitka主包
python -m pip install nuitka

# 安装Nuitka商业版 (可选，提供更好的优化)
python -m pip install nuitka-commercial

# 安装依赖分析工具
python -m pip install ordered-set
```

### 3. 安装C编译器
```bash
# 安装Visual Studio Build Tools (Windows)
# 下载地址: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
# 选择: 使用C++的桌面开发

# 或者安装MinGW-w64
# 下载地址: https://www.mingw-w64.org/downloads/
```

## 🎯 打包步骤

### 步骤1: 清理项目
```bash
# 删除临时文件和缓存
python -c "
import os
import shutil

# 删除常见缓存目录
for item in ['__pycache__', '.pytest_cache', '.mypy_cache', 'build', 'dist', '*.egg-info']:
    if os.path.exists(item):
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

print('✅ 清理完成')
"
```

### 步骤2: 基础打包命令
```bash
# 基础打包 (适合测试)
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --enable-plugin=numpy \
    --enable-plugin=torch \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput
```

### 步骤3: 优化打包 (推荐)
```bash
# 完整优化打包
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --enable-plugin=numpy \
    --enable-plugin=torch \
    --include-package=funasr \
    --include-package=modelscope \
    --include-package-data=funasr \
    --include-package-data=modelscope \
    --include-data-dir=config=./config \
    --include-data-dir=model=./model \
    --include-data-file=config.yaml=./config.yaml \
    --include-data-file=voice_correction_dict.txt=./voice_correction_dict.txt \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput \
    --windows-icon-from-ico=icon.ico \
    --windows-disable-console \
    --jobs=8 \
    --lto=yes \
    --clang \
    --assume-yes-for-downloads
```

### 步骤4: 分模块打包 (解决大文件问题)
```bash
# 先打包核心模块
python -m nuitka funasr_voice_module.py \
    --module \
    --enable-plugin=numpy \
    --enable-plugin=torch \
    --include-package=funasr \
    --include-package-data=funasr \
    --output-dir=build_modules

# 再打包主程序
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --module-interaction=build_modules/funasr_voice_module.py \
    --include-data-dir=config=./config \
    --include-data-dir=model=./model \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput
```

## 📦 必需包含的数据文件

### 配置文件
```bash
# 主配置文件
--include-data-file=config.yaml=./config.yaml

# 语音纠错词典
--include-data-file=voice_correction_dict.txt=./voice_correction_dict.txt
```

### 模型文件 (重要)
```bash
# FunASR模型目录
--include-data-dir=model/fun=./model/fun

# 如果使用了VAD模型
--include-data-dir=model/vad=./model/vad

# 标点模型
--include-data-dir=model/punc=./model/punc
```

### 依赖包数据
```bash
# FunASR资源文件
--include-package-data=funasr
--include-package-data=modelscope

# 特定模块
--include-package=funasr
--include-package=modelscope
--include-package=torch
--include-package=torchaudio
```

## ⚠️ 常见问题解决

### 1. 模型加载失败
```bash
# 确保包含所有模型文件
--include-data-dir=model=./model \
--include-package-data=funasr \
--include-package-data=modelscope
```

### 2. PyAudio问题
```bash
# Windows系统需要包含音频驱动
--include-data-file=*.pyd=./ \
--include-package=pyaudio
```

### 3. PyTorch CUDA支持
```bash
# 如果需要CUDA支持
--enable-plugin=torch \
--include-package=torch \
--include-package=torchvision \
--include-package=torchaudio
```

### 4. 文件过大问题
```bash
# 使用UPX压缩
--upx-dir=C:\upx \
--upx-binary=upx.exe

# 或者分模块打包
--module \
--follow-imports
```

## 🚀 高级优化选项

### 性能优化
```bash
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --enable-plugin=numpy \
    --enable-plugin=torch \
    --include-package=funasr \
    --include-package-data=funasr \
    --include-data-dir=config=./config \
    --include-data-dir=model=./model \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput \
    --windows-disable-console \
    --jobs=8 \
    --lto=yes \
    --clang \
    --assume-yes-for-downloads \
    --nofollow-import-to=tkinter \
    --nofollow-import-to=matplotlib \
    --nofollow-import-to=test \
    --no-prefer-source-code
```

### 大小优化
```bash
# 最小化打包
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --include-package=funasr \
    --include-package-data=funasr \
    --include-data-dir=config=./config \
    --include-data-dir=model=./model \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput \
    --windows-disable-console \
    --jobs=8 \
    --lto=yes \
    --upx-dir=C:\upx \
    --remove-output \
    --no-pyi-file
```

## 📁 打包后文件结构
```
build/
└── FunASR_VoiceInput.dist/
    ├── FunASR_VoiceInput.exe      # 主程序
    ├── python3x.dll               # Python运行时
    ├── *.pyd                      # 扩展模块
    ├── config/
    │   └── config.yaml           # 配置文件
    ├── model/
    │   ├── fun/                  # FunASR模型
    │   ├── vad/                  # VAD模型
    │   └── punc/                 # 标点模型
    └── voice_correction_dict.txt  # 纠错词典
```

## 🧪 测试打包结果

### 1. 基础功能测试
```bash
# 进入打包目录
cd build\FunASR_VoiceInput.dist

# 测试基本功能
FunASR_VoiceInput.exe --help
FunASR_VoiceInput.exe --test-mode
```

### 2. 语音识别测试
```bash
# 测试语音识别
FunASR_VoiceInput.exe --mode=fast --duration=10

# 测试小数识别
FunASR_VoiceInput.exe --test-decimal
```

### 3. GUI界面测试
```bash
# 测试GUI界面
FunASR_VoiceInput.exe --gui
```

## 📊 性能对比

| 打包方式 | 文件大小 | 启动时间 | 内存占用 | 推荐度 |
|---------|---------|---------|---------|--------|
| 源码运行 | - | 2-3秒 | 低 | ⭐⭐⭐ |
| PyInstaller | 200-300MB | 5-8秒 | 中 | ⭐⭐ |
| Nuitka基础 | 150-200MB | 3-5秒 | 低 | ⭐⭐⭐⭐ |
| Nuitka优化 | 100-150MB | 2-4秒 | 低 | ⭐⭐⭐⭐⭐ |

## 🎯 推荐方案

### 快速测试
```bash
# 基础打包，适合测试
python -m nuitka main_f.py --standalone --enable-plugin=pyside6
```

### 生产发布
```bash
# 完整优化打包
python -m nuitka main_f.py \
    --standalone \
    --enable-plugin=pyside6 \
    --enable-plugin=numpy \
    --include-package=funasr \
    --include-data-dir=config=./config \
    --include-data-dir=model=./model \
    --windows-disable-console \
    --jobs=8 \
    --lto=yes \
    --output-dir=build \
    --output-filename=FunASR_VoiceInput
```

## 🔧 故障排除

### 1. 编译器错误
```bash
# 安装Visual Studio Build Tools
# 或者使用MinGW
python -m nuitka --mingw64 main_f.py
```

### 2. 内存不足
```bash
# 减少并行任务
python -m nuitka main_f.py --jobs=2
```

### 3. 模型文件缺失
```bash
# 检查模型文件路径
--include-data-dir=model=./model
--include-package-data=funasr
```

### 4. 运行时错误
```bash
# 启用调试模式
python -m nuitka main_f.py --debug --execute
```

## 📚 参考资源

- [Nuitka官方文档](https://nuitka.net/doc/user-manual.html)
- [Nuitka GitHub](https://github.com/Nuitka/Nuitka)
- [PySide6 Nuitka插件](https://nuitka.net/doc/user-manual.html#pyside6-plugin)
- [PyTorch Nuitka支持](https://nuitka.net/doc/user-manual.html#torch-plugin)