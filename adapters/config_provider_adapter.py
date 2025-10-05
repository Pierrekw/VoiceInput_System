# -*- coding: utf-8 -*-
"""
配置提供者适配器

将现有的ConfigLoader类适配为IConfigProvider接口，确保向后兼容性。
采用适配器模式包装现有实现，不修改原有代码。
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Callable, Union, Protocol
from datetime import datetime

from interfaces.config_provider import (
    IConfigProvider, ConfigFormat, ConfigScope, ConfigMetadata, ConfigChangeEvent
)


class ConfigLoaderProtocol(Protocol):
    """ConfigLoader协议，定义期望的接口"""
    def get(self, key: str, default: Any = None) -> Any:
        ...

    def __getattr__(self, name: str) -> Any:
        ...

# 导入现有的ConfigLoader类
from typing import cast

try:
    from config_loader import ConfigLoader as OriginalConfigLoader, config as original_config
    _ConfigLoaderType = OriginalConfigLoader  # type: ignore
    _config = original_config
except ImportError:
    # 如果导入失败，创建一个占位符
    class _FallbackConfigLoader:
        def __init__(self):
            self._config = {}
        def get(self, key, default=None):
            return default
    _ConfigLoaderType = _FallbackConfigLoader  # type: ignore
    _config = _ConfigLoaderType()

logger = logging.getLogger(__name__)


class ConfigProviderAdapter(IConfigProvider):
    """
    配置提供者适配器

    将现有的ConfigLoader类适配为IConfigProvider接口。
    保持原有功能的同时提供新的接口支持。
    """

    def __init__(self, config_loader: Optional[Any] = None):
        """
        初始化配置提供者适配器

        Args:
            config_loader: 现有的ConfigLoader实例，如果为None则使用全局实例
        """
        self._config_loader = config_loader or _config
        self._initialized = False
        self._auto_reload = False
        self._watchers: Dict[str, Callable[[ConfigChangeEvent], None]] = {}
        self._watcher_counter = 0
        self._cache_enabled = False
        self._cache_ttl = 300.0
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}

        logger.info("ConfigProviderAdapter initialized with ConfigLoader")

    # 初始化方法
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
        """
        try:
            self._auto_reload = auto_reload
            self._initialized = True

            # ConfigLoader在导入时已经自动加载了配置
            # 这里主要是为了接口一致性

            if auto_reload:
                logger.info("Auto reload enabled (Note: actual file watching not implemented in adapter)")

            logger.info("ConfigProviderAdapter initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ConfigProviderAdapter: {e}")
            return False

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.initialize, config_file, format, auto_reload)

    def is_initialized(self) -> bool:
        """检查配置提供者是否已初始化"""
        return self._initialized

    # 配置访问方法
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键 (如 "audio.sample_rate")
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        try:
            # 检查缓存
            if self._cache_enabled and key in self._cache:
                if self._is_cache_valid(key):
                    return self._cache[key]
                else:
                    del self._cache[key]
                    if key in self._cache_timestamps:
                        del self._cache_timestamps[key]

            # 使用ConfigLoader的get方法
            value = self._config_loader.get(key, default)

            # 缓存结果
            if self._cache_enabled:
                self._cache[key] = value
                self._cache_timestamps[key] = datetime.now().timestamp()

            return value
        except Exception as e:
            logger.error(f"Failed to get config value '{key}': {e}")
            return default

    async def get_async(self, key: str, default: Any = None) -> Any:
        """
        异步获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get, key, default)

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
        try:
            # ConfigLoader不支持动态设置配置
            # 这里只能在运行时设置，并且不会持久化到文件
            if scope == ConfigScope.RUNTIME:
                # 获取旧值
                old_value = self.get(key)

                # 将值存储在内部字典中
                if not hasattr(self._config_loader, '_runtime_config'):
                    setattr(self._config_loader, '_runtime_config', {})
                setattr(self._config_loader, '_runtime_config',
                       getattr(self._config_loader, '_runtime_config', {}))
                getattr(self._config_loader, '_runtime_config')[key] = value

                # 清除缓存
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]

                # 触发变更事件
                self._notify_watchers(key, old_value, value, scope)

                logger.info(f"Runtime config set: {key} = {value}")
                return True
            else:
                logger.warning(f"Cannot set config in scope {scope.value}, only RUNTIME is supported")
                return False
        except Exception as e:
            logger.error(f"Failed to set config '{key}': {e}")
            return False

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.set, key, value, scope)

    def exists(self, key: str) -> bool:
        """
        检查配置键是否存在

        Args:
            key: 配置键

        Returns:
            bool: 存在返回True，否则返回False
        """
        try:
            return self.get(key) is not None
        except Exception as e:
            logger.error(f"Failed to check config existence '{key}': {e}")
            return False

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
        try:
            if hasattr(self._config_loader, '_runtime_config') and key in self._config_loader._runtime_config:
                old_value = self._config_loader._runtime_config[key]
                del self._config_loader._runtime_config[key]

                # 清除缓存
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]

                # 触发变更事件
                self._notify_watchers(key, old_value, None, ConfigScope.RUNTIME)

                logger.info(f"Runtime config deleted: {key}")
                return True
            else:
                logger.warning(f"Cannot delete config key '{key}', not found in runtime config")
                return False
        except Exception as e:
            logger.error(f"Failed to delete config '{key}': {e}")
            return False

    async def delete_async(self, key: str) -> bool:
        """
        异步删除配置项

        Args:
            key: 配置键

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete, key)

    def get_all(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """
        获取所有配置

        Args:
            scope: 配置作用域，如果为None则获取所有作用域的配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            if scope == ConfigScope.RUNTIME:
                return getattr(self._config_loader, '_runtime_config', {}).copy()
            else:
                # ConfigLoader没有获取所有配置的公开方法
                # 这里返回空字典，实际实现中可能需要反射或其他方法
                return {}
        except Exception as e:
            logger.error(f"Failed to get all configs: {e}")
            return {}

    async def get_all_async(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """
        异步获取所有配置

        Args:
            scope: 配置作用域，如果为None则获取所有作用域的配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_all, scope)

    def get_keys(self, pattern: str = "*", scope: Optional[ConfigScope] = None) -> List[str]:
        """
        获取配置键列表

        Args:
            pattern: 键模式，支持通配符
            scope: 配置作用域

        Returns:
            List[str]: 配置键列表
        """
        try:
            if scope == ConfigScope.RUNTIME:
                runtime_config = getattr(self._config_loader, '_runtime_config', {})
                if pattern == "*":
                    return list(runtime_config.keys())
                else:
                    import fnmatch
                    return [key for key in runtime_config.keys() if fnmatch.fnmatch(key, pattern)]
            else:
                # ConfigLoader不支持获取所有键，这里返回空列表
                return []
        except Exception as e:
            logger.error(f"Failed to get config keys: {e}")
            return []

    # 重载和保存方法
    def reload(self) -> bool:
        """
        重新加载配置文件

        Returns:
            bool: 重新加载成功返回True，失败返回False
        """
        try:
            # ConfigLoader不支持动态重载
            # 这里可以触发重新初始化
            logger.info("Config reload requested (Note: not implemented in ConfigLoader)")
            return False
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            return False

    async def reload_async(self) -> bool:
        """
        异步重新加载配置文件

        Returns:
            bool: 重新加载成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.reload)

    def save(self, file_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            file_path: 文件路径，如果为None则使用原配置文件

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # ConfigLoader不支持保存配置
            logger.warning("Config save requested (Note: not implemented in ConfigLoader)")
            return False
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    async def save_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步保存配置到文件

        Args:
            file_path: 文件路径，如果为None则使用原配置文件

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save, file_path)

    # 事件监听方法
    def watch(self, callback: Callable[[ConfigChangeEvent], None]) -> str:
        """
        监听配置变更

        Args:
            callback: 变更回调函数

        Returns:
            str: 监听器ID
        """
        watcher_id = f"watcher_{self._watcher_counter}"
        self._watcher_counter += 1
        self._watchers[watcher_id] = callback
        logger.info(f"Config watcher registered: {watcher_id}")
        return watcher_id

    async def watch_async(self, callback: Callable[[ConfigChangeEvent], None]) -> str:
        """
        异步监听配置变更

        Args:
            callback: 变更回调函数

        Returns:
            str: 监听器ID
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.watch, callback)

    def unwatch(self, watcher_id: str) -> bool:
        """
        取消监听配置变更

        Args:
            watcher_id: 监听器ID

        Returns:
            bool: 取消成功返回True，失败返回False
        """
        if watcher_id in self._watchers:
            del self._watchers[watcher_id]
            logger.info(f"Config watcher unregistered: {watcher_id}")
            return True
        return False

    def _notify_watchers(self, key: str, old_value: Any, new_value: Any, scope: ConfigScope) -> None:
        """通知所有监听器配置变更"""
        try:
            event = ConfigChangeEvent(
                key=key,
                old_value=old_value,
                new_value=new_value,
                scope=scope,
                timestamp=datetime.now().timestamp(),
                source="ConfigProviderAdapter"
            )

            for callback in self._watchers.values():
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in config watcher callback: {e}")
        except Exception as e:
            logger.error(f"Failed to notify config watchers: {e}")

    # 元数据方法
    def get_metadata(self, key: str) -> Optional[ConfigMetadata]:
        """
        获取配置元数据

        Args:
            key: 配置键

        Returns:
            Optional[ConfigMetadata]: 配置元数据，如果不存在则返回None
        """
        try:
            value = self.get(key)
            if value is not None:
                return ConfigMetadata(
                    key=key,
                    value=value,
                    scope=ConfigScope.SYSTEM,  # 假设都是系统配置
                    data_type=type(value),
                    description=f"Configuration value for {key}",
                    default_value=None,
                    is_sensitive=False,
                    is_readonly=False
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get config metadata '{key}': {e}")
            return None

    def validate(self, key: str, value: Any) -> bool:
        """
        验证配置值

        Args:
            key: 配置键
            value: 配置值

        Returns:
            bool: 验证通过返回True，失败返回False
        """
        try:
            # 基本验证
            if key is None or not isinstance(key, str):
                return False

            # 这里可以添加更具体的验证逻辑
            return True
        except Exception as e:
            logger.error(f"Failed to validate config '{key}': {e}")
            return False

    def get_schema(self) -> Dict[str, Any]:
        """
        获取配置模式

        Returns:
            Dict[str, Any]: 配置模式字典
        """
        return {
            "type": "object",
            "properties": {
                # ConfigLoader没有提供模式信息，这里返回空对象
            }
        }

    # 环境变量方法
    def apply_env_overrides(self, prefix: str = "VOICE_INPUT_") -> int:
        """
        应用环境变量覆盖

        Args:
            prefix: 环境变量前缀

        Returns:
            int: 应用的环境变量数量
        """
        try:
            count = 0
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    config_key = key[len(prefix):].lower().replace('_', '.')
                    self.set(config_key, value, ConfigScope.SYSTEM)
                    count += 1
            logger.info(f"Applied {count} environment variable overrides")
            return count
        except Exception as e:
            logger.error(f"Failed to apply environment overrides: {e}")
            return 0

    def set_env_prefix(self, prefix: str) -> None:
        """
        设置环境变量前缀

        Args:
            prefix: 环境变量前缀
        """
        logger.info(f"Environment variable prefix set to: {prefix}")

    def merge(self, config_dict: Dict[str, Any], scope: ConfigScope = ConfigScope.USER) -> None:
        """
        合并配置字典

        Args:
            config_dict: 配置字典
            scope: 配置作用域
        """
        # 简化实现：将配置合并到运行时配置
        if scope == ConfigScope.RUNTIME:
            for key, value in config_dict.items():
                self.set(key, value, scope)
        else:
            logger.warning(f"Config merge not supported for scope {scope.value}")

    async def merge_async(self, config_dict: Dict[str, Any], scope: ConfigScope = ConfigScope.USER) -> None:
        """
        异步合并配置字典

        Args:
            config_dict: 配置字典
            scope: 配置作用域
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.merge, config_dict, scope)

    def import_from_file(self, file_path: str, format: Optional[ConfigFormat] = None) -> bool:
        """
        从文件导入配置

        Args:
            file_path: 文件路径
            format: 文件格式，如果为None则自动检测

        Returns:
            bool: 导入成功返回True，失败返回False
        """
        # 简化实现：不支持文件导入
        logger.warning("Config import from file not supported in adapter")
        return False

    async def import_from_file_async(self, file_path: str, format: Optional[ConfigFormat] = None) -> bool:
        """
        异步从文件导入配置

        Args:
            file_path: 文件路径
            format: 文件格式，如果为None则自动检测

        Returns:
            bool: 导入成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.import_from_file, file_path, format)

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
        # 简化实现：不支持文件导出
        logger.warning("Config export to file not supported in adapter")
        return False

    async def export_to_file_async(self, file_path: str, format: ConfigFormat, scope: Optional[ConfigScope] = None) -> bool:
        """
        异步导出配置到文件

        Args:
            file_path: 文件路径
            format: 文件格式
            scope: 配置作用域，如果为None则导出所有配置

        Returns:
            bool: 导出成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.export_to_file, file_path, format, scope)

    def get_env_mappings(self) -> Dict[str, str]:
        """
        获取环境变量映射关系

        Returns:
            Dict[str, str]: 环境变量到配置键的映射
        """
        return {
            "VOICE_INPUT_MODEL_PATH": "model.default_path",
            "VOICE_INPUT_TIMEOUT_SECONDS": "recognition.timeout_seconds",
            "VOICE_INPUT_TEST_MODE": "system.test_mode"
        }

    # 缓存方法
    def enable_cache(self, ttl: float = 300.0) -> None:
        """
        启用配置缓存

        Args:
            ttl: 缓存生存时间（秒）
        """
        self._cache_enabled = True
        self._cache_ttl = ttl
        logger.info(f"Config cache enabled with TTL: {ttl}s")

    def disable_cache(self) -> None:
        """禁用配置缓存"""
        self._cache_enabled = False
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Config cache disabled")

    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Config cache cleared")

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_timestamps:
            return False
        age = datetime.now().timestamp() - self._cache_timestamps[key]
        return age < self._cache_ttl

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计字典
        """
        return {
            "enabled": self._cache_enabled,
            "ttl": self._cache_ttl,
            "size": len(self._cache),
            "keys": list(self._cache.keys())
        }

    # 统计和诊断
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取配置使用统计

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        return {
            "initialized": self._initialized,
            "auto_reload": self._auto_reload,
            "watchers_count": len(self._watchers),
            "cache_stats": self.get_cache_stats(),
            "runtime_config_keys": len(getattr(self._config_loader, '_runtime_config', {}))
        }

    def get_diagnostics_info(self) -> Dict[str, Any]:
        """
        获取诊断信息

        Returns:
            Dict[str, Any]: 诊断信息字典
        """
        try:
            import yaml  # type: ignore
            config_file_exists = os.path.exists("config.yaml")

            return {
                "initialized": self._initialized,
                "config_file_exists": config_file_exists,
                "auto_reload": self._auto_reload,
                "cache_enabled": self._cache_enabled,
                "watchers_count": len(self._watchers),
                "runtime_config_size": len(getattr(self._config_loader, '_runtime_config', {})),
                "statistics": self.get_statistics()
            }
        except Exception as e:
            logger.error(f"Failed to get diagnostics info: {e}")
            return {"error": str(e)}

    # 资源管理
    def cleanup(self) -> None:
        """清理配置提供者资源"""
        try:
            self._watchers.clear()
            self.clear_cache()
            self._initialized = False
            logger.info("ConfigProviderAdapter cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

    async def cleanup_async(self) -> None:
        """异步清理配置提供者资源"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.cleanup)

    # 属性访问器
    @property
    def wrapped_instance(self) -> Any:
        """获取包装的ConfigLoader实例"""
        return self._config_loader

    def __getattr__(self, name: str) -> Any:
        """代理未定义的属性到原ConfigLoader实例"""
        return getattr(self._config_loader, name)

    def __repr__(self) -> str:
        return f"ConfigProviderAdapter(initialized={self._initialized}, watchers={len(self._watchers)})"