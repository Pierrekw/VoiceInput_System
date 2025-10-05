# 详细目录重构实施指南

## 1. 总体重构计划

本指南提供了从现有混合结构到新的清晰目录结构的详细步骤，包括文件移动、导入路径修改和共享组件管理。

## 2. 详细目录结构设计

最终目标结构：

```
Voice_Input/
├── shared/
│   ├── __init__.py
│   ├── adapters/
│   ├── config_loader.py
│   ├── excel_exporter.py
│   ├── interfaces/
│   ├── text_processor.py
│   └── voice_correction_dict.txt
├── sync_system/
│   ├── __init__.py
│   ├── audio_capture_v.py
│   └── main.py
├── async_system/
│   ├── __init__.py
│   ├── async_audio/
│   ├── async_config/
│   ├── events/
│   ├── error_handling/
│   ├── optimization/
│   └── main_production.py
├── models/
│   └── [模型文件...]
├── configs/
│   ├── config.yaml
│   ├── sync_config.yaml
│   └── async_config.yaml
├── tests/
│   ├── sync/
│   ├── async/
│   └── shared/
├── docs/
├── examples/
├── logs/
├── requirements_sync.txt
├── requirements_async.txt
└── README.md
```

## 3. 文件移动清单

### 3.1 创建新目录结构

首先创建所有必要的目录：

```bash
mkdir -p shared/adapters shared/interfaces sync_system async_system/models async_system/async_audio async_system/async_config async_system/events async_system/error_handling async_system/optimization models configs tests/sync tests/async tests/shared
```

### 3.2 移动共享组件

```bash
# 移动共享接口
move interfaces shared/

# 移动适配器
move adapters shared/

# 移动配置加载器
move config_loader.py shared/

# 移动Excel导出器
move excel_exporter.py shared/

# 移动文本处理器
move text_processor.py shared/

# 移动语音纠错词典
move voice_correction_dict.txt shared/
```

### 3.3 移动同步系统文件

```bash
# 移动同步系统主文件
move main.py sync_system/

# 移动音频捕获模块
move audio_capture_v.py sync_system/
```

### 3.4 移动异步系统文件

```bash
# 移动异步系统主文件
move main_production.py async_system/

# 移动异步音频模块
move async_audio async_system/

# 移动异步配置模块
move async_config async_system/

# 移动事件系统
move events async_system/

# 移动错误处理
move error_handling async_system/

# 移动优化模块
move optimization async_system/
```

### 3.5 移动配置和模型文件

```bash
# 移动配置文件
move config.yaml configs/

# 创建系统特定配置文件
copy configs/config.yaml configs/sync_config.yaml
copy configs/config.yaml configs/async_config.yaml

# 移动模型文件（如果有单独的模型文件夹）
# 假设模型文件目前在根目录下
# move *.bin models/
# move *.json models/
```

## 4. 导入路径修改策略

### 4.1 基础导入修改原则

所有导入语句需要根据新的目录结构进行更新。主要原则是：

- 从共享组件导入：`from shared.xxx import yyy`
- 系统内部导入：`from .xxx import yyy` 或 `from ..xxx import yyy`
- 跨系统导入（应尽量避免）：`from sync_system.xxx import yyy` 或 `from async_system.xxx import yyy`

### 4.2 同步系统导入修改

修改 `sync_system/main.py`：

```python
# 原导入
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter
from config_loader import config

# 修改为
from .audio_capture_v import AudioCapture, start_keyboard_listener
from shared.excel_exporter import ExcelExporter
from shared.config_loader import config
```

修改 `sync_system/audio_capture_v.py`：

```python
# 原导入
from text_processor import extract_measurements, correct_voice_errors
from excel_exporter import ExcelExporter
from config_loader import config

# 修改为
from shared.text_processor import extract_measurements, correct_voice_errors
from shared.excel_exporter import ExcelExporter
from shared.config_loader import config
```

### 4.3 异步系统导入修改

修改 `async_system/main_production.py`：

```python
# 原导入
from events.event_bus import AsyncEventBus, EventPriority
from events.event_types import (...) 
from interfaces.audio_processor import RecognitionResult
from events.system_coordinator import SystemCoordinator
from optimization.async_optimizer import (...) 
from error_handling.async_error_handler import (...) 
from async_audio.async_audio_stream_controller import (...) 
from text_processor import extract_measurements
from adapters.data_exporter_adapter import DataExporterAdapter
from async_audio.async_audio_capture import AsyncAudioCapture
from async_config import AsyncConfigLoader, create_audio_config_validator, create_system_config_validator

# 修改为
from .events.event_bus import AsyncEventBus, EventPriority
from .events.event_types import (...) 
from shared.interfaces.audio_processor import RecognitionResult
from .events.system_coordinator import SystemCoordinator
from .optimization.async_optimizer import (...) 
from .error_handling.async_error_handler import (...) 
from .async_audio.async_audio_stream_controller import (...) 
from shared.text_processor import extract_measurements
from shared.adapters.data_exporter_adapter import DataExporterAdapter
from .async_audio.async_audio_capture import AsyncAudioCapture
from .async_config import AsyncConfigLoader, create_audio_config_validator, create_system_config_validator
```

### 4.4 适配器模块导入修改

修改 `shared/adapters/async_audio_processor_adapter.py`：

```python
# 原导入
from interfaces.audio_processor import IAudioProcessor, AudioProcessorState, RecognitionResult
from async_audio.async_audio_capture import AsyncAudioCapture

# 修改为
from ..interfaces.audio_processor import IAudioProcessor, AudioProcessorState, RecognitionResult
from async_system.async_audio.async_audio_capture import AsyncAudioCapture
```

### 4.5 批量修改工具

可以使用Python脚本批量处理导入路径修改：

```python
import os
import re

# 修改同步系统导入
for root, _, files in os.walk('sync_system'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换导入路径
            content = re.sub(r'from audio_capture_v import', r'from .audio_capture_v import', content)
            content = re.sub(r'from excel_exporter import', r'from shared.excel_exporter import', content)
            content = re.sub(r'from config_loader import', r'from shared.config_loader import', content)
            content = re.sub(r'from text_processor import', r'from shared.text_processor import', content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

# 类似地处理异步系统和共享组件的导入
```

## 5. 共享组件管理

### 5.1 创建共享模块 `__init__.py`

确保 `shared/__init__.py` 包含所有需要暴露的共享组件：

```python
# shared/__init__.py
from .text_processor import extract_measurements, correct_voice_errors, process_voice_text
export_measurements, correct_voice_errors, process_voice_text
from .config_loader import config
from .excel_exporter import ExcelExporter
from .interfaces import IAudioProcessor, IDataExporter, ITTSProvider, IConfigProvider, ISystemController

__all__ = [
    'extract_measurements', 'correct_voice_errors', 'process_voice_text',
    'config',
    'ExcelExporter',
    'IAudioProcessor', 'IDataExporter', 'ITTSProvider', 'IConfigProvider', 'ISystemController'
]
```

### 5.2 配置系统的分离与共享

修改 `shared/config_loader.py` 以支持多配置文件：

```python
# 原代码
def load_config(config_path='config.yaml'):
    # 加载配置逻辑

# 修改为
def load_config(config_path=None):
    # 默认配置路径逻辑
    if config_path is None:
        # 根据调用位置自动选择配置文件
        import inspect
        caller_file = inspect.stack()[1].filename
        if 'sync_system' in caller_file:
            config_path = 'configs/sync_config.yaml'
        elif 'async_system' in caller_file:
            config_path = 'configs/async_config.yaml'
        else:
            config_path = 'configs/config.yaml'
    
    # 加载配置逻辑
```

### 5.3 模型文件管理

创建 `shared/model_manager.py` 来统一管理模型加载：

```python
# shared/model_manager.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelManager: