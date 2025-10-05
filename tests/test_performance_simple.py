# -*- coding: utf-8 -*-
"""
简化性能对比测试

不依赖复杂的外部库，专注于核心性能指标对比。
"""

import sys
import os
import time
import asyncio
import statistics
import threading
import gc
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class SimplePerformanceTest:
    """简化的性能测试类"""

    def __init__(self, name: str):
        self.name = name
        self.results = []

    def measure_operation_time(self, operation, *args, **kwargs):
        """测量单个操作时间"""
        start_time = time.perf_counter()
        try:
            result = operation(*args, **kwargs)
            end_time = time.perf_counter()
            return {
                'success': True,
                'duration': end_time - start_time,
                'result': result
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                'success': False,
                'duration': end_time - start_time,
                'error': str(e)
            }

    def run_batch_test(self, operation, iterations: int = 1000, *args, **kwargs) -> Dict[str, Any]:
        """运行批量测试"""
        print(f"运行 {self.name} 批量测试 ({iterations} 次迭代)...")

        durations = []
        successes = 0
        errors = 0

        for i in range(iterations):
            result = self.measure_operation_time(operation, *args, **kwargs)

            if result['success']:
                successes += 1
                durations.append(result['duration'])
            else:
                errors += 1

            # 每100次迭代显示进度
            if (i + 1) % 100 == 0:
                print(f"  进度: {i + 1}/{iterations}")

        if durations:
            return {
                'name': self.name,
                'iterations': iterations,
                'successes': successes,
                'errors': errors,
                'success_rate': successes / iterations,
                'avg_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p95_duration': sorted(durations)[int(len(durations) * 0.95)],
                'throughput': successes / sum(durations) if durations else 0
            }
        else:
            return {
                'name': self.name,
                'iterations': iterations,
                'successes': 0,
                'errors': errors,
                'success_rate': 0,
                'error': '所有操作都失败了'
            }


class SyncSystemPerformanceTest:
    """同步系统性能测试"""

    def __init__(self):
        self.test_name = "同步系统"

    def test_number_extraction(self):
        """测试数字提取性能"""
        try:
            from audio_capture_v import extract_measurements

            # 测试数据
            test_texts = [
                "温度二十五点五度",
                "压力一百二十千帕",
                "流量三点一四立方米每小时",
                "深度零点八米",
                "重量两千克",
                "速度三十公里每小时",
                "长度一百二十三点四五厘米",
                "电压二百二十伏",
                "功率五千瓦",
                "频率五十赫兹"
            ]

            def extract_operation():
                # 模拟随机选择文本进行提取
                import random
                text = random.choice(test_texts)
                return extract_measurements(text)

            test = SimplePerformanceTest(f"{self.test_name} - 数字提取")
            return test.run_batch_test(extract_operation, iterations=1000)

        except Exception as e:
            return {'name': f"{self.test_name} - 数字提取", 'error': str(e)}

    def test_callback_processing(self):
        """测试回调处理性能"""
        try:
            from audio_capture_v import AudioCapture

            capture = AudioCapture()
            test_texts = [
                "测量值为十二点五",
                "温度三十度",
                "压力一百千帕"
            ]

            def callback_operation():
                import random
                text = random.choice(test_texts)
                return capture.filtered_callback(text)

            test = SimplePerformanceTest(f"{self.test_name} - 回调处理")
            return test.run_batch_test(callback_operation, iterations=500)

        except Exception as e:
            return {'name': f"{self.test_name} - 回调处理", 'error': str(e)}


class AsyncSystemPerformanceTest:
    """异步系统性能测试"""

    def __init__(self):
        self.test_name = "异步系统"

    async def test_event_publishing(self):
        """测试事件发布性能"""
        try:
            from events.event_bus import AsyncEventBus
            from events.event_types import AudioDataReceivedEvent

            event_bus = AsyncEventBus()
            await event_bus.start()

            def event_operation():
                # 这个需要在异步上下文中运行
                pass

            # 创建异步测试函数
            async def async_event_test():
                test_data = [f"test_data_{i}".encode() for i in range(10)]
                durations = []
                successes = 0
                errors = 0

                for i in range(100):  # 较少的迭代次数，因为异步操作较重
                    start_time = time.perf_counter()

                    try:
                        data = test_data[i % len(test_data)]
                        event = AudioDataReceivedEvent(
                            source="PerfTest",
                            stream_id="perf_stream",
                            audio_data=data,
                            size=len(data),
                            sequence_number=i
                        )

                        await event_bus.publish(event)

                        end_time = time.perf_counter()
                        durations.append(end_time - start_time)
                        successes += 1

                    except Exception:
                        errors += 1

                await event_bus.stop()

                if durations:
                    return {
                        'name': f"{self.test_name} - 事件发布",
                        'iterations': 100,
                        'successes': successes,
                        'errors': errors,
                        'success_rate': successes / 100,
                        'avg_duration': statistics.mean(durations),
                        'throughput': successes / sum(durations) if durations else 0
                    }
                else:
                    return {
                        'name': f"{self.test_name} - 事件发布",
                        'iterations': 100,
                        'successes': 0,
                        'errors': errors,
                        'success_rate': 0
                    }

            return await async_event_test()

        except Exception as e:
            return {'name': f"{self.test_name} - 事件发布", 'error': str(e)}


class ConcurrencyTest:
    """并发性能测试"""

    def test_sync_concurrency(self, thread_count: int = 4):
        """测试同步系统并发性能"""
        print(f"测试同步系统并发性能 ({thread_count} 线程)...")

        try:
            from audio_capture_v import extract_measurements

            test_texts = [
                "温度二十五点五度",
                "压力一百二十千帕",
                "流量三点一四"
            ]

            results = []
            threads = []

            def worker():
                """工作线程"""
                thread_results = []
                for _ in range(100):  # 每个线程处理100次
                    start_time = time.perf_counter()
                    try:
                        import random
                        text = random.choice(test_texts)
                        extract_measurements(text)
                        end_time = time.perf_counter()
                        thread_results.append(end_time - start_time)
                    except Exception:
                        pass
                results.extend(thread_results)

            # 启动线程
            start_time = time.perf_counter()
            for _ in range(thread_count):
                thread = threading.Thread(target=worker)
                thread.start()
                threads.append(thread)

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            end_time = time.perf_counter()
            total_duration = end_time - start_time

            if results:
                return {
                    'name': f"同步并发 ({thread_count} 线程)",
                    'total_operations': len(results),
                    'total_duration': total_duration,
                    'avg_duration': statistics.mean(results),
                    'throughput': len(results) / total_duration
                }
            else:
                return {'name': f"同步并发 ({thread_count} 线程)", 'error': '无成功操作'}

        except Exception as e:
            return {'name': f"同步并发 ({thread_count} 线程)", 'error': str(e)}

    async def test_async_concurrency(self, task_count: int = 10):
        """测试异步系统并发性能"""
        print(f"测试异步系统并发性能 ({task_count} 任务)...")

        try:
            from events.event_bus import AsyncEventBus
            from events.event_types import AudioDataReceivedEvent

            event_bus = AsyncEventBus()
            await event_bus.start()

            async def worker(task_id: int):
                """异步工作任务"""
                task_results = []
                for i in range(50):  # 每个任务处理50次
                    start_time = time.perf_counter()
                    try:
                        data = f"task_{task_id}_data_{i}".encode()
                        event = AudioDataReceivedEvent(
                            source=f"Task{task_id}",
                            stream_id=f"stream_{task_id}",
                            audio_data=data,
                            size=len(data),
                            sequence_number=i
                        )

                        await event_bus.publish(event)

                        end_time = time.perf_counter()
                        task_results.append(end_time - start_time)

                    except Exception:
                        pass

                    await asyncio.sleep(0.001)  # 小延迟避免过度占用CPU

                return task_results

            # 启动异步任务
            start_time = time.perf_counter()
            tasks = [worker(i) for i in range(task_count)]
            task_results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            # 合并所有结果
            all_results = []
            for results in task_results:
                all_results.extend(results)

            total_duration = end_time - start_time

            await event_bus.stop()

            if all_results:
                return {
                    'name': f"异步并发 ({task_count} 任务)",
                    'total_operations': len(all_results),
                    'total_duration': total_duration,
                    'avg_duration': statistics.mean(all_results),
                    'throughput': len(all_results) / total_duration
                }
            else:
                return {'name': f"异步并发 ({task_count} 任务)", 'error': '无成功操作'}

        except Exception as e:
            return {'name': f"异步并发 ({task_count} 任务)", 'error': str(e)}


async def run_simple_performance_comparison():
    """运行简化性能对比测试"""
    print("=" * 60)
    print("简化性能对比测试开始")
    print("=" * 60)

    results = {
        'timestamp': datetime.now().isoformat(),
        'sync_tests': {},
        'async_tests': {},
        'concurrency_tests': {}
    }

    # 测试同步系统
    print("\n测试同步系统...")
    sync_test = SyncSystemPerformanceTest()

    # 数字提取测试
    sync_number_result = sync_test.test_number_extraction()
    results['sync_tests']['number_extraction'] = sync_number_result
    if 'error' not in sync_number_result:
        print(f"  [OK] 数字提取: 吞吐量 {sync_number_result.get('throughput', 0):.2f} ops/sec")
    else:
        print(f"  [ERROR] 数字提取: {sync_number_result['error']}")

    # 回调处理测试
    sync_callback_result = sync_test.test_callback_processing()
    results['sync_tests']['callback_processing'] = sync_callback_result
    if 'error' not in sync_callback_result:
        print(f"  [OK] 回调处理: 吞吐量 {sync_callback_result.get('throughput', 0):.2f} ops/sec")
    else:
        print(f"  [ERROR] 回调处理: {sync_callback_result['error']}")

    # 清理内存
    gc.collect()

    # 测试异步系统
    print("\n测试异步系统...")
    async_test = AsyncSystemPerformanceTest()

    # 事件发布测试
    async_event_result = await async_test.test_event_publishing()
    results['async_tests']['event_publishing'] = async_event_result
    if 'error' not in async_event_result:
        print(f"  [OK] 事件发布: 吞吐量 {async_event_result.get('throughput', 0):.2f} ops/sec")
    else:
        print(f"  [ERROR] 事件发布: {async_event_result['error']}")

    # 清理内存
    gc.collect()

    # 并发性能测试
    print("\n测试并发性能...")
    concurrency_test = ConcurrencyTest()

    # 同步并发
    sync_concurrency_result = concurrency_test.test_sync_concurrency(thread_count=4)
    results['concurrency_tests']['sync_concurrency'] = sync_concurrency_result
    if 'error' not in sync_concurrency_result:
        print(f"  [OK] 同步并发: 吞吐量 {sync_concurrency_result.get('throughput', 0):.2f} ops/sec")
    else:
        print(f"  [ERROR] 同步并发: {sync_concurrency_result['error']}")

    # 异步并发
    async_concurrency_result = await concurrency_test.test_async_concurrency(task_count=10)
    results['concurrency_tests']['async_concurrency'] = async_concurrency_result
    if 'error' not in async_concurrency_result:
        print(f"  [OK] 异步并发: 吞吐量 {async_concurrency_result.get('throughput', 0):.2f} ops/sec")
    else:
        print(f"  [ERROR] 异步并发: {async_concurrency_result['error']}")

    # 生成对比报告
    print("\n" + "=" * 60)
    print("性能对比结果:")
    print("=" * 60)

    # 简单的性能对比
    sync_throughput = sync_number_result.get('throughput', 0)
    async_throughput = async_event_result.get('throughput', 0)

    if sync_throughput > 0 and async_throughput > 0:
        improvement = ((async_throughput - sync_throughput) / sync_throughput) * 100
        print(f"单线程性能对比:")
        print(f"  同步系统吞吐量: {sync_throughput:.2f} ops/sec")
        print(f"  异步系统吞吐量: {async_throughput:.2f} ops/sec")
        print(f"  性能变化: {improvement:+.2f}%")

    sync_conc_throughput = sync_concurrency_result.get('throughput', 0)
    async_conc_throughput = async_concurrency_result.get('throughput', 0)

    if sync_conc_throughput > 0 and async_conc_throughput > 0:
        conc_improvement = ((async_conc_throughput - sync_conc_throughput) / sync_conc_throughput) * 100
        print(f"\n并发性能对比:")
        print(f"  同步并发吞吐量: {sync_conc_throughput:.2f} ops/sec")
        print(f"  异步并发吞吐量: {async_conc_throughput:.2f} ops/sec")
        print(f"  性能变化: {conc_improvement:+.2f}%")

    # 给出建议
    if improvement > 20:
        recommendation = "强烈推荐迁移到异步系统"
    elif improvement > 0:
        recommendation = "建议考虑迁移到异步系统"
    else:
        recommendation = "保持当前系统，异步优势不明显"

    print(f"\n建议: {recommendation}")

    return results


def run_simple_performance_tests_sync():
    """同步运行简化性能测试"""
    try:
        # 检查是否在异步环境中
        try:
            asyncio.get_running_loop()
            # 在异步环境中，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_simple_performance_comparison())
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，直接运行
            return asyncio.run(run_simple_performance_comparison())
    except Exception as e:
        print(f"运行性能测试时发生异常: {e}")
        return None


if __name__ == "__main__":
    # 运行简化性能对比测试
    results = run_simple_performance_tests_sync()