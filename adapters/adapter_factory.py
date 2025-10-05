# -*- coding: utf-8 -*-
"""
适配器工厂

提供适配器实例的创建和管理功能，支持工厂模式和注册机制。
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Type, TypeVar, Optional, Callable, List, Generic

from interfaces import (
    IAudioProcessor, IDataExporter, ITTSProvider,
    IConfigProvider, ISystemController
)
from .audio_processor_adapter import AudioProcessorAdapter
from .data_exporter_adapter import DataExporterAdapter
from .tts_provider_adapter import TTSProviderAdapter
from .config_provider_adapter import ConfigProviderAdapter

# Re-export the adapter classes for type safety
__all__ = ['AdapterFactory', 'global_adapter_factory',
           'create_audio_processor_adapter', 'create_data_exporter_adapter',
           'create_tts_provider_adapter', 'create_config_provider_adapter',
           'AudioProcessorAdapter', 'DataExporterAdapter',
           'TTSProviderAdapter', 'ConfigProviderAdapter']

logger = logging.getLogger(__name__)

# 定义类型变量，T表示任何接口类型
T = TypeVar('T')


class AdapterFactory:
    """
    适配器工厂类

    负责创建各种适配器实例，支持参数化配置和自定义工厂函数。
    """

    def __init__(self):
        """初始化适配器工厂"""
        self._factories: Dict[Type, Callable] = {}
        self._default_configs: Dict[Type, Dict[str, Any]] = {}
        self._interface_to_adapter_map: Dict[Type, Type] = {
            IAudioProcessor: AudioProcessorAdapter,
            IDataExporter: DataExporterAdapter,
            ITTSProvider: TTSProviderAdapter,
            IConfigProvider: ConfigProviderAdapter,
        }
        self._register_default_factories()

    def _register_default_factories(self) -> None:
        """注册默认的适配器工厂"""
        # 注册音频处理器适配器工厂
        self.register_factory(
            IAudioProcessor,
            lambda **kwargs: AudioProcessorAdapter(**kwargs)
        )

        # 注册数据导出器适配器工厂
        self.register_factory(
            IDataExporter,
            lambda **kwargs: DataExporterAdapter(**kwargs)
        )

        # 注册TTS服务适配器工厂
        self.register_factory(
            ITTSProvider,
            lambda **kwargs: TTSProviderAdapter(**kwargs)
        )

        # 注册配置提供者适配器工厂
        self.register_factory(
            IConfigProvider,
            lambda **kwargs: ConfigProviderAdapter(**kwargs)
        )

        logger.info("Default adapter factories registered")

    def register_factory(self, interface_type: type, factory_func: Callable[..., Any]) -> None:
        """
        注册适配器工厂函数

        Args:
            interface_type: 接口类型
            factory_func: 工厂函数，接受关键字参数并返回实现了该接口的适配器实例
        """
        self._factories[interface_type] = factory_func
        logger.debug(f"Factory registered for {interface_type.__name__}")

    def create_adapter_by_interface(
        self,
        interface_type: type,
        wrapped_instance: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """
        通过接口类型创建适配器实例

        Args:
            interface_type: 接口类型
            wrapped_instance: 要包装的实例
            **kwargs: 传递给适配器的参数

        Returns:
            Any: 适配器实例

        Raises:
            ValueError: 不支持的接口类型
        """
        if interface_type not in self._interface_to_adapter_map:
            raise ValueError(f"没有找到支持{interface_type.__name__}接口的适配器")

        adapter_class = self._interface_to_adapter_map[interface_type]
        return self.create_adapter(adapter_class, wrapped_instance, **kwargs)

    def create_adapter(
        self,
        interface_type: Type[T],
        wrapped_instance: Optional[Any] = None,
        **kwargs
    ) -> T:
        """
        创建适配器实例

        Args:
            interface_type: 接口类型
            wrapped_instance: 要包装的现有实例，如果为None则创建新实例
            **kwargs: 传递给适配器构造函数的参数

        Returns:
            T: 适配器实例

        Raises:
            ValueError: 不支持的接口类型或工厂未注册
        """
        if interface_type not in self._factories:
            raise ValueError(f"No factory registered for interface type: {interface_type.__name__}")

        try:
            # 获取默认配置
            default_config = self._default_configs.get(interface_type, {}).copy()
            default_config.update(kwargs)

            # 如果提供了包装实例，添加到参数中
            if wrapped_instance is not None:
                # 根据适配器类型确定参数名
                if interface_type == AudioProcessorAdapter:
                    default_config['audio_capture'] = wrapped_instance
                elif interface_type == DataExporterAdapter:
                    default_config['excel_exporter'] = wrapped_instance
                elif interface_type == TTSProviderAdapter:
                    default_config['tts_engine'] = wrapped_instance
                elif interface_type == ConfigProviderAdapter:
                    default_config['config_loader'] = wrapped_instance

            # 创建适配器实例
            factory_func = self._factories[interface_type]
            adapter = factory_func(**default_config)

            logger.info(f"Created adapter for {interface_type.__name__}")
            return adapter

        except Exception as e:
            logger.error(f"Failed to create adapter for {interface_type.__name__}: {e}")
            raise

    def set_default_config(self, interface_type: Type, config: Dict[str, Any]) -> None:
        """
        设置接口类型的默认配置

        Args:
            interface_type: 接口类型
            config: 默认配置字典
        """
        self._default_configs[interface_type] = config
        logger.debug(f"Default config set for {interface_type.__name__}")

    def get_default_config(self, interface_type: Type) -> Dict[str, Any]:
        """
        获取接口类型的默认配置

        Args:
            interface_type: 接口类型

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return self._default_configs.get(interface_type, {}).copy()

    def get_supported_interfaces(self) -> List[Type]:
        """
        获取支持的接口类型列表

        Returns:
            List[Type]: 支持的接口类型列表
        """
        return list(self._factories.keys())

    def is_supported(self, interface_type: Type) -> bool:
        """
        检查是否支持指定的接口类型

        Args:
            interface_type: 接口类型

        Returns:
            bool: 支持返回True，否则返回False
        """
        return interface_type in self._factories

    def clear_factories(self) -> None:
        """清除所有注册的工厂"""
        self._factories.clear()
        self._default_configs.clear()
        logger.info("All adapter factories cleared")

    def __repr__(self) -> str:
        return f"AdapterFactory(registered={len(self._factories)})"


# 全局适配器工厂实例
global_adapter_factory: AdapterFactory = AdapterFactory()


def create_audio_processor_adapter(
    wrapped_instance: Optional[Any] = None,
    **kwargs
) -> IAudioProcessor:
    """
    创建音频处理器适配器的便捷函数

    Args:
        wrapped_instance: 要包装的AudioCapture实例
        **kwargs: 传递给适配器的参数

    Returns:
        IAudioProcessor: 音频处理器适配器实例
    """
    return global_adapter_factory.create_adapter_by_interface(
        IAudioProcessor,
        wrapped_instance=wrapped_instance,
        **kwargs
    )  # type: ignore


def create_data_exporter_adapter(
    wrapped_instance: Optional[Any] = None,
    **kwargs
) -> IDataExporter:
    """
    创建数据导出器适配器的便捷函数

    Args:
        wrapped_instance: 要包装的ExcelExporter实例
        **kwargs: 传递给适配器的参数

    Returns:
        IDataExporter: 数据导出器适配器实例
    """
    return global_adapter_factory.create_adapter_by_interface(
        IDataExporter,
        wrapped_instance=wrapped_instance,
        **kwargs
    )  # type: ignore


def create_tts_provider_adapter(
    wrapped_instance: Optional[Any] = None,
    **kwargs
) -> ITTSProvider:
    """
    创建TTS服务适配器的便捷函数

    Args:
        wrapped_instance: 要包装的TTS实例
        **kwargs: 传递给适配器的参数

    Returns:
        ITTSProvider: TTS服务适配器实例
    """
    return global_adapter_factory.create_adapter_by_interface(
        ITTSProvider,
        wrapped_instance=wrapped_instance,
        **kwargs
    )  # type: ignore


def create_config_provider_adapter(
    wrapped_instance: Optional[Any] = None,
    **kwargs
) -> IConfigProvider:
    """
    创建配置提供者适配器的便捷函数

    Args:
        wrapped_instance: 要包装的ConfigLoader实例
        **kwargs: 传递给适配器的参数

    Returns:
        IConfigProvider: 配置提供者适配器实例
    """
    return global_adapter_factory.create_adapter_by_interface(
        IConfigProvider,
        wrapped_instance=wrapped_instance,
        **kwargs
    )  # type: ignore


def set_adapter_default_config(interface_type: Type, config: Dict[str, Any]) -> None:
    """
    设置适配器默认配置的便捷函数

    Args:
        interface_type: 接口类型
        config: 默认配置字典
    """
    global_adapter_factory.set_default_config(interface_type, config)


def get_adapter_default_config(interface_type: Type) -> Dict[str, Any]:
    """
    获取适配器默认配置的便捷函数

    Args:
        interface_type: 接口类型

    Returns:
        Dict[str, Any]: 默认配置字典
    """
    return global_adapter_factory.get_default_config(interface_type)