# -*- coding: utf-8 -*-
"""
适配器注册表

提供适配器的注册、发现和管理功能，支持适配器的生命周期管理。
"""

import logging
from typing import Dict, List, Optional, Type, Any, Set
from dataclasses import dataclass
from datetime import datetime

from interfaces import (
    IAudioProcessor, IDataExporter, ITTSProvider,
    IConfigProvider, ISystemController
)

logger = logging.getLogger(__name__)


@dataclass
class AdapterInfo:
    """适配器信息数据类"""
    interface_type: Type
    adapter_class: Type
    wrapped_class: Optional[Type] = None
    description: str = ""
    version: str = "1.0.0"
    registered_at: datetime = None
    is_active: bool = True

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = datetime.now()

    def __repr__(self) -> str:
        return f"AdapterInfo({self.interface_type.__name__} -> {self.adapter_class.__name__})"


class AdapterRegistry:
    """
    适配器注册表

    管理所有已注册的适配器信息，提供注册、查询、生命周期管理等功能。
    """

    def __init__(self):
        """初始化适配器注册表"""
        self._adapters: Dict[Type, List[AdapterInfo]] = {}
        self._default_adapters: Dict[Type, str] = {}
        self._active_adapters: Set[str] = set()
        self._adapter_counter = 0

        # 注册默认适配器
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """注册默认的适配器"""
        from .audio_processor_adapter import AudioProcessorAdapter
        from .data_exporter_adapter import DataExporterAdapter
        from .tts_provider_adapter import TTSProviderAdapter
        from .config_provider_adapter import ConfigProviderAdapter

        # 注册默认适配器
        self.register_adapter(
            IAudioProcessor,
            AudioProcessorAdapter,
            wrapped_class=AudioProcessorAdapter.__init__.__annotations__.get('audio_capture'),
            description="AudioCapture到IAudioProcessor的适配器"
        )

        self.register_adapter(
            IDataExporter,
            DataExporterAdapter,
            wrapped_class=DataExporterAdapter.__init__.__annotations__.get('excel_exporter'),
            description="ExcelExporter到IDataExporter的适配器"
        )

        self.register_adapter(
            ITTSProvider,
            TTSProviderAdapter,
            wrapped_class=TTSProviderAdapter.__init__.__annotations__.get('tts_engine'),
            description="TTS到ITTSProvider的适配器"
        )

        self.register_adapter(
            IConfigProvider,
            ConfigProviderAdapter,
            wrapped_class=ConfigProviderAdapter.__init__.__annotations__.get('config_loader'),
            description="ConfigLoader到IConfigProvider的适配器"
        )

        logger.info("Default adapters registered")

    def register_adapter(
        self,
        interface_type: Type,
        adapter_class: Type,
        wrapped_class: Optional[Type] = None,
        description: str = "",
        version: str = "1.0.0",
        set_as_default: bool = False
    ) -> str:
        """
        注册适配器

        Args:
            interface_type: 接口类型
            adapter_class: 适配器类
            wrapped_class: 被包装的类
            description: 描述信息
            version: 版本号
            set_as_default: 是否设为默认适配器

        Returns:
            str: 适配器ID
        """
        adapter_id = f"adapter_{self._adapter_counter}"
        self._adapter_counter += 1

        adapter_info = AdapterInfo(
            interface_type=interface_type,
            adapter_class=adapter_class,
            wrapped_class=wrapped_class,
            description=description,
            version=version
        )

        if interface_type not in self._adapters:
            self._adapters[interface_type] = []

        self._adapters[interface_type].append(adapter_info)
        self._active_adapters.add(adapter_id)

        # 设为默认适配器
        if set_as_default or interface_type not in self._default_adapters:
            self._default_adapters[interface_type] = adapter_id

        logger.info(f"Adapter registered: {adapter_id} for {interface_type.__name__}")
        return adapter_id

    def unregister_adapter(self, adapter_id: str) -> bool:
        """
        注销适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            bool: 注销成功返回True，失败返回False
        """
        try:
            # 从所有接口类型中查找适配器
            for interface_type, adapters in self._adapters.items():
                for i, adapter_info in enumerate(adapters):
                    # 通过时间戳或其他方式匹配适配器
                    if id(adapter_info) == adapter_id or adapter_info.adapter_class.__name__ == adapter_id:
                        del adapters[i]
                        self._active_adapters.discard(adapter_id)

                        # 如果是默认适配器，需要重新选择默认
                        if self._default_adapters.get(interface_type) == adapter_id:
                            if adapters:
                                self._default_adapters[interface_type] = str(id(adapters[0]))
                            else:
                                del self._default_adapters[interface_type]

                        logger.info(f"Adapter unregistered: {adapter_id}")
                        return True

            logger.warning(f"Adapter not found: {adapter_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to unregister adapter {adapter_id}: {e}")
            return False

    def get_adapter_info(self, adapter_id: str) -> Optional[AdapterInfo]:
        """
        获取适配器信息

        Args:
            adapter_id: 适配器ID

        Returns:
            Optional[AdapterInfo]: 适配器信息，如果不存在则返回None
        """
        for adapters in self._adapters.values():
            for adapter_info in adapters:
                if str(id(adapter_info)) == adapter_id or adapter_info.adapter_class.__name__ == adapter_id:
                    return adapter_info
        return None

    def get_adapters_for_interface(self, interface_type: Type) -> List[AdapterInfo]:
        """
        获取指定接口的所有适配器

        Args:
            interface_type: 接口类型

        Returns:
            List[AdapterInfo]: 适配器信息列表
        """
        return self._adapters.get(interface_type, []).copy()

    def get_default_adapter(self, interface_type: Type) -> Optional[AdapterInfo]:
        """
        获取接口的默认适配器

        Args:
            interface_type: 接口类型

        Returns:
            Optional[AdapterInfo]: 默认适配器信息，如果不存在则返回None
        """
        adapter_id = self._default_adapters.get(interface_type)
        if adapter_id:
            return self.get_adapter_info(adapter_id)

        # 如果没有默认适配器，返回第一个注册的适配器
        adapters = self.get_adapters_for_interface(interface_type)
        return adapters[0] if adapters else None

    def set_default_adapter(self, interface_type: Type, adapter_id: str) -> bool:
        """
        设置接口的默认适配器

        Args:
            interface_type: 接口类型
            adapter_id: 适配器ID

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        adapter_info = self.get_adapter_info(adapter_id)
        if adapter_info and adapter_info.interface_type == interface_type:
            self._default_adapters[interface_type] = adapter_id
            logger.info(f"Default adapter set for {interface_type.__name__}: {adapter_id}")
            return True
        else:
            logger.warning(f"Cannot set default adapter: adapter not found or interface mismatch")
            return False

    def get_supported_interfaces(self) -> List[Type]:
        """
        获取所有支持的接口类型

        Returns:
            List[Type]: 接口类型列表
        """
        return list(self._adapters.keys())

    def is_interface_supported(self, interface_type: Type) -> bool:
        """
        检查是否支持指定的接口类型

        Args:
            interface_type: 接口类型

        Returns:
            bool: 支持返回True，否则返回False
        """
        return interface_type in self._adapters

    def activate_adapter(self, adapter_id: str) -> bool:
        """
        激活适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            bool: 激活成功返回True，失败返回False
        """
        adapter_info = self.get_adapter_info(adapter_id)
        if adapter_info:
            adapter_info.is_active = True
            self._active_adapters.add(adapter_id)
            logger.info(f"Adapter activated: {adapter_id}")
            return True
        return False

    def deactivate_adapter(self, adapter_id: str) -> bool:
        """
        停用适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            bool: 停用成功返回True，失败返回False
        """
        adapter_info = self.get_adapter_info(adapter_id)
        if adapter_info:
            adapter_info.is_active = False
            self._active_adapters.discard(adapter_id)
            logger.info(f"Adapter deactivated: {adapter_id}")
            return True
        return False

    def get_active_adapters(self) -> List[AdapterInfo]:
        """
        获取所有激活的适配器

        Returns:
            List[AdapterInfo]: 激活的适配器信息列表
        """
        active_adapters = []
        for adapters in self._adapters.values():
            for adapter_info in adapters:
                if adapter_info.is_active:
                    active_adapters.append(adapter_info)
        return active_adapters

    def get_adapter_statistics(self) -> Dict[str, Any]:
        """
        获取适配器统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        total_adapters = sum(len(adapters) for adapters in self._adapters.values())
        active_adapters = len(self._active_adapters)
        supported_interfaces = len(self._adapters)

        interface_stats = {}
        for interface_type, adapters in self._adapters.items():
            active_count = sum(1 for adapter in adapters if adapter.is_active)
            interface_stats[interface_type.__name__] = {
                "total": len(adapters),
                "active": active_count,
                "default": self.get_default_adapter(interface_type).__class__.__name__ if self.get_default_adapter(interface_type) else None
            }

        return {
            "total_adapters": total_adapters,
            "active_adapters": active_adapters,
            "supported_interfaces": supported_interfaces,
            "interface_stats": interface_stats,
            "registration_time": datetime.now().isoformat()
        }

    def clear_registry(self) -> None:
        """清空所有注册的适配器"""
        self._adapters.clear()
        self._default_adapters.clear()
        self._active_adapters.clear()
        self._adapter_counter = 0
        logger.info("Adapter registry cleared")

    def export_registry(self) -> Dict[str, Any]:
        """
        导出注册表信息

        Returns:
            Dict[str, Any]: 注册表信息字典
        """
        registry_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "adapters": {},
            "default_adapters": {},
            "statistics": self.get_adapter_statistics()
        }

        for interface_type, adapters in self._adapters.items():
            interface_name = interface_type.__name__
            registry_data["adapters"][interface_name] = []

            for adapter_info in adapters:
                adapter_data = {
                    "adapter_class": adapter_info.adapter_class.__name__,
                    "wrapped_class": adapter_info.wrapped_class.__name__ if adapter_info.wrapped_class else None,
                    "description": adapter_info.description,
                    "version": adapter_info.version,
                    "registered_at": adapter_info.registered_at.isoformat(),
                    "is_active": adapter_info.is_active
                }
                registry_data["adapters"][interface_name].append(adapter_data)

        for interface_type, adapter_id in self._default_adapters.items():
            registry_data["default_adapters"][interface_type.__name__] = adapter_id

        return registry_data

    def import_registry(self, registry_data: Dict[str, Any]) -> bool:
        """
        导入注册表信息

        Args:
            registry_data: 注册表数据字典

        Returns:
            bool: 导入成功返回True，失败返回False
        """
        try:
            # 这里可以实现导入逻辑
            # 由于涉及到类的动态加载，这里简化处理
            logger.info("Registry import requested (Note: full import not implemented)")
            return True
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return False

    def __repr__(self) -> str:
        return f"AdapterRegistry(interfaces={len(self._adapters)}, adapters={sum(len(adapters) for adapters in self._adapters.values())})"


# 全局适配器注册表实例
global_adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """
    获取全局适配器注册表实例

    Returns:
        AdapterRegistry: 适配器注册表实例
    """
    return global_adapter_registry


def register_adapter(
    interface_type: Type,
    adapter_class: Type,
    wrapped_class: Optional[Type] = None,
    description: str = "",
    version: str = "1.0.0",
    set_as_default: bool = False
) -> str:
    """
    注册适配器的便捷函数

    Args:
        interface_type: 接口类型
        adapter_class: 适配器类
        wrapped_class: 被包装的类
        description: 描述信息
        version: 版本号
        set_as_default: 是否设为默认适配器

    Returns:
        str: 适配器ID
    """
    return global_adapter_registry.register_adapter(
        interface_type=interface_type,
        adapter_class=adapter_class,
        wrapped_class=wrapped_class,
        description=description,
        version=version,
        set_as_default=set_as_default
    )


def get_default_adapter(interface_type: Type) -> Optional[Type]:
    """
    获取接口默认适配器类的便捷函数

    Args:
        interface_type: 接口类型

    Returns:
        Optional[Type]: 默认适配器类，如果不存在则返回None
    """
    adapter_info = global_adapter_registry.get_default_adapter(interface_type)
    return adapter_info.adapter_class if adapter_info else None


def list_supported_interfaces() -> List[Type]:
    """
    获取所有支持的接口类型的便捷函数

    Returns:
        List[Type]: 接口类型列表
    """
    return global_adapter_registry.get_supported_interfaces()