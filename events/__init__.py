# -*- coding: utf-8 -*-
"""
事件驱动模块

提供完整的事件驱动架构，包括事件总线、事件处理器和事件类型定义。
"""

from .base_event import (
    BaseEvent, EventPriority, EventMetadata,
    AudioEvent, SystemEvent, RecognitionEvent,
    TTSEvent, ConfigurationEvent, DataEvent
)
from .event_bus import EventBus, AsyncEventBus
from .event_handler import EventHandler, event_handler
from .event_types import (
    AudioStreamStartedEvent, AudioStreamStoppedEvent,
    AudioDataReceivedEvent, RecognitionStartedEvent,
    RecognitionCompletedEvent, RecognitionPartialEvent,
    TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent,
    ComponentStateChangedEvent, SystemStartedEvent, SystemShutdownEvent,
    ErrorEvent, PerformanceMetricEvent, create_error_event, create_metric_event
)
from .system_coordinator import SystemCoordinator, get_global_coordinator

__all__ = [
    # 基础事件类
    "BaseEvent",
    "EventPriority",
    "EventMetadata",

    # 事件类型
    "AudioEvent",
    "SystemEvent",
    "RecognitionEvent",
    "TTSEvent",
    "ConfigurationEvent",
    "DataEvent",

    # 具体事件
    "AudioStreamStartedEvent",
    "AudioStreamStoppedEvent",
    "AudioDataReceivedEvent",
    "RecognitionStartedEvent",
    "RecognitionCompletedEvent",
    "RecognitionPartialEvent",
    "TTSPlaybackStartedEvent",
    "TTSPlaybackCompletedEvent",
    "ComponentStateChangedEvent",
    "SystemStartedEvent",
    "SystemShutdownEvent",
    "ErrorEvent",
    "PerformanceMetricEvent",
    "create_error_event",
    "create_metric_event",

    # 事件总线
    "EventBus",
    "AsyncEventBus",

    # 事件处理器
    "EventHandler",
    "event_handler",

    # 系统协调器
    "SystemCoordinator",
    "get_global_coordinator"
]

__version__ = "1.0.0"
__author__ = "Voice Input System Team"

# 模块级别日志配置
import logging
logger = logging.getLogger(__name__)
logger.info("Event-driven module initialized")