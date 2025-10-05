# -*- coding: utf-8 -*-
"""
异步配置加载器

提供高性能的异步配置文件加载、热重载和验证功能。
支持YAML、JSON等多种格式。
"""

import asyncio
import logging
import json
import yaml
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
import aiofiles


@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    config_path: str
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    changed_keys: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AsyncConfigLoader:
    """异步配置加载器"""

    def __init__(self, config_path: Union[str, Path], enable_hot_reload: bool = True):
        self.config_path = Path(config_path)
        self.enable_hot_reload = enable_hot_reload

        # 日志记录器
        self.logger = logging.getLogger('async_config.loader')

        # 配置缓存
        self._config: Dict[str, Any] = {}
        self._config_hash: str = ""
        self._last_modified: float = 0.0

        # 简化的文件监控
        self._watcher_task: Optional[asyncio.Task] = None
        self._watcher_running: bool = False

        # 变更回调
        self._change_callbacks: List[Callable[[ConfigChangeEvent], None]] = []

        # 配置验证器
        self._validators: List[Callable[[Dict[str, Any]], ConfigValidationResult]] = []

    async def initialize(self) -> bool:
        """初始化配置加载器"""
        try:
            # 检查配置文件是否存在
            if not self.config_path.exists():
                self.logger.error(f"配置文件不存在: {self.config_path}")
                return False

            # 首次加载配置
            success = await self.load_config()
            if not success:
                return False

            # 启动文件监控
            if self.enable_hot_reload:
                await self._start_file_watcher()

            self.logger.info(f"异步配置加载器已初始化: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"配置加载器初始化失败: {e}")
            return False

    async def load_config(self) -> bool:
        """异步加载配置文件"""
        try:
            # 异步读取文件
            async with aiofiles.open(self.config_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # 解析配置
            config = await self._parse_config(content)
            if config is None:
                return False

            # 验证配置
            validation_result = await self._validate_config(config)
            if not validation_result.is_valid:
                self.logger.error(f"配置验证失败: {validation_result.errors}")
                return False

            # 检查配置是否变更
            old_config = self._config.copy()
            config_hash = self._calculate_hash(content)

            if config_hash != self._config_hash:
                # 检测变更的键
                changed_keys = self._detect_changes(old_config, config)

                # 更新配置
                self._config = config
                self._config_hash = config_hash
                self._last_modified = time.time()

                # 触发变更事件
                if old_config:  # 不是首次加载
                    await self._notify_change(old_config, config, changed_keys)

                self.logger.info(f"配置加载成功，变更键: {changed_keys}")

            return True

        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            return False

    async def _parse_config(self, content: str) -> Optional[Dict[str, Any]]:
        """解析配置内容"""
        try:
            file_ext = self.config_path.suffix.lower()

            if file_ext in ['.yaml', '.yml']:
                return yaml.safe_load(content) or {}
            elif file_ext == '.json':
                return json.loads(content) or {}
            else:
                self.logger.error(f"不支持的配置文件格式: {file_ext}")
                return None

        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析错误: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"配置解析错误: {e}")
            return None

    async def _validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        result = ConfigValidationResult(is_valid=True)

        # 执行所有验证器
        for validator in self._validators:
            try:
                validation_result = validator(config)
                if not validation_result.is_valid:
                    result.is_valid = False
                result.errors.extend(validation_result.errors)
                result.warnings.extend(validation_result.warnings)
            except Exception as e:
                result.errors.append(f"验证器执行失败: {e}")
                result.is_valid = False

        return result

    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _detect_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """检测变更的配置键"""
        changed_keys = []

        # 检查新增和修改的键
        for key, value in new_config.items():
            if key not in old_config or old_config[key] != value:
                changed_keys.append(key)

        # 检查删除的键
        for key in old_config:
            if key not in new_config:
                changed_keys.append(f"deleted:{key}")

        return changed_keys

    async def _notify_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any], changed_keys: List[str]):
        """通知配置变更"""
        try:
            event = ConfigChangeEvent(
                config_path=str(self.config_path),
                old_config=old_config,
                new_config=new_config,
                changed_keys=changed_keys
            )

            # 调用所有回调函数
            for callback in self._change_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"配置变更回调执行失败: {e}")

        except Exception as e:
            self.logger.error(f"配置变更通知失败: {e}")

    async def _start_file_watcher(self):
        """启动简化版文件监控"""
        try:
            self._watcher_running = True
            self._watcher_task = asyncio.create_task(self._file_watcher_loop())
            self.logger.info("配置文件监控已启动（简化版）")

        except Exception as e:
            self.logger.error(f"文件监控启动失败: {e}")

    async def _file_watcher_loop(self):
        """文件监控循环"""
        self._last_modified = self.config_path.stat().st_mtime

        while self._watcher_running:
            try:
                await asyncio.sleep(1.0)  # 每秒检查一次

                # 检查文件修改时间
                current_mtime = self.config_path.stat().st_mtime
                if current_mtime > self._last_modified:
                    self.logger.info(f"检测到配置文件变更: {self.config_path}")
                    self._last_modified = current_mtime

                    # 重新加载配置
                    await self.load_config()

            except Exception as e:
                self.logger.error(f"文件监控错误: {e}")
                await asyncio.sleep(5.0)  # 出错时等待5秒再继续

    async def stop(self):
        """停止配置加载器"""
        try:
            # 停止文件监控
            if self._watcher_running:
                self._watcher_running = False
                if self._watcher_task:
                    self._watcher_task.cancel()
                    try:
                        await self._watcher_task
                    except asyncio.CancelledError:
                        pass
                self.logger.info("配置文件监控已停止")

            self.logger.info("异步配置加载器已停止")

        except Exception as e:
            self.logger.error(f"配置加载器停止失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """设置配置值（仅在内存中，不持久化）"""
        keys = key.split('.')
        config = self._config

        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def add_validator(self, validator: Callable[[Dict[str, Any]], ConfigValidationResult]):
        """添加配置验证器"""
        self._validators.append(validator)

    def add_change_callback(self, callback: Callable[[ConfigChangeEvent], None]):
        """添加配置变更回调"""
        self._change_callbacks.append(callback)

    def is_loaded(self) -> bool:
        """检查配置是否已加载"""
        return bool(self._config)

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'config_path': str(self.config_path),
            'is_loaded': self.is_loaded(),
            'last_modified': self._last_modified,
            'config_hash': self._config_hash,
            'hot_reload_enabled': self.enable_hot_reload,
            'validator_count': len(self._validators),
            'callback_count': len(self._change_callbacks)
        }


# 预定义的配置验证器
def create_audio_config_validator() -> Callable[[Dict[str, Any]], ConfigValidationResult]:
    """创建音频配置验证器"""
    def validator(config: Dict[str, Any]) -> ConfigValidationResult:
        result = ConfigValidationResult(is_valid=True)

        try:
            audio_config = config.get('audio', {})

            # 验证采样率
            sample_rate = audio_config.get('sample_rate')
            if sample_rate is not None:
                if not isinstance(sample_rate, (int, float)) or sample_rate <= 0:
                    result.errors.append("audio.sample_rate 必须是正数")
                    result.is_valid = False

            # 验证缓冲区大小
            chunk_size = audio_config.get('chunk_size')
            if chunk_size is not None:
                if not isinstance(chunk_size, int) or chunk_size <= 0:
                    result.errors.append("audio.chunk_size 必须是正整数")
                    result.is_valid = False

            # 验证通道数
            channels = audio_config.get('channels')
            if channels is not None:
                if not isinstance(channels, int) or channels <= 0:
                    result.errors.append("audio.channels 必须是正整数")
                    result.is_valid = False

        except Exception as e:
            result.errors.append(f"音频配置验证异常: {e}")
            result.is_valid = False

        return result

    return validator


def create_system_config_validator() -> Callable[[Dict[str, Any]], ConfigValidationResult]:
    """创建系统配置验证器"""
    def validator(config: Dict[str, Any]) -> ConfigValidationResult:
        result = ConfigValidationResult(is_valid=True)

        try:
            system_config = config.get('system', {})

            # 验证超时时间
            timeout = system_config.get('timeout_seconds')
            if timeout is not None:
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    result.errors.append("system.timeout_seconds 必须是正数")
                    result.is_valid = False

            # 验证日志级别
            log_level = system_config.get('log_level')
            if log_level is not None:
                valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                if log_level not in valid_levels:
                    result.errors.append(f"system.log_level 必须是以下值之一: {valid_levels}")
                    result.is_valid = False

        except Exception as e:
            result.errors.append(f"系统配置验证异常: {e}")
            result.is_valid = False

        return result

    return validator