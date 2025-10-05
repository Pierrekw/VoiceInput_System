# -*- coding: utf-8 -*-
"""
事件处理器定义

定义事件处理器基类和相关装饰器。
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps

from .base_event import BaseEvent

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """事件处理器抽象基类"""

    def __init__(self, name: Optional[str] = None):
        """
        初始化事件处理器

        Args:
            name: 处理器名称
        """
        self.name = name or self.__class__.__name__
        self.enabled = True
        self.handle_count = 0
        self.error_count = 0
        self.total_handle_time = 0.0
        self.max_handle_time = 0.0

    @abstractmethod
    async def handle(self, event: BaseEvent) -> None:
        """
        处理事件

        Args:
            event: 要处理的事件
        """
        pass

    async def safe_handle(self, event: BaseEvent) -> bool:
        """
        安全地处理事件（包含错误处理）

        Args:
            event: 要处理的事件

        Returns:
            bool: 处理是否成功
        """
        if not self.enabled:
            return False

        start_time = time.time()
        success = True

        try:
            # 先增加总处理次数
            self.handle_count += 1
            await self.handle(event)

        except Exception as e:
            self.error_count += 1
            success = False
            logger.error(f"❌ 事件处理器 '{self.name}' 处理事件失败: {e}", exc_info=True)

        finally:
            handle_time = time.time() - start_time
            self.total_handle_time += handle_time
            self.max_handle_time = max(self.max_handle_time, handle_time)

        return success

    def get_statistics(self) -> dict:
        """获取处理器统计信息"""
        avg_handle_time = self.total_handle_time / max(1, self.handle_count)
        # 计算成功率：(总处理次数 - 错误次数) / 总处理次数
        success_rate = (self.handle_count - self.error_count) / max(1, self.handle_count) if self.handle_count > 0 else 0

        return {
            "name": self.name,
            "enabled": self.enabled,
            "handle_count": self.handle_count,  # 总处理次数
            "error_count": self.error_count,    # 失败次数
            "success_rate": success_rate,       # 成功率
            "avg_handle_time": avg_handle_time,
            "max_handle_time": self.max_handle_time,
            "total_handle_time": self.total_handle_time
        }

    def enable(self) -> None:
        """启用处理器"""
        self.enabled = True

    def disable(self) -> None:
        """禁用处理器"""
        self.enabled = False

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.handle_count = 0
        self.error_count = 0
        self.total_handle_time = 0.0
        self.max_handle_time = 0.0


class FunctionEventHandler(EventHandler):
    """函数事件处理器"""

    def __init__(self, handler_func: Callable, name: Optional[str] = None):
        """
        初始化函数事件处理器

        Args:
            handler_func: 处理函数
            name: 处理器名称
        """
        super().__init__(name or handler_func.__name__)
        self.handler_func = handler_func

    async def handle(self, event: BaseEvent) -> None:
        """处理事件"""
        if asyncio.iscoroutinefunction(self.handler_func):
            await self.handler_func(event)
        else:
            self.handler_func(event)


class ConditionalEventHandler(EventHandler):
    """条件事件处理器"""

    def __init__(
        self,
        condition: Callable[[BaseEvent], bool],
        handler: EventHandler,
        name: Optional[str] = None
    ):
        """
        初始化条件事件处理器

        Args:
            condition: 条件判断函数
            handler: 被包装的处理器
            name: 处理器名称
        """
        super().__init__(name or f"Conditional({handler.name})")
        self.condition = condition
        self.handler = handler

    async def handle(self, event: BaseEvent) -> None:
        """处理事件（带条件检查）"""
        if self.condition(event):
            await self.handler.handle(event)


class BatchEventHandler(EventHandler):
    """批量事件处理器"""

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 1.0,
        name: Optional[str] = None
    ):
        """
        初始化批量事件处理器

        Args:
            batch_size: 批量大小
            batch_timeout: 批量超时时间
            name: 处理器名称
        """
        super().__init__(name)
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._event_queue: List[BaseEvent] = []
        self._last_batch_time = 0.0
        self._batch_timer_task: Optional[asyncio.Task] = None

    async def handle(self, event: BaseEvent) -> None:
        """处理事件（添加到批量队列）"""
        self._event_queue.append(event)

        # 检查是否需要处理批量
        if len(self._event_queue) >= self.batch_size:
            await self._process_batch()
        elif not self._batch_timer_task:
            # 启动批量定时器
            self._batch_timer_task = asyncio.create_task(self._batch_timer())

    async def _batch_timer(self) -> None:
        """批量定时器"""
        await asyncio.sleep(self.batch_timeout)
        if self._event_queue:
            await self._process_batch()
        self._batch_timer_task = None

    async def _process_batch(self) -> None:
        """处理批量事件"""
        if not self._event_queue:
            return

        batch = self._event_queue.copy()
        self._event_queue.clear()
        self._last_batch_time = time.time()

        await self.handle_batch(batch)

    @abstractmethod
    async def handle_batch(self, events: List[BaseEvent]) -> None:
        """处理批量事件"""
        pass


class RetryEventHandler(EventHandler):
    """重试事件处理器"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        name: Optional[str] = None
    ):
        """
        初始化重试事件处理器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            backoff_factor: 退避因子
            name: 处理器名称
        """
        super().__init__(name)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor

    async def handle_with_retry(self, event: BaseEvent) -> None:
        """带重试的事件处理"""
        last_exception = None
        current_delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                await self.handle(event)
                return  # 成功则返回

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"⚠️ 事件处理失败，{current_delay}s后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff_factor
                else:
                    logger.error(f"❌ 事件处理重试{self.max_retries}次后仍失败: {e}")

        # 重试失败，重新抛出最后的异常
        if last_exception:
            raise last_exception

    async def safe_handle(self, event: BaseEvent) -> bool:
        """安全的重试处理"""
        try:
            await self.handle_with_retry(event)
            self.handle_count += 1
            return True
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ 重试处理器 '{self.name}' 最终失败: {e}")
            return False


# 装饰器

def event_handler(event_types: Optional[Union[Type[BaseEvent], List[Type[BaseEvent]]]] = None, name: Optional[str] = None):
    """
    事件处理器装饰器

    Args:
        event_types: 支持的事件类型
        name: 处理器名称
    """
    def decorator(func: Callable) -> EventHandler:
        handler = FunctionEventHandler(func, name)
        if event_types:
            # 这里可以添加事件类型注册逻辑
            pass
        return handler

    return decorator


def conditional_event_handler(condition: Callable[[BaseEvent], bool]):
    """
    条件事件处理器装饰器

    Args:
        condition: 条件判断函数
    """
    def decorator(handler_func: Callable) -> EventHandler:
        base_handler = FunctionEventHandler(handler_func)
        return ConditionalEventHandler(condition, base_handler)

    return decorator


def retry_event_handler(max_retries: int = 3, retry_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    重试事件处理器装饰器

    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        backoff_factor: 退避因子
    """
    def decorator(handler_func: Callable) -> EventHandler:
        class DecoratedRetryHandler(RetryEventHandler):
            def __init__(self):
                super().__init__(max_retries, retry_delay, backoff_factor, handler_func.__name__)

            async def handle(self, event: BaseEvent) -> None:
                if asyncio.iscoroutinefunction(handler_func):
                    await handler_func(event)
                else:
                    handler_func(event)

        return DecoratedRetryHandler()

    return decorator


def batch_event_handler(batch_size: int = 10, batch_timeout: float = 1.0):
    """
    批量事件处理器装饰器

    Args:
        batch_size: 批量大小
        batch_timeout: 批量超时时间
    """
    def decorator(handler_func: Callable) -> EventHandler:
        class DecoratedBatchHandler(BatchEventHandler):
            def __init__(self):
                super().__init__(batch_size, batch_timeout, handler_func.__name__)

            async def handle_batch(self, events: List[BaseEvent]) -> None:
                if asyncio.iscoroutinefunction(handler_func):
                    await handler_func(events)
                else:
                    handler_func(events)

        return DecoratedBatchHandler()

    return decorator


# 便捷函数

def create_handler(handler_func: Callable, name: Optional[str] = None) -> EventHandler:
    """创建事件处理器的便捷函数"""
    return FunctionEventHandler(handler_func, name)


def create_conditional_handler(
    condition: Callable[[BaseEvent], bool],
    handler: EventHandler,
    name: Optional[str] = None
) -> ConditionalEventHandler:
    """创建条件事件处理器的便捷函数"""
    return ConditionalEventHandler(condition, handler, name)


# 预定义的通用处理器

class LoggingEventHandler(EventHandler):
    """日志事件处理器"""

    async def handle(self, event: BaseEvent) -> None:
        """记录事件日志"""
        logger.info(f"📝 {event}")

        if event.data:
            logger.debug(f"📄 事件数据: {event.data}")


class MetricsEventHandler(EventHandler):
    """指标事件处理器"""

    def __init__(self, metrics_collector: Optional[Any] = None):
        """
        初始化指标事件处理器

        Args:
            metrics_collector: 指标收集器
        """
        super().__init__("MetricsHandler")
        self.metrics_collector = metrics_collector

    async def handle(self, event: BaseEvent) -> None:
        """收集指标"""
        if self.metrics_collector:
            await self._collect_metrics(event)

    async def _collect_metrics(self, event: BaseEvent) -> None:
        """收集具体指标"""
        # 这里可以实现具体的指标收集逻辑
        pass


class AlertEventHandler(EventHandler):
    """告警事件处理器"""

    def __init__(self, alert_thresholds: Optional[Dict[str, Any]] = None):
        """
        初始化告警事件处理器

        Args:
            alert_thresholds: 告警阈值配置
        """
        super().__init__("AlertHandler")
        self.alert_thresholds = alert_thresholds or {}

    async def handle(self, event: BaseEvent) -> None:
        """处理告警"""
        if event.is_high_priority():
            await self._send_alert(event)

    async def _send_alert(self, event: BaseEvent) -> None:
        """发送告警"""
        logger.warning(f"🚨 高优先级事件告警: {event}")

        # 这里可以实现具体的告警发送逻辑
        # 例如：发送邮件、推送通知等


# 处理器工厂

class EventHandlerFactory:
    """事件处理器工厂"""

    @staticmethod
    def create_logging_handler() -> LoggingEventHandler:
        """创建日志处理器"""
        return LoggingEventHandler()

    @staticmethod
    def create_metrics_handler(metrics_collector: Optional[Any] = None) -> MetricsEventHandler:
        """创建指标处理器"""
        return MetricsEventHandler(metrics_collector)

    @staticmethod
    def create_alert_handler(alert_thresholds: Optional[Dict[str, Any]] = None) -> AlertEventHandler:
        """创建告警处理器"""
        return AlertEventHandler(alert_thresholds)

    @staticmethod
    def create_retry_handler(
        handler_func: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> RetryEventHandler:
        """创建重试处理器"""
        @retry_event_handler(max_retries, retry_delay)
        def wrapper(event: BaseEvent):
            if asyncio.iscoroutinefunction(handler_func):
                return handler_func(event)
            else:
                return handler_func(event)

        # 创建RetryEventHandler实例
        class CustomRetryHandler(RetryEventHandler):
            def __init__(self):
                super().__init__(max_retries, retry_delay)

            async def handle(self, event: BaseEvent) -> None:
                await wrapper(event)

        return CustomRetryHandler()