#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境延迟记录器
轻量级的延迟记录系统，适合生产环境常态化使用
"""

import time
import logging
import threading
from collections import deque
from typing import Deque, Dict, Any, List, Optional

class ProductionLatencyLogger:
    """生产环境延迟记录器"""

    def __init__(self, max_records: int = 100):
        self.max_records = max_records
        self.records: Deque[Dict[str, Any]] = deque(maxlen=max_records)
        self.current_session_start = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger("LATENCY")

    def start_session(self):
        """开始新的语音识别会话"""
        with self.lock:
            self.current_session_start = time.time()
            self.logger.debug(f"[LATENCY] 会话开始")

    def record_voice_input_end(self, audio_duration: float):
        """记录语音输入结束"""
        if not self.current_session_start:
            return

        current_time = time.time()
        voice_latency = current_time - self.current_session_start

        record = {
            'timestamp': current_time,
            'voice_latency': voice_latency,
            'audio_duration': audio_duration,
            'type': 'voice_input'
        }

        with self.lock:
            self.records.append(record)

        self.logger.debug(f"[LATENCY] 语音输入完成 | 音频时长: {audio_duration:.2f}s | 输入延迟: {voice_latency*1000:.1f}ms")

    def record_asr_complete(self, text: str, asr_latency: float):
        """记录ASR完成"""
        if not self.current_session_start:
            return

        current_time = time.time()
        total_latency = current_time - self.current_session_start

        record = {
            'timestamp': current_time,
            'total_latency': total_latency,
            'asr_latency': asr_latency,
            'text': text[:50],  # 只保存前50个字符
            'type': 'asr_complete'
        }

        with self.lock:
            self.records.append(record)

        self.logger.debug(f"[LATENCY] ASR完成: '{text[:30]}...' | ASR延迟: {asr_latency*1000:.1f}ms | 总延迟: {total_latency*1000:.1f}ms")

    def record_terminal_display(self, text: str, display_latency: float):
        """记录终端显示"""
        if not self.current_session_start:
            return

        current_time = time.time()
        end_to_end_latency = current_time - self.current_session_start

        record = {
            'timestamp': current_time,
            'end_to_end_latency': end_to_end_latency,
            'display_latency': display_latency,
            'text': text[:50],
            'type': 'terminal_display'
        }

        with self.lock:
            self.records.append(record)

        self.logger.debug(f"[LATENCY] 终端显示: '{text[:30]}...' | 显示延迟: {display_latency*1000:.2f}ms | 端到端延迟: {end_to_end_latency*1000:.1f}ms")

    def get_recent_summary(self, count: int = 10) -> Dict:
        """获取最近的延迟统计摘要"""
        with self.lock:
            recent_records = list(self.records)[-count:]

        if not recent_records:
            return {"message": "暂无记录"}

        # 按类型分组
        asr_records = [r for r in recent_records if r['type'] == 'asr_complete']
        terminal_records = [r for r in recent_records if r['type'] == 'terminal_display']

        summary: Dict[str, Any] = {
            'total_records': len(recent_records),
            'asr_count': len(asr_records),
            'terminal_count': len(terminal_records),
            'avg_end_to_end_latency': 0,
            'max_end_to_end_latency': 0,
            'recent_examples': []
        }

        if terminal_records:
            end_to_end_latencies = [r['end_to_end_latency'] for r in terminal_records]
            summary['avg_end_to_end_latency'] = sum(end_to_end_latencies) / len(end_to_end_latencies)
            summary['max_end_to_end_latency'] = max(end_to_end_latencies)

            # 获取最近的例子
            for record in terminal_records[-3:]:
                summary['recent_examples'].append({
                    'text': record['text'],
                    'latency_ms': record['end_to_end_latency'] * 1000
                })

        return summary

    def end_session(self):
        """结束当前会话"""
        with self.lock:
            if self.current_session_start:
                session_duration = time.time() - self.current_session_start
                self.logger.debug(f"[LATENCY] 会话结束 | 总时长: {session_duration:.2f}s")
                self.current_session_start = None

# 全局实例
production_latency_logger = ProductionLatencyLogger()

# 便捷函数
def log_voice_input_end(audio_duration: float):
    """记录语音输入结束"""
    production_latency_logger.record_voice_input_end(audio_duration)

def log_asr_complete(text: str, asr_latency: float):
    """记录ASR完成"""
    production_latency_logger.record_asr_complete(text, asr_latency)

def log_terminal_display(text: str, display_latency: float = 0.0):
    """记录终端显示"""
    production_latency_logger.record_terminal_display(text, display_latency)

def start_latency_session():
    """开始延迟记录会话"""
    production_latency_logger.start_session()

def end_latency_session():
    """结束延迟记录会话"""
    production_latency_logger.end_session()

def get_latency_summary():
    """获取延迟摘要"""
    return production_latency_logger.get_recent_summary()