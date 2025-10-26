# FunASR语音输入系统 - Claude项目规则

## 🎯 项目概述
这是一个基于FunASR框架的高性能中文语音识别系统，集成TEN VAD神经网络、FFmpeg音频预处理、GUI图形界面，支持实时语音识别、性能监控、延迟优化和Excel数据导出功能。

## 📋 当前版本 (v2.6)
- **发布日期**: 2025-10-26
- **核心特性**: TEN VAD + FFmpeg预处理 + 组件化GUI架构 + Utils工具包 + 项目规范化
- **主要修复**: 解决停止阻塞问题、日志系统修复、类型安全优化、文件组织规范化、工具包集成

## 🔄 重要/主要更新记录

### 2025-10-26 - v2.6 最终精简版
- **项目结构重大重组**: 创建Utils工具包，根目录从29个文件减少到6个文件 (减少79%)
- **文件命名规范化**: 将`funasr_voice_TENVAD.py`重命名为`funasr_voice_tenvad.py`，符合Python命名规范
- **工具包集成**: 将6个核心工具模块集中到utils目录，统一import路径
- **未使用模块归档**: 清理4个未使用的工具模块到archive目录
- **文档管理严格化**: 严格控制MD文件创建，只保留必要文档
- **实用化100%**: 所有保留模块都在实际使用中

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
├── utils/                    # 🔧 Utils工具包 (v2.6新增)
│   ├── __init__.py           # 包初始化和便捷导入
│   ├── README.md             # 工具包说明文档
│   ├── performance_monitor.py   # 性能监控
│   ├── config_loader.py         # 配置管理
│   ├── logging_utils.py         # 日志工具
│   ├── debug_performance_tracker.py  # Debug性能追踪
│   └── production_latency_logger.py  # 生产延迟日志
├── main_f.py                 # 核心系统类
├── funasr_voice_tenvad.py    # TEN VAD + FFmpeg集成模块
├── voice_gui.py              # 主要GUI界面
├── excel_exporter.py         # Excel导出模块
├── text_processor_clean.py   # 文本处理模块 (重构优化)
├── config.yaml               # 配置文件
├── archive/                  # 归档文件目录
├── reports/                  # Excel输出目录
├── Logs/                     # 日志文件目录
└── onnx_deps/                # ONNX依赖目录
```

### 运行测试的标准方式
```bash
# 从项目根目录运行测试 (正确方式)
python tests/test_text_processor_refactor.py
python tests/test_funasr_voice_module.py

# 错误方式 - 不要在根目录创建测试文件
# ❌ python test_something.py  (禁止)
```
### 🎯 修改核心模块的标准方式 (v2.6新增)
```bash
# 1. 修改重要模块前必须备份 (避免文件混乱)
cp main_f.py main_f_bak.py
cp funasr_voice_TENVAD.py funasr_voice_TENVAD_bak.py
cp voice_gui.py voice_gui_bak.py

# 2. 然后在原文件中修改，不要创建新文件
modify main_f.py  # ✅ 正确方式

# 3. 禁止的命名方式 (避免文件混乱)
# ❌ main_f_new.py, main_f_fixed.py, main_f_final.py, main_f_v2.py
# ❌ main_f_new_fixed_final.py, main_f_2025_10_26.py
```

### 📁 文件组织规则 (v2.6新增)

#### 1. MD文档文件管理 (严格控制)

**🚨 重要限制**: 严禁随意创建新的MD文件！

**允许的MD文档**:
```
项目根目录/
├── README.md                           # 主项目说明文档

Docs/目录/
├── DevelopmentRecord.MD                # 开发记录 (唯一允许的开发文档)
└── [分支特定文档]/                       # 新分支可建一个MD文档
    └── [分支名].md                      # 仅在必要时，需用户批准
```

**🚫 禁止的MD文件**:
- ❌ 未经用户批准新建任何MD文件
- ❌ 创建重复、冗余的文档
- ❌ 为小功能创建单独的MD文档
- ❌ 创建临时性MD文档

**✅ 文档管理原则**:
- 主项目信息全部记录在 README.md
- 开发过程记录在 Docs/DevelopmentRecord.MD
- 新分支可创建一个文档，但需要用户批准
- 其他所有信息都应整合到现有文档中

#### 2. 日志文件统一管理
```
Logs/                      # ⚠️ 所有日志文件必须放在这里
├── voice_recognition.log
├── voice_recognition_debug.log
├── performance_test.log
├── debug_performance_test.log
├── gui_debug.log
├── excel_export.log
└── [模块名]_[功能].log    # 标准命名格式
```

**日志使用规范**:
- 新建Python文件必须使用 `logging_utils.py` 管理日志
- 确保日志文件名包含模块名，方便debug
- 禁止在项目根目录创建.log文件
- 禁止使用Python默认logging而不指定文件名

#### 3. 新建Python文件的日志要求
```python
# 标准日志使用模板
import logging
from logging_utils import setup_logger

# 设置带文件名的日志
logger = setup_logger(
    name='模块名',
    log_file='Logs/模块名_功能.log'
)

def some_function():
    logger.info("这是一条信息日志")
    logger.debug("这是调试信息")
    logger.error("这是错误信息")
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
- 重要修改需要记录到 Docs/DevelopmentRecord.MD
- 测试文件需要包含在 tests/README.md 中
- **新增**: 所有新文档必须放在 Docs/ 目录内，只有README.md可以在根目录

## 🚨 重要提醒 (v2.6更新)

### 当Claude需要创建测试文件时:
1. ✅ **必须**放在 `tests/` 目录下
2. ✅ **必须**使用 `test_*.py` 命名
3. ✅ **必须**添加正确的导入路径
4. ✅ **必须**从项目根目录运行测试

### 当Claude需要修改核心模块时:
1. ✅ **必须**先备份原文件: `cp xx.py xx_bak.py`
2. ✅ **必须**在原文件中修改，不创建新文件
3. ✅ **必须**使用 `logging_utils.py` 管理日志
4. ✅ **必须**确保日志文件在 Logs/ 目录

### 当Claude需要创建文档时:
1. ✅ **必须**放在 `Docs/` 目录下
2. ✅ **只有README.md可以放在根目录**
3. ✅ **必须**使用有意义的文件名

### 常见错误 (禁止):
- ❌ 在根目录创建 `test_*.py` 文件
- ❌ 创建 `xxx_new.py`, `xxx_fixed.py`, `xxx_final.py` 等重复文件
- ❌ 在根目录创建 `.log` 文件
- ❌ **在根目录创建除README.md外的MD文件**
- ❌ **未经用户批准创建任何新的MD文件**
- ❌ **为小功能或临时需求创建MD文档**
- ❌ 忘记添加导入路径修复
- ❌ 测试文件命名不规范
- ❌ 不使用logging_utils.py管理日志

### 🚨 文档创建红线 (v2.6重要更新)
**绝对禁止**:
1. 不得创建任何新的MD文件，除非用户明确批准
2. 不得为每个小功能创建单独文档
3. 不得创建重复内容的文档
4. 不得创建临时性或测试性MD文档

**唯一允许**:
1. README.md (主项目文档)
2. Docs/DevelopmentRecord.MD (开发记录)
3. 新分支的一个文档 (需要用户批准)

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

# 类型检查 (v2.5更新)
mypy voice_gui.py gui_components.py voice_gui_refractor.py main_f.py funasr_voice_TENVAD.py --ignore-missing-imports --explicit-package-bases
mypy text_processor_clean.py --ignore-missing-imports --strict
```

## 🔧 v2.6版本重要修复 (2025-10-26)

### 新增项目规范化规则
1. **📁 文件组织规范**: 所有MD文档统一放在Docs/目录，日志文件统一放在Logs/目录
2. **🔧 模块修改规范**: 重要模块修改前必须备份，避免创建重复文件
3. **📝 日志管理规范**: 新建Python文件必须使用logging_utils.py管理日志
4. **🎯 命名规范**: 禁止xxx_new、xxx_fixed、xxx_final等混乱的命名方式

### v2.5版本已解决的关键问题
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
**最后更新**: 2025-10-26
**版本**: v2.6
**项目状态**: 活跃开发中，支持质量检测场景 + 项目规范化