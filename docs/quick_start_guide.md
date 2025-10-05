# Voice Input System 快速开始指南

## 🚀 快速开始

本指南将帮助您快速上手Voice Input System的异步化架构。

## 📋 前置条件

- Python 3.8+
- 虚拟环境 (推荐使用venv)
- uv包管理器

## 🛠️ 环境设置

### 1. 激活虚拟环境
```bash
# Windows
source .venv/Scripts/activate

# Linux/Mac
source .venv/bin/activate
```

### 2. 安装依赖
```bash
uv add pytest psutil aiofiles
```

## 🎯 基本使用

### 1. 直接使用适配器

```python
from adapters.audio_processor_adapter import AudioProcessorAdapter
import asyncio

async def main():
    # 创建音频处理器适配器
    processor = AudioProcessorAdapter(test_mode=True)

    # 检查状态
    state = processor.get_state()
    print(f"处理器状态: {state}")

    # 提取数值
    text = "二十五点五"
    measurements = processor.extract_measurements(text)
    print(f"提取的数值: {measurements}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 使用依赖注入容器

```python
from container import DIContainer
from interfaces import IAudioProcessor
from adapters.audio_processor_adapter import AudioProcessorAdapter

# 创建容器
container = DIContainer()

# 注册服务
def create_processor():
    return AudioProcessorAdapter(test_mode=True)

container.register_transient(IAudioProcessor, create_processor)

# 解析服务
processor = container.resolve(IAudioProcessor)
print(f"解析的服务类型: {type(processor).__name__}")
```

### 3. 使用适配器工厂

```python
from adapters.adapter_factory import global_adapter_factory
from interfaces import IAudioProcessor

# 设置默认配置
global_adapter_factory.set_default_config(IAudioProcessor, {
    "test_mode": True
})

# 创建适配器
processor = global_adapter_factory.create_adapter(IAudioProcessor)
```

## 🧪 运行测试

### 1. 运行所有测试
```bash
python -m pytest tests/ -v
```

### 2. 运行特定测试
```bash
# 适配器测试
python -m pytest tests/adapters/ -v

# 容器测试
python -m pytest tests/container/ -v

# 性能测试
python tests/performance/adapter_benchmark.py
```

## 🎭 运行示例

### 1. 直接适配器演示
```bash
python examples/direct_adapter_demo.py
```

### 2. 容器配置示例
```bash
python examples/container_setup_example.py
```

## 📚 主要概念

### 接口 (Interfaces)
- **IAudioProcessor**: 音频处理接口
- **IDataExporter**: 数据导出接口
- **ITTSProvider**: TTS服务接口
- **IConfigProvider**: 配置管理接口

### 适配器 (Adapters)
- 包装现有实现
- 提供统一的接口
- 支持同步和异步调用

### 依赖注入 (DI Container)
- 管理服务生命周期
- 支持依赖解析
- 提供作用域管理

## 🔧 配置选项

### 适配器配置
```python
# 音频处理器配置
AudioProcessorAdapter(
    test_mode=True,
    timeout=30,
    buffer_size=1024
)

# 数据导出器配置
DataExporterAdapter(
    auto_save=True,
    format="xlsx",
    max_records=1000
)
```

### 容器生命周期
- **Transient**: 每次请求创建新实例
- **Scoped**: 作用域内共享实例
- **Singleton**: 全局单例实例

## 🚨 常见问题

### Q: 如何处理导入错误？
A: 确保虚拟环境已激活，所有依赖已安装：
```bash
source .venv/Scripts/activate
uv install
```

### Q: 适配器创建失败怎么办？
A: 检查接口类型是否正确，工厂是否已注册：
```python
from adapters.adapter_factory import global_adapter_factory
supported = global_adapter_factory.get_supported_interfaces()
print(f"支持的接口: {supported}")
```

### Q: 异步方法如何使用？
A: 确保在异步上下文中调用：
```python
async def async_example():
    processor = AudioProcessorAdapter()
    # 注意：当前适配器主要提供同步方法
    result = processor.extract_measurements("二十五点五")
    return result
```

## 📖 更多资源

- [Phase 1 完成总结](phase1_completion_summary.md)
- [接口文档](../interfaces/README.md)
- [适配器文档](../adapters/README.md)
- [容器文档](../container/README.md)

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 编写测试
4. 提交Pull Request

## 📞 获取帮助

如果您遇到问题或需要帮助：

1. 查看文档
2. 运行测试示例
3. 检查日志输出
4. 提交Issue

---

*快速开始指南 v1.0*
*最后更新: 2025-10-05*