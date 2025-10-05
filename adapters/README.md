# Voice Input System - 适配器模块文档

## 📋 概述

本模块提供现有代码到新接口的适配器实现，采用适配器模式包装现有实现，确保系统的向后兼容性。这是系统解耦和异步化改造的关键中间层。

## 🏗️ 适配器架构

```
adapters/
├── __init__.py              # 模块导出
├── audio_processor_adapter.py   # 音频处理器适配器
├── data_exporter_adapter.py     # 数据导出器适配器
├── tts_provider_adapter.py      # TTS语音服务适配器
├── config_provider_adapter.py   # 配置提供者适配器
├── adapter_factory.py          # 适配器工厂
├── adapter_registry.py         # 适配器注册表
└── README.md                  # 本文档
```

## 🔌 核心适配器实现

### 1. AudioProcessorAdapter - 音频处理器适配器

将现有的 `AudioCapture` 类适配为 `IAudioProcessor` 接口。

**主要功能**:
- 包装 AudioCapture 的所有方法
- 提供同步和异步两种调用模式
- 保持原有功能的完整性
- 增强错误处理和日志记录

**使用示例**:
```python
from adapters import AudioProcessorAdapter
from audio_capture_v import AudioCapture

# 使用现有实例创建适配器
capture = AudioCapture(test_mode=True)
adapter = AudioProcessorAdapter(audio_capture=capture)

# 或者创建新实例
adapter = AudioProcessorAdapter(test_mode=True)

# 使用接口方法
result = await adapter.start_recognition_async()
values = adapter.extract_measurements("二十五点五")
```

### 2. DataExporterAdapter - 数据导出器适配器

将现有的 `ExcelExporter` 类适配为 `IDataExporter` 接口。

**主要功能**:
- 包装 ExcelExporter 的数据操作方法
- 提供统一的数据格式转换
- 增强批量操作和错误处理
- 支持文件管理和统计功能

**使用示例**:
```python
from adapters import DataExporterAdapter
from excel_exporter import ExcelExporter

# 创建适配器
exporter = DataExporterAdapter()

# 异步导出数据
data = [(1.5, "一点五"), (2.0, "二点零")]
result = await exporter.append_data_async(data)

# 批量导出
batches = [[1.0, 2.0], [3.0, 4.0]]
results = await exporter.batch_export_async(batches)
```

### 3. TTSProviderAdapter - TTS语音服务适配器

将现有的 `TTS` 类适配为 `ITTSProvider` 接口。

**主要功能**:
- 包装 TTS 的语音合成和播放功能
- 提供统一的配置和状态管理
- 支持批量处理和便捷方法
- 增强音频格式支持

**使用示例**:
```python
from adapters import TTSProviderAdapter

# 创建适配器
tts = TTSProviderAdapter()

# 异步语音合成
result = await tts.speak_async("测试语音合成")

# 批量数字播报
numbers = [25, 100, 50]
results = await tts.speak_numbers_async(numbers)
```

### 4. ConfigProviderAdapter - 配置提供者适配器

将现有的 `ConfigLoader` 类适配为 `IConfigProvider` 接口。

**主要功能**:
- 包装 ConfigLoader 的配置访问方法
- 提供运行时配置修改功能
- 支持配置变更监听
- 增强缓存和环境变量支持

**使用示例**:
```python
from adapters import ConfigProviderAdapter

# 创建适配器
config = ConfigProviderAdapter()

# 异步配置访问
timeout = await config.get_async("recognition.timeout_seconds", 60)

# 运行时配置修改
await config.set_async("custom.setting", "value")

# 监听配置变更
def on_config_change(event):
    print(f"Config changed: {event.data['key']}")

watcher_id = await config.watch_async(on_config_change)
```

## 🏭 适配器工厂和注册表

### AdapterFactory - 适配器工厂

提供适配器实例的创建和管理功能。

**主要功能**:
- 统一的适配器创建接口
- 支持参数化配置
- 默认配置管理
- 类型安全的工厂方法

**使用示例**:
```python
from adapters.adapter_factory import global_adapter_factory

# 设置默认配置
global_adapter_factory.set_default_config(
    IAudioProcessor,
    {"test_mode": True, "timeout": 30}
)

# 创建适配器
processor = global_adapter_factory.create_adapter(IAudioProcessor)

# 使用便捷函数
from adapters import create_audio_processor_adapter
processor = create_audio_processor_adapter(test_mode=True)
```

### AdapterRegistry - 适配器注册表

管理适配器的注册、发现和生命周期。

**主要功能**:
- 适配器注册和发现
- 默认适配器管理
- 版本控制支持
- 统计和诊断信息

**使用示例**:
```python
from adapters.adapter_registry import global_adapter_registry

# 获取支持的接口
interfaces = global_adapter_registry.get_supported_interfaces()

# 获取默认适配器
default_adapter = global_adapter_registry.get_default_adapter(IAudioProcessor)

# 获取统计信息
stats = global_adapter_registry.get_adapter_statistics()
print(f"Total adapters: {stats['total_adapters']}")
```

## 🔄 依赖注入集成

### 与 DIContainer 集成

适配器完美兼容依赖注入容器。

**基本集成**:
```python
from container import DIContainer
from adapters import AudioProcessorAdapter

container = DIContainer()

# 注册适配器
container.register_singleton(
    IAudioProcessor,
    lambda: AudioProcessorAdapter(test_mode=True)
)

# 解析适配器
processor = container.resolve(IAudioProcessor)
```

**复杂依赖注入**:
```python
# 注册所有适配器
container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
container.register_singleton(IDataExporter, lambda: DataExporterAdapter())
container.register_singleton(ITTSProvider, lambda: TTSProviderAdapter())

# 注册有依赖的适配器
container.register_transient(
    IAudioProcessor,
    lambda c: AudioProcessorAdapter(
        config_provider=c.resolve(IConfigProvider),
        data_exporter=c.resolve(IDataExporter),
        tts_provider=c.resolve(ITTSProvider)
    )
)
```

## 📊 适配器对比

| 原类 | 适配器接口 | 主要增强 | 异步支持 |
|------|------------|----------|----------|
| AudioCapture | IAudioProcessor | 异步调用、错误处理、状态管理 | ✅ |
| ExcelExporter | IDataExporter | 批量操作、格式转换、文件管理 | ✅ |
| TTS | ITTSProvider | 配置管理、批量处理、格式支持 | ✅ |
| ConfigLoader | IConfigProvider | 运行时修改、事件监听、缓存 | ✅ |

## 🧪 测试和验证

### 运行测试

```bash
# 运行所有适配器测试
python -m pytest tests/adapters/ -v

# 运行特定适配器测试
python -m pytest tests/adapters/test_audio_processor_adapter.py -v

# 运行集成测试
python -m pytest tests/adapters/test_adapter_integration.py -v
```

### 测试覆盖率

```bash
# 生成测试覆盖率报告
python -m pytest tests/adapters/ --cov=adapters --cov-report=html
```

## 🛠️ 最佳实践

### 1. 使用工厂创建适配器

```python
# 推荐：使用工厂
adapter = global_adapter_factory.create_adapter(IAudioProcessor)

# 不推荐：直接实例化
adapter = AudioProcessorAdapter()
```

### 2. 利用依赖注入

```python
# 推荐：通过容器管理
container.register_singleton(IAudioProcessor, factory)

# 不推荐：直接创建管理
processor = AudioProcessorAdapter()
```

### 3. 优先使用异步方法

```python
# 推荐：异步调用
result = await adapter.start_recognition_async()

# 可用：同步调用
result = adapter.start_recognition()
```

### 4. 合理配置生命周期

```python
# 单例：全局共享的服务
container.register_singleton(IConfigProvider, factory)

# 瞬态：每次需要新实例的服务
container.register_transient(IAudioProcessor, factory)

# 作用域：会话内共享的服务
container.register_scoped(IDataExporter, factory)
```

## 🚀 迁移路径

### 从现有代码迁移

1. **识别现有实例**
   ```python
   # 现有代码
   capture = AudioCapture()
   ```

2. **创建适配器**
   ```python
   # 迁移后
   adapter = AudioProcessorAdapter(audio_capture=capture)
   ```

3. **更新调用方式**
   ```python
   # 现有调用
   result = capture.listen_realtime_vosk()

   # 迁移后
   result = await adapter.start_recognition_async()
   ```

4. **集成到容器**
   ```python
   # 完全迁移后
   container.register_singleton(IAudioProcessor, factory)
   processor = container.resolve(IAudioProcessor)
   result = await processor.start_recognition_async()
   ```

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```
   ImportError: cannot import name 'AudioCapture'
   ```
   **解决**: 确保在正确的环境中运行，相关模块可用

2. **适配器创建失败**
   ```
   ValueError: No factory registered for interface type
   ```
   **解决**: 检查接口类型是否正确，工厂是否已注册

3. **异步方法不工作**
   ```
   RuntimeError: There is no current event loop
   ```
   **解决**: 确保在异步上下文中调用

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查适配器状态**
   ```python
   diagnostics = adapter.get_diagnostics_info()
   print(diagnostics)
   ```

3. **验证工厂注册**
   ```python
   supported = global_adapter_factory.get_supported_interfaces()
   print(f"Supported interfaces: {supported}")
   ```

---

*📅 文档版本: v1.0*
*🔄 最后更新: 2025-10-05*
*👤 维护者: Voice Input System Team*