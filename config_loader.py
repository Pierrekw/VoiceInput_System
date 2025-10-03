import os
import yaml
import logging
from typing import Dict, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    配置加载器，负责读取和解析config.yaml文件
    提供默认值并支持环境变量覆盖
    """
    
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}
    _config_file_path = "config.yaml"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """加载配置文件，设置默认值并应用环境变量覆盖"""
        # 默认配置
        default_config = {
            "model": {
                "default_path": "model/cn",
                "available_models": [
                    {"name": "中文标准模型（高精度）", "path": "model/cn", "description": "完整的中文语音识别模型，准确率高"},
                    {"name": "中文小模型（快速加载）", "path": "model/cns", "description": "精简版中文语音识别模型，启动速度快，占用内存少"},
                    {"name": "英文标准模型", "path": "model/us", "description": "完整的英文语音识别模型"},
                    {"name": "英文小模型", "path": "model/uss", "description": "精简版英文语音识别模型"}
                ]
            },
            "recognition": {
                "timeout_seconds": 60,
                "buffer_size": 10000,
                "sleep_times": {
                    "small": 0.01,
                    "short": 0.05,
                    "medium": 0.1,
                    "long": 0.5,
                    "test": 2
                }
            },
            "system": {
                "log_level": "INFO",
                "global_unload": False,
                "test_mode": False,
                "vosk_log_level": 0
            },
            "excel": {
                "file_name": "measurement_data.xlsx",
                "auto_export": True,
                "formatting": {
                    "auto_numbering": True,
                    "include_timestamp": True,
                    "header_language": "zh"
                }
            },
            "voice_commands": {
                "pause_commands": ["暂停录音", "暂停"],
                "resume_commands": ["继续录音", "继续", "恢复"],
                "stop_commands": ["停止录音", "停止", "结束"]
            },
            "error_correction": {
                "dictionary_path": "voice_correction_dict.txt",
                "enabled": True
            }
        }
        
        # 加载配置文件
        if os.path.exists(self._config_file_path):
            try:
                with open(self._config_file_path, 'r', encoding='utf-8') as file:
                    user_config = yaml.safe_load(file)
                    # 合并用户配置到默认配置
                    self._merge_configs(default_config, user_config)
                    logger.info(f"成功加载配置文件: {self._config_file_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                # 使用默认配置
        else:
            logger.warning(f"配置文件不存在: {self._config_file_path}，使用默认配置")
        
        # 应用环境变量覆盖
        self._apply_environment_overrides(default_config)
        
        # 保存最终配置
        self._config = default_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> None:
        """递归合并配置字典"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def _apply_environment_overrides(self, config: Dict[str, Any]) -> None:
        """应用环境变量覆盖配置"""
        # 模型路径覆盖
        if os.environ.get("MODEL_PATH"):
            config["model"]["default_path"] = os.environ.get("MODEL_PATH")
        
        # 超时设置覆盖
        if os.environ.get("TIMEOUT_SECONDS"):
            try:
                config["recognition"]["timeout_seconds"] = int(os.environ.get("TIMEOUT_SECONDS"))
            except ValueError:
                logger.error("环境变量TIMEOUT_SECONDS不是有效的整数")
        
        # 全局卸载覆盖
        if os.environ.get("VOICE_INPUT_GLOBAL_UNLOAD") in ("1", "true", "True"):
            config["system"]["global_unload"] = True
        
        # 测试模式覆盖
        if os.environ.get("VOICE_INPUT_TEST_MODE") in ("1", "true", "True"):
            config["system"]["test_mode"] = True
        
        # VOSK日志级别覆盖
        if os.environ.get("VOSK_LOG_LEVEL"):
            try:
                config["system"]["vosk_log_level"] = int(os.environ.get("VOSK_LOG_LEVEL"))
            except ValueError:
                logger.error("环境变量VOSK_LOG_LEVEL不是有效的整数")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        获取指定路径的配置值
        路径格式："section.key.subkey"
        """
        keys = path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model_path(self) -> str:
        """获取模型路径"""
        return self.get("model.default_path")
    
    def get_timeout_seconds(self) -> int:
        """获取超时时间"""
        return self.get("recognition.timeout_seconds")
    
    def get_global_unload(self) -> bool:
        """获取全局卸载设置"""
        return self.get("system.global_unload")
    
    def get_test_mode(self) -> bool:
        """获取测试模式设置"""
        return self.get("system.test_mode")
    
    def get_sleep_time(self, sleep_type: str) -> float:
        """获取指定类型的睡眠时间"""
        return self.get(f"recognition.sleep_times.{sleep_type}", 0.1)
    
    def get_excel_file_name(self) -> str:
        """获取Excel文件名"""
        return self.get("excel.file_name")
    
    def get_vosk_log_level(self) -> int:
        """获取VOSK日志级别"""
        return self.get("system.vosk_log_level")
    
    def get_log_level(self) -> str:
        """获取系统日志级别"""
        return self.get("system.log_level")

# 全局配置实例
config = ConfigLoader()