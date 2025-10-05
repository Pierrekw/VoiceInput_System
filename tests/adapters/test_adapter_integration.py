# -*- coding: utf-8 -*-
"""
适配器集成测试

测试适配器与依赖注入容器的集成，以及适配器之间的协作。
"""

import pytest
import unittest
from unittest.mock import Mock, patch

from interfaces import IAudioProcessor, IDataExporter, ITTSProvider, IConfigProvider
from container import DIContainer
from adapters import (
    AudioProcessorAdapter, DataExporterAdapter,
    TTSProviderAdapter, ConfigProviderAdapter
)
from adapters.adapter_factory import global_adapter_factory


class TestAdapterDIIntegration(unittest.TestCase):
    """适配器与依赖注入容器集成测试"""

    def setUp(self):
        """测试前准备"""
        self.container = DIContainer()

    def test_register_audio_processor_adapter(self):
        """测试注册音频处理器适配器"""
        # 注册适配器
        self.container.register_transient(
            IAudioProcessor,
            lambda: AudioProcessorAdapter(test_mode=True)
        )

        # 验证注册成功
        self.assertTrue(self.container.is_registered(IAudioProcessor))

        # 解析适配器
        processor = self.container.resolve(IAudioProcessor)

        # 验证适配器
        self.assertIsInstance(processor, AudioProcessorAdapter)
        self.assertIsInstance(processor, IAudioProcessor)

    def test_register_data_exporter_adapter(self):
        """测试注册数据导出器适配器"""
        # 注册适配器
        self.container.register_singleton(
            IDataExporter,
            lambda: DataExporterAdapter()
        )

        # 验证注册成功
        self.assertTrue(self.container.is_registered(IDataExporter))

        # 解析适配器
        exporter = self.container.resolve(IDataExporter)

        # 验证适配器
        self.assertIsInstance(exporter, DataExporterAdapter)
        self.assertIsInstance(exporter, IDataExporter)

    def test_register_tts_provider_adapter(self):
        """测试注册TTS服务适配器"""
        # 注册适配器
        self.container.register_transient(
            ITTSProvider,
            lambda: TTSProviderAdapter()
        )

        # 验证注册成功
        self.assertTrue(self.container.is_registered(ITTSProvider))

        # 解析适配器
        tts = self.container.resolve(ITTSProvider)

        # 验证适配器
        self.assertIsInstance(tts, TTSProviderAdapter)
        self.assertIsInstance(tts, ITTSProvider)

    def test_register_config_provider_adapter(self):
        """测试注册配置提供者适配器"""
        # 注册适配器
        self.container.register_singleton(
            IConfigProvider,
            lambda: ConfigProviderAdapter()
        )

        # 验证注册成功
        self.assertTrue(self.container.is_registered(IConfigProvider))

        # 解析适配器
        config = self.container.resolve(IConfigProvider)

        # 验证适配器
        self.assertIsInstance(config, ConfigProviderAdapter)
        self.assertIsInstance(config, IConfigProvider)

    def test_multiple_adapters_dependency_injection(self):
        """测试多个适配器的依赖注入"""
        # 注册所有适配器
        self.container.register_singleton(IConfigProvider, lambda: ConfigProviderAdapter())
        self.container.register_singleton(IDataExporter, lambda: DataExporterAdapter())
        self.container.register_singleton(ITTSProvider, lambda: TTSProviderAdapter())
        self.container.register_transient(
            IAudioProcessor,
            lambda c: AudioProcessorAdapter(
                config_provider=c.resolve(IConfigProvider),
                data_exporter=c.resolve(IDataExporter),
                tts_provider=c.resolve(ITTSProvider)
            )
        )

        # 解析所有适配器
        config = self.container.resolve(IConfigProvider)
        exporter = self.container.resolve(IDataExporter)
        tts = self.container.resolve(ITTSProvider)
        processor = self.container.resolve(IAudioProcessor)

        # 验证适配器
        self.assertIsInstance(config, IConfigProvider)
        self.assertIsInstance(exporter, IDataExporter)
        self.assertIsInstance(tts, ITTSProvider)
        self.assertIsInstance(processor, IAudioProcessor)

        # 验证单例行为
        config2 = self.container.resolve(IConfigProvider)
        self.assertIs(config, config2)

        # 验证瞬态行为
        processor2 = self.container.resolve(IAudioProcessor)
        self.assertIsNot(processor, processor2)

    @patch('adapters.audio_processor_adapter.AudioCapture')
    def test_adapter_factory_integration(self, mock_capture_class):
        """测试适配器工厂与容器集成"""
        # 设置mock
        mock_capture_instance = Mock()
        mock_capture_class.return_value = mock_capture_instance

        # 使用工厂创建适配器并注册到容器
        self.container.register_transient(
            IAudioProcessor,
            lambda: global_adapter_factory.create_adapter(IAudioProcessor)
        )

        # 解析适配器
        processor = self.container.resolve(IAudioProcessor)

        # 验证适配器创建
        self.assertIsInstance(processor, AudioProcessorAdapter)
        mock_capture_class.assert_called_once()

    def test_adapter_scoped_lifetime(self):
        """测试适配器作用域生命周期"""
        # 注册作用域适配器
        self.container.register_scoped(IConfigProvider, lambda: ConfigProviderAdapter())

        # 在作用域内解析适配器
        with self.container.create_scope():
            config1 = self.container.resolve(IConfigProvider)
            config2 = self.container.resolve(IConfigProvider)

            # 验证同一作用域内返回相同实例
            self.assertIs(config1, config2)

        # 在新作用域内解析
        with self.container.create_scope():
            config3 = self.container.resolve(IConfigProvider)

            # 验证不同作用域返回不同实例
            self.assertIsNot(config1, config3)


class TestAdapterFactoryIntegration(unittest.TestCase):
    """适配器工厂集成测试"""

    def test_global_factory_with_container(self):
        """测试全局工厂与容器集成"""
        container = DIContainer()

        # 使用全局工厂注册适配器
        container.register_singleton(
            IConfigProvider,
            lambda: global_adapter_factory.create_adapter(IConfigProvider)
        )

        # 解析适配器
        config = container.resolve(IConfigProvider)

        # 验证适配器类型
        self.assertIsInstance(config, ConfigProviderAdapter)

    def test_factory_default_config_with_container(self):
        """测试工厂默认配置与容器集成"""
        container = DIContainer()

        # 设置默认配置
        global_adapter_factory.set_default_config(
            IConfigProvider,
            {"test_config": "test_value"}
        )

        # 注册适配器
        container.register_singleton(
            IConfigProvider,
            lambda: global_adapter_factory.create_adapter(IConfigProvider)
        )

        # 解析适配器
        config = container.resolve(IConfigProvider)

        # 验证适配器创建成功
        self.assertIsInstance(config, ConfigProviderAdapter)

    def test_factory_parameter_override(self):
        """测试工厂参数覆盖"""
        container = DIContainer()

        # 注册带参数的适配器
        container.register_transient(
            IAudioProcessor,
            lambda: global_adapter_factory.create_adapter(
                IAudioProcessor,
                test_param="test_value"
            )
        )

        # 解析适配器
        processor = container.resolve(IAudioProcessor)

        # 验证适配器创建成功
        self.assertIsInstance(processor, AudioProcessorAdapter)


class TestAdapterErrorHandlingIntegration(unittest.TestCase):
    """适配器错误处理集成测试"""

    def setUp(self):
        """测试前准备"""
        self.container = DIContainer()

    def test_adapter_creation_failure(self):
        """测试适配器创建失败处理"""
        # 注册会失败的工厂
        def failing_factory():
            raise Exception("Adapter creation failed")

        self.container.register_transient(IAudioProcessor, failing_factory)

        # 尝试解析应该抛出异常
        with self.assertRaises(Exception):
            self.container.resolve(IAudioProcessor)

    def test_adapter_dependency_missing(self):
        """测试适配器依赖缺失处理"""
        # 注册依赖其他服务的适配器
        def dependent_factory(container):
            # 尝试解析不存在的服务
            container.resolve(type("NonExistentService"))
            return Mock()

        self.container.register_transient(IAudioProcessor, dependent_factory)

        # 尝试解析应该抛出异常
        with self.assertRaises(Exception):
            self.container.resolve(IAudioProcessor)

    def test_adapter_initialization_failure(self):
        """测试适配器初始化失败处理"""
        # 注册初始化失败的适配器
        class FailingAdapter:
            def __init__(self):
                raise Exception("Initialization failed")

        self.container.register_transient(IAudioProcessor, lambda: FailingAdapter())

        # 尝试解析应该抛出异常
        with self.assertRaises(Exception):
            self.container.resolve(IAudioProcessor)


class TestAdapterLifecycleIntegration(unittest.TestCase):
    """适配器生命周期集成测试"""

    def setUp(self):
        """测试前准备"""
        self.container = DIContainer()

    def test_adapter_cleanup_on_dispose(self):
        """测试容器释放时适配器清理"""
        # 创建带清理方法的适配器
        class CleanupAdapter:
            def __init__(self):
                self.cleaned_up = False

            def cleanup(self):
                self.cleaned_up = True

        # 注册适配器
        self.container.register_singleton(IAudioProcessor, lambda: CleanupAdapter())

        # 解析适配器
        adapter = self.container.resolve(IAudioProcessor)

        # 释放容器
        self.container.dispose()

        # 验证适配器被清理（如果实现了清理方法）
        # 注意：这里需要适配器实际实现cleanup方法

    def test_adapter_singleton_lifecycle(self):
        """测试单例适配器生命周期"""
        # 注册单例适配器
        self.container.register_singleton(
            IConfigProvider,
            lambda: ConfigProviderAdapter()
        )

        # 多次解析应该返回相同实例
        config1 = self.container.resolve(IConfigProvider)
        config2 = self.container.resolve(IConfigProvider)

        self.assertIs(config1, config2)

        # 验证实例状态一致
        self.assertEqual(config1.is_initialized(), config2.is_initialized())

    def test_adapter_scoped_lifecycle(self):
        """测试作用域适配器生命周期"""
        # 注册作用域适配器
        self.container.register_scoped(
            IDataExporter,
            lambda: DataExporterAdapter()
        )

        # 在同一作用域内应该返回相同实例
        with self.container.create_scope():
            exporter1 = self.container.resolve(IDataExporter)
            exporter2 = self.container.resolve(IDataExporter)
            self.assertIs(exporter1, exporter2)

        # 在不同作用域内应该返回不同实例
        with self.container.create_scope():
            exporter3 = self.container.resolve(IDataExporter)
            self.assertIsNot(exporter1, exporter3)


if __name__ == '__main__':
    unittest.main()