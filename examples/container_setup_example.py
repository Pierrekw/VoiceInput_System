# -*- coding: utf-8 -*-
"""
容器配置示例

展示如何配置和使用依赖注入容器的各种功能。
"""

import asyncio
from typing import Any, Dict

from container import DIContainer
from interfaces import (
    IAudioProcessor, IDataExporter, ITTSProvider, IConfigProvider
)
from adapters import (
    AudioProcessorAdapter, DataExporterAdapter,
    TTSProviderAdapter, ConfigProviderAdapter
)


def basic_container_setup():
    """基础容器配置示例"""
    print("=== 基础容器配置 ===")

    container = DIContainer()

    # 注册简单的服务
    container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
    container.register_singleton(IDataExporter, lambda: DataExporterAdapter())
    container.register_singleton(ITTSProvider, lambda: TTSProviderAdapter())

    # 解析服务
    config = container.resolve(IConfigProvider)
    exporter = container.resolve(IDataExporter)

    print(f"配置提供者: {type(config).__name__}")
    print(f"数据导出器: {type(exporter).__name__}")
    print(f"容器服务数量: {container.get_service_count()}")

    return container


def dependency_injection_example():
    """依赖注入示例"""
    print("\n=== 依赖注入示例 ===")

    container = DIContainer()

    # 注册基础服务
    container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
    container.register_singleton(IDataExporter, lambda: DataExporterAdapter())
    container.register_singleton(ITTSProvider, lambda: TTSProviderAdapter())

    # 注册有依赖的服务
    def create_audio_processor_with_deps(c):
        return AudioProcessorAdapter(
            config_provider=c.resolve(IConfigProvider),
            data_exporter=c.resolve(IDataExporter),
            tts_provider=c.resolve(ITTSProvider)
        )

    container.register_transient(IAudioProcessor, create_audio_processor_with_deps)

    # 解析服务
    processor = container.resolve(IAudioProcessor)

    print(f"音频处理器: {type(processor).__name__}")
    print(f"配置提供者: {type(processor.config_provider).__name__}")
    print(f"数据导出器: {type(processor.data_exporter).__name__}")
    print(f"TTS服务: {type(processor.tts_provider).__name__}")


def lifetime_management_example():
    """生命周期管理示例"""
    print("\n=== 生命周期管理示例 ===")

    container = DIContainer()

    # 单例服务
    container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())

    # 瞬态服务
    container.register_transient(ITTSProvider, lambda: TTSProviderAdapter())

    # 作用域服务
    container.register_scoped(IDataExporter, lambda: DataExporterAdapter())

    # 测试单例
    config1 = container.resolve(IConfigProvider)
    config2 = container.resolve(IConfigProvider)
    print(f"单例服务 - 同一实例: {config1 is config2}")

    # 测试瞬态
    tts1 = container.resolve(ITTSProvider)
    tts2 = container.resolve(ITTSProvider)
    print(f"瞬态服务 - 不同实例: {tts1 is not tts2}")

    # 测试作用域
    with container.create_scope():
        exporter1 = container.resolve(IDataExporter)
        exporter2 = container.resolve(IDataExporter)
        print(f"作用域内 - 同一实例: {exporter1 is exporter2}")

    with container.create_scope():
        exporter3 = container.resolve(IDataExporter)
        print(f"不同作用域 - 不同实例: {exporter1 is not exporter3}")


def factory_pattern_example():
    """工厂模式示例"""
    print("\n=== 工厂模式示例 ===")

    from adapters.adapter_factory import global_adapter_factory

    # 使用工厂创建适配器
    audio_processor = global_adapter_factory.create_adapter(IAudioProcessor)
    data_exporter = global_adapter_factory.create_adapter(IDataExporter)

    print(f"工厂创建音频处理器: {type(audio_processor).__name__}")
    print(f"工厂创建数据导出器: {type(data_exporter).__name__}")

    # 设置默认配置
    global_adapter_factory.set_default_config(IAudioProcessor, {
        "test_mode": True,
        "timeout": 30
    })

    # 使用默认配置创建
    processor_with_config = global_adapter_factory.create_adapter(IAudioProcessor)
    print(f"带配置的音频处理器: {type(processor_with_config).__name__}")


def container_validation_example():
    """容器验证示例"""
    print("\n=== 容器验证示例 ===")

    container = DIContainer()

    # 注册服务
    container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
    container.register_singleton(IDataExporter, lambda: DataExporterAdapter())

    # 验证注册
    errors = container.validate_registrations()

    if errors:
        print("验证发现错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("所有服务注册验证通过")

    # 检查服务状态
    registered_services = container.get_registered_services()
    print(f"已注册的服务: {[s.__name__ for s in registered_services]}")


def child_container_example():
    """子容器示例"""
    print("\n=== 子容器示例 ===")

    # 父容器
    parent = DIContainer()
    parent.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())

    # 创建子容器
    child = parent.create_child_container()
    child.register_transient(ITTSProvider, lambda: TTSProviderAdapter())

    print(f"父容器服务数: {parent.get_service_count()}")
    print(f"子容器服务数: {child.get_service_count()}")

    # 子容器可以访问父容器的服务
    parent_config = parent.resolve(IConfigProvider)
    child_config = child.resolve(IConfigProvider)

    print(f"父子容器配置服务相同: {parent_config is child_config}")


async def async_container_example():
    """异步容器使用示例"""
    print("\n=== 异步容器使用示例 ===")

    container = DIContainer()
    container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
    container.register_singleton(IAudioProcessor, lambda: AudioProcessorAdapter())

    # 解析服务
    config = container.resolve(IConfigProvider)
    processor = container.resolve(IAudioProcessor)

    # 异步操作
    await config.set_async("demo.key", "demo_value")
    value = await config.get_async("demo.key")

    print(f"异步配置操作: {value}")

    # 异步音频处理
    state = processor.get_state()
    print(f"音频处理器状态: {state}")


def run_all_examples():
    """运行所有示例"""
    print("Voice Input System 容器配置示例")
    print("=" * 50)

    # 基础配置
    container = basic_container_setup()

    # 依赖注入
    dependency_injection_example()

    # 生命周期管理
    lifetime_management_example()

    # 工厂模式
    factory_pattern_example()

    # 容器验证
    container_validation_example()

    # 子容器
    child_container_example()

    # 异步操作
    asyncio.run(async_container_example())

    print("\n" + "=" * 50)
    print("所有示例运行完成")


if __name__ == "__main__":
    run_all_examples()