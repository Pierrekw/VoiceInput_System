# -*- coding: utf-8 -*-
"""
异步错误处理增强模块

提供异常传播、错误恢复和监控功能。
"""

import asyncio
import logging
import traceback
import time
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import weakref


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"
    IO = "io"
    AUDIO = "audio"
    RECOGNITION = "recognition"
    TTS = "tts"
    SYSTEM = "system"
    USER = "user"
    TIMEOUT = "timeout"


@dataclass
class ErrorInfo:
    """错误信息"""
    exception: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    component: str = ""
    retry_count: int = 0
    resolved: bool = False
    resolution_message: str = ""


class AsyncErrorHandler:
    """异步错误处理器"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.error_history: List[ErrorInfo] = []
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.retry_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
        self.logger = logging.getLogger(__name__)

        # 错误统计
        self.error_stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'errors_by_severity': {severity.value: 0 for severity in ErrorSeverity},
            'errors_by_category': {category.value: 0 for category in ErrorCategory}
        }

    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """注册异常处理器"""
        self.error_handlers[exception_type] = handler

    def register_retry_strategy(self, name: str, strategy: Callable):
        """注册重试策略"""
        self.retry_strategies[name] = strategy

    def get_circuit_breaker(self, name: str, **kwargs) -> 'CircuitBreaker':
        """获取或创建熔断器"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, **kwargs)
        return self.circuit_breakers[name]

    async def handle_error(self, error_info: ErrorInfo) -> bool:
        """处理错误"""
        try:
            # 记录错误
            await self._record_error(error_info)

            # 更新统计
            self._update_stats(error_info)

            # 尝试处理
            handled = await self._try_handle_error(error_info)

            return handled

        except Exception as e:
            self.logger.error(f"错误处理器自身异常: {e}")
            return False

    async def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        self.error_history.append(error_info)

        # 限制历史记录数量
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

        # 记录到日志
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)

        self.logger.log(
            log_level,
            f"错误 [{error_info.severity.value}] {error_info.category.value}: "
            f"{error_info.exception} (组件: {error_info.component})"
        )

    def _update_stats(self, error_info: ErrorInfo):
        """更新错误统计"""
        self.error_stats['total_errors'] += 1
        self.error_stats['errors_by_severity'][error_info.severity.value] += 1
        self.error_stats['errors_by_category'][error_info.category.value] += 1

        if error_info.resolved:
            self.error_stats['resolved_errors'] += 1

    async def _try_handle_error(self, error_info: ErrorInfo) -> bool:
        """尝试处理错误"""
        exception_type = type(error_info.exception)

        # 查找注册的处理器
        for exc_type, handler in self.error_handlers.items():
            if isinstance(error_info.exception, exc_type):
                try:
                    result = await handler(error_info)
                    if result:
                        error_info.resolved = True
                        error_info.resolution_message = f"通过 {handler.__name__} 处理"
                        return True
                except Exception as e:
                    self.logger.error(f"错误处理器 {handler.__name__} 失败: {e}")

        # 默认处理策略
        return await self._default_error_handling(error_info)

    async def _default_error_handling(self, error_info: ErrorInfo) -> bool:
        """默认错误处理策略"""
        # 根据严重程度决定处理方式
        if error_info.severity == ErrorSeverity.CRITICAL:
            # 关键错误：可能需要重启组件
            return await self._handle_critical_error(error_info)
        elif error_info.severity == ErrorSeverity.HIGH:
            # 高级错误：尝试恢复
            return await self._handle_high_severity_error(error_info)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            # 中级错误：记录并继续
            return await self._handle_medium_severity_error(error_info)
        else:
            # 低级错误：仅记录
            return await self._handle_low_severity_error(error_info)

    async def _handle_critical_error(self, error_info: ErrorInfo) -> bool:
        """处理关键错误"""
        self.logger.critical(f"关键错误发生: {error_info.exception}")

        # 可以在这里实现紧急恢复逻辑
        # 例如：重启组件、切换到备用系统等

        return False  # 关键错误通常需要人工干预

    async def _handle_high_severity_error(self, error_info: ErrorInfo) -> bool:
        """处理高级错误"""
        # 尝试重试
        if error_info.retry_count < 3:
            retry_strategy = self.retry_strategies.get(error_info.category.value)
            if retry_strategy:
                try:
                    await retry_strategy(error_info)
                    error_info.resolved = True
                    error_info.resolution_message = "重试成功"
                    return True
                except Exception as e:
                    self.logger.error(f"重试失败: {e}")

        return False

    async def _handle_medium_severity_error(self, error_info: ErrorInfo) -> bool:
        """处理中级错误"""
        # 记录错误，尝试继续运行
        return True

    async def _handle_low_severity_error(self, error_info: ErrorInfo) -> bool:
        """处理低级错误"""
        # 仅记录，不影响系统运行
        return True

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        recent_errors = self.error_history[-10:]  # 最近10个错误

        return {
            'total_errors': self.error_stats['total_errors'],
            'resolved_errors': self.error_stats['resolved_errors'],
            'resolution_rate': (
                self.error_stats['resolved_errors'] / max(1, self.error_stats['total_errors']) * 100
            ),
            'errors_by_severity': self.error_stats['errors_by_severity'].copy(),
            'errors_by_category': self.error_stats['errors_by_category'].copy(),
            'recent_errors': [
                {
                    'exception': str(error.exception),
                    'severity': error.severity.value,
                    'category': error.category.value,
                    'component': error.component,
                    'timestamp': error.timestamp,
                    'resolved': error.resolved
                }
                for error in recent_errors
            ]
        }


class CircuitBreaker:
    """熔断器"""

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: float = 60.0, expected_exception: Type[Exception] = Exception):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f"熔断器 {self.name} 处于开启状态")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = 'CLOSED'

    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class AsyncRetryManager:
    """异步重试管理器"""

    def __init__(self):
        self.retry_strategies = {
            'exponential_backoff': self._exponential_backoff,
            'linear_backoff': self._linear_backoff,
            'fixed_delay': self._fixed_delay,
            'immediate': self._immediate_retry
        }

    def register_strategy(self, name: str, strategy: Callable):
        """注册重试策略"""
        self.retry_strategies[name] = strategy

    async def retry(self, func: Callable, max_attempts: int = 3,
                   strategy: str = 'exponential_backoff',
                   exceptions: tuple = (Exception,), **strategy_kwargs):
        """重试执行函数"""
        last_exception = None

        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except exceptions as e:
                last_exception = e
                if attempt == max_attempts - 1:
                    break

                # 应用重试策略
                if strategy in self.retry_strategies:
                    delay = await self.retry_strategies[strategy](attempt, **strategy_kwargs)
                    if delay > 0:
                        await asyncio.sleep(delay)

        raise last_exception

    async def _exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """指数退避策略"""
        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay

    async def _linear_backoff(self, attempt: int, delay: float = 1.0) -> float:
        """线性退避策略"""
        return delay * (attempt + 1)

    async def _fixed_delay(self, attempt: int, delay: float = 1.0) -> float:
        """固定延迟策略"""
        return delay

    async def _immediate_retry(self, attempt: int) -> float:
        """立即重试策略"""
        return 0


class ErrorContext:
    """错误上下文管理器"""

    def __init__(self, error_handler: AsyncErrorHandler, component: str,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM):
        self.error_handler = error_handler
        self.component = component
        self.severity = severity
        self.category = category

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, Exception):
            error_info = ErrorInfo(
                exception=exc_val,
                severity=self.severity,
                category=self.category,
                component=self.component
            )
            await self.error_handler.handle_error(error_info)
            return True  # 抑制异常
        return False


# 全局错误处理器实例
_global_error_handler: Optional[AsyncErrorHandler] = None
_global_retry_manager: Optional[AsyncRetryManager] = None

def get_global_error_handler() -> AsyncErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = AsyncErrorHandler()
    return _global_error_handler

def get_global_retry_manager() -> AsyncRetryManager:
    """获取全局重试管理器"""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = AsyncRetryManager()
    return _global_retry_manager

async def safe_execute(func: Callable, *args,
                      component: str = "unknown",
                      severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                      category: ErrorCategory = ErrorCategory.SYSTEM,
                      **kwargs):
    """安全执行函数"""
    error_handler = get_global_error_handler()

    async with ErrorContext(error_handler, component, severity, category):
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

async def safe_retry(func: Callable, max_attempts: int = 3,
                    component: str = "unknown",
                    strategy: str = 'exponential_backoff',
                    **strategy_kwargs):
    """安全重试执行"""
    retry_manager = get_global_retry_manager()
    error_handler = get_global_error_handler()

    async def wrapped_func():
        async with ErrorContext(error_handler, component):
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()

    return await retry_manager.retry(
        wrapped_func,
        max_attempts=max_attempts,
        strategy=strategy,
        **strategy_kwargs
    )