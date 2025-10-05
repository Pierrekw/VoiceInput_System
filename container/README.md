# Voice Input System - 依赖注入容器文档

## 📋 概述

本模块提供了完整的依赖注入容器实现，支持服务的注册、解析、生命周期管理等功能。这是系统解耦和组件化架构的核心基础设施。

## 🏗️ 架构组件

```
container/
├── __init__.py              # 模块导出
├── di_container.py          # 核心DI容器实现
├── service_registry.py      # 服务注册表和描述符
├── service_factory.py       # 服务工厂实现
├── exceptions.py            # 异常类定义
└── README.md               # 本文档
```

## 🔌 核心类和接口

### 1. DIContainer - 依赖注入容器

核心容器类，提供服务注册、解析、生命周期管理等功能。

#### 基本用法
```python
from container import DIContainer

# 创建容器
container = DIContainer()

# 注册服务
container.register_transient(IAudioProcessor, AudioProcessor)
container.register_singleton(IConfigProvider, ConfigProvider)

# 解析服务
audio_processor = container.resolve(IAudioProcessor)
config_provider = container.resolve(IConfigProvider)
```

#### 服务注册方法
```python
# 瞬态服务 - 每次解析都创建新实例
container.register_transient(IService, ServiceImplementation)

# 作用域服务 - 同一作用域内返回相同实例
container.register_scoped(IService, ServiceImplementation)

# 单例服务 - 整个容器生命周期内只有一个实例
container.register_singleton(IService, ServiceImplementation)

# 实例注册 - 直接注册预创建实例（单例）
container.register_instance(IService, pre_created_instance)

# 工厂方法注册
container.register_factory(IService, lambda c: ServiceImplementation())
```

### 2. ServiceLifetime - 服务生命周期

```python
class ServiceLifetime(Enum):
    TRANSIENT = "transient"     # 瞬态
    SCOPED = "scoped"           # 作用域
    SINGLETON = "singleton"     # 单例
```

### 3. ServiceDescriptor - 服务描述符

描述一个服务的完整信息，包括类型、实现、生命周期等。

## 🔄 高级功能

### 作用域管理
```python
# 创建作用域
with container.create_scope():
    # 在同一作用域内，作用域服务返回相同实例
    service1 = container.resolve(IScopedService)
    service2 = container.resolve(IScopedService)
    assert service1 is service2

# 作用域结束后，作用域服务实例被释放
```

### 工厂方法
```python
# 使用工厂方法创建服务
container.register_factory(
    IComplexService,
    lambda container: ComplexService(
        container.resolve(IDependency1),
        container.resolve(IDependency2)
    )
)
```

### 反射注入
```python
class Service:
    def __init__(self, dependency: IDependency):
        self.dependency = dependency

# 容器会自动分析构造函数并注入依赖
container.register_transient(IService, Service)
```

### 子容器
```python
# 创建子容器，继承父容器的注册
child_container = container.create_child_container()

# 子容器可以覆盖父容器的注册
child_container.register_singleton(IService, DifferentImplementation)
```

## 🧪 使用示例

### 基本示例
```python
from interfaces import IAudioProcessor, IConfigProvider
from container import DIContainer

# 创建并配置容器
container = DIContainer()
container.register_singleton(IConfigProvider, ConfigProvider)
container.register_transient(IAudioProcessor, AudioProcessor)

# 解析服务
audio_processor = container.resolve(IAudioProcessor)
config_provider = container.resolve(IConfigProvider)

# 使用服务
result = audio_processor.start_recognition()
```

### 复杂示例
```python
class AudioService:
    def __init__(
        self,
        config: IConfigProvider,
        exporter: IDataExporter,
        tts: ITTSProvider
    ):
        self.config = config
        self.exporter = exporter
        self.tts = tts

class VoiceInputSystem:
    def __init__(self, container: DIContainer):
        self.container = container
        self.audio_service = container.resolve(AudioService)

    async def run(self):
        # 使用服务
        await self.audio_service.process_audio()

# 配置容器
container = DIContainer()
container.register_singleton(IConfigProvider, ConfigProvider)
container.register_scoped(IDataExporter, ExcelExporter)
container.register_transient(ITTSProvider, TTSService)
container.register_transient(AudioService, AudioService)

# 创建系统
system = VoiceInputSystem(container)
await system.run()
```

### 异步支持
```python
class AsyncAudioProcessor(IAudioProcessor):
    def __init__(self, config: IConfigProvider):
        self.config = config

    async def start_recognition_async(self) -> RecognitionResult:
        # 异步处理逻辑
        return await self._process_audio()

# 容器支持异步服务的注册和解析
container.register_transient(IAudioProcessor, AsyncAudioProcessor)
processor = container.resolve(IAudioProcessor)
result = await processor.start_recognition_async()
```

## 🛡️ 错误处理

### 常见异常类型
```python
from container.exceptions import (
    ServiceNotRegisteredError,
    CircularDependencyError,
    ServiceCreationError,
    ContainerDisposedError
)

try:
    service = container.resolve(IService)
except ServiceNotRegisteredError:
    print("服务未注册")
except CircularDependencyError:
    print("检测到循环依赖")
except ServiceCreationError:
    print("服务创建失败")
```

### 验证注册
```python
# 验证所有服务注册
errors = container.validate_registrations()
if errors:
    print("注册验证失败:")
    for error in errors:
        print(f"  - {error}")
else:
    print("所有服务注册验证通过")
```

## 📊 性能优化

### 最佳实践
1. **合理使用生命周期**：
   - 无状态服务使用 `Transient`
   - 需要状态共享的服务使用 `Scoped`
   - 全局唯一服务使用 `Singleton`

2. **避免循环依赖**：
   - 使用接口而非具体类型
   - 考虑使用 `Lazy<T>` 模式
   - 重新设计依赖关系

3. **及时释放资源**：
   ```python
   # 使用上下文管理器
   with container.create_scope():
       service = container.resolve(IService)
       # 使用服务...

   # 或手动释放
   container.dispose()
   ```

### 性能监控
```python
# 获取容器统计信息
print(f"已注册服务数量: {container.get_service_count()}")
print(f"已注册服务类型: {container.get_registered_services()}")

# 检查服务是否已注册
if container.is_registered(IService):
    service = container.resolve(IService)
```

## 🔧 扩展和自定义

### 自定义工厂
```python
from container.service_factory import ServiceFactory

class CustomFactory(ServiceFactory):
    def create(self, container: DIContainer) -> Any:
        # 自定义创建逻辑
        return CustomService(container.resolve(IDependency))

    def can_create(self) -> bool:
        return True

# 注册自定义工厂
container.register_factory(IService, CustomFactory())
```

### 自定义异常
```python
from container.exceptions import DIContainerError

class CustomServiceError(DIContainerError):
    def __init__(self, service_name: str, reason: str):
        super().__init__(f"Custom service '{service_name}' error: {reason}")
```

## 🚀 迁移指导

### 从现有代码迁移到DI容器
1. **识别依赖关系**
2. **定义接口**
3. **注册服务**
4. **修改构造函数支持依赖注入**
5. **逐步替换直接创建为容器解析**

### 示例迁移
```python
# 原有代码
class VoiceInputSystem:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.exporter = ExcelExporter()

# 迁移后
class VoiceInputSystem:
    def __init__(self, audio_processor: IAudioProcessor, exporter: IDataExporter):
        self.audio_processor = audio_processor
        self.exporter = exporter

# 配置容器
container = DIContainer()
container.register_transient(IAudioProcessor, AudioProcessor)
container.register_singleton(IDataExporter, ExcelExporter)

# 创建系统
system = VoiceInputSystem(
    container.resolve(IAudioProcessor),
    container.resolve(IDataExporter)
)
```

---

*📅 文档版本: v1.0*
*🔄 最后更新: 2025-10-05*
*👤 维护者: Voice Input System Team*