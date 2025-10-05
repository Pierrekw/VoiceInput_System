# -*- coding: utf-8 -*-
"""
事件总线实现

提供异步事件发布、订阅和分发功能。
"""

import asyncio
import logging
import time
import weakref
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from collections import defaultdict
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .base_event import BaseEvent, EventPriority
from .event_handler import EventHandler

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """事件订阅信息"""
    event_type: Type[BaseEvent]
    handler: EventHandler
    filter_func: Optional[Callable[[BaseEvent], bool]] = None
    priority: int = 0
    enabled: bool = True


class EventBusMetrics:
    """事件总线指标"""

    def __init__(self):
        """初始化指标"""
        self.events_published = 0
        self.events_processed = 0
        self.events_failed = 0
        self.subscriptions_count = 0
        self.start_time = time.time()
        self._event_type_counts: Dict[str, int] = defaultdict(int)
        self._handler_times: List[float] = []

    def record_event_published(self, event_type: str):
        """记录事件发布"""
        self.events_published += 1
        self._event_type_counts[event_type] += 1

    def record_event_processed(self, handle_time: float):
        """记录事件处理"""
        self.events_processed += 1
        self._handler_times.append(handle_time)

        # 保持最近1000次的处理时间
        if len(self._handler_times) > 1000:
            self._handler_times = self._handler_times[-1000:]

    def record_event_failed(self):
        """记录事件失败"""
        self.events_failed += 1

    def record_subscription_added(self):
        """记录订阅添加"""
        self.subscriptions_count += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        avg_handle_time = sum(self._handler_times) / max(1, len(self._handler_times))
        success_rate = (self.events_processed / max(1, self.events_published)) * 100

        return {
            "uptime": uptime,
            "events_published": self.events_published,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "subscriptions_count": self.subscriptions_count,
            "success_rate": success_rate,
            "avg_handle_time": avg_handle_time,
            "throughput": self.events_published / max(1, uptime),
            "event_type_counts": dict(self._event_type_counts)
        }


class AsyncEventBus:
    """异步事件总线"""

    def __init__(self, max_concurrent_handlers: int = 100):
        """
        初始化异步事件总线

        Args:
            max_concurrent_handlers: 最大并发处理器数量
        """
        self._subscriptions: Dict[Type[BaseEvent], List[EventSubscription]] = defaultdict(list)
        self._global_subscriptions: List[EventSubscription] = []
        self._semaphore = asyncio.Semaphore(max_concurrent_handlers)
        self._metrics = EventBusMetrics()
        self._running = False
        self._event_queue = asyncio.Queue()
        self._dispatcher_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """启动事件总线"""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        self._dispatcher_task = asyncio.create_task(self._dispatcher())
        logger.info("🚀 事件总线已启动")

    async def stop(self) -> None:
        """停止事件总线"""
        if not self._running:
            return

        logger.info("🛑 正在停止事件总线...")
        self._running = False
        self._shutdown_event.set()

        if self._dispatcher_task:
            await self._dispatcher_task

        # 清空队列
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info("✅ 事件总线已停止")

    @property
    def is_running(self) -> bool:
        """检查事件总线是否运行中"""
        return self._running

    async def subscribe(
        self,
        event_type: Type[BaseEvent],
        handler: Union[EventHandler, Callable],
        filter_func: Optional[Callable[[BaseEvent], bool]] = None,
        priority: int = 0
    ) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器或处理函数
            filter_func: 事件过滤函数
            priority: 订阅优先级

        Returns:
            str: 订阅ID
        """
        # 如果是普通函数，包装为FunctionEventHandler
        if not hasattr(handler, 'safe_handle') and callable(handler):
            from .event_handler import FunctionEventHandler
            handler = FunctionEventHandler(handler)

        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            filter_func=filter_func,
            priority=priority
        )

        # 按优先级插入
        subscriptions = self._subscriptions[event_type]
        insert_pos = 0
        for i, sub in enumerate(subscriptions):
            if sub.priority < priority:
                insert_pos = i
                break
            insert_pos = i + 1

        subscriptions.insert(insert_pos, subscription)
        self._metrics.record_subscription_added()

        handler_name = getattr(handler, '__name__', str(handler))
        logger.debug(f"📝 已订阅事件类型: {event_type.__name__} (处理器: {handler_name})")
        return str(id(subscription))

    async def subscribe_all(
        self,
        handler: EventHandler,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None,
        priority: int = 0
    ) -> str:
        """
        订阅所有事件

        Args:
            handler: 事件处理器
            filter_func: 事件过滤函数
            priority: 订阅优先级

        Returns:
            str: 订阅ID
        """
        subscription = EventSubscription(
            event_type=BaseEvent,  # 基类表示所有事件
            handler=handler,
            filter_func=filter_func,
            priority=priority
        )

        self._global_subscriptions.append(subscription)
        self._metrics.record_subscription_added()

        handler_name = getattr(handler, '__name__', str(handler))
        logger.debug(f"📝 已订阅所有事件 (处理器: {handler_name})")
        return str(id(subscription))

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            subscription_id: 订阅ID

        Returns:
            bool: 是否成功取消
        """
        # 在类型特定的订阅中查找
        for event_type, subscriptions in self._subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if str(id(subscription)) == subscription_id:
                    subscriptions.pop(i)
                    logger.debug(f"🗑️ 已取消订阅: {event_type.__name__}")
                    return True

        # 在全局订阅中查找
        for i, subscription in enumerate(self._global_subscriptions):
            if str(id(subscription)) == subscription_id:
                self._global_subscriptions.pop(i)
                logger.debug(f"🗑️ 已取消全局订阅")
                return True

        return False

    async def publish(self, event: BaseEvent) -> None:
        """
        发布事件

        Args:
            event: 要发布的事件
        """
        if not self._running:
            logger.warning("⚠️ 事件总线未运行，丢弃事件: {event}")
            return

        try:
            await self._event_queue.put(event)
            self._metrics.record_event_published(event.event_type)
            logger.debug(f"📤 事件已发布: {event.event_type} (ID: {event.event_id[:8]})")
        except Exception as e:
            logger.error(f"❌ 发布事件失败: {e}")
            self._metrics.record_event_failed()

    async def publish_and_wait(self, event: BaseEvent, timeout: Optional[float] = None) -> None:
        """
        发布事件并等待处理完成

        Args:
            event: 要发布的事件
            timeout: 等待超时时间
        """
        if not self._running:
            await self.publish(event)
            return

        # 创建完成信号
        completed = asyncio.Event()
        original_handle = event.__class__.handle

        async def wrapped_handler():
            try:
                await original_handle(event)
            finally:
                completed.set()

        # 临时替换处理器方法
        event.__class__.handle = wrapped_handler

        try:
            await self.publish(event)
            if timeout:
                await asyncio.wait_for(completed.wait(), timeout=timeout)
            else:
                await completed.wait()
        finally:
            # 恢复原始处理器方法
            event.__class__.handle = original_handle

    @asynccontextmanager
    async def event_context(self, event: BaseEvent):
        """
        事件上下文管理器

        Args:
            event: 事件对象
        """
        await self.publish(event)
        try:
            yield event
        finally:
            # 事件后处理
            pass

    async def _dispatcher(self) -> None:
        """事件分发器"""
        logger.debug("🚀 事件分发器已启动")

        while self._running:
            try:
                # 等待事件或关闭信号
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(self._event_queue.get()),
                        asyncio.create_task(self._shutdown_event.wait())
                    ],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # 检查是否是关闭事件
                if self._shutdown_event.is_set():
                    break

                # 获取事件
                for task in done:
                    if not task.cancelled():
                        event = task.result()
                        await self._dispatch_event(event)
                        break

            except Exception as e:
                logger.error(f"❌ 事件分发器异常: {e}")

        logger.debug("🛑 事件分发器已停止")

    async def _dispatch_event(self, event: BaseEvent) -> None:
        """分发单个事件"""
        start_time = time.time()

        try:
            # 获取所有相关的订阅
            subscriptions = self._get_subscriptions_for_event(event)

            if not subscriptions:
                logger.debug(f"⚠️ 没有处理器订阅事件: {event.event_type}")
                return

            # 并发处理事件
            handler_tasks = []
            for subscription in subscriptions:
                if subscription.enabled and (not subscription.filter_func or subscription.filter_func(event)):
                    task = asyncio.create_task(
                        self._handle_subscription(subscription, event)
                    )
                    handler_tasks.append(task)

            if handler_tasks:
                # 等待所有处理器完成
                results = await asyncio.gather(*handler_tasks, return_exceptions=True)
                
                # 检查是否有处理器失败
                for result in results:
                    if isinstance(result, Exception):
                        self._metrics.record_event_failed()

            handle_time = time.time() - start_time
            self._metrics.record_event_processed(handle_time)

        except Exception as e:
            logger.error(f"❌ 分发事件失败: {e}")
            self._metrics.record_event_failed()

    async def _handle_subscription(self, subscription: EventSubscription, event: BaseEvent) -> None:
        """处理单个订阅"""
        async with self._semaphore:
            try:
                await subscription.handler.safe_handle(event)
            except Exception as e:
                handler_name = getattr(subscription.handler, '__name__', str(subscription.handler))
                logger.error(f"❌ 处理订阅失败 ({handler_name}): {e}")

    def _get_subscriptions_for_event(self, event: BaseEvent) -> List[EventSubscription]:
        """获取事件相关的订阅"""
        subscriptions = []

        # 添加类型特定订阅
        if type(event) in self._subscriptions:
            subscriptions.extend(self._subscriptions[type(event)])

        # 添加全局订阅
        subscriptions.extend(self._global_subscriptions)

        # 按优先级排序
        subscriptions.sort(key=lambda s: s.priority, reverse=True)

        return subscriptions

    def get_metrics(self) -> Dict[str, Any]:
        """获取事件总线指标"""
        return self._metrics.get_statistics()

    def get_subscription_count(self) -> int:
        """获取订阅数量"""
        count = len(self._global_subscriptions)
        for subscriptions in self._subscriptions.values():
            count += len(subscriptions)
        return count

    def get_event_type_stats(self) -> Dict[str, int]:
        """获取事件类型统计"""
        stats = {}
        for event_type, subscriptions in self._subscriptions.items():
            stats[event_type.__name__] = len(subscriptions)
        return stats

    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """
        批量发布事件

        Args:
            events: 事件列表
        """
        if not events:
            return

        for event in events:
            await self.publish(event)

        logger.debug(f"📤 批量发布 {len(events)} 个事件")


# 同步适配器（向后兼容）

class EventBus:
    """同步事件总线（AsyncEventBus的同步适配器）"""

    def __init__(self, max_concurrent_handlers: int = 100):
        """
        初始化同步事件总线

        Args:
            max_concurrent_handlers: 最大并发处理器数量
        """
        self._async_bus = AsyncEventBus(max_concurrent_handlers)
        self._loop = None
        self._ensure_loop()

    def _ensure_loop(self):
        """确保事件循环存在"""
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def start(self):
        """启动事件总线"""
        self._ensure_loop()
        if not self._loop.is_running():
            self._loop.run_until_complete(self._async_bus.start())
        else:
            asyncio.create_task(self._async_bus.start())

    def stop(self):
        """停止事件总线"""
        self._ensure_loop()
        if self._loop.is_running():
            asyncio.create_task(self._async_bus.stop())
        else:
            self._loop.run_until_complete(self._async_bus.stop())

    def publish(self, event: BaseEvent) -> None:
        """发布事件（同步）"""
        self._ensure_loop()
        if self._loop.is_running():
            asyncio.create_task(self._async_bus.publish(event))
        else:
            self._loop.run_until_complete(self._async_bus.publish(event))

    def subscribe(self, event_type: Type[BaseEvent], handler: Union[EventHandler, Callable], **kwargs) -> str:
        """订阅事件（同步）"""
        self._ensure_loop()
        if self._loop.is_running():
            return asyncio.create_task(self._async_bus.subscribe(event_type, handler, **kwargs)).result()
        else:
            return self._loop.run_until_complete(self._async_bus.subscribe(event_type, handler, **kwargs))

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅（同步）"""
        self._ensure_loop()
        if self._loop.is_running():
            return asyncio.create_task(self._async_bus.unsubscribe(subscription_id)).result()
        else:
            return self._loop.run_until_complete(self._async_bus.unsubscribe(subscription_id))

    @property
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._async_bus.is_running

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return self._async_bus.get_metrics()

    def get_subscription_count(self) -> int:
        """获取订阅数量"""
        return self._async_bus.get_subscription_count()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._async_bus.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._async_bus.stop()


# 全局事件总线实例
_global_event_bus = EventBus()


def get_global_event_bus() -> EventBus:
    """获取全局事件总线"""
    return _global_event_bus


def start_global_event_bus() -> None:
    """启动全局事件总线"""
    _global_event_bus.start()


def stop_global_event_bus() -> None:
    """停止全局事件总线"""
    _global_event_bus.stop()