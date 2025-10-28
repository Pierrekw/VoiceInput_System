# Utils 工具包

这个目录包含了各种专用工具和调试模块，用于支持语音输入系统的各种功能。

## 📁 目录结构

```
utils/
├── __init__.py                    # 包初始化文件
├── README.md                      # 本说明文档
├── debug_performance_tracker.py   # Debug性能追踪工具
├── production_latency_logger.py   # 生产环境延迟日志工具
├── performance_monitor.py         # 性能监控工具
├── config_loader.py               # 配置管理工具
└── logging_utils.py               # 日志工具
```

## 🔧 工具文件说明

### 1. 调试工具

#### debug_performance_tracker.py
- **用途**: Debug模式下的性能追踪和延迟分析
- **主要功能**:
  - 追踪语音识别各步骤的性能指标
  - 记录详细的时间戳和延迟数据
  - 生成性能分析报告
- **使用方式**:
  ```python
  from utils.debug_performance_tracker import debug_tracker
  debug_tracker.start_step("语音识别")
  # ... 执行语音识别
  debug_tracker.end_step("语音识别")
  ```

#### production_latency_logger.py
- **用途**: 生产环境下的延迟记录和监控
- **主要功能**:
  - 记录端到端的语音识别延迟
  - 保存生产环境性能数据
  - 支持延迟会话管理
- **使用方式**:
  ```python
  from utils.production_latency_logger import (
      start_latency_session, end_latency_session,
      log_voice_input_end, log_asr_complete
  )
  start_latency_session()
  log_voice_input_end(audio_duration)
  log_asr_complete(recognition_result)
  end_latency_session()
  ```

### 2. 配置工具

#### configure_ten_vad.py
- **用途**: TEN VAD神经网络语音活动检测的配置工具
- **主要功能**:
  - 配置TEN VAD参数
  - 测试VAD性能
  - 优化VAD设置
- **使用方式**: 直接运行脚本进行配置

#### setup_ffmpeg_env.py
- **用途**: FFmpeg音频预处理环境设置
- **主要功能**:
  - 配置FFmpeg路径
  - 验证FFmpeg安装
  - 设置音频预处理参数
- **使用方式**: 直接运行脚本进行环境设置

#### safe_funasr_import.py
- **用途**: FunASR模块的安全导入和错误处理
- **主要功能**:
  - 安全导入FunASR相关模块
  - 处理导入失败的情况
  - 提供备用方案
- **使用方式**:
  ```python
  from utils.safe_funasr_import import safe_import_funasr
  funasr_available = safe_import_funasr()
  ```

## 📦 Utils工具包最终结构 (v2.6)

### 🎯 核心原则
- **实用导向**: 只保留项目实际使用的工具模块
- **功能完整**: 涵盖配置、日志、性能监控、调试等核心功能
- **结构清晰**: 7个工具模块，职责明确

### 📊 模块分类
1. **核心基础设施** (3个):
   - `config_loader.py` - 配置管理
   - `logging_utils.py` - 日志工具
   - `performance_monitor.py` - 性能监控

2. **调试和分析工具** (2个):
   - `debug_performance_tracker.py` - Debug性能追踪
   - `production_latency_logger.py` - 生产延迟日志

3. **配置和优化工具** (2个):
   - `configure_ten_vad.py` - TEN VAD配置

### 🗃️ 已归档模块
以下模块因未在主项目中使用，已移至archive/目录：
- `setup_ffmpeg_env.py` - FFmpeg设置已集成到主程序
- `safe_funasr_import.py` - FunASR导入已在主程序中处理
- `smart_decimal_config.py` - 智能小数点配置，当前未使用

## 📦 导入方式

### 方式1: 从utils包导入 (推荐)
```python
# 导入调试工具
from utils.debug_performance_tracker import debug_tracker

# 导入生产延迟日志工具
from utils.production_latency_logger import start_latency_session, end_latency_session

# 导入配置工具
from utils.configure_ten_vad import configure_vad
from utils.safe_funasr_import import safe_import_funasr
```

### 方式2: 通过包初始化导入
```python
import utils

# 使用调试工具
utils.debug_tracker.start_step("测试")

# 使用延迟日志
utils.start_latency_session()
```

## 🎯 使用注意事项

1. **调试工具**: 仅在debug模式下使用，生产环境应谨慎使用
2. **延迟日志**: 生产环境可以正常使用，有助于性能监控
3. **配置工具**: 主要用于环境设置和参数调整
4. **安全导入**: 确保FunASR模块的稳定导入

## 📊 依赖关系

- `debug_performance_tracker.py`: 依赖 `logging_utils.py`
- `production_latency_logger.py`: 依赖 `logging_utils.py`
- 其他工具相对独立，可单独使用

## 🔄 更新历史

- **2025-10-26**: 创建utils目录，整理专用工具文件
- 从根目录移动6个工具文件到utils目录
- 更新主程序的import路径
- 创建包结构和说明文档

## 💡 维护说明

- 新的工具文件可以添加到此目录
- 需要更新 `__init__.py` 中的导出列表
- 确保新工具遵循项目的日志规范
- 保持工具的独立性和可复用性