#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils工具包
包含各种专用工具和调试模块
"""

# 导入主要工具模块，提供便捷访问
#from ..debug.debug_performance_tracker import debug_tracker
from .production_latency_logger import (
    start_latency_session, end_latency_session,
    log_voice_input_end, log_asr_complete, log_terminal_display
)

# 导入核心模块
from .performance_monitor import performance_monitor, PerformanceStep
from .config_loader import config
from .logging_utils import (
    LoggingManager, get_logger, setup_logger, get_app_logger, get_silent_logger
)

__all__ = [
    # 调试工具
    'debug_tracker',

    # 生产延迟日志工具
    'start_latency_session',
    'end_latency_session',
    'log_voice_input_end',
    'log_asr_complete',
    'log_terminal_display',

    # 核心模块
    'performance_monitor',
    'PerformanceStep',
    'config',

    # 日志工具
    'LoggingManager',
    'get_logger',
    'setup_logger',
    'get_app_logger',
    'get_silent_logger',
]

__version__ = "1.0.0"
__author__ = "Voice Input System"