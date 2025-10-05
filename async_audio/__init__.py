# -*- coding: utf-8 -*-
"""
异步音频处理模块

提供基于asyncio的现代异步音频处理功能，包括：
- 异步音频流管理
- 异步语音识别
- 异步TTS播放
- 事件驱动的状态管理
"""

from .async_audio_capture import (
    AsyncAudioCapture,
    AsyncAudioStream,
    AsyncRecognizer,
    AsyncTTSPlayer,
    AsyncAudioProcessorState,
    AudioChunk,
    RecognitionTask,
    TTSRequest,
    create_async_audio_capture
)

__all__ = [
    "AsyncAudioCapture",
    "AsyncAudioStream",
    "AsyncRecognizer",
    "AsyncTTSPlayer",
    "AsyncAudioProcessorState",
    "AudioChunk",
    "RecognitionTask",
    "TTSRequest",
    "create_async_audio_capture"
]

__version__ = "1.0.0"
__author__ = "Voice Input System Team"

# 模块级别日志配置
import logging
logger = logging.getLogger(__name__)
logger.info("AsyncAudio module initialized")