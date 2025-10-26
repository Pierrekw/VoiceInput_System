# Voice Input 项目部署清单

## 📋 项目复制清单

### 🎯 核心文件 (必须复制)
- **主程序文件**
  - `voice_gui.py` - GUI主程序 (77KB)
  - `main_f.py` - 命令行主程序 (48KB)
  - `config.yaml` - 配置文件 (8KB)
  - `config_loader.py` - 配置加载器 (18KB)

- **核心模块**
  - `excel_utils.py` - Excel处理工具 (29KB)
  - `funasr_voice_tenvad.py` - FunASR语音识别 (29KB)
  - `text_processor.py` - 文本处理器 (27KB)

- **依赖配置**
  - `requirements.txt` - Python依赖列表
  - `pyproject.toml` - UV项目配置
  - `uv.lock` - UV锁定文件 (456KB)
  - `setup.py` - 安装脚本

- **项目配置**
  - `README.md` - 项目说明
  - `LICENSE` - 许可证
  - `voice_correction_dict.txt` - 语音纠错词典

### 🔧 配置和模板 (必须复制)
- **Excel模板**
  - `reports/templates/` - Excel模板目录
  - `reports/clean_measure_template.xlsx` - 清洁测量模板

- **模型文件** (重要 - 约1GB)
  - `model/` - 完整模型目录
  ```
  model/
  ├── SenseVoiceSmall/           # 语音识别模型
  ├── speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online/
  ├── speech_fsmn_vad_zh-cn-16k-common-onnx/    # VAD模型
  ├── speech_ptts_autolabel_16k/    # 标点模型
  ├── cn/、cns/、fun/               # 中文模型
  └── 其他模型文件...
  ```

### 📁 目录结构 (必须创建)
```
Voice_Input/
├── 📄 核心程序文件
├── 🔧 配置文件
├── 📦 依赖配置
├── 🤖 模型目录 (model/)
├── 📊 Excel模板 (reports/)
├── 📝 日志目录 (logs/)
├── 🗂️ 输出目录 (outputs/)
├── 🧪 测试文件 (tests/)
├── 🔧 工具模块 (utils/)
├── 📚 文档 (docs/)
└── 🗄️ 存档 (archive/)
```

### ❌ 可以排除的文件
- `.git/` - Git版本控制 (可重新初始化)
- `.venv/` - 虚拟环境 (需在新机器重新创建)
- `__pycache__/` - Python缓存 (运行时自动生成)
- `.mypy_cache/` - MyPy缓存 (运行时自动生成)
- `reports/*.xlsx` - 历史报告文件 (可选)
- `Logs/` - 历史日志文件 (可选)
- `backup/` - 备份文件 (可选)
- `archive/` - 存档文件 (可选)
- `.coverage` - 测试覆盖率文件

## 📦 项目大小估算

### 必须复制的文件
- **核心代码**: ~300KB
- **模型文件**: ~1GB
- **配置文件**: ~500KB
- **模板文件**: ~50KB

**总计**: 约1.01GB

### 可选文件
- **历史报告**: ~10MB (200+个Excel文件)
- **日志文件**: ~5MB
- **Git历史**: ~500MB

## 🚀 部署步骤

### 1. 准备目标机器
```bash
# 确保Python 3.11+已安装
python --version

# 安装uv (推荐)
pip install uv

# 或安装pip (备选)
pip install --upgrade pip
```

### 2. 复制项目文件
```bash
# 方法1: 使用压缩包
tar -czf voice_input_deploy.tar.gz --exclude='.git' --exclude='.venv' --exclude='__pycache__' .

# 方法2: 使用Git (推荐)
git clone <repository_url>
cd voice_input
```

### 3. 安装依赖
```bash
# 使用uv (推荐)
uv sync

# 或使用pip (备选)
pip install -r requirements.txt
```

### 4. 配置检查
```bash
# 检查配置文件
python -c "import yaml; print('Config OK')"

# 检查模型文件
python -c "import os; print('Models OK' if os.path.exists('model/SenseVoiceSmall') else 'Models Missing')"
```

### 5. 运行测试
```bash
# 运行GUI版本
python voice_gui.py

# 运行命令行版本
python main_f.py
```

## ⚠️ 注意事项

### 🔴 关键提醒
1. **模型文件不可缺失** - 缺少模型将导致语音识别失败
2. **Python版本要求** - 必须使用Python 3.11或更高版本
3. **路径问题** - 确保所有相对路径在新环境中正确
4. **权限问题** - 确保有写入logs/和reports/目录的权限

### 🟡 建议配置
1. **内存要求** - 建议至少4GB RAM (模型加载需要)
2. **存储空间** - 建议至少5GB可用空间
3. **音频设备** - 确保麦克风可用且有权限
4. **网络连接** - 首次运行可能需要下载依赖

### 🟢 可选优化
1. **SSD硬盘** - 提高模型加载速度
2. **GPU支持** - 如有GPU可考虑GPU版本的torch
3. **多核CPU** - 提高音频处理性能

## 🐛 常见问题解决

### 模型加载失败
```bash
# 检查模型文件完整性
find model/ -name "*.onnx" -o -name "*.bin" | wc -l
```

### 依赖安装失败
```bash
# 清理缓存重试
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### 配置文件错误
```bash
# 验证YAML语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### 权限问题
```bash
# 创建必要目录
mkdir -p logs reports outputs
chmod 755 logs reports outputs
```