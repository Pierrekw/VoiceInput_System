# Voice Input System - 接口定义文档

## 📋 概述

本目录包含了Voice Input System的所有核心接口定义，为系统的解耦和异步化改造提供抽象层。

## 🏗️ 接口架构

```
interfaces/
├── __init__.py              # 接口模块导出
├── audio_processor.py       # 音频处理器接口
├── data_exporter.py         # 数据导出器接口
├── tts_provider.py          # TTS语音服务接口
├── config_provider.py       # 配置提供者接口
├── system_controller.py     # 系统控制器接口
└── README.md               # 本文档
```

## 🔌 核心接口

### 1. IAudioProcessor - 音频处理器接口

负责音频处理的核心功能，包括语音识别、数值提取、TTS控制等。

**主要功能**:
- 语音模型管理（加载/卸载）
- 实时语音识别（同步/异步）
- 数值提取和语音命令处理
- TTS语音播报控制
- 状态管理和配置

**关键方法**:
```python
# 核心识别方法
async def start_recognition_async() -> RecognitionResult
def extract_measurements(text: str) -> List[float]

# TTS控制方法
async def speak_text_async(text: str) -> None
def toggle_tts() -> bool

# 状态管理
def get_state() -> AudioProcessorState
def pause_recognition() -> None
```

### 2. IDataExporter - 数据导出器接口

负责数据的持久化存储，主要处理Excel文件操作。

**主要功能**:
- Excel文件创建和格式化
- 数据追加和批量导出
- 会话数据管理
- 配置管理和统计

**关键方法**:
```python
# 数据导出方法
async def append_data_async(data) -> ExportResult
async def append_with_text_async(data) -> List[Tuple]

# 文件管理方法
async def create_new_file_async() -> bool
async def format_excel_async() -> bool

# 统计方法
def get_export_statistics() -> Dict[str, Any]
```

### 3. ITTSProvider - TTS语音服务接口

负责文本转语音功能，提供语音合成和播放控制。

**主要功能**:
- 文本转语音合成
- 音频播放控制
- 音质参数调节
- 批量语音处理

**关键方法**:
```python
# 核心合成方法
async def speak_async(text: str) -> TTSResult
async def synthesize_speech_async(text: str, output_file: str) -> TTSResult

# 播放控制方法
async def play_audio_async(file_path: str) -> PlaybackResult
async def stop_playback_async() -> bool

# 便捷方法
async def speak_number_async(number: Union[int, float]) -> TTSResult
```

### 4. IConfigProvider - 配置提供者接口

负责配置管理，支持热重载、环境变量覆盖等功能。

**主要功能**:
- 配置文件加载和解析
- 配置项读写和验证
- 环境变量覆盖
- 配置变更监听

**关键方法**:
```python
# 配置访问方法
async def get_async(key: str, default: Any = None) -> Any
async def set_async(key: str, value: Any) -> bool

# 文件管理方法
async def reload_async() -> bool
async def save_async(file_path: Optional[str] = None) -> bool

# 监听方法
async def watch_async(callback: Callable[[ConfigChangeEvent], None]) -> str
```

### 5. ISystemController - 系统控制器接口

负责系统整体协调和控制，管理组件生命周期。

**主要功能**:
- 系统生命周期管理
- 组件协调和配置
- 事件处理和通知
- 健康检查和诊断

**关键方法**:
```python
# 生命周期管理
async def initialize_async(config: Optional[ComponentConfig] = None) -> bool
async def start_async() -> bool
async def stop_async() -> bool

# 组件管理
def set_audio_processor(processor: IAudioProcessor) -> None
def get_audio_processor() -> Optional[IAudioProcessor]

# 事件管理
async def publish_event_async(event: SystemEvent) -> None
async def subscribe_async(event_type: EventType, callback) -> str
```

## 🔄 同步/异步设计原则

### 设计理念
所有接口都提供了同步和异步两种方法，以支持渐进式迁移：

1. **同步方法**: 保持与现有代码的兼容性
2. **异步方法**: 为未来的异步化提供支持
3. **统一接口**: 确保API的一致性

### 命名约定
- **同步方法**: 使用标准命名，如 `start_recognition()`
- **异步方法**: 添加 `_async` 后缀，如 `start_recognition_async()`

### 返回值设计
- **同步方法**: 直接返回结果或抛出异常
- **异步方法**: 返回协程对象，使用 `await` 获取结果

## 📊 数据类型定义

### 核心数据类
每个接口都定义了相应的数据类，用于封装复杂的数据结构：

```python
# 音频处理相关
class RecognitionResult:     # 识别结果
class VoiceCommand:          # 语音命令
class AudioProcessorState:   # 处理器状态

# 数据导出相关
class ExportRecord:          # 导出记录
class ExportResult:          # 导出结果
class ExportConfig:          # 导出配置

# TTS相关
class TTSResult:             # TTS结果
class PlaybackResult:        # 播放结果
class TTSConfig:             # TTS配置

# 配置相关
class ConfigMetadata:        # 配置元数据
class ConfigChangeEvent:     # 配置变更事件

# 系统控制相关
class SystemEvent:           # 系统事件
class SystemInfo:            # 系统信息
class ComponentConfig:       # 组件配置
```

### 枚举类型
使用枚举类型提高代码的可读性和类型安全：

```python
class AudioProcessorState(Enum):     # 音频处理器状态
class ExportStatus(Enum):            # 导出状态
class TTSState(Enum):               # TTS状态
class SystemState(Enum):            # 系统状态
class EventType(Enum):              # 事件类型
```

## 🧪 使用示例

### 基本使用模式

```python
from interfaces import IAudioProcessor, IDataExporter

# 创建实例（具体实现类）
audio_processor = SomeAudioProcessor()
data_exporter = SomeDataExporter()

# 同步调用
result = audio_processor.start_recognition()
export_result = data_exporter.append_data(data)

# 异步调用
async def main():
    result = await audio_processor.start_recognition_async()
    export_result = await data_exporter.append_data_async(data)
```

### 依赖注入模式

```python
from interfaces import ISystemController, IAudioProcessor

class MySystemController(ISystemController):
    def __init__(self):
        self.audio_processor: Optional[IAudioProcessor] = None

    def set_audio_processor(self, processor: IAudioProcessor) -> None:
        self.audio_processor = processor

    async def start_async(self) -> bool:
        if self.audio_processor:
            return await self.audio_processor.start_recognition_async()
        return False
```

## 🔧 类型注解和文档

### 类型注解策略
- 使用完整的类型注解，包括参数和返回值
- 使用 `typing` 模块的类型（List, Dict, Optional, Union等）
- 使用 `asyncio.Future` 和协程类型

### 文档字符串标准
```python
def method_name(self, param1: str, param2: Optional[int] = None) -> bool:
    """
    方法功能简述

    Args:
        param1: 参数1的描述
        param2: 参数2的描述，可选参数

    Returns:
        bool: 返回值的描述

    Raises:
        ValueError: 异常情况的描述
        RuntimeError: 另一种异常情况的描述

    Example:
        >>> result = obj.method_name("test", 42)
        >>> print(result)
        True
    """
```

## 🚀 迁移指导

### 从现有代码迁移
1. **识别需要接口化的类**
2. **创建适配器类实现接口**
3. **逐步替换直接调用为接口调用**
4. **验证功能完整性**

### 异步化迁移步骤
1. **保持现有同步方法不变**
2. **添加对应的异步方法**
3. **逐步将调用方改为异步调用**
4. **优化异步性能和错误处理**

## 📈 扩展指南

### 添加新接口
1. 在相应文件中定义新的接口类
2. 添加必要的数据类和枚举
3. 实现完整的类型注解
4. 编写详细的文档字符串
5. 更新 `__init__.py` 导出

### 接口版本控制
- 使用语义化版本号
- 向后兼容的更改不增加主版本号
- 破坏性更改需要增加主版本号

---

*📅 文档版本: v1.0*
*🔄 最后更新: 2025-10-05*
*👤 维护者: Voice Input System Team*