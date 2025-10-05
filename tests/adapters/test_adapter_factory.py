# -*- coding: utf-8 -*-
"""
适配器工厂测试

测试适配器工厂的创建和管理功能。
"""

import pytest
import unittest
from unittest.mock import Mock, patch

from interfaces import IAudioProcessor, IDataExporter, ITTSProvider, IConfigProvider
from adapters.adapter_factory import AdapterFactory, global_adapter_factory
from adapters.audio_processor_adapter import AudioProcessorAdapter
from adapters.data_exporter_adapter import DataExporterAdapter
from adapters.tts_provider_adapter import TTSProviderAdapter
from adapters.config_provider_adapter import ConfigProviderAdapter


class TestAdapterFactory(unittest.TestCase):
    """适配器工厂测试类"""

    def setUp(self):
        """测试前准备"""
        self.factory = AdapterFactory()

    def test_register_factory(self):
        """测试工厂注册"""
        # 创建一个简单的测试工厂函数
        def test_factory(**kwargs):
            return Mock()

        # 注册工厂
        self.factory.register_factory(IAudioProcessor, test_factory)

        # 验证注册成功
        self.assertTrue(self.factory.is_supported(IAudioProcessor))
        self.assertIn(IAudioProcessor, self.factory.get_supported_interfaces())

    def test_create_adapter_audio_processor(self):
        """测试创建音频处理器适配器"""
        adapter = self.factory.create_adapter(IAudioProcessor)

        # 验证适配器类型
        self.assertIsInstance(adapter, AudioProcessorAdapter)
        self.assertIsInstance(adapter, IAudioProcessor)

    def test_create_adapter_data_exporter(self):
        """测试创建数据导出器适配器"""
        adapter = self.factory.create_adapter(IDataExporter)

        # 验证适配器类型
        self.assertIsInstance(adapter, DataExporterAdapter)
        self.assertIsInstance(adapter, IDataExporter)

    def test_create_adapter_tts_provider(self):
        """测试创建TTS服务适配器"""
        adapter = self.factory.create_adapter(ITTSProvider)

        # 验证适配器类型
        self.assertIsInstance(adapter, TTSProviderAdapter)
        self.assertIsInstance(adapter, ITTSProvider)

    def test_create_adapter_config_provider(self):
        """测试创建配置提供者适配器"""
        adapter = self.factory.create_adapter(IConfigProvider)

        # 验证适配器类型
        self.assertIsInstance(adapter, ConfigProviderAdapter)
        self.assertIsInstance(adapter, IConfigProvider)

    def test_create_adapter_with_wrapped_instance(self):
        """测试使用包装实例创建适配器"""
        # 创建模拟的包装实例
        mock_capture = Mock()
        mock_capture.test_attr = "test_value"

        # 创建适配器
        adapter = self.factory.create_adapter(
            IAudioProcessor,
            wrapped_instance=mock_capture
        )

        # 验证包装实例被正确传递
        self.assertEqual(adapter.wrapped_instance, mock_capture)

    def test_create_adapter_with_kwargs(self):
        """测试使用关键字参数创建适配器"""
        kwargs = {
            "test_param1": "value1",
            "test_param2": "value2"
        }

        # 创建适配器
        adapter = self.factory.create_adapter(IAudioProcessor, **kwargs)

        # 验证适配器创建成功（具体参数验证需要根据适配器实现）
        self.assertIsInstance(adapter, AudioProcessorAdapter)

    def test_create_adapter_unsupported_interface(self):
        """测试创建不支持的接口类型适配器"""
        with self.assertRaises(ValueError):
            self.factory.create_adapter(str)  # str类型未注册工厂

    def test_default_config_management(self):
        """测试默认配置管理"""
        config = {"test_key": "test_value"}

        # 设置默认配置
        self.factory.set_default_config(IAudioProcessor, config)

        # 获取默认配置
        retrieved_config = self.factory.get_default_config(IAudioProcessor)

        # 验证配置
        self.assertEqual(retrieved_config, config)

    def test_create_adapter_with_default_config(self):
        """测试使用默认配置创建适配器"""
        # 设置默认配置
        default_config = {"test_param": "default_value"}
        self.factory.set_default_config(IAudioProcessor, default_config)

        # 创建适配器（默认配置会被应用）
        adapter = self.factory.create_adapter(IAudioProcessor)

        # 验证适配器创建成功
        self.assertIsInstance(adapter, AudioProcessorAdapter)

    def test_create_adapter_override_default_config(self):
        """测试覆盖默认配置创建适配器"""
        # 设置默认配置
        default_config = {"test_param": "default_value"}
        self.factory.set_default_config(IAudioProcessor, default_config)

        # 使用覆盖参数创建适配器
        override_config = {"test_param": "override_value"}
        adapter = self.factory.create_adapter(IAudioProcessor, **override_config)

        # 验证适配器创建成功
        self.assertIsInstance(adapter, AudioProcessorAdapter)

    def test_clear_factories(self):
        """测试清除工厂"""
        # 验证初始状态有工厂
        self.assertTrue(len(self.factory.get_supported_interfaces()) > 0)

        # 清除工厂
        self.factory.clear_factories()

        # 验证所有工厂被清除
        self.assertEqual(len(self.factory.get_supported_interfaces()), 0)
        self.assertFalse(self.factory.is_supported(IAudioProcessor))

    def test_factory_repr(self):
        """测试工厂的字符串表示"""
        repr_str = repr(self.factory)
        self.assertIn("AdapterFactory", repr_str)
        self.assertIn("registered=", repr_str)


class TestGlobalAdapterFactory(unittest.TestCase):
    """全局适配器工厂测试类"""

    def test_global_factory_exists(self):
        """测试全局工厂存在"""
        self.assertIsNotNone(global_adapter_factory)
        self.assertIsInstance(global_adapter_factory, AdapterFactory)

    def test_global_factory_has_defaults(self):
        """测试全局工厂有默认工厂注册"""
        supported_interfaces = global_adapter_factory.get_supported_interfaces()

        # 验证主要接口已注册
        self.assertIn(IAudioProcessor, supported_interfaces)
        self.assertIn(IDataExporter, supported_interfaces)
        self.assertIn(ITTSProvider, supported_interfaces)
        self.assertIn(IConfigProvider, supported_interfaces)

    @patch('adapters.audio_processor_adapter.AudioCapture')
    def test_global_factory_create_audio_processor(self, mock_capture_class):
        """测试全局工厂创建音频处理器适配器"""
        # 设置mock返回值
        mock_instance = Mock()
        mock_capture_class.return_value = mock_instance

        # 创建适配器
        adapter = global_adapter_factory.create_adapter(IAudioProcessor)

        # 验证适配器创建成功
        self.assertIsInstance(adapter, AudioProcessorAdapter)


class TestAdapterFactoryErrorHandling(unittest.TestCase):
    """适配器工厂错误处理测试"""

    def setUp(self):
        """测试前准备"""
        self.factory = AdapterFactory()

    def test_create_adapter_with_invalid_interface(self):
        """测试创建无效接口类型适配器"""
        with self.assertRaises(ValueError):
            self.factory.create_adapter(type(None))

    def test_set_default_config_invalid_type(self):
        """测试为无效类型设置默认配置"""
        # 这应该不会抛出异常，但配置不会生效
        self.factory.set_default_config(str, {"test": "value"})

    def test_create_adapter_factory_exception(self):
        """测试工厂函数异常处理"""
        def failing_factory(**kwargs):
            raise Exception("Factory failed")

        # 注册会失败的工厂
        self.factory.register_factory(IAudioProcessor, failing_factory)

        # 创建适配器时应该抛出异常
        with self.assertRaises(Exception):
            self.factory.create_adapter(IAudioProcessor)


if __name__ == '__main__':
    unittest.main()