import os
import yaml  # type: ignore
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
                ],
                "device": "cpu",
                "funasr": {
                    "path": "f:/04_AI/01_Workplace/Voice_Input/model/fun",
                    "chunk_size": [0, 10, 5],
                    "encoder_chunk_look_back": 4,
                    "decoder_chunk_look_back": 1,
                    "disable_update": True,
                    "trust_remote_code": False
                }
            },
            "recognition": {
                "timeout_seconds": 60,
                "buffer_size": 10000,
                "pause_timeout_multiplier": 3
            },
            "system": {
                "log_level": "INFO",
                "global_unload": False,
                "test_mode": False,
                "vosk_log_level": 0
            },
            "audio": {
                "sample_rate": 16000,
                "chunk_size": 8000,
                "ffmpeg_preprocessing": {
                    "enabled": False,
                    "filter_chain": "highpass=f=80, afftdn=nf=-25, loudnorm, volume=2.0",
                    "options": {
                        "process_input": True,
                        "save_processed": False,
                        "processed_prefix": "processed_"
                    }
                }
            },
            "excel": {
                "file_name": "report",
                "auto_export": True,
                "formatting": {
                    "auto_numbering": True,
                    "include_timestamp": True,
                    "header_language": "zh",
                    "include_original": True
                }
            },
            "voice_commands": {
                "pause_commands": ["暂停", "暂停录音", "暂停识别", "pause", "暂停一下"],
                "resume_commands": ["继续", "继续录音", "恢复", "恢复识别", "resume", "继续识别"],
                "stop_commands": ["停止", "停止录音", "结束", "exit", "stop", "停止识别", "结束识别"],
                "config": {
                    "match_mode": "fuzzy",
                    "min_match_length": 2,
                    "confidence_threshold": 0.8
                }
            },
            "error_correction": {
                "dictionary_path": "voice_correction_dict.txt",
                "enabled": True
            },
            "special_texts": {
                "enabled": True,
                "exportable_texts": [
                    {
                        "base_text": "OK",
                        "variants": ["OK", "ok", "Okay", "okay", "好", "可以", "确认"]
                    },
                    {
                        "base_text": "Not OK",
                        "variants": ["Not OK", "not ok", "note ok", "Note OK", "不", "不行", "错误", "NG"]
                    }
                ]
            },
            "vad": {
                "energy_threshold": 0.015,
                "min_speech_duration": 0.3,
                "min_silence_duration": 0.6,
                "speech_padding": 0.3,
                "description": {
                    "energy_threshold": "检测语音的最小能量阈值，较小值更敏感但可能误检测",
                    "min_speech_duration": "有效语音的最小持续时间（秒）",
                    "min_silence_duration": "语音结束后的静音等待时间（秒）- 🔑 影响延迟的关键参数",
                    "speech_padding": "语音前后的额外音频填充时间（秒）"
                },
                "presets": {
                    "fast": {
                        "energy_threshold": 0.01,
                        "min_speech_duration": 0.1,
                        "min_silence_duration": 0.2,
                        "speech_padding": 0.2,
                        "description": "快速响应模式 - 减少延迟但可能误检测"
                    },
                    "balanced": {
                        "energy_threshold": 0.015,
                        "min_speech_duration": 0.3,
                        "min_silence_duration": 0.6,
                        "speech_padding": 0.3,
                        "description": "平衡模式 - 默认设置"
                    },
                    "accuracy": {
                        "energy_threshold": 0.02,
                        "min_speech_duration": 0.5,
                        "min_silence_duration": 1.0,
                        "speech_padding": 0.4,
                        "description": "高准确性模式 - 增加稳定性但延迟较高"
                    }
                }
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

        # 应用VAD预设模式
        self._apply_vad_mode(default_config)

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
        timeout_env = os.environ.get("TIMEOUT_SECONDS")
        if timeout_env:
            try:
                config["recognition"]["timeout_seconds"] = int(timeout_env)
            except ValueError:
                logger.error("环境变量TIMEOUT_SECONDS不是有效的整数")
        
        # 全局卸载覆盖
        if os.environ.get("VOICE_INPUT_GLOBAL_UNLOAD") in ("1", "true", "True"):
            config["system"]["global_unload"] = True
        
        # 测试模式覆盖
        if os.environ.get("VOICE_INPUT_TEST_MODE") in ("1", "true", "True"):
            config["system"]["test_mode"] = True
        
        # VOSK日志级别覆盖
        vosk_log_level_env = os.environ.get("VOSK_LOG_LEVEL")
        if vosk_log_level_env:
            try:
                config["system"]["vosk_log_level"] = int(vosk_log_level_env)
            except ValueError:
                logger.error("环境变量VOSK_LOG_LEVEL不是有效的整数")

    def _apply_vad_mode(self, config: Dict[str, Any]) -> None:
        """应用VAD预设模式"""
        try:
            vad_config = config.get("vad", {})
            if not vad_config:
                return

            mode = vad_config.get("mode", "balanced")
            if mode == "customized":
                logger.info("VAD使用自定义配置")
                return

            presets = vad_config.get("presets", {})
            preset = presets.get(mode)

            if preset:
                # 应用预设参数（跳过description和use_case字段）
                for key, value in preset.items():
                    if key not in ["description", "use_case"]:
                        vad_config[key] = value

                logger.info(f"VAD已应用预设模式: {mode} - {preset.get('description', '')}")
            else:
                logger.warning(f"VAD预设模式不存在: {mode}，使用默认配置")

        except Exception as e:
            logger.warning(f"应用VAD预设模式失败: {e}")

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
    
    def get_excel_file_name(self) -> str:
        """获取Excel文件名"""
        return self.get("excel.file_name")
    
    def get_vosk_log_level(self) -> int:
        """获取VOSK日志级别"""
        return self.get("system.vosk_log_level")
    
    def get_log_level(self) -> str:
        """获取系统日志级别"""
        return self.get("system.log_level")
    
    def get_pause_timeout_multiplier(self) -> int:
        """获取暂停超时乘数"""
        return self.get("recognition.pause_timeout_multiplier", 3)
    
    def get_sample_rate(self) -> int:
        """获取音频采样率"""
        return self.get("audio.sample_rate", 16000)
    
    def get_chunk_size(self) -> int:
        """获取音频块大小"""
        return self.get("audio.chunk_size", 8000)

    def is_ffmpeg_preprocessing_enabled(self) -> bool:
        """获取FFmpeg音频预处理是否启用"""
        return self.get("audio.ffmpeg_preprocessing.enabled", False)

    def get_ffmpeg_filter_chain(self) -> str:
        """获取FFmpeg滤镜链"""
        return self.get("audio.ffmpeg_preprocessing.filter_chain", "highpass=f=80, afftdn=nf=-25, loudnorm, volume=2.0")

    def get_ffmpeg_options(self) -> dict:
        """获取FFmpeg预处理选项"""
        return self.get("audio.ffmpeg_preprocessing.options", {
            "process_input": True,
            "save_processed": False,
            "processed_prefix": "processed_"
        })

    def is_error_correction_enabled(self) -> bool:
        """获取错误修正功能是否启用"""
        return self.get("error_correction.enabled", True)
    
    def get_error_correction_dict_path(self) -> str:
        """获取错误修正字典路径"""
        return self.get("error_correction.dictionary_path", "voice_correction_dict.txt")
    
    def get_special_texts_config(self) -> dict:
        """获取特定文本配置"""
        return self.get("special_texts", {})
    
    def is_special_text_export_enabled(self) -> bool:
        """获取特定文本导出是否启用"""
        return self.get("special_texts.enabled", True)
    
    def get_exportable_texts(self) -> list:
        """获取可导出的特定文本列表"""
        return self.get("special_texts.exportable_texts", [])
    
    def get_funasr_config(self) -> dict:
        """获取FunASR相关配置"""
        return self.get("model.funasr", {})
    
    def get_funasr_path(self) -> str:
        """获取FunASR模型路径"""
        return self.get("model.funasr.path", "")

    def get_voice_commands_config(self) -> dict:
        """获取语音命令配置"""
        return self.get("voice_commands", {})

    def get_pause_commands(self) -> list:
        """获取暂停命令列表"""
        return self.get("voice_commands.pause_commands", [])

    def get_resume_commands(self) -> list:
        """获取继续命令列表"""
        return self.get("voice_commands.resume_commands", [])

    def get_stop_commands(self) -> list:
        """获取停止命令列表"""
        return self.get("voice_commands.stop_commands", [])

    def get_voice_command_config(self) -> dict:
        """获取语音命令识别配置"""
        return self.get("voice_commands.config", {})

    def get_vad_config(self) -> dict:
        """获取VAD配置"""
        return self.get("vad", {})

    def get_vad_energy_threshold(self) -> float:
        """获取VAD能量阈值"""
        return self.get("vad.energy_threshold", 0.015)

    def get_gui_display_threshold(self) -> float:
        """获取GUI能量显示阈值（独立于VAD检测）"""
        return self.get("vad.gui_display_threshold", 0.00001)

    def get_vad_min_speech_duration(self) -> float:
        """获取VAD最小语音持续时间"""
        return self.get("vad.min_speech_duration", 0.3)

    def get_vad_min_silence_duration(self) -> float:
        """获取VAD最小静音持续时间"""
        return self.get("vad.min_silence_duration", 0.6)

    def get_vad_speech_padding(self) -> float:
        """获取VAD语音填充时间"""
        return self.get("vad.speech_padding", 0.3)

    def get_vad_preset(self, preset_name: str) -> dict:
        """获取VAD预设配置"""
        presets = self.get("vad.presets", {})
        return presets.get(preset_name, {})

    def apply_vad_preset(self, preset_name: str) -> bool:
        """应用VAD预设配置"""
        preset = self.get_vad_preset(preset_name)
        if preset:
            # 更新VAD配置
            if "vad" not in self._config:
                self._config["vad"] = {}

            for key, value in preset.items():
                if key != "description":  # 跳过描述字段
                    self._config["vad"][key] = value

            logger.info(f"已应用VAD预设: {preset_name}")
            return True
        else:
            logger.warning(f"VAD预设不存在: {preset_name}")
            return False

    def get_vad_description(self) -> dict:
        """获取VAD参数说明"""
        return self.get("vad.description", {})

# 全局配置实例
config = ConfigLoader()