# -*- coding: utf-8 -*-
"""
简单集成测试

测试基础的依赖注入和适配器功能。
"""

import asyncio
from container import DIContainer
from interfaces import IConfigProvider, IAudioProcessor
from adapters import ConfigProviderAdapter, AudioProcessorAdapter


def simple_container_test():
    """简单的容器测试"""
    print("=== 简单容器测试 ===")

    container = DIContainer()

    # 使用类而不是lambda函数
    container.register_singleton(IConfigProvider, ConfigProviderAdapter)
    container.register_singleton(IAudioProcessor, AudioProcessorAdapter)

    print(f"注册的服务数量: {container.get_service_count()}")

    # 解析服务
    try:
        config = container.resolve(IConfigProvider)
        print(f"配置提供者类型: {type(config).__name__}")
        print(f"配置提供者是否为IConfigProvider实例: {isinstance(config, IConfigProvider)}")

        processor = container.resolve(IAudioProcessor)
        print(f"音频处理器类型: {type(processor).__name__}")
        print(f"音频处理器是否为IAudioProcessor实例: {isinstance(processor, IAudioProcessor)}")

        # 测试基本功能
        state = processor.get_state()
        print(f"音频处理器状态: {state}")

        return True

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def async_functionality_test():
    """异步功能测试"""
    print("\n=== 异步功能测试 ===")

    container = DIContainer()
    container.register_singleton(IConfigProvider, ConfigProviderAdapter)

    try:
        config = container.resolve(IConfigProvider)

        # 测试异步配置操作
        await config.set_async("test.key", "test_value")
        value = await config.get_async("test.key", "default")
        print(f"异步配置操作结果: {value}")

        # 测试缓存大小
        cache_size = config.get_cache_size()
        print(f"配置缓存大小: {cache_size}")

        return True

    except Exception as e:
        print(f"异步操作错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def factory_test():
    """工厂测试"""
    print("\n=== 工厂测试 ===")

    from adapters.adapter_factory import global_adapter_factory

    try:
        # 使用工厂创建适配器
        config = global_adapter_factory.create_adapter(IConfigProvider)
        processor = global_adapter_factory.create_adapter(IAudioProcessor)

        print(f"工厂创建配置提供者: {type(config).__name__}")
        print(f"工厂创建音频处理器: {type(processor).__name__}")

        return True

    except Exception as e:
        print(f"工厂测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("Voice Input System 简单集成测试")
    print("=" * 40)

    results = []

    # 基础容器测试
    results.append(("容器测试", simple_container_test()))

    # 异步功能测试
    results.append(("异步功能测试", await async_functionality_test()))

    # 工厂测试
    results.append(("工厂测试", factory_test()))

    # 总结结果
    print("\n" + "=" * 40)
    print("测试结果总结:")
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {test_name}: {status}")

    all_passed = all(success for _, success in results)
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())