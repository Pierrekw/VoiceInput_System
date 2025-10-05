# -*- coding: utf-8 -*-
"""
性能对比测试套件

对比原始同步系统和新异步系统的性能指标。
"""

import sys
import os
import time
import asyncio
import statistics
import threading
import psutil
import gc
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置所有指标"""
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.cpu_usage = []
        self.response_times = []
        self.throughput_samples = []
        self.error_count = 0
        self.success_count = 0

    def start_monitoring(self):
        """开始性能监控"""
        self.start_time = time.time()
        self.reset()

        # 启动资源监控线程
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止性能监控"""
        self.end_time = time.time()
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1)

    def _monitor_resources(self):
        """监控系统资源使用"""
        process = psutil.Process()

        while self.monitoring:
            try:
                # 内存使用率
                memory_percent = process.memory_percent()
                self.memory_usage.append(memory_percent)

                # CPU使用率
                cpu_percent = process.cpu_percent()
                self.cpu_usage.append(cpu_percent)

                time.sleep(0.1)  # 每100ms采样一次
            except Exception:
                break

    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.response_times.append(response_time)

    def record_success(self):
        """记录成功操作"""
        self.success_count += 1

    def record_error(self):
        """记录错误操作"""
        self.error_count += 1

    def record_throughput(self, operations_per_second: float):
        """记录吞吐量"""
        self.throughput_samples.append(operations_per_second)

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0

        return {
            'duration': duration,
            'total_operations': self.success_count + self.error_count,
            'success_rate': self.success_count / max(1, self.success_count + self.error_count),
            'avg_response_time': statistics.mean(self.response_times) if self.response_times else 0,
            'median_response_time': statistics.median(self.response_times) if self.response_times else 0,
            'p95_response_time': self._percentile(self.response_times, 95) if self.response_times else 0,
            'p99_response_time': self._percentile(self.response_times, 99) if self.response_times else 0,
            'avg_memory_usage': statistics.mean(self.memory_usage) if self.memory_usage else 0,
            'max_memory_usage': max(self.memory_usage) if self.memory_usage else 0,
            'avg_cpu_usage': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            'max_cpu_usage': max(self.cpu_usage) if self.cpu_usage else 0,
            'avg_throughput': statistics.mean(self.throughput_samples) if self.throughput_samples else 0,
            'peak_throughput': max(self.throughput_samples) if self.throughput_samples else 0,
            'error_rate': self.error_count / max(1, self.success_count + self.error_count)
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class SyncSystemTest:
    """原始同步系统测试"""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    def setup(self):
        """设置测试环境"""
        try:
            from audio_capture_v import AudioCapture
            from excel_exporter import ExcelExporter
            from main import VoiceInputSystem

            self.audio_capture = AudioCapture()
            self.excel_exporter = ExcelExporter()
            self.voice_system = VoiceInputSystem()

            return True
        except Exception as e:
            print(f"同步系统设置失败: {e}")
            return False

    def test_audio_processing_performance(self, duration: float = 10.0) -> Dict[str, Any]:
        """测试音频处理性能"""
        print(f"测试同步系统音频处理性能 ({duration}秒)...")

        self.metrics.start_monitoring()
        start_time = time.time()

        try:
            # 模拟音频数据处理
            test_texts = [
                "温度二十五点五度",
                "压力一百二十千帕",
                "流量三点一四立方米每小时",
                "深度零点八米",
                "重量两千克",
                "速度三十公里每小时"
            ]

            operation_count = 0
            while time.time() - start_time < duration:
                for text in test_texts:
                    op_start = time.time()

                    try:
                        # 模拟音频处理流程
                        result = self.audio_capture.filtered_callback(text)

                        op_end = time.time()
                        self.metrics.record_response_time(op_end - op_start)
                        self.metrics.record_success()
                        operation_count += 1

                    except Exception as e:
                        self.metrics.record_error()
                        print(f"处理失败: {e}")

                # 模拟处理延迟
                time.sleep(0.01)

            # 计算吞吐量
            actual_duration = time.time() - start_time
            throughput = operation_count / actual_duration
            self.metrics.record_throughput(throughput)

        finally:
            self.metrics.stop_monitoring()

        return self.metrics.get_summary()

    def test_concurrent_performance(self, thread_count: int = 4, duration: float = 5.0) -> Dict[str, Any]:
        """测试并发性能"""
        print(f"测试同步系统并发性能 ({thread_count}线程, {duration}秒)...")

        self.metrics.start_monitoring()
        start_time = time.time()

        def worker_thread():
            """工作线程"""
            test_texts = ["温度二十五点五度", "压力一百二十千帕", "流量三点一四"]

            while time.time() - start_time < duration:
                for text in test_texts:
                    op_start = time.time()

                    try:
                        self.audio_capture.filtered_callback(text)
                        op_end = time.time()
                        self.metrics.record_response_time(op_end - op_start)
                        self.metrics.record_success()
                    except Exception:
                        self.metrics.record_error()

                time.sleep(0.01)

        try:
            # 启动多个线程
            threads = []
            for _ in range(thread_count):
                thread = threading.Thread(target=worker_thread)
                thread.start()
                threads.append(thread)

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 计算总吞吐量
            actual_duration = time.time() - start_time
            total_operations = self.metrics.success_count + self.metrics.error_count
            throughput = total_operations / actual_duration
            self.metrics.record_throughput(throughput)

        finally:
            self.metrics.stop_monitoring()

        return self.metrics.get_summary()


class AsyncSystemTest:
    """新异步系统测试"""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    async def setup(self):
        """设置测试环境"""
        try:
            from events.event_bus import AsyncEventBus
            from events.event_types import AudioDataReceivedEvent
            from events.system_coordinator import SystemCoordinator

            self.event_bus = AsyncEventBus()
            await self.event_bus.start()

            self.coordinator = SystemCoordinator(self.event_bus)
            await self.coordinator.start()

            return True
        except Exception as e:
            print(f"异步系统设置失败: {e}")
            return False

    async def cleanup(self):
        """清理测试环境"""
        try:
            if hasattr(self, 'coordinator'):
                await self.coordinator.stop()
            if hasattr(self, 'event_bus'):
                await self.event_bus.stop()
        except Exception:
            pass

    async def test_event_processing_performance(self, duration: float = 10.0) -> Dict[str, Any]:
        """测试事件处理性能"""
        print(f"测试异步系统事件处理性能 ({duration}秒)...")

        self.metrics.start_monitoring()
        start_time = time.time()

        try:
            # 创建事件处理器
            processed_events = []

            async def event_handler(event):
                processed_events.append(event)

            await self.event_bus.subscribe(AudioDataReceivedEvent, event_handler)

            # 生成测试事件
            test_data = [
                b"mock_audio_data_1",
                b"mock_audio_data_2",
                b"mock_audio_data_3",
                b"mock_audio_data_4",
                b"mock_audio_data_5"
            ]

            event_count = 0
            while time.time() - start_time < duration:
                for i, data in enumerate(test_data):
                    op_start = time.time()

                    try:
                        event = AudioDataReceivedEvent(
                            source="PerformanceTest",
                            stream_id="perf_test_stream",
                            audio_data=data,
                            size=len(data),
                            sequence_number=event_count + i
                        )

                        await self.event_bus.publish(event)

                        op_end = time.time()
                        self.metrics.record_response_time(op_end - op_start)
                        self.metrics.record_success()
                        event_count += 1

                    except Exception as e:
                        self.metrics.record_error()
                        print(f"事件发布失败: {e}")

                # 模拟处理延迟
                await asyncio.sleep(0.001)

            # 等待事件处理完成
            await asyncio.sleep(0.1)

            # 计算吞吐量
            actual_duration = time.time() - start_time
            throughput = event_count / actual_duration
            self.metrics.record_throughput(throughput)

        finally:
            self.metrics.stop_monitoring()

        return self.metrics.get_summary()

    async def test_concurrent_performance(self, concurrent_tasks: int = 10, duration: float = 5.0) -> Dict[str, Any]:
        """测试并发性能"""
        print(f"测试异步系统并发性能 ({concurrent_tasks}任务, {duration}秒)...")

        self.metrics.start_monitoring()
        start_time = time.time()

        async def event_producer(task_id: int):
            """事件生产者任务"""
            test_data = [f"task_{task_id}_data_{i}".encode() for i in range(5)]

            while time.time() - start_time < duration:
                for i, data in enumerate(test_data):
                    op_start = time.time()

                    try:
                        event = AudioDataReceivedEvent(
                            source=f"Task{task_id}",
                            stream_id=f"stream_{task_id}",
                            audio_data=data,
                            size=len(data),
                            sequence_number=i
                        )

                        await self.event_bus.publish(event)

                        op_end = time.time()
                        self.metrics.record_response_time(op_end - op_start)
                        self.metrics.record_success()

                    except Exception:
                        self.metrics.record_error()

                await asyncio.sleep(0.001)

        try:
            # 启动多个并发任务
            tasks = []
            for task_id in range(concurrent_tasks):
                task = asyncio.create_task(event_producer(task_id))
                tasks.append(task)

            # 等待所有任务完成
            await asyncio.gather(*tasks)

            # 计算总吞吐量
            actual_duration = time.time() - start_time
            total_operations = self.metrics.success_count + self.metrics.error_count
            throughput = total_operations / actual_duration
            self.metrics.record_throughput(throughput)

        finally:
            self.metrics.stop_monitoring()

        return self.metrics.get_summary()


class PerformanceComparison:
    """性能对比测试主类"""

    def __init__(self):
        self.results = {}
        self.timestamp = datetime.now().isoformat()

    async def run_full_comparison(self) -> Dict[str, Any]:
        """运行完整性能对比"""
        print("=" * 60)
        print("🚀 性能对比测试开始")
        print("=" * 60)

        # 强制垃圾回收
        gc.collect()

        # 测试原始同步系统
        print("\n📊 测试原始同步系统...")
        sync_test = SyncSystemTest()

        if sync_test.setup():
            sync_results = {
                'single_thread': sync_test.test_audio_processing_performance(duration=10.0),
                'multi_thread': sync_test.test_concurrent_performance(thread_count=4, duration=5.0)
            }
            self.results['sync_system'] = sync_results
        else:
            print("❌ 同步系统设置失败，跳过测试")
            self.results['sync_system'] = None

        # 清理内存
        del sync_test
        gc.collect()

        # 测试新异步系统
        print("\n⚡ 测试新异步系统...")
        async_test = AsyncSystemTest()

        if await async_test.setup():
            async_results = {
                'single_task': await async_test.test_event_processing_performance(duration=10.0),
                'multi_task': await async_test.test_concurrent_performance(concurrent_tasks=10, duration=5.0)
            }
            self.results['async_system'] = async_results

            await async_test.cleanup()
        else:
            print("❌ 异步系统设置失败，跳过测试")
            self.results['async_system'] = None

        # 清理内存
        del async_test
        gc.collect()

        # 生成对比报告
        comparison_report = self._generate_comparison_report()

        print("\n" + "=" * 60)
        print("✅ 性能对比测试完成")
        print("=" * 60)

        return {
            'timestamp': self.timestamp,
            'results': self.results,
            'comparison': comparison_report
        }

    def _generate_comparison_report(self) -> Dict[str, Any]:
        """生成对比报告"""
        if not self.results.get('sync_system') or not self.results.get('async_system'):
            return {'error': '缺少测试数据'}

        sync_single = self.results['sync_system']['single_thread']
        async_single = self.results['async_system']['single_task']

        sync_multi = self.results['sync_system']['multi_thread']
        async_multi = self.results['async_system']['multi_task']

        return {
            'single_thread_comparison': {
                'sync_avg_response_time': sync_single['avg_response_time'],
                'async_avg_response_time': async_single['avg_response_time'],
                'response_time_improvement': ((sync_single['avg_response_time'] - async_single['avg_response_time']) / sync_single['avg_response_time'] * 100) if sync_single['avg_response_time'] > 0 else 0,
                'sync_throughput': sync_single['avg_throughput'],
                'async_throughput': async_single['avg_throughput'],
                'throughput_improvement': ((async_single['avg_throughput'] - sync_single['avg_throughput']) / sync_single['avg_throughput'] * 100) if sync_single['avg_throughput'] > 0 else 0,
                'sync_memory_usage': sync_single['avg_memory_usage'],
                'async_memory_usage': async_single['avg_memory_usage'],
                'memory_efficiency': ((sync_single['avg_memory_usage'] - async_single['avg_memory_usage']) / sync_single['avg_memory_usage'] * 100) if sync_single['avg_memory_usage'] > 0 else 0
            },
            'concurrent_comparison': {
                'sync_throughput': sync_multi['avg_throughput'],
                'async_throughput': async_multi['avg_throughput'],
                'concurrent_improvement': ((async_multi['avg_throughput'] - sync_multi['avg_throughput']) / sync_multi['avg_throughput'] * 100) if sync_multi['avg_throughput'] > 0 else 0,
                'sync_success_rate': sync_multi['success_rate'],
                'async_success_rate': async_multi['success_rate'],
                'reliability_improvement': async_multi['success_rate'] - sync_multi['success_rate']
            },
            'summary': {
                'overall_performance_gain': self._calculate_overall_gain(),
                'recommendation': self._get_recommendation()
            }
        }

    def _calculate_overall_gain(self) -> float:
        """计算总体性能提升"""
        try:
            sync_throughput = self.results['sync_system']['single_thread']['avg_throughput']
            async_throughput = self.results['async_system']['single_task']['avg_throughput']

            if sync_throughput > 0:
                return ((async_throughput - sync_throughput) / sync_throughput) * 100
            return 0
        except:
            return 0

    def _get_recommendation(self) -> str:
        """获取迁移建议"""
        overall_gain = self._calculate_overall_gain()

        if overall_gain > 50:
            return "强烈推荐迁移到异步系统，性能提升显著"
        elif overall_gain > 20:
            return "推荐迁移到异步系统，有明显性能优势"
        elif overall_gain > 0:
            return "可以考虑迁移到异步系统，有适度性能提升"
        else:
            return "建议保持当前系统，异步系统优势不明显"

    def save_results(self, filename: str = None) -> str:
        """保存测试结果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_comparison_{timestamp}.json"

        filepath = os.path.join("tests", "results", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': self.timestamp,
                'results': self.results,
                'comparison': self._generate_comparison_report()
            }, f, indent=2, ensure_ascii=False)

        return filepath


async def run_performance_comparison():
    """运行性能对比测试的主函数"""
    comparison = PerformanceComparison()

    try:
        results = await comparison.run_full_comparison()

        # 打印关键结果
        print("\n📈 性能对比结果:")
        if 'comparison' in results and 'summary' in results['comparison']:
            summary = results['comparison']['summary']
            print(f"  总体性能提升: {summary['overall_performance_gain']:.2f}%")
            print(f"  建议: {summary['recommendation']}")

        # 保存结果
        saved_file = comparison.save_results()
        print(f"\n💾 详细结果已保存到: {saved_file}")

        return results

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行性能对比测试
    results = asyncio.run(run_performance_comparison())