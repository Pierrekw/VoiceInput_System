# Voice Input System - Project Information

## 📋 项目概览
实时语音识别系统，具有暂停/恢复功能和自动Excel导出功能，专为测量数据收集而设计。

## 🏗️ 项目架构
```
Voice_Input/
├── main.py                    # 主入口文件 (v0.1.2)
├── audio_capture_v.py         # 音频捕获和识别模块
├── excel_exporter.py          # Excel导出功能模块
├── TTSengine.py              # 文本转语音引擎
├── config_loader.py          # 配置加载器
├── config.yaml               # 主配置文件
├── claude/                   # 文档和项目信息
│   ├── project_info.md       # 项目信息文件 (本文件)
│   ├── PROJECT_SUMMARY.md    # 项目总结
│   ├── QUICK_REFERENCE.md    # 快速参考
│   ├── README.md            # 说明文档
│   ├── CHANGELOG.md         # 变更日志
│   └── TEST_RESULTS.md      # 测试结果
├── tests/                    # 测试文件目录
├── tests_develop/           # 开发测试目录
├── model/                   # Vosk模型存储目录
├── backup/                  # 备份目录
├── audio_capture/           # 音频处理模块
├── WaveOutput/              # 波形输出目录
├── voice_input.egg-info/    # 包信息
├── .venv/                   # 虚拟环境
├── .git/                    # Git版本控制
├── .claude/                 # Claude配置
├── .mypy_cache/             # MyPy缓存
├── .pytest_cache/           # Pytest缓存
└── 依赖文件:
    ├── requirements.txt
    ├── pyproject.toml
    ├── uv.lock
    ├── .pre-commit-config.yaml
    ├── pytest.ini
    └── .python-version
```

## 🎯 核心功能模块

### 1. 音频捕获模块 (audio_capture_v.py)
- **功能**: 实时语音识别和音频处理
- **技术栈**: PyAudio, Vosk
- **特性**:
  - 支持中文语音识别
  - 暂停/恢复控制
  - 语音命令识别
  - 键盘事件处理
  - 中文数字转换

### 2. Excel导出模块 (excel_exporter.py)
- **功能**: 自动化Excel数据导出
- **技术栈**: openpyxl, pandas
- **特性**:
  - 专业格式化
  - 自动编号
  - 时间戳记录
  - 多语言支持

### 3. 文本转语音模块 (TTSengine.py)
- **功能**: 语音反馈系统
- **技术栈**: piper-tts
- **特性**:
  - 可切换TTS开关
  - 数字语音确认

### 4. 配置系统 (config.yaml + config_loader.py)
- **功能**: 集中化配置管理
- **覆盖范围**: 模型、音频、Excel、系统设置
- **特性**: 热加载配置支持

## 🔧 技术规格

### 开发环境
- **系统Python**: 3.12.10 (主机环境)
- **虚拟环境Python**: 3.11.11 (.venv)
- **包管理**: uv 0.8.0 + pip
- **版本控制**: git 2.51.0.windows.2
- **虚拟环境**: .venv
- **代码质量**: MyPy类型检查, pre-commit钩子

### ⚠️ 重要环境说明
**必须激活虚拟环境**: 每次运行Python代码前都必须先激活虚拟环境
```bash
# Windows (推荐)
.venv\Scripts\activate

# 或使用Git Bash
source .venv/scripts/activate

# 激活成功后，Python版本会显示为3.11.11
python --version  # 应该显示 Python 3.11.11
```

### 项目管理工具
- **uv**: 现代Python包管理器，用于依赖管理和虚拟环境
- **git**: 版本控制系统，当前分支: develop
- **主要分支**: main (用于PR合并)

### 核心依赖
```toml
pyaudio = "0.2.14"          # 音频处理
vosk = "0.3.45"             # 语音识别
cn2an = "0.5.23"            # 中文数字转换
openpyxl = "3.1.5"          # Excel操作
pynput = "1.8.1"            # 键盘控制
piper-tts = ">=1.3.0"       # 文本转语音
```

### 测试框架
- **测试工具**: pytest 8.4.2
- **覆盖率**: pytest-cov
- **测试状态**: 18/18 测试通过 ✅

## 📊 配置参数详情

### 模型配置
- **默认模型**: model/cn (中文标准模型)
- **可选模型**: cn(标准), cns(小), us(英文), uss(英文小)
- **音频采样**: 16kHz
- **缓冲大小**: 8k

### 系统配置
- **超时时间**: 60秒 (可配置1-60秒)
- **缓冲大小**: 10,000条记录
- **日志级别**: INFO
- **测试模式**: false (生产环境)

### Excel配置
- **输出文件**: measurement_data.xlsx
- **自动导出**: 启用
- **格式化**: 自动编号 + 时间戳
- **语言**: 中文表头

## 🎮 控制系统

### 键盘控制
- **空格键**: 开始/暂停/恢复循环
- **ESC键**: 停止并退出
- **T键**: 切换TTS开关

### 语音命令
- **暂停**: ["暂停录音", "暂停"]
- **继续**: ["继续录音", "继续", "恢复"]
- **停止**: ["停止录音", "停止", "结束"]

## 📈 性能指标

### 测试覆盖
- **集成测试**: 5个测试 - 通过
- **全系统测试**: 6个测试 - 通过
- **主模块测试**: 7个测试 - 通过
- **总通过率**: 100%

### 性能优化
- **内存管理**: 自动资源清理
- **线程安全**: 并发操作锁机制
- **响应速度**: 生产环境50ms检测间隔

## 🔍 调试与维护

### 日志系统
- **主日志**: voice_input.log
- **级别**: DEBUG/INFO/WARNING/ERROR
- **格式**: 时间戳 + 模块 + 消息

### 常见问题
1. **PyAudio未找到**: 在虚拟环境中重新安装
   ```bash
   .venv\Scripts\activate
   uv pip install pyaudio
   ```
2. **模型缺失**: 下载对应模型到model/目录
3. **Excel权限**: 确保文件未被其他程序占用
4. **环境问题**: 忘记激活虚拟环境导致包找不到
   - **症状**: `ModuleNotFoundError: No module named 'xxx'`
   - **解决**: 必须先运行 `.venv\Scripts\activate`
5. **uv vs pip**: 优先使用uv管理依赖，pip作为备用
   ```bash
   uv sync           # 推荐使用uv同步
   pip install -r requirements.txt  # 备用方案
   ```

### 开发命令

#### 环境管理 (uv + git)
```bash
# 激活虚拟环境 (必须步骤)
.venv\Scripts\activate
# 或 Git Bash: source .venv/scripts/activate

# 检查环境状态
python --version      # 应显示 Python 3.11.11
uv --version         # 检查uv版本
git branch           # 当前分支应为 develop
git status           # 检查工作区状态

# 依赖管理
uv sync              # 同步依赖
uv add <package>     # 添加新依赖
uv pip list          # 查看已安装包
```

#### 开发工作流
```bash
# 运行测试 (必须先激活环境)
python -m pytest -v

# 类型检查
python -m mypy .

# 代码格式化
pre-commit run --all-files

# Git工作流
git add .
git commit -m "commit message"
git push origin develop
```

## 📝 版本信息
- **当前版本**: v0.1.2
- **最后更新**: 2025-10-05
- **Git分支**: develop
- **状态**: 生产就绪

---
*本文档由系统自动生成，最后更新时间: 2025-10-05*