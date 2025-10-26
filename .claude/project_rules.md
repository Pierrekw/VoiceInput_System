# FunASR语音输入系统 - Claude项目规则

## 🎯 项目概述
这是一个基于FunASR框架的高性能中文语音识别系统，集成TEN VAD神经网络、FFmpeg音频预处理、GUI图形界面，支持实时语音识别、性能监控、延迟优化和Excel数据导出功能。

## 📋 当前版本 (v2.5)
- **发布日期**: 2025-10-26
- **核心特性**: TEN VAD + FFmpeg预处理 + 组件化GUI架构
- **主要修复**: 解决停止阻塞问题、日志系统修复、类型安全优化

## 📁 重要目录结构规则

### 🧪 测试和调试文件位置 (重要!)
- **所有测试文件都必须放在 `tests/` 目录下**
- **所有调试开发文件都必须放在 `debug/` 目录下**
- **禁止在项目根目录创建测试和调试文件**
- 测试文件命名规范: `test_*.py`
- 调试文件命名规范: `debug_*.py`
- 测试函数命名规范: `def test_*()`

### 🔧 工具文件位置 (重要!)
- **所有工具类和辅助函数都必须放在 `utils/` 目录下**
- **禁止在项目根目录创建工具文件**
- 工具文件命名规范: `*.py` (如 `file_utils.py`, `data_utils.py`)
- 工具函数命名规范: `def function_name()`

### 📚 文档文件位置 (重要!)
- **所有.md文件都必须放在 `docs/` 目录下**
- **只有README.md可以放在根目录**
- 禁止在根目录创建其他.md文件

#### 📋 tests/ 目录下的测试文件 (v2.5更新)
```bash
tests/
├── test_debug_performance.py      # 性能调试测试 (从根目录移动)
├── test_performance.py           # 性能测试 (从根目录移动)
├── test_ffmpeg_preprocessing.py  # FFmpeg预处理测试 (从根目录移动)
├── test_vad_comparison.py        # VAD对比测试 (从根目录移动)
├── test_text_processor_refactor.py    # 文本处理器重构测试
├── test_funasr.py                    # FunASR核心功能测试
├── test_improvements.py              # 功能改进测试
├── test_excel_functionality.py       # Excel功能测试
├── test_gui_cache_fix.py             # GUI缓存修复测试
├── integrated_test.py                # 集成测试
└── README.md                         # 测试说明文档
```

```
Voice_Input/
├── .claude/                  # Claude配置目录 (当前文件)
├── docs/                     # ⚠️ 所有.md文档必须放在这里 (除了README.md)
│   └── DevelopmentRecord.md   # 开发记录
├── tests/                    # ⚠️ 所有测试文件必须放在这里
│   ├── test_*.py             # 测试文件 (39个文件)
│   ├── final_*.py            # 集成测试文件
│   ├── FINAL_VERIFICATION_REPORT.md
│   └── README.md             # 测试说明文档
├── debug/                    # ⚠️ 所有调试开发文件必须放在这里
│   ├── debug_*.py            # 调试文件
│   ├── check_*.py            # 检查文件 (9个文件)
│   └── README.md             # 调试说明文档
├── utils/                    # ⚠️ 所有工具类和辅助函数必须放在这里
│   ├── create_*.py           # 创建工具 (4个文件)
│   ├── performance_*.py      # 性能工具 (4个文件)
│   ├── audio_performance_optimizer.py
│   ├── logging_utils.py      # 日志工具
│   ├── update_template.py    # 更新工具
│   └── README.md             # 工具说明文档
├── archive/                  # 🗂️ 备份和旧版本文件
│   ├── *_backup.py           # 备份文件 (2个文件)
│   ├── *_bak.py              # 旧版本文件 (2个文件)
│   ├── funasr_voice_*.py     # 旧版语音模块 (3个文件)
│   ├── excel_exporter*.py    # 旧版导出模块 (2个文件)
│   ├── voice_gui_*.py        # 旧版GUI文件 (2个文件)
│   ├── configure_ten_vad.py  # 配置工具
│   ├── setup_ffmpeg_env.py   # 环境设置
│   ├── smart_decimal_config.py
│   ├── TTSengine.py          # 语音引擎
│   ├── safe_funasr_import.py  # 安全导入
│   └── README.md             # 备份说明文档
├── main_f.py                 # ✅ 核心系统类
├── excel_exporter_enhanced.py # ✅ 增强Excel导出模块
├── voice_gui.py              # ✅ 主要GUI界面
├── funasr_voice_TENVAD.py    # ✅ TEN VAD + FFmpeg集成模块
├── text_processor_clean.py   # ✅ 文本处理模块
├── measure_spec_manager.py   # ✅ 测量规范管理器
├── config_loader.py          # ✅ 配置加载器
├── config.yaml               # ✅ 配置文件
├── README.md                 # ✅ 项目说明 (唯一允许在根目录的.md文件)
├── setup.py                  # ✅ 项目安装脚本
├── requirements.txt          # ✅ 依赖文件
├── voice_correction_dict.txt # ✅ 语音纠正词典
├── reports/                  # Excel输出目录
│   └── templates/            # Excel模板目录
├── logs/                     # 日志文件目录
├── model/                    # 模型目录
├── onnx_deps/                # ONNX依赖目录
├── backup/                   # 备份目录
├── build_scripts/            # 构建脚本目录
├── examples/                 # 示例目录
├── outputs/                  # 输出目录
└── __init__.py               # 包初始化
```

### 运行测试、调试和工具的标准方式
```bash
# 从项目根目录运行测试 (正确方式)
python tests/test_text_processor_refactor.py
python tests/test_funasr_voice_module.py

# 从项目根目录运行调试 (正确方式)
python debug/debug_excel_format.py
python debug/debug_performance.py

# 从项目根目录使用工具 (正确方式)
from utils.file_utils import *
from utils.data_utils import process_data
from utils.excel_utils import ExcelHelper

# 错误方式 - 不要在根目录创建测试、调试和工具文件
# ❌ python test_something.py  (禁止)
# ❌ python debug_something.py  (禁止)
# ❌ 创建 utils_tool.py  (禁止，应该放在utils/目录)
```
### 修改文件的标准方式
```bash
# 修改原文件 (正确方式)
modify test_processor_refactor.py

# 错误方式 - 新建新文件
# ❌ create new test_processor_refactor_clean.py [example]  (禁止)
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
- `logging_utils.py` - 日志工具类 (新增,用于统一日志记录)


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

### 2. 类型安全要求 (已修复)
- 所有新代码必须通过 MyPy 类型检查
- 核心模块检查命令 (v2.5更新):
```bash
# 检查核心GUI和语音模块
mypy voice_gui.py gui_components.py voice_gui_refractor.py main_f.py funasr_voice_TENVAD.py --ignore-missing-imports --explicit-package-bases

# 严格模式检查文本处理模块
mypy text_processor_clean.py --ignore-missing-imports --strict

# 检查日志系统 (已修复super()类型错误)
mypy logging_utils.py --ignore-missing-imports
```

### 3. 文档要求
- 新功能需要更新 README.md
- 重要修改需要记录到 DevelopmentRecord.md
- 测试文件需要包含在 tests/README.md 中

## 🚨 重要提醒

### 当Claude需要创建测试和调试文件时:
1. ✅ **测试文件必须**放在 `tests/` 目录下
2. ✅ **调试文件必须**放在 `debug/` 目录下
3. ✅ **工具文件必须**放在 `utils/` 目录下
4. ✅ **必须**使用 `test_*.py`, `debug_*.py` 或相应的工具命名
5. ✅ **必须**添加正确的导入路径
6. ✅ **必须**从项目根目录运行

### 当Claude需要创建文档文件时:
1. ✅ **必须**放在 `docs/` 目录下
2. ✅ **只有README.md可以放在根目录**
3. ✅ **必须**使用 `.md` 扩展名

### 当Claude需要处理备份和旧版本文件时:
1. ✅ **必须**放在 `archive/` 目录下
2. ✅ **可以**保留原有的 `*_backup.py`, `*_bak.py` 命名
3. ✅ **应该**添加说明文档

### 根目录保留的核心文件 (实际整理结果):
- ✅ **核心业务文件 (8个)**:
  - main_f.py, excel_exporter_enhanced.py, voice_gui.py
  - funasr_voice_TENVAD.py, text_processor_clean.py, measure_spec_manager.py
  - config_loader.py, __init__.py
- ✅ **配置文件 (3个)**:
  - config.yaml, requirements.txt, voice_correction_dict.txt
- ✅ **安装脚本 (1个)**:
  - setup.py
- ✅ **README.md (1个)**:
  - 唯一允许在根目录的文档文件

**总计: 13个核心文件** (非常精简！)

### 常见错误 (禁止) - v2.6更新:
- ❌ 在根目录创建 `test_*.py`, `debug_*.py`, `check_*.py` 文件
- ❌ 在根目录创建 `create_*.py`, `utils_*.py` 工具文件
- ❌ 在根目录创建 `.md` 文件 (除了README.md)
- ❌ 忘记添加导入路径修复
- ❌ 文件命名不规范

## 🚀 启动方式和命令 (v2.5更新)

### GUI图形界面 (推荐)
```bash
# 现代化GUI界面
python voice_gui.py

# 组件化GUI界面 (重构版)
python voice_gui_refractor.py

# 导入GUI组件进行开发
from gui_components import *
from voice_gui_refractor import VoiceRecognitionApp
```

### 命令行界面
```bash
# 核心命令行系统
python main_f.py

# 旧版命令行
python start_funasr.py

# 指定识别时长
python main_f.py -d 60  # 识别60秒
python main_f.py -d -1  # 无限时模式

# 调试模式
python main_f.py --debug
```

### TEN VAD模块 (新架构)
```bash
# 使用TEN VAD + FFmpeg集成模块
from funasr_voice_TENVAD import FunASRVoiceRecognizer

# 对比原版模块
from funasr_voice_module import FunASRVoiceRecognizer
```

### 测试、调试和工具使用命令 (v2.6更新)
```bash
# 📊 核心功能测试
python tests/test_text_processor_refactor.py
python tests/test_funasr.py
python tests/test_improvements.py

# 🔍 调试和开发测试
python debug/debug_excel_format.py
python debug/debug_performance.py
python debug/check_excel_content.py
python debug/check_template.py
python debug/check_user_template.py

# 🔧 功能专项测试
python tests/test_ffmpeg_preprocessing.py
python tests/test_vad_comparison.py
python tests/test_excel_functionality.py
python tests/test_gui_cache_fix.py

# 🧪 集成测试
python tests/integrated_test.py
python tests/final_integration_test.py
python tests/final_complete_test.py
python tests/test_20rows_formatting.py

# 🛠️ 工具使用
from utils.create_clean_template import create_clean_template
from utils.create_missing_specs import create_missing_specs
from utils.update_template import update_template
from utils.logging_utils import get_logger
from utils.performance_monitor import PerformanceMonitor

# ❌ 错误方式 - 不要在根目录运行这些文件
# python performance_test.py  (已移动到debug/)
# python check_excel.py  (已移动到debug/)
# python create_template.py  (已移动到utils/)
```

### 配置验证
```bash
# 验证配置文件
python -c "from config_loader import config; print(config.get_timeout_seconds())"

# 类型检查 (v2.5更新)
mypy voice_gui.py gui_components.py voice_gui_refractor.py main_f.py funasr_voice_TENVAD.py --ignore-missing-imports --explicit-package-bases
mypy text_processor_clean.py --ignore-missing-imports --strict
```

## 🔧 v2.5版本重要修复 (2025-10-26)

### 已解决的关键问题
1. **🐛 停止阻塞问题**: FFmpeg预处理导致的音频流阻塞已完全修复
2. **📝 日志系统错误**: logging_utils.py中super()类型错误已修复
3. **🔍 类型安全问题**: 所有核心模块通过MyPy严格类型检查
4. **✨ 组件化架构**: 新增gui_components.py和voice_gui_refractor.py

### 架构变更
- **FFmpeg处理方式**: 从实时处理改为批量预处理，保持音频流连续性
- **GUI组件化**: 支持模块化开发和维护
- **类型安全**: 完善的类型注解和静态检查

### 测试验证
- ✅ 停止功能测试: 线程在0.0秒内正常结束
- ✅ GUI启动测试: 无日志创建失败错误
- ✅ 类型检查: MyPy检查通过，无类型错误
- ✅ 功能完整性: 所有核心功能正常工作

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
- `README.md` - 完整的项目说明和使用指南 (根目录)
- `docs/DevelopmentRecord.md` - 详细的开发记录和技术决策
- `docs/API文档.md` - API接口文档
- `tests/README.md` - 测试文件说明和运行指南
- `debug/README.md` - 调试文件说明和使用指南

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