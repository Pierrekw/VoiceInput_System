# -*- coding: utf-8 -*-
"""
异步系统性能优化模块

提供性能监控、调优和优化功能。
"""

import asyncio
import time
import gc
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import weakref


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    queued_events: int = 0
    avg_response_time: float = 0.0
    throughput: float = 0.0
    timestamp: float = field(default_factory=time.time)


class AsyncPerformanceMonitor:
    """异步性能监控器"""

    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.process = psutil.Process()
        self._lock = asyncio.Lock()

        # 性能优化配置
        self.optimization_settings = {
            'gc_threshold': 100,  # 垃圾回收阈值
            'max_memory_mb': 512,  # 最大内存限制
            'max_active_tasks': 100,  # 最大活跃任务数
            'batch_size': 10,  # 批处理大小
        }

    async def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = await self._collect_metrics()
                async with self._lock:
                    self.metrics_history.append(metrics)
                    # 保留最近1000个指标
                    if len(self.metrics_history) > 1000:
                        self.metrics_history = self.metrics_history[-1000:]

                # 自动优化
                await self._auto_optimize(metrics)

                await asyncio.sleep(self.sample_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"监控错误: {e}")
                await asyncio.sleep(self.sample_interval)

    async def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU使用率
        cpu_percent = self.process.cpu_percent()

        # 内存使用
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()

        # 异步任务统计
        try:
            active_tasks = len(asyncio.all_tasks())
        except:
            active_tasks = 0

        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            active_tasks=active_tasks,
            timestamp=time.time()
        )

    async def _auto_optimize(self, metrics: PerformanceMetrics):
        """自动性能优化"""
        settings = self.optimization_settings

        # 内存优化
        if metrics.memory_mb > settings['max_memory_mb']:
            await self._optimize_memory()

        # 垃圾回收优化
        if len(self.metrics_history) % settings['gc_threshold'] == 0:
            gc.collect()

        # 任务数优化
        if metrics.active_tasks > settings['max_active_tasks']:
            await self._optimize_tasks()

    async def _optimize_memory(self):
        """内存优化"""
        # 强制垃圾回收
        collected = gc.collect()

        # 清理弱引用缓存
        if hasattr(gc, 'get_count'):
            counts = gc.get_count()
            if sum(counts) > 1000:
                gc.collect()

    async def _optimize_tasks(self):
        """任务优化"""
        # 可以在这里实现任务优先级调整
        pass

    def get_recent_metrics(self, count: int = 10) -> List[PerformanceMetrics]:
        """获取最近的性能指标"""
        return self.metrics_history[-count:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}

        recent = self.metrics_history[-10:]  # 最近10个采样点

        return {
            'avg_cpu': sum(m.cpu_percent for m in recent) / len(recent),
            'avg_memory_mb': sum(m.memory_mb for m in recent) / len(recent),
            'avg_memory_percent': sum(m.memory_percent for m in recent) / len(recent),
            'avg_active_tasks': sum(m.active_tasks for m in recent) / len(recent),
            'max_memory_mb': max(m.memory_mb for m in recent),
            'max_cpu_percent': max(m.cpu_percent for m in recent),
            'sample_count': len(recent),
            'monitoring_duration': len(self.metrics_history) * self.sample_interval
        }


class AsyncTaskPool:
    """异步任务池优化器"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks = set()
        self.completed_tasks = 0
        self.failed_tasks = 0

    async def submit_task(self, coro, name: str = None) -> asyncio.Task:
        """提交任务到池中"""
        async def wrapped_task():
            async with self.semaphore:
                try:
                    result = await coro
                    self.completed_tasks += 1
                    return result
                except Exception as e:
                    self.failed_tasks += 1
                    raise e
                finally:
                    # 清理任务引用
                    task = asyncio.current_task()
                    if task in self.active_tasks:
                        self.active_tasks.remove(task)

        task = asyncio.create_task(wrapped_task(), name=name)
        self.active_tasks.add(task)
        return task

    async def wait_for_completion(self, timeout: Optional[float] = None):
        """等待所有任务完成"""
        if self.active_tasks:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks, return_exceptions=True),
                timeout=timeout
            )

    def get_stats(self) -> Dict[str, int]:
        """获取任务池统计"""
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'max_workers': self.max_workers
        }


class BatchProcessor:
    """批处理器优化器"""

    def __init__(self, batch_size: int = 10, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending_items: List[Any] = []
        self.processor: Optional[Callable] = None
        self.flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def set_processor(self, processor: Callable):
        """设置批处理函数"""
        self.processor = processor

    async def add_item(self, item: Any):
        """添加项目到批处理队列"""
        async with self._lock:
            self.pending_items.append(item)

            # 达到批处理大小
            if len(self.pending_items) >= self.batch_size:
                await self._flush_batch()

        # 启动定时刷新任务
        if self.flush_task is None or self.flush_task.done():
            self.flush_task = asyncio.create_task(self._flush_timer())

    async def _flush_timer(self):
        """定时刷新"""
        await asyncio.sleep(self.flush_interval)
        async with self._lock:
            if self.pending_items:
                await self._flush_batch()

    async def _flush_batch(self):
        """刷新批处理"""
        if not self.pending_items or not self.processor:
            return

        batch = self.pending_items.copy()
        self.pending_items.clear()

        try:
            await self.processor(batch)
        except Exception as e:
            print(f"批处理错误: {e}")

    async def flush_now(self):
        """立即刷新所有待处理项目"""
        async with self._lock:
            await self._flush_batch()


class ResourcePool:
    """资源池管理器"""

    def __init__(self, factory: Callable, max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self.available = asyncio.Queue(maxsize=max_size)
        self.in_use = weakref.WeakSet()
        self.created_count = 0

    async def acquire(self) -> Any:
        """获取资源"""
        try:
            # 尝试从可用队列获取
            resource = self.available.get_nowait()
        except asyncio.QueueEmpty:
            # 创建新资源
            if self.created_count < self.max_size:
                resource = await self._create_resource()
            else:
                # 等待资源释放
                resource = await self.available.get()

        self.in_use.add(resource)
        return resource

    async def release(self, resource: Any):
        """释放资源"""
        if resource in self.in_use:
            self.in_use.remove(resource)
            try:
                self.available.put_nowait(resource)
            except asyncio.QueueFull:
                # 池已满，丢弃资源
                pass

    async def _create_resource(self) -> Any:
        """创建新资源"""
        self.created_count += 1
        if asyncio.iscoroutinefunction(self.factory):
            return await self.factory()
        else:
            return self.factory()

    def get_stats(self) -> Dict[str, int]:
        """获取资源池统计"""
        return {
            'created_count': self.created_count,
            'available_count': self.available.qsize(),
            'in_use_count': len(self.in_use),
            'max_size': self.max_size
        }


class AsyncOptimizer:
    """异步系统优化器主类"""

    def __init__(self):
        self.monitor = AsyncPerformanceMonitor()
        self.task_pool = AsyncTaskPool()
        self.batch_processor = BatchProcessor()
        self.resource_pools: Dict[str, ResourcePool] = {}

    async def start(self):
        """启动优化器"""
        await self.monitor.start_monitoring()

    async def stop(self):
        """停止优化器"""
        await self.monitor.stop_monitoring()
        await self.task_pool.wait_for_completion(timeout=5.0)
        await self.batch_processor.flush_now()

    def create_resource_pool(self, name: str, factory: Callable, max_size: int = 10):
        """创建资源池"""
        self.resource_pools[name] = ResourcePool(factory, max_size)

    async def get_resource(self, pool_name: str) -> Any:
        """获取资源池中的资源"""
        if pool_name in self.resource_pools:
            return await self.resource_pools[pool_name].acquire()
        raise ValueError(f"Resource pool '{pool_name}' not found")

    async def release_resource(self, pool_name: str, resource: Any):
        """释放资源回池"""
        if pool_name in self.resource_pools:
            await self.resource_pools[pool_name].release(resource)

    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        return {
            'performance_metrics': self.monitor.get_performance_summary(),
            'task_pool_stats': self.task_pool.get_stats(),
            'resource_pool_stats': {
                name: pool.get_stats()
                for name, pool in self.resource_pools.items()
            }
        }


# 全局优化器实例
_global_optimizer: Optional[AsyncOptimizer] = None

def get_global_optimizer() -> AsyncOptimizer:
    """获取全局优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = AsyncOptimizer()
    return _global_optimizer

async def start_global_optimizer():
    """启动全局优化器"""
    optimizer = get_global_optimizer()
    await optimizer.start()

async def stop_global_optimizer():
    """停止全局优化器"""
    optimizer = get_global_optimizer()
    await optimizer.stop()