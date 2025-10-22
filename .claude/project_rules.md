# FunASR语音输入系统 - Claude项目规则

## 🎯 项目概述
这是一个基于FunASR框架的高性能中文语音识别系统，支持实时语音识别、性能监控、延迟优化和Excel数据导出功能。

## 📁 重要目录结构规则

### 🧪 测试文件位置 (重要!)
- **所有测试文件都必须放在 `tests/` 目录下**
- **禁止在项目根目录创建测试文件**
- 测试文件命名规范: `test_*.py`
- 测试函数命名规范: `def test_*()`

```
Voice_Input/
├── .claude/                  # Claude配置目录 (当前文件)
├── tests/                    # ⚠️ 所有测试文件必须放在这里
│   ├── test_*.py             # 测试文件
│   └── README.md             # 测试说明文档
├── main_f.py                 # 核心系统类
├── funasr_voice_module.py    # FunASR识别模块
├── text_processor_clean.py   # 文本处理模块 (重构优化)
├── excel_exporter.py         # Excel导出模块
├── voice_gui.py              # 主要GUI界面
├── start_funasr.py           # 主启动脚本
├── config_loader.py          # 配置加载器
├── config.yaml              # 配置文件
├── performance_monitor.py    # 性能监控模块
├── reports/                  # Excel输出目录
├── logs/                     # 日志文件目录
├── build_scripts/            # 构建脚本目录
└── onnx_deps/                # ONNX依赖目录
```

### 运行测试的标准方式
```bash
# 从项目根目录运行测试 (正确方式)
python tests/test_text_processor_refactor.py
python tests/test_funasr.py

# 错误方式 - 不要在根目录创建测试文件
# ❌ python test_something.py  (禁止)
```

## 🔧 核心模块说明

### 核心系统模块
- `main_f.py` - **主系统类**，包含 `FunASRVoiceSystem`
- `funasr_voice_module.py` - **FunASR识别模块**，语音识别核心
- `text_processor_clean.py` - **文本处理模块** (重构后)，统一处理所有文本操作
  - 包含 `TextProcessor` 类：中文数字转换、文本清理、相似度计算
  - 包含 `VoiceCommandProcessor` 类：语音命令识别和匹配
- `excel_exporter.py` - **Excel导出模块**，实时数据导出

### 配置管理
- `config_loader.py` - 配置加载器，支持动态配置
- `config.yaml` - 主配置文件，包含VAD、语音命令、性能参数
- `smart_decimal_config.py` - 智能小数点配置

### 性能监控系统
- `performance_monitor.py` - 性能监控模块
- `debug_performance_tracker.py` - Debug模式性能追踪
- `production_latency_logger.py` - 生产环境延迟记录
- `performance_optimizer.py` - 性能优化工具
- `audio_performance_optimizer.py` - 音频性能优化

### GUI界面模块
- `voice_gui.py` - **主要GUI界面**，支持多模式识别
- `stable_gui.py` - 稳定版GUI
- `start_voice_gui.py` - GUI启动脚本

### 测试和工具模块
- `start_funasr.py` - **主启动脚本**，命令行方式启动
- `performance_test.py` - 性能测试工具
- `debug_performance_test.py` - Debug性能测试
- `debug_gui_issues.py` - GUI问题调试工具

### 辅助模块
- `safe_funasr_import.py` - 安全导入FunASR
- `setup_ffmpeg_env.py` - FFmpeg环境设置
- `TTSengine.py` - 文本转语音引擎
- `setup.py` - 项目安装脚本

## 📋 开发规范

### 1. 测试开发规范
```python
# 测试文件模板 (tests/test_example.py)
import sys
import os

# 重要: 添加父目录到路径 (因为tests是子目录)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_example():
    """测试函数命名规范"""
    pass

if __name__ == "__main__":
    test_example()
```

### 2. 类型安全要求
- 所有新代码必须通过 MyPy 类型检查
- 核心模块需要通过严格模式检查:
```bash
mypy text_processor_clean.py --ignore-missing-imports --strict
```

### 3. 文档要求
- 新功能需要更新 README.md
- 重要修改需要记录到 DevelopmentRecord.md
- 测试文件需要包含在 tests/README.md 中

## 🚨 重要提醒

### 当Claude需要创建测试文件时:
1. ✅ **必须**放在 `tests/` 目录下
2. ✅ **必须**使用 `test_*.py` 命名
3. ✅ **必须**添加正确的导入路径
4. ✅ **必须**从项目根目录运行测试

### 常见错误 (禁止):
- ❌ 在根目录创建 `test_*.py` 文件
- ❌ 忘记添加导入路径修复
- ❌ 测试文件命名不规范

## 🚀 启动方式和命令

### 命令行启动
```bash
# 主启动方式 (推荐)
python start_funasr.py

# 指定识别时长
python start_funasr.py -d 60  # 识别60秒
python start_funasr.py -d -1  # 无限时模式

# 调试模式
python start_funasr.py --debug

# GUI启动
python start_voice_gui.py
python stable_gui.py
```

### 测试命令
```bash
# 运行重构测试 (最重要)
python tests/test_text_processor_refactor.py

# 运行其他测试
python tests/test_funasr.py
python tests/test_improvements.py

# 性能测试
python performance_test.py
```

### 配置验证
```bash
# 验证配置文件
python -c "from config_loader import config; print(config.get_timeout_seconds())"

# 类型检查
mypy text_processor_clean.py --ignore-missing-imports --strict
mypy main_f.py --ignore-missing-imports
```

## 🎯 重构历史

### 文本处理器重构 (2025-10-22) - ⭐ 重要
- **问题**: 文本处理函数分散在 `main_f.py` 中，不便于维护
- **解决**: 将所有文本处理功能统一到 `text_processor_clean.py`
- **新增**: `VoiceCommandProcessor` 类，专门处理语音命令
- **优势**: 模块化、可复用、易测试、类型安全
- **测试**: `tests/test_text_processor_refactor.py` 验证重构成功
- **类型**: 通过 MyPy 严格模式检查

### 性能优化 (2025-10-19) - v2.2
- **问题**: 语音输入延迟高，用户体验差
- **解决**: VAD配置优化，支持 fast/balanced/accuracy 三种模式
- **效果**: 延迟从 ~100ms 降至 ~25ms，提升4倍
- **新增**: 完整的性能监控系统

### 无限时模式 (2025-10-19) - v2.1
- **问题**: 系统在60秒后自动停止
- **解决**: 支持无限时模式，配置 `timeout_seconds: -1`
- **新增**: 语音命令配置化，模糊匹配算法

## 🎯 核心特性和技术栈

### 主要功能特性
- **🎤 高精度语音识别**: 基于FunASR框架，支持实时中文语音识别
- **⚡ 极速响应**: 优化的VAD配置，延迟低至0.35秒（fast模式）
- **📊 性能监控**: 详细的延迟追踪和性能分析，支持debug和生产模式
- **🗣️ 智能语音命令**: 支持中英文语音控制（暂停、继续、停止）
- **📊 Excel自动导出**: 实时将识别结果写入Excel文件
- **🎛️ VAD配置**: 可调节的语音活动检测参数，支持多种预设
- **🔄 音频异常恢复**: 自动重试机制，防止突然终止
- **📝 数字智能提取**: 自动识别和转换中文数字

### 技术栈
- **核心**: FunASR (阿里巴巴开源语音识别框架)
- **音频**: PyAudio (实时音频处理)
- **界面**: PySide6 (Qt GUI框架)
- **导出**: openpyxl (Excel文件处理)
- **类型检查**: MyPy (静态类型检查)
- **配置**: PyYAML (配置文件解析)

## 🎨 质量检测场景应用

### 业务背景
- **应用场景**: 质量检测录入系统
- **核心需求**: 零件号录入、测量序号管理、数据自动归类
- **工作流程**: 语音输入零件号 → 选择测量序号 → 语音录入测量数据 → 自动Excel保存

### 计划功能 (DevelopmentRecord.md v2.3)
- **零件管理**: 零件号输入、搜索、缓存
- **测量序号**: 每个零件预定义测量序号(100,200,300等)
- **智能归类**: 根据当前零件和序号自动归类测量数据
- **Excel集成**: 增加零件号和测量序号列

## 📊 项目状态和版本

### 当前版本状态
- **版本**: v2.3 (开发中) - 质量检测功能规划
- **上一版本**: v2.2 - 性能优化重大更新
- **代码质量**: ✅ 通过 MyPy 严格类型检查
- **测试覆盖**: ✅ 完整的测试套件
- **文档完整性**: ✅ 全面的项目文档

### 开发环境
- **Python**: 3.8+
- **操作系统**: Windows (主要支持)
- **依赖**: FunASR, PyAudio, PySide6, openpyxl, PyYAML
- **类型检查**: MyPy (严格模式)
- **测试**: 独立测试脚本，无需测试框架

## 📞 获取帮助

### 查看文档
- `README.md` - 完整的项目说明和使用指南
- `DevelopmentRecord.md` - 详细的开发记录和技术决策
- `tests/README.md` - 测试文件说明和运行指南

### 运行验证
```bash
# 验证基本功能
python tests/test_text_processor_refactor.py

# 验证配置加载
python -c "from config_loader import config; print('配置正常')"

# 检查类型安全
mypy text_processor_clean.py --ignore-missing-imports --strict
```

---
**创建时间**: 2025-10-22
**最后更新**: 2025-10-22
**版本**: v1.0
**项目状态**: 活跃开发中，支持质量检测场景