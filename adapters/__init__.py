# -*- coding: utf-8 -*-
"""
Voice Input System - 适配器模块

本模块提供现有代码到新接口的适配器实现，确保系统的向后兼容性。
采用适配器模式包装现有实现，不修改原有代码。

主要组件:
- AudioProcessorAdapter: 音频处理器适配器
- DataExporterAdapter: 数据导出器适配器
- TTSProviderAdapter: TTS语音服务适配器
- ConfigProviderAdapter: 配置提供者适配器
- AdapterFactory: 适配器工厂
- AdapterRegistry: 适配器注册表
"""

from .audio_processor_adapter import AudioProcessorAdapter
from .data_exporter_adapter import DataExporterAdapter
from .tts_provider_adapter import TTSProviderAdapter
from .config_provider_adapter import ConfigProviderAdapter
from .adapter_factory import AdapterFactory
from .adapter_registry import AdapterRegistry

__all__ = [
    # 适配器实现
    "AudioProcessorAdapter",
    "DataExporterAdapter",
    "TTSProviderAdapter",
    "ConfigProviderAdapter",

    # 工厂和注册
    "AdapterFactory",
    "AdapterRegistry"
]

__version__ = "1.0.0"
__author__ = "Voice Input System Team"