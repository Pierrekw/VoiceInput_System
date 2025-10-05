# -*- coding: utf-8 -*-
"""
共享配置模块示例

此文件展示了如何设计一个灵活的共享配置系统，支持同步和异步系统的不同需求，
同时保持配置的一致性和可维护性。
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置相关错误"""
    pass


class BaseConfig:
    """基础配置类，包含所有系统共享的配置项"""
    
    def __init__(self, config_path: Union[str, Path] = None):
        # 配置文件路径
        self._config_path = self._resolve_config_path(config_path)
        # 配置数据存储
        self._config_data = {}
        # 已加载标记
        self._loaded = False
        # 默认配置
        self._default_config = {
            'general': {
                'log_level': 'INFO',
                'vosk_log_level': -1,
                'test_mode': False,
                'timeout_seconds': 30
            },
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'format': 16,
                'chunk_size': 4096
            },
            'recognition': {
                'model_path': 'models',
                'language': 'zh-CN',
                'confidence_threshold': 0.5
            },
            'tts': {
                'enabled': True,
                'voice': 'zh-CN',
                'speed': 1.0,
                'volume': 1.0
            },
            'excel': {
                'auto_export': True,
                'file_path': 'voice_data.xlsx',
                'sheet_name': 'Data',
                'auto_numbering': True,
                'include_timestamp': True
            },
            'error_correction': {
                'enabled': True,
                'dictionary_path': 'voice_correction_dict.txt'
            }
        }
    
    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """解析配置文件路径"""
        if config_path:
            return Path(config_path)
        
        # 根据调用位置自动选择配置文件
        import inspect
        caller_file = inspect.stack()[2].filename  # 获取调用者的文件路径
        caller_dir = Path(caller_file).parent.name
        
        if 'sync_system' in caller_file:
            return Path('configs/sync_config.yaml')
        elif 'async_system' in caller_file:
            return Path('configs/async_config.yaml')
        else:
            return Path('configs/config.yaml')
    
    def load(self) -> 'BaseConfig':
        """加载配置文件"""
        try:
            # 如果配置文件存在，加载配置
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"✅ 加载配置文件成功: {self._config_path}")
            else:
                # 使用默认配置
                self._config_data = self._default_config
                logger.warning(f"⚠️ 配置文件不存在，使用默认配置: {self._config_path}")
                # 可选：创建默认配置文件
                self._create_default_config()
            
            # 合并默认配置和用户配置
            self._merge_defaults()
            
            # 验证配置完整性
            self._validate_config()
            
            self._loaded = True
            return self
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        try:
            # 确保目录存在
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._default_config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"✅ 创建默认配置文件成功: {self._config_path}")
        except Exception as e:
            logger.warning(f"⚠️ 创建默认配置文件失败: {e}")
    
    def _merge_defaults(self) -> None:
        """合并默认配置和用户配置"""
        def deep_merge(default: Dict, user: Dict) -> Dict:
            """深度合并两个字典"""
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        self._config_data = deep_merge(self._default_config, self._config_data)
    
    def _validate_config(self) -> None:
        """验证配置完整性"""
        # 这里可以添加配置验证逻辑
        # 例如检查必要的配置项是否存在，值是否合法等
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号分隔的嵌套路径"""
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"⚠️ 配置项不存在: {key}, 使用默认值: {default}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项，支持点号分隔的嵌套路径"""
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        config = self._config_data
        
        try:
            for k in keys[:-1]:
                if k not in config or not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            logger.debug(f"🔧 更新配置项: {key} = {value}")
        except Exception as e:
            logger.error(f"❌ 设置配置项失败: {key}, 错误: {e}")
            raise ConfigError(f"Failed to set configuration: {key}")
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"✅ 保存配置文件成功: {self._config_path}")
        except Exception as e:
            logger.error(f"❌ 保存配置文件失败: {e}")
            raise ConfigError(f"Failed to save configuration: {e}")
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get('general.log_level', 'INFO')
    
    def get_vosk_log_level(self) -> int:
        """获取VOSK日志级别"""
        return self.get('general.vosk_log_level', -1)
    
    def get_test_mode(self) -> bool:
        """获取测试模式状态"""
        return self.get('general.test_mode', False)
    
    def get_timeout_seconds(self) -> int:
        """获取超时时间（秒）"""
        return self.get('general.timeout_seconds', 30)


class SyncConfig(BaseConfig):
    """同步系统专用配置类"""
    
    def __init__(self, config_path: Union[str, Path] = None):
        super().__init__(config_path or 'configs/sync_config.yaml')
        # 同步系统特有的默认配置
        self._default_config.update({
            'sync_specific': {
                'buffer_size': 1024,
                'processing_threads': 1,
                'keyboard_control': True,
                'hotkey': 'space',
                'realtime_display': True
            }
        })
    
    def get_buffer_size(self) -> int:
        """获取缓冲区大小"""
        return self.get('sync_specific.buffer_size', 1024)
    
    def get_processing_threads(self) -> int:
        """获取处理线程数"""
        return self.get('sync_specific.processing_threads', 1)
    
    def is_keyboard_control_enabled(self) -> bool:
        """获取键盘控制是否启用"""
        return self.get('sync_specific.keyboard_control', True)
    
    def get_hotkey(self) -> str:
        """获取热键"""
        return self.get('sync_specific.hotkey', 'space')


class AsyncConfig(BaseConfig):
    """异步系统专用配置类"""
    
    def __init__(self, config_path: Union[str, Path] = None):
        super().__init__(config_path or 'configs/async_config.yaml')
        # 异步系统特有的默认配置
        self._default_config.update({
            'async_specific': {
                'event_loop_policy': 'default',
                'max_concurrent_tasks': 10,
                'task_timeout': 60,
                'event_bus_capacity': 100,
                'stream_buffer_size': 4096,
                'coordinator_update_interval': 0.1
            }
        })
    
    def get_event_loop_policy(self) -> str:
        """获取事件循环策略"""
        return self.get('async_specific.event_loop_policy', 'default')
    
    def get_max_concurrent_tasks(self) -> int:
        """获取最大并发任务数"""
        return self.get('async_specific.max_concurrent_tasks', 10)
    
    def get_task_timeout(self) -> int:
        """获取任务超时时间（秒）"""
        return self.get('async_specific.task_timeout', 60)
    
    def get_event_bus_capacity(self) -> int:
        """获取事件总线容量"""
        return self.get('async_specific.event_bus_capacity', 100)


# 创建单例实例
# 共享配置实例
shared_config = BaseConfig().load()
# 同步系统配置实例
sync_config = SyncConfig().load()
# 异步系统配置实例
async_config = AsyncConfig().load()


# 兼容旧版API的函数
# 这些函数用于保持向后兼容性，允许现有代码继续工作
def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值（兼容旧版API）"""
    return shared_config.get(key, default)

def set_config_value(key: str, value: Any) -> None:
    """设置配置值（兼容旧版API）"""
    shared_config.set(key, value)

def save_config() -> None:
    """保存配置（兼容旧版API）"""
    shared_config.save()


# 示例用法
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 测试共享配置
    print("\n=== 测试共享配置 ===")
    print(f"日志级别: {shared_config.get_log_level()}")
    print(f"VOSK日志级别: {shared_config.get_vosk_log_level()}")
    print(f"测试模式: {shared_config.get_test_mode()}")
    print(f"Excel自动导出: {shared_config.get('excel.auto_export')}")
    
    # 测试同步系统配置
    print("\n=== 测试同步系统配置 ===")
    print(f"缓冲区大小: {sync_config.get_buffer_size()}")
    print(f"处理线程数: {sync_config.get_processing_threads()}")
    print(f"键盘控制启用: {sync_config.is_keyboard_control_enabled()}")
    print(f"热键: {sync_config.get_hotkey()}")
    
    # 测试异步系统配置
    print("\n=== 测试异步系统配置 ===")
    print(f"事件循环策略: {async_config.get_event_loop_policy()}")
    print(f"最大并发任务数: {async_config.get_max_concurrent_tasks()}")
    print(f"任务超时时间: {async_config.get_task_timeout()}")
    print(f"事件总线容量: {async_config.get_event_bus_capacity()}")
    
    # 测试配置更新
    print("\n=== 测试配置更新 ===")
    shared_config.set('general.log_level', 'DEBUG')
    print(f"更新后日志级别: {shared_config.get_log_level()}")
    
    # 测试不存在的配置项
    print("\n=== 测试不存在的配置项 ===")
    unknown_value = shared_config.get('unknown.config.item', '默认值')
    print(f"未知配置项: {unknown_value}")