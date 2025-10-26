# Voice Input 语音识别系统安装指南

## 📖 系统概述

Voice Input是一个基于FunASR的中文语音识别系统，支持实时语音转文字和自动Excel导出功能。

### 🎯 主要功能
- **实时语音识别** - 基于阿里巴巴FunASR引擎
- **GUI和命令行界面** - 支持图形界面和命令行操作
- **Excel自动导出** - 支持模板化Excel报告生成
- **语音命令控制** - 支持"切换100"、"切换200"等命令
- **暂停/恢复功能** - 灵活的录音控制

### 🔧 技术栈
- **语音引擎**: FunASR + SenseVoiceSmall
- **GUI框架**: PySide6
- **音频处理**: PyAudio + librosa
- **数据处理**: pandas + openpyxl
- **配置管理**: PyYAML + OmegaConf

## 🖥️ 系统要求

### 最低配置
- **操作系统**: Windows 10/11 (64位)
- **Python版本**: 3.11 或更高版本
- **内存**: 4GB RAM
- **存储**: 5GB 可用空间
- **音频设备**: 麦克风

### 推荐配置
- **操作系统**: Windows 11 (64位)
- **Python版本**: 3.11+
- **内存**: 8GB RAM
- **存储**: 10GB 可用空间 (SSD推荐)
- **处理器**: 多核CPU
- **音频设备**: 高质量麦克风

## 📦 安装步骤

### 步骤1: 安装Python

1. **下载Python**
   - 访问 [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - 下载Python 3.11或更高版本

2. **安装Python**
   ```bash
   # 验证Python版本
   python --version
   # 或
   python3 --version
   ```

3. **更新pip**
   ```bash
   python -m pip install --upgrade pip
   ```

### 步骤2: 获取项目代码

#### 方法A: Git克隆 (推荐)
```bash
git clone <repository_url>
cd voice_input
```

#### 方法B: 下载压缩包
1. 下载项目压缩包
2. 解压到目标目录
3. 进入项目目录

### 步骤3: 安装UV包管理器 (推荐)

```bash
# 安装uv
pip install uv

# 验证安装
uv --version
```

### 步骤4: 安装项目依赖

#### 使用UV (推荐方法)
```bash
# 在项目目录中运行
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

#### 使用pip (备选方法)
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate     # Windows
# 或
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 步骤5: 验证安装

```bash
# 检查核心依赖
python -c "import funasr; print('FunASR OK')"
python -c "import PySide6; print('PySide6 OK')"
python -c "import pandas; print('pandas OK')"
python -c "import openpyxl; print('openpyxl OK')"

# 检查模型文件
python -c "
import os
required_models = ['model/SenseVoiceSmall', 'model/speech_fsmn_vad_zh-cn-16k-common-onnx']
missing = [m for m in required_models if not os.path.exists(m)]
if missing:
    print(f'Missing models: {missing}')
else:
    print('All models found')
"
```

## 🚀 运行程序

### 运行GUI版本 (推荐)
```bash
python voice_gui.py
```

### 运行命令行版本
```bash
python main_f.py
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行类型检查
mypy .

# 运行特定测试
python -m pytest tests/test_voice_recognition.py
```

## ⚙️ 配置说明

### 主要配置文件: `config.yaml`

```yaml
# 语音识别配置
vad:
  energy_threshold: 0.010        # 语音活动检测阈值
  min_silence_duration: 0.8      # 最小静音时长

# Excel配置
excel:
  template_path: reports/templates/enhanced_measure_template.xlsx
  file_naming_pattern: Report_{part_no}_{batch_no}_{timestamp}

# 模型配置
model:
  asr_model_path: model/SenseVoiceSmall
  vad_model_path: model/speech_fsmn_vad_zh-cn-16k-common-onnx
```

### 配置检查
```bash
# 验证配置文件语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 测试配置加载
python -c "from config_loader import ConfigLoader; print('Config loaded successfully')"
```

## 📁 目录结构说明

```
Voice_Input/
├── 📄 核心程序
│   ├── voice_gui.py              # GUI主程序
│   ├── main_f.py                 # 命令行主程序
│   ├── config.yaml               # 主配置文件
│   └── config_loader.py          # 配置加载器
│
├── 🤖 模型文件
│   └── model/                    # FunASR模型目录 (约1GB)
│       ├── SenseVoiceSmall/      # 语音识别模型
│       ├── speech_fsmn_vad_zh-cn-16k-common-onnx/  # VAD模型
│       └── speech_ptts_autolabel_16k/             # 标点模型
│
├── 📊 Excel模板
│   └── reports/
│       └── templates/            # Excel模板目录
│           └── enhanced_measure_template.xlsx
│
├── 🔧 核心模块
│   ├── excel_utils.py            # Excel处理工具
│   ├── funasr_voice_tenvad.py    # FunASR语音识别
│   └── text_processor.py         # 文本处理器
│
├── 📦 依赖配置
│   ├── requirements.txt          # Python依赖列表
│   ├── pyproject.toml           # UV项目配置
│   └── uv.lock                  # UV锁定文件
│
├── 📝 运行时目录 (自动创建)
│   ├── logs/                     # 日志文件
│   ├── outputs/                  # 输出文件
│   └── reports/                  # 生成的Excel报告
│
└── 📚 文档和工具
    ├── README.md                 # 项目说明
    ├── DEPLOYMENT_CHECKLIST.md   # 部署清单
    └── INSTALLATION_GUIDE.md     # 安装指南 (本文件)
```

## 🔧 故障排除

### 常见问题

#### 1. Python版本不兼容
```bash
# 检查Python版本
python --version

# 如果版本过低，请升级到3.11+
```

#### 2. 依赖安装失败
```bash
# 清理pip缓存
pip cache purge

# 重新安装依赖
pip install -r requirements.txt --no-cache-dir

# 或使用uv
uv sync --refresh
```

#### 3. 模型加载失败
```bash
# 检查模型文件是否存在
dir model\SenseVoiceSmall
dir model\speech_fsmn_vad_zh-cn-16k-common-onnx

# 如果缺失，需要重新下载模型文件
```

#### 4. 音频设备问题
```bash
# 测试音频设备
python -c "import pyaudio; p = pyaudio.PyAudio(); print(f'Available devices: {p.get_device_count()}')"
```

#### 5. GUI启动失败
```bash
# 检查PySide6安装
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"

# 如果失败，重新安装
pip uninstall PySide6
pip install PySide6==6.8.2
```

#### 6. Excel导出失败
```bash
# 检查openpyxl安装
python -c "import openpyxl; print('openpyxl OK')"

# 检查模板文件
python -c "import os; print('Template exists:' if os.path.exists('reports/templates/enhanced_measure_template.xlsx') else 'Template missing')"
```

### 日志查看

```bash
# 查看最新日志
tail -f logs/voice_gui_*.log

# 查看错误日志
grep -i error logs/*.log
```

### 性能优化

```bash
# 清理Python缓存
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +

# 清理mypy缓存
rm -rf .mypy_cache/
```

## 📞 技术支持

### 自助诊断
```bash
# 运行系统诊断
python -c "
import sys
print(f'Python: {sys.version}')
try:
    import funasr
    print('FunASR: OK')
except ImportError as e:
    print(f'FunASR: {e}')
try:
    import PySide6
    print('PySide6: OK')
except ImportError as e:
    print(f'PySide6: {e}')
"
```

### 获取帮助
1. 查看 `README.md` 获取更多技术细节
2. 查看 `DEPLOYMENT_CHECKLIST.md` 获取部署清单
3. 检查 `logs/` 目录中的日志文件
4. 提交Issue到项目仓库

## 🔄 更新和维护

### 更新依赖
```bash
# 使用uv更新
uv sync --upgrade

# 使用pip更新
pip install --upgrade -r requirements.txt
```

### 备份配置
```bash
# 备份配置文件
cp config.yaml config.yaml.backup
cp reports/templates/ reports/templates_backup/ -r
```

### 清理日志
```bash
# 清理旧日志 (保留最近7天)
find logs/ -name "*.log" -mtime +7 -delete
```

---

**🎉 安装完成！现在您可以开始使用Voice Input语音识别系统了。**