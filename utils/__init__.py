#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils工具包
包含各种专用工具和调试模块
"""

# 导入主要工具模块，提供便捷访问
from .debug_performance_tracker import debug_tracker
from .production_latency_logger import (
    start_latency_session, end_latency_session,
    log_voice_input_end, log_asr_complete, log_terminal_display
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
]

__version__ = "1.0.0"
__author__ = "Voice Input System"