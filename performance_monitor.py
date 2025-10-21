#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块
用于精确记录和分析语音识别系统各步骤的性能指标
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class PerformanceRecord:
    """单次性能记录"""
    step_name: str
    start_time: float
    end_time: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[int] = None

@dataclass
class PerformanceSummary:
    """性能汇总统计"""
    step_name: str
    total_count: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    median_duration: float
    p95_duration: float  # 95百分位数
    p99_duration: float  # 99百分位数

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self._records: List[PerformanceRecord] = []
        self._current_operations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._session_start_time = time.time()
        self._enabled = True

    def start_timer(self, step_name: str, metadata: Dict[str, Any] = None) -> str:
        """开始计时"""
        if not self._enabled:
            return ""

        timestamp = time.time()
        thread_id = threading.get_ident()
        operation_id = f"{step_name}_{timestamp}_{thread_id}"

        metadata = metadata or {}

        with self._lock:
            self._current_operations[operation_id] = {
                'step_name': step_name,
                'start_time': timestamp,
                'metadata': metadata,
                'thread_id': thread_id
            }

        logger.debug(f"[PERF] 开始: {step_name} | 时间戳: {timestamp:.6f} | 线程: {thread_id} | 元数据: {metadata}")

        return operation_id

    def end_timer(self, operation_id: str, additional_metadata: Dict[str, Any] = None) -> Optional[float]:
        """结束计时并记录"""
        if not self._enabled or not operation_id:
            return None

        end_time = time.time()

        with self._lock:
            if operation_id not in self._current_operations:
                logger.warning(f"[PERF] 操作ID不存在: {operation_id}")
                return None

            operation = self._current_operations.pop(operation_id)
            start_time = operation['start_time']
            step_name = operation['step_name']
            thread_id = operation['thread_id']

            duration = end_time - start_time

            # 合并元数据
            metadata = operation['metadata'].copy()
            if additional_metadata:
                metadata.update(additional_metadata)

            # 创建性能记录
            record = PerformanceRecord(
                step_name=step_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                metadata=metadata,
                thread_id=thread_id
            )

            self._records.append(record)

            logger.debug(f"[PERF] 完成: {step_name} | 耗时: {duration:.6f}s | 开始: {start_time:.6f} | 结束: {end_time:.6f} | 线程: {thread_id} | 元数据: {metadata}")

            return duration

    def record_step(self, step_name: str, metadata: Dict[str, Any] = None):
        """记录单个步骤（自动计时）"""
        operation_id = self.start_timer(step_name, metadata)
        time.sleep(0)  # 确保时间戳有微小差异
        return self.end_timer(operation_id)

    def get_records_by_step(self, step_name: str) -> List[PerformanceRecord]:
        """获取指定步骤的所有记录"""
        with self._lock:
            return [record for record in self._records if record.step_name == step_name]

    def get_summary_by_step(self, step_name: str) -> Optional[PerformanceSummary]:
        """获取指定步骤的性能汇总"""
        records = self.get_records_by_step(step_name)

        if not records:
            return None

        durations = [record.duration for record in records]

        return PerformanceSummary(
            step_name=step_name,
            total_count=len(records),
            total_duration=sum(durations),
            avg_duration=statistics.mean(durations),
            min_duration=min(durations),
            max_duration=max(durations),
            median_duration=statistics.median(durations),
            p95_duration=statistics.quantiles(durations, n=100)[94] if len(durations) >= 100 else max(durations),
            p99_duration=statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations)
        )

    def get_all_summaries(self) -> List[PerformanceSummary]:
        """获取所有步骤的性能汇总"""
        step_names = set(record.step_name for record in self._records)
        summaries = []

        for step_name in step_names:
            summary = self.get_summary_by_step(step_name)
            if summary:
                summaries.append(summary)

        return sorted(summaries, key=lambda x: x.avg_duration, reverse=True)

    def analyze_pipeline(self, pipeline_steps: List[str]) -> Dict[str, Any]:
        """分析完整流水线性能"""
        with self._lock:
            # 按线程ID分组记录
            thread_records = defaultdict(list)
            for record in self._records:
                if record.step_name in pipeline_steps:
                    thread_records[record.thread_id].append(record)

        analysis: Dict[str, Any] = {
            'total_sessions': len(thread_records),
            'pipeline_steps': pipeline_steps,
            'sessions': []
        }

        for thread_id, records in thread_records.items():
            # 按时间排序
            records.sort(key=lambda x: x.start_time)

            session_analysis: Dict[str, Any] = {
                'thread_id': thread_id,
                'step_count': len(records),
                'total_duration': records[-1].end_time - records[0].start_time if records else 0,
                'steps': {}
            }

            step_times: Dict[str, List[float]] = {}
            for record in records:
                if record.step_name not in step_times:
                    step_times[record.step_name] = []
                step_times[record.step_name].append(record.duration)

            for step in pipeline_steps:
                if step in step_times:
                    durations = step_times[step]
                    session_analysis['steps'][step] = {
                        'count': len(durations),
                        'total': sum(durations),
                        'avg': statistics.mean(durations),
                        'min': min(durations),
                        'max': max(durations)
                    }

            analysis['sessions'].append(session_analysis)

        return analysis

    def export_performance_report(self) -> str:
        """导出性能报告"""
        if not self._records:
            return "暂无性能数据"

        report = []
        report.append("=" * 80)
        report.append("🔍 语音识别系统性能分析报告")
        report.append("=" * 80)
        report.append(f"分析时间段: {self._session_start_time:.6f} - {time.time():.6f}")
        report.append(f"总操作数: {len(self._records)}")
        report.append("")

        # 各步骤性能汇总
        summaries = self.get_all_summaries()
        if summaries:
            report.append("📊 各步骤性能汇总 (按平均耗时排序):")
            report.append("-" * 80)
            report.append(f"{'步骤名称':<20} {'次数':<6} {'平均耗时':<12} {'最小耗时':<12} {'最大耗时':<12} {'P95耗时':<12}")
            report.append("-" * 80)

            for summary in summaries:
                report.append(f"{summary.step_name:<20} {summary.total_count:<6} {summary.avg_duration:<12.6f} "
                             f"{summary.min_duration:<12.6f} {summary.max_duration:<12.6f} {summary.p95_duration:<12.6f}")

            report.append("")

        # 瓶颈分析
        if summaries:
            bottleneck = summaries[0]  # 平均耗时最长的步骤
            report.append("⚠️ 性能瓶颈分析:")
            report.append(f"最耗时步骤: {bottleneck.step_name} (平均: {bottleneck.avg_duration:.6f}s)")
            report.append(f"最大耗时: {bottleneck.max_duration:.6f}s")
            report.append(f"出现次数: {bottleneck.total_count}")
            report.append("")

        # 流水线分析
        pipeline_steps = [
            '音频输入',
            '音频处理',
            '语音识别',
            '文本处理',
            'Excel写入'
        ]

        pipeline_analysis = self.analyze_pipeline(pipeline_steps)
        if pipeline_analysis['sessions']:
            report.append("🔄 流水线分析:")
            report.append(f"完整会话数: {pipeline_analysis['total_sessions']}")

            # 计算平均流水线时间
            total_durations = [session['total_duration'] for session in pipeline_analysis['sessions'] if session['total_duration'] > 0]
            if total_durations:
                report.append(f"平均端到端耗时: {statistics.mean(total_durations):.6f}s")
                report.append(f"最快端到端耗时: {min(total_durations):.6f}s")
                report.append(f"最慢端到端耗时: {max(total_durations):.6f}s")
            report.append("")

        # 优化建议
        report.append("💡 优化建议:")

        if summaries:
            # 找出最耗时的几个步骤
            slowest_steps = summaries[:3]
            for i, summary in enumerate(slowest_steps, 1):
                if summary.avg_duration > 1.0:  # 超过1秒的步骤需要优化
                    report.append(f"{i}. 优化 {summary.step_name} (当前平均: {summary.avg_duration:.6f}s)")

        # 基于步骤给出具体建议
        step_names = [s.step_name for s in summaries]
        if '语音识别' in step_names:
            speech_summary = next(s for s in summaries if s.step_name == '语音识别')
            if speech_summary.avg_duration > 2.0:
                report.append("• 考虑使用更小的chunk_size或调整模型参数")
                report.append("• 检查FunASR模型配置，优化batch_size")

        if 'Excel写入' in step_names:
            excel_summary = next(s for s in summaries if s.step_name == 'Excel写入')
            if excel_summary.avg_duration > 0.1:
                report.append("• 优化Excel写入频率，考虑批量写入")
                report.append("• 检查Excel文件大小，考虑分文件存储")

        if '文本处理' in step_names:
            text_summary = next(s for s in summaries if s.step_name == '文本处理')
            if text_summary.avg_duration > 0.01:
                report.append("• 简化文本处理算法")
                report.append("• 缓存常用转换结果")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def clear_records(self):
        """清空所有记录"""
        with self._lock:
            self._records.clear()
            self._current_operations.clear()
            self._session_start_time = time.time()

    def enable(self):
        """启用性能监控"""
        self._enabled = True
        logger.info("性能监控已启用")

    def disable(self):
        """禁用性能监控"""
        self._enabled = False
        logger.info("性能监控已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

# 装饰器版本，用于函数计时
def performance_step(step_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = step_name or func.__name__
            operation_id = performance_monitor.start_timer(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                    performance_monitor.end_timer(operation_id, {
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    })
        return wrapper
    return decorator

# 上下文管理器版本
class PerformanceStep:
    """性能监控上下文管理器"""

    def __init__(self, step_name: str, metadata: Dict[str, Any] = None):
        self.step_name = step_name
        self.metadata = metadata or {}
        self.operation_id = None

    def __enter__(self):
        self.operation_id = performance_monitor.start_timer(self.step_name, self.metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        metadata = self.metadata.copy()
        if exc_type:
            metadata['error'] = str(exc_type.__name__)
            metadata['error_message'] = str(exc_val)

        performance_monitor.end_timer(self.operation_id, metadata)