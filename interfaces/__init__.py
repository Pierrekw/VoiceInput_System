# -*- coding: utf-8 -*-
"""
Voice Input System - 接口定义模块

本模块定义了语音输入系统的所有核心接口，为系统解耦和异步化改造提供抽象层。

主要接口:
- IAudioProcessor: 音频处理器接口
- IDataExporter: 数据导出器接口
- ITTSProvider: TTS语音服务接口
- IConfigProvider: 配置提供者接口
- ISystemController: 系统控制器接口
"""

from .audio_processor import IAudioProcessor, AudioProcessorState
from .data_exporter import IDataExporter
from .tts_provider import ITTSProvider
from .config_provider import IConfigProvider
from .system_controller import ISystemController

__all__ = [
    "IAudioProcessor",
    "AudioProcessorState",
    "IDataExporter",
    "ITTSProvider",
    "IConfigProvider",
    "ISystemController"
]

__version__ = "1.0.0"
__author__ = "Voice Input System Team"