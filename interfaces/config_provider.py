# -*- coding: utf-8 -*-
"""
配置提供者接口定义

IConfigProvider定义了配置管理的抽象接口，支持配置加载、
热重载、环境变量覆盖等功能。提供同步和异步两种调用模式。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass
import asyncio


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    YAML = "yaml"           # YAML格式
    JSON = "json"           # JSON格式
    TOML = "toml"           # TOML格式
    INI = "ini"             # INI格式
    XML = "xml"             # XML格式


class ConfigScope(Enum):
    """配置作用域枚举"""
    SYSTEM = "system"       # 系统级配置
    USER = "user"           # 用户级配置
    APP = "app"             # 应用级配置
    RUNTIME = "runtime"     # 运行时配置


@dataclass
class ConfigMetadata:
    """配置元数据"""
    key: str
    value: Any
    scope: ConfigScope
    data_type: type
    description: str = ""
    default_value: Any = None
    is_sensitive: bool = False
    is_readonly: bool = False
    validation_rule: Optional[str] = None

    def __post_init__(self):
        # 自动推断数据类型
        if self.data_type is type(None) and self.value is not None:
            self.data_type = type(self.value)


@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    key: str
    old_value: Any
    new_value: Any
    scope: ConfigScope
    timestamp: float
    source: str = "unknown"

    def __repr__(self) -> str:
        return f"ConfigChangeEvent(key='{self.key}', old={self.old_value}, new={self.new_value})"


class IConfigProvider(ABC):
    """
    配置提供者接口

    定义了配置管理的核心功能，包括配置加载、热重载、
    环境变量覆盖、变更通知等。支持同步和异步两种调用模式。
    """

    @abstractmethod
    def initialize(
        self,
        config_file: Optional[str] = None,
        format: Optional[ConfigFormat] = None,
        auto_reload: bool = False
    ) -> bool:
        """
        初始化配置提供者

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            format: 配置文件格式，如果为None则自动检测
            auto_reload: 是否启用自动重载

        Returns:
            bool: 初始化成功返回True，失败返回False

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        pass

    @abstractmethod
    async def initialize_async(
        self,
        config_file: Optional[str] = None,
        format: Optional[ConfigFormat] = None,
        auto_reload: bool = False
    ) -> bool:
        """
        异步初始化配置提供者

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            format: 配置文件格式，如果为None则自动检测
            auto_reload: 是否启用自动重载

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查配置提供者是否已初始化

        Returns:
            bool: 已初始化返回True，否则返回False
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键 (如 "audio.sample_rate")
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        pass

    @abstractmethod
    async def get_async(self, key: str, default: Any = None) -> Any:
        """
        异步获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            scope: 配置作用域

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            PermissionError: 尝试设置只读配置
            ValueError: 配置值验证失败
        """
        pass

    @abstractmethod
    async def set_async(self, key: str, value: Any, scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """
        异步设置配置值

        Args:
            key: 配置键
            value: 配置值
            scope: 配置作用域

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查配置键是否存在

        Args:
            key: 配置键

        Returns:
            bool: 存在返回True，否则返回False
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除配置项

        Args:
            key: 配置键

        Returns:
            bool: 删除成功返回True，失败返回False

        Raises:
            PermissionError: 尝试删除只读配置
        """
        pass

    @abstractmethod
    async def delete_async(self, key: str) -> bool:
        """
        异步删除配置项

        Args:
            key: 配置键

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_all(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """
        获取所有配置

        Args:
            scope: 配置作用域，如果为None则获取所有作用域的配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        pass

    @abstractmethod
    async def get_all_async(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """
        异步获取所有配置

        Args:
            scope: 配置作用域，如果为None则获取所有作用域的配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        pass

    @abstractmethod
    def get_keys(self, pattern: str = "*", scope: Optional[ConfigScope] = None) -> List[str]:
        """
        获取配置键列表

        Args:
            pattern: 键模式，支持通配符
            scope: 配置作用域

        Returns:
            List[str]: 配置键列表
        """
        pass

    @abstractmethod
    def reload(self) -> bool:
        """
        重新加载配置文件

        Returns:
            bool: 重新加载成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def reload_async(self) -> bool:
        """
        异步重新加载配置文件

        Returns:
            bool: 重新加载成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def save(self, file_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            file_path: 文件路径，如果为None则使用原配置文件

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def save_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步保存配置到文件

        Args:
            file_path: 文件路径，如果为None则使用原配置文件

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def watch(self, callback: Callable[[ConfigChangeEvent], None]) -> str:
        """
        监听配置变更

        Args:
            callback: 变更回调函数

        Returns:
            str: 监听器ID
        """
        pass

    @abstractmethod
    async def watch_async(self, callback: Callable[[ConfigChangeEvent], None]) -> str:
        """
        异步监听配置变更

        Args:
            callback: 变更回调函数

        Returns:
            str: 监听器ID
        """
        pass

    @abstractmethod
    def unwatch(self, watcher_id: str) -> bool:
        """
        取消监听配置变更

        Args:
            watcher_id: 监听器ID

        Returns:
            bool: 取消成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_metadata(self, key: str) -> Optional[ConfigMetadata]:
        """
        获取配置元数据

        Args:
            key: 配置键

        Returns:
            Optional[ConfigMetadata]: 配置元数据，如果不存在则返回None
        """
        pass

    @abstractmethod
    def validate(self, key: str, value: Any) -> bool:
        """
        验证配置值

        Args:
            key: 配置键
            value: 配置值

        Returns:
            bool: 验证通过返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        获取配置模式

        Returns:
            Dict[str, Any]: 配置模式字典
        """
        pass

    # 环境变量相关方法
    @abstractmethod
    def apply_env_overrides(self, prefix: str = "VOICE_INPUT_") -> int:
        """
        应用环境变量覆盖

        Args:
            prefix: 环境变量前缀

        Returns:
            int: 应用的环境变量数量
        """
        pass

    @abstractmethod
    def set_env_prefix(self, prefix: str) -> None:
        """
        设置环境变量前缀

        Args:
            prefix: 环境变量前缀
        """
        pass

    @abstractmethod
    def get_env_mappings(self) -> Dict[str, str]:
        """
        获取环境变量映射关系

        Returns:
            Dict[str, str]: 环境变量到配置键的映射
        """
        pass

    # 配置合并和导入导出
    @abstractmethod
    def merge(self, config_dict: Dict[str, Any], scope: ConfigScope = ConfigScope.USER) -> None:
        """
        合并配置字典

        Args:
            config_dict: 配置字典
            scope: 配置作用域
        """
        pass

    @abstractmethod
    async def merge_async(self, config_dict: Dict[str, Any], scope: ConfigScope = ConfigScope.USER) -> None:
        """
        异步合并配置字典

        Args:
            config_dict: 配置字典
            scope: 配置作用域
        """
        pass

    @abstractmethod
    def import_from_file(self, file_path: str, format: Optional[ConfigFormat] = None) -> bool:
        """
        从文件导入配置

        Args:
            file_path: 文件路径
            format: 文件格式，如果为None则自动检测

        Returns:
            bool: 导入成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def import_from_file_async(self, file_path: str, format: Optional[ConfigFormat] = None) -> bool:
        """
        异步从文件导入配置

        Args:
            file_path: 文件路径
            format: 文件格式，如果为None则自动检测

        Returns:
            bool: 导入成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def export_to_file(self, file_path: str, format: ConfigFormat, scope: Optional[ConfigScope] = None) -> bool:
        """
        导出配置到文件

        Args:
            file_path: 文件路径
            format: 文件格式
            scope: 配置作用域，如果为None则导出所有配置

        Returns:
            bool: 导出成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def export_to_file_async(
        self,
        file_path: str,
        format: ConfigFormat,
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """
        异步导出配置到文件

        Args:
            file_path: 文件路径
            format: 文件格式
            scope: 配置作用域，如果为None则导出所有配置

        Returns:
            bool: 导出成功返回True，失败返回False
        """
        pass

    # 缓存和性能优化
    @abstractmethod
    def enable_cache(self, ttl: float = 300.0) -> None:
        """
        启用配置缓存

        Args:
            ttl: 缓存生存时间（秒）
        """
        pass

    @abstractmethod
    def disable_cache(self) -> None:
        """禁用配置缓存"""
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """清空配置缓存"""
        pass

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计字典
        """
        pass

    # 统计和诊断
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取配置使用统计

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        pass

    @abstractmethod
    def get_diagnostics_info(self) -> Dict[str, Any]:
        """
        获取诊断信息

        Returns:
            Dict[str, Any]: 诊断信息字典
        """
        pass

    # 资源管理
    @abstractmethod
    def cleanup(self) -> None:
        """清理配置提供者资源"""
        pass

    @abstractmethod
    async def cleanup_async(self) -> None:
        """异步清理配置提供者资源"""
        pass