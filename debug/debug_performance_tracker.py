#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug性能追踪器
专门用于分析语音输入到终端显示的延迟问题
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import statistics

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class VoiceLatencyRecord:
    """语音延迟记录"""
    session_id: str
    step_name: str
    timestamp: float
    relative_time: float  # 相对于会话开始的时间
    text: str = ""
    metadata: Dict[str, Any] = None

class DebugPerformanceTracker:
    """Debug性能追踪器"""

    def __init__(self):
        self._records: List[VoiceLatencyRecord] = []
        self._session_start_time: Optional[float] = None
        self._current_session_id: Optional[str] = None
        self._last_voice_input_time: Optional[float] = None
        self._last_recognition_time: Optional[float] = None
        self._lock = threading.Lock()
        self._enabled = False

    def start_debug_session(self, session_id: str = None):
        """开始调试会话"""
        with self._lock:
            self._session_start_time = time.time()
            self._current_session_id = session_id or f"session_{int(self._session_start_time)}"
            self._last_voice_input_time = None
            self._last_recognition_time = None
            self._enabled = True

        logger.info(f"🔍 开始Debug性能追踪会话: {self._current_session_id}")
        self._record_step("SESSION_START", "调试会话开始")

    def stop_debug_session(self):
        """停止调试会话"""
        if not self._enabled:
            return

        with self._lock:
            self._record_step("SESSION_END", "调试会话结束")
            self._enabled = False

        logger.info(f"🔍 Debug性能追踪会话结束: {self._current_session_id}")
        # 生成延迟分析报告
        self._generate_latency_report()

    def _record_step(self, step_name: str, description: str, text: str = "", metadata: Dict = None):
        """记录步骤"""
        if not self._enabled or not self._session_start_time:
            return

        current_time = time.time()
        relative_time = current_time - self._session_start_time

        record = VoiceLatencyRecord(
            session_id=self._current_session_id,
            step_name=step_name,
            timestamp=current_time,
            relative_time=relative_time,
            text=text,
            metadata=metadata or {}
        )

        self._records.append(record)

        # 详细日志输出
        logger.debug(f"[DEBUG_LATENCY] {step_name:20} | 时间: {relative_time:6.3f}s | 文本: {text[:20]:20}")

    def record_voice_input_start(self, audio_energy: float = 0.0):
        """记录语音输入开始"""
        self._last_voice_input_time = time.time()
        self._record_step("VOICE_INPUT_START", "检测到语音输入", "", {"energy": audio_energy})

    def record_voice_input_end(self, audio_duration: float = 0.0):
        """记录语音输入结束"""
        if self._last_voice_input_time:
            input_latency = time.time() - self._last_voice_input_time
            self._record_step("VOICE_INPUT_END", "语音输入结束", "", {
                "input_duration": audio_duration,
                "input_latency": input_latency
            })

    def record_asr_start(self, audio_length: int = 0):
        """记录ASR处理开始"""
        self._last_asr_start_time = time.time()
        self._record_step("ASR_START", "开始语音识别", "", {"audio_length": audio_length})

    def record_asr_result(self, text: str, confidence: float = 0.0):
        """记录ASR结果"""
        asr_latency = time.time() - self._last_asr_start_time if hasattr(self, '_last_asr_start_time') else 0
        self._record_step("ASR_RESULT", "语音识别完成", text, {
            "confidence": confidence,
            "asr_latency": asr_latency
        })

    def record_text_processing_start(self, text: str):
        """记录文本处理开始"""
        self._last_text_processing_start = time.time()
        self._record_step("TEXT_PROCESSING_START", "开始文本处理", text)

    def record_text_processing_end(self, processed_text: str, has_number: bool = False):
        """记录文本处理结束"""
        processing_latency = time.time() - self._last_text_processing_start if hasattr(self, '_last_text_processing_start') else 0
        self._record_step("TEXT_PROCESSING_END", "文本处理完成", processed_text, {
            "processing_latency": processing_latency,
            "has_number": has_number
        })

    def record_terminal_display(self, text: str):
        """记录终端显示"""
        current_time = time.time()

        # 计算端到端延迟
        end_to_end_latency: float = 0.0
        if hasattr(self, '_last_voice_input_time') and self._last_voice_input_time:
            end_to_end_latency = current_time - self._last_voice_input_time

        self._record_step("TERMINAL_DISPLAY", "终端显示", text, {
            "end_to_end_latency": end_to_end_latency
        })

    def record_excel_write(self, text: str, excel_latency: float = 0.0):
        """记录Excel写入"""
        self._record_step("EXCEL_WRITE", "Excel写入", text, {"excel_latency": excel_latency})

    def _generate_latency_report(self):
        """生成延迟分析报告"""
        if not self._records:
            return

        print("\n" + "="*80)
        print("🔍 语音识别延迟分析报告")
        print("="*80)

        # 按时间线分析
        self._analyze_timeline()

        # 延迟统计
        self._analyze_latency_statistics()

        # 瓶颈分析
        self._analyze_bottlenecks()

        print("="*80)

    def _analyze_timeline(self):
        """分析时间线"""
        print("📅 时间线分析:")
        print("-" * 60)

        # 按会话分组
        sessions = defaultdict(list)
        for record in self._records:
            sessions[record.session_id].append(record)

        for session_id, records in sessions.items():
            print(f"\n会话: {session_id}")
            print(f"{'步骤':<25} {'相对时间':<12} {'文本':<25}")
            print("-" * 60)

            for record in records:
                text_preview = record.text[:20] if record.text else ""
                print(f"{record.step_name:<25} {record.relative_time:>8.3f}s   {text_preview:<25}")

    def _analyze_latency_statistics(self):
        """分析延迟统计"""
        print("\n📊 延迟统计:")
        print("-" * 60)

        # 计算各步骤延迟
        step_durations = defaultdict(list)
        last_record = None

        for record in self._records:
            if last_record and last_record.session_id == record.session_id:
                duration = record.relative_time - last_record.relative_time
                step_durations[record.step_name].append(duration)
            last_record = record

        # 输出统计结果
        for step_name, durations in step_durations.items():
            if durations:
                avg_duration = statistics.mean(durations)
                max_duration = max(durations)
                min_duration = min(durations)
                print(f"{step_name:<25}: 平均 {avg_duration*1000:6.1f}ms, "
                      f"最大 {max_duration*1000:6.1f}ms, 最小 {min_duration*1000:6.1f}ms")

    def _analyze_bottlenecks(self):
        """分析瓶颈"""
        print("\n⚠️ 瓶颈分析:")
        print("-" * 60)

        # 找出最耗时的步骤
        step_durations = defaultdict(list)
        last_record = None

        for record in self._records:
            if last_record and last_record.session_id == record.session_id:
                duration = record.relative_time - last_record.relative_time
                step_durations[record.step_name].append(duration)
            last_record = record

        # 按平均延迟排序
        avg_durations = {}
        for step_name, durations in step_durations.items():
            if durations:
                avg_durations[step_name] = statistics.mean(durations)

        if avg_durations:
            sorted_steps = sorted(avg_durations.items(), key=lambda x: x[1], reverse=True)

            print("最耗时的步骤 (按平均延迟排序):")
            for i, (step_name, avg_duration) in enumerate(sorted_steps[:5], 1):
                print(f"  {i}. {step_name:<25}: {avg_duration*1000:6.1f}ms")

        # 分析端到端延迟
        terminal_records = [r for r in self._records if r.step_name == "TERMINAL_DISPLAY"]
        if terminal_records:
            end_to_end_latencies = []
            for record in terminal_records:
                if record.metadata and "end_to_end_latency" in record.metadata:
                    end_to_end_latencies.append(record.metadata["end_to_end_latency"])

            if end_to_end_latencies:
                avg_e2e = statistics.mean(end_to_end_latencies)
                max_e2e = max(end_to_end_latencies)
                print(f"\n🎯 端到端延迟统计:")
                print(f"   平均延迟: {avg_e2e*1000:6.1f}ms")
                print(f"   最大延迟: {max_e2e*1000:6.1f}ms")

                if avg_e2e > 0.3:  # 如果延迟超过300ms
                    print(f"   ⚠️ 检测到显著延迟 ({avg_e2e*1000:.1f}ms)，建议优化")

    def clear_records(self):
        """清空记录"""
        with self._lock:
            self._records.clear()
            self._session_start_time = None
            self._current_session_id = None
            self._enabled = False

# 全局debug追踪器实例
debug_tracker = DebugPerformanceTracker()

# 装饰器版本
def debug_latency_tracker(step_name: str = None, include_text: bool = False):
    """调试延迟追踪装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if debug_tracker._enabled:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)

                    # 提取文本（如果存在）
                    text = ""
                    if include_text and args:
                        text = str(args[0]) if args else ""

                    debug_tracker._record_step(
                        step_name or func.__name__,
                        f"完成 {func.__name__}",
                        text,
                        {"duration": time.time() - start_time}
                    )
                    return result
                except Exception as e:
                    debug_tracker._record_step(
                        f"ERROR_{step_name or func.__name__}",
                        f"错误 {func.__name__}: {e}"
                    )
                    raise
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator