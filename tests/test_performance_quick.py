# -*- coding: utf-8 -*-
"""
快速性能对比测试

轻量级测试，快速获得核心性能对比数据。
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


def quick_sync_test():
    """快速同步系统测试"""
    print("测试同步系统...")

    try:
        from audio_capture_v import extract_measurements

        # 测试数据
        test_texts = [
            "温度二十五点五度",
            "压力一百二十千帕",
            "流量三点一四",
            "深度零点八米",
            "重量两千克"
        ]

        # 测试数字提取性能
        durations = []
        start_time = time.perf_counter()

        for i in range(100):  # 减少测试次数
            text_start = time.perf_counter()
            try:
                text = test_texts[i % len(test_texts)]
                result = extract_measurements(text)
                text_end = time.perf_counter()
                durations.append(text_end - text_start)
            except Exception:
                pass

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        if durations:
            return {
                'system': '同步系统',
                'operations': len(durations),
                'total_duration': total_duration,
                'avg_duration': statistics.mean(durations),
                'throughput': len(durations) / total_duration
            }
        else:
            return {'system': '同步系统', 'error': '无成功操作'}

    except Exception as e:
        return {'system': '同步系统', 'error': str(e)}


async def quick_async_test():
    """快速异步系统测试"""
    print("测试异步系统...")

    try:
        from events.event_bus import AsyncEventBus
        from events.event_types import AudioDataReceivedEvent

        event_bus = AsyncEventBus()
        await event_bus.start()

        # 测试事件发布性能
        durations = []
        start_time = time.perf_counter()

        for i in range(50):  # 减少测试次数
            event_start = time.perf_counter()
            try:
                data = f"test_data_{i}".encode()
                event = AudioDataReceivedEvent(
                    source="QuickTest",
                    stream_id="quick_stream",
                    audio_data=data,
                    size=len(data),
                    sequence_number=i
                )

                await event_bus.publish(event)
                event_end = time.perf_counter()
                durations.append(event_end - event_start)

                # 小延迟避免过度占用
                await asyncio.sleep(0.001)

            except Exception:
                pass

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        await event_bus.stop()

        if durations:
            return {
                'system': '异步系统',
                'operations': len(durations),
                'total_duration': total_duration,
                'avg_duration': statistics.mean(durations),
                'throughput': len(durations) / total_duration
            }
        else:
            return {'system': '异步系统', 'error': '无成功操作'}

    except Exception as e:
        return {'system': '异步系统', 'error': str(e)}


def quick_concurrency_test():
    """快速并发测试"""
    print("测试并发性能...")

    results = {}

    # 同步并发测试 (2线程)
    try:
        from audio_capture_v import extract_measurements

        test_texts = ["温度二十五点五度", "压力一百二十", "流量三点一四"]
        sync_results = []

        def sync_worker():
            worker_results = []
            for i in range(25):  # 每线程25次
                start = time.perf_counter()
                try:
                    text = test_texts[i % len(test_texts)]
                    extract_measurements(text)
                    end = time.perf_counter()
                    worker_results.append(end - start)
                except Exception:
                    pass
            return worker_results

        start_time = time.perf_counter()
        threads = []
        for _ in range(2):
            thread = threading.Thread(target=sync_worker)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        end_time = time.perf_counter()

        results['sync_concurrency'] = {
            'system': '同步并发(2线程)',
            'total_duration': end_time - start_time,
            'operations': 50,  # 2线程 * 25次
            'throughput': 50 / (end_time - start_time)
        }

    except Exception as e:
        results['sync_concurrency'] = {'system': '同步并发', 'error': str(e)}

    return results


async def quick_async_concurrency_test():
    """快速异步并发测试"""
    try:
        from events.event_bus import AsyncEventBus
        from events.event_types import AudioDataReceivedEvent

        event_bus = AsyncEventBus()
        await event_bus.start()

        async def async_worker(task_id: int):
            for i in range(15):  # 每任务15次
                data = f"task_{task_id}_data_{i}".encode()
                event = AudioDataReceivedEvent(
                    source=f"Task{task_id}",
                    stream_id=f"stream_{task_id}",
                    audio_data=data,
                    size=len(data),
                    sequence_number=i
                )
                await event_bus.publish(event)
                await asyncio.sleep(0.001)

        start_time = time.perf_counter()
        tasks = [async_worker(i) for i in range(3)]  # 3个异步任务
        await asyncio.gather(*tasks)
        end_time = time.perf_counter()

        await event_bus.stop()

        return {
            'system': '异步并发(3任务)',
            'total_duration': end_time - start_time,
            'operations': 45,  # 3任务 * 15次
            'throughput': 45 / (end_time - start_time)
        }

    except Exception as e:
        return {'system': '异步并发', 'error': str(e)}


async def run_quick_performance_test():
    """运行快速性能对比测试"""
    print("=" * 50)
    print("快速性能对比测试")
    print("=" * 50)

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    # 单线程性能测试
    print("\n单线程性能测试:")
    sync_result = quick_sync_test()
    results['tests']['sync_single'] = sync_result

    if 'error' not in sync_result:
        print(f"  同步系统: {sync_result['throughput']:.2f} ops/sec")
    else:
        print(f"  同步系统: 错误 - {sync_result['error']}")

    # 清理内存
    gc.collect()

    async_result = await quick_async_test()
    results['tests']['async_single'] = async_result

    if 'error' not in async_result:
        print(f"  异步系统: {async_result['throughput']:.2f} ops/sec")
    else:
        print(f"  异步系统: 错误 - {async_result['error']}")

    # 并发性能测试
    print("\n并发性能测试:")
    concurrency_result = quick_concurrency_test()
    results['tests']['sync_concurrency'] = concurrency_result.get('sync_concurrency', {})

    if 'error' not in concurrency_result.get('sync_concurrency', {}):
        print(f"  同步并发: {concurrency_result['sync_concurrency']['throughput']:.2f} ops/sec")
    else:
        print(f"  同步并发: 错误")

    async_concurrency_result = await quick_async_concurrency_test()
    results['tests']['async_concurrency'] = async_concurrency_result

    if 'error' not in async_concurrency_result:
        print(f"  异步并发: {async_concurrency_result['throughput']:.2f} ops/sec")
    else:
        print(f"  异步并发: 错误 - {async_concurrency_result['error']}")

    # 生成对比报告
    print("\n" + "=" * 50)
    print("性能对比结果:")
    print("=" * 50)

    # 单线程对比
    if 'error' not in sync_result and 'error' not in async_result:
        sync_throughput = sync_result['throughput']
        async_throughput = async_result['throughput']

        if sync_throughput > 0:
            improvement = ((async_throughput - sync_throughput) / sync_throughput) * 100
            print(f"单线程性能:")
            print(f"  同步: {sync_throughput:.2f} ops/sec")
            print(f"  异步: {async_throughput:.2f} ops/sec")
            print(f"  变化: {improvement:+.1f}%")

    # 并发对比
    sync_conc = concurrency_result.get('sync_concurrency', {})
    if 'error' not in sync_conc and 'error' not in async_concurrency_result:
        sync_conc_throughput = sync_conc['throughput']
        async_conc_throughput = async_concurrency_result['throughput']

        if sync_conc_throughput > 0:
            conc_improvement = ((async_conc_throughput - sync_conc_throughput) / sync_conc_throughput) * 100
            print(f"\n并发性能:")
            print(f"  同步: {sync_conc_throughput:.2f} ops/sec")
            print(f"  异步: {async_conc_throughput:.2f} ops/sec")
            print(f"  变化: {conc_improvement:+.1f}%")

    # 给出建议
    if 'improvement' in locals() and improvement > 20:
        recommendation = "强烈推荐迁移到异步系统"
    elif 'improvement' in locals() and improvement > 0:
        recommendation = "建议考虑迁移到异步系统"
    else:
        recommendation = "保持当前系统，异步优势不明显"

    print(f"\n建议: {recommendation}")

    return results


def run_quick_performance_test_sync():
    """同步运行快速性能测试"""
    try:
        # 检查是否在异步环境中
        try:
            asyncio.get_running_loop()
            # 在异步环境中，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_quick_performance_test())
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，直接运行
            return asyncio.run(run_quick_performance_test())
    except Exception as e:
        print(f"运行性能测试时发生异常: {e}")
        return None


if __name__ == "__main__":
    # 运行快速性能对比测试
    results = run_quick_performance_test_sync()