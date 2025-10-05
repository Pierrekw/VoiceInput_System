# -*- coding: utf-8 -*-
"""
系统事件协调器

负责协调系统中各个组件的事件通信和状态同步。
"""

import asyncio
import logging
import time
from typing import Callable, Dict, List, Any, Optional, Set, Type
from collections import defaultdict
from dataclasses import dataclass

from .base_event import BaseEvent, EventPriority
from .event_bus import AsyncEventBus
from .event_handler import EventHandler
from .event_types import (
    ComponentStateChangedEvent, SystemStartedEvent, SystemShutdownEvent,
    ErrorEvent, PerformanceMetricEvent
)

logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """组件信息"""
    name: str
    component_type: str
    state: str
    dependencies: Set[str]
    dependents: Set[str]
    last_activity: float
    health_status: str = "healthy"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SystemCoordinator:
    """系统事件协调器"""

    def __init__(self, event_bus: Optional[AsyncEventBus] = None):
        """
        初始化系统协调器

        Args:
            event_bus: 事件总线实例
        """
        self._event_bus = event_bus or AsyncEventBus()
        self._components: Dict[str, ComponentInfo] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._health_checkers: Dict[str, List[Callable]] = defaultdict(list)
        self._system_state = "initializing"
        self._start_time = time.time()
        self._coordination_handlers: List[EventHandler] = []

    async def start(self) -> None:
        """启动系统协调器"""
        logger.info("🚀 启动系统协调器...")

        try:
            # 启动事件总线
            await self._event_bus.start()

            # 注册协调器事件处理器
            await self._register_coordination_handlers()

            # 更新系统状态
            self._system_state = "running"
            self._start_time = time.time()

            # 发布系统启动事件
            await self._publish_system_started_event()

            logger.info("✅ 系统协调器已启动")

        except Exception as e:
            logger.error(f"❌ 系统协调器启动失败: {e}")
            self._system_state = "error"

    async def stop(self) -> None:
        """停止系统协调器"""
        logger.info("🛑 停止系统协调器...")

        try:
            # 更新系统状态
            self._system_state = "shutting"

            # 发布系统关闭事件
            await self._publish_system_shutdown_event()

            # 等待所有组件停止
            await self._wait_for_components_shutdown()

            # 停止事件总线
            await self._event_bus.stop()

            self._system_state = "stopped"
            logger.info("✅ 系统协调器已停止")

        except Exception as e:
            logger.error(f"❌ 系统协调器停止失败: {e}")

    async def register_component(
        self,
        name: str,
        component_type: str,
        dependencies: Optional[List[str]] = None,
        health_checker: Optional[Callable] = None
    ) -> bool:
        """
        注册组件

        Args:
            name: 组件名称
            component_type: 组件类型
            dependencies: 依赖的组件列表
            health_checker: 健康检查函数

        Returns:
            bool: 注册是否成功
        """
        if name in self._components:
            logger.warning(f"⚠️ 组件 '{name}' 已存在")
            return False

        try:
            # 创建组件信息
            component_info = ComponentInfo(
                name=name,
                component_type=component_type,
                state="registered",
                dependencies=set(dependencies or []),
                dependents=set(),
                last_activity=time.time()
            )

            # 注册组件
            self._components[name] = component_info

            # 更新依赖关系
            for dep in component_info.dependencies:
                if dep in self._components:
                    self._components[dep].dependents.add(name)
                else:
                    logger.warning(f"⚠️ 依赖组件 '{dep}' 未注册")

            # 注册健康检查器
            if health_checker:
                self._health_checkers[name].append(health_checker)

            # 发布组件注册事件
            await self._publish_component_state_changed_event(
                name, "registered", component_type
            )

            logger.info(f"📝 组件已注册: {name} (类型: {component_type})")
            return True

        except Exception as e:
            logger.error(f"❌ 注册组件 '{name}' 失败: {e}")
            return False

    async def unregister_component(self, name: str) -> bool:
        """
        注销组件

        Args:
            name: 组件名称

        Returns:
            bool: 注销是否成功
        """
        if name not in self._components:
            logger.warning(f"⚠️ 组件 '{name}' 不存在")
            return False

        try:
            component_info = self._components[name]

            # 检查依赖关系
            if component_info.dependents:
                logger.warning(f"⚠️ 组件 '{name}' 仍有依赖者: {component_info.dependents}")
                return False

            # 移除依赖关系
            for dep in component_info.dependencies:
                if dep in self._components:
                    self._components[dep].dependents.discard(name)

            # 移除组件
            del self._components[name]
            del self._health_checkers[name]

            # 发布组件注销事件
            await self._publish_component_state_changed_event(
                name, "unregistered", component_info.component_type
            )

            logger.info(f"🗑️ 组件已注销: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ 注销组件 '{name}' 失败: {e}")
            return False

    async def update_component_state(
        self,
        name: str,
        state: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新组件状态

        Args:
            name: 组件名称
            state: 新状态
            metadata: 元数据
        """
        if name not in self._components:
            logger.warning(f"⚠️ 组件 '{name}' 不存在")
            return

        component_info = self._components[name]
        old_state = component_info.state

        # 更新状态
        component_info.state = state
        component_info.last_activity = time.time()
        if metadata:
            component_info.metadata.update(metadata)

        # 发布状态变更事件
        await self._publish_component_state_changed_event(
            name, state, component_info.component_type, old_state
        )

        # 检查是否需要级联停止依赖组件
        if state in ["stopped", "error"]:
            await self._check_dependent_components(name)

    async def add_dependency(self, component: str, dependency: str) -> bool:
        """
        添加依赖关系

        Args:
            component: 组件名称
            dependency: 依赖的组件名称

        Returns:
            bool: 是否成功添加
        """
        if component not in self._components or dependency not in self._components:
            logger.warning(f"⚠️ 组件或依赖不存在: {component} -> {dependency}")
            return False

        if dependency in self._components[component].dependencies:
            logger.debug(f"依赖已存在: {component} -> {dependency}")
            return True

        # 检查循环依赖
        if self._would_create_circular_dependency(component, dependency):
            logger.error(f"❌ 检测到循环依赖: {component} -> {dependency}")
            return False

        # 添加依赖关系
        self._components[component].dependencies.add(dependency)
        self._components[dependency].dependents.add(component)

        logger.debug(f"✅ 添加依赖: {component} -> {dependency}")
        return True

    def _would_create_circular_dependency(self, component: str, dependency: str) -> bool:
        """检查是否会创建循环依赖"""
        visited = set()
        stack = [dependency]

        while stack:
            current = stack.pop()
            if current == component:
                return True
            if current in visited:
                continue
            visited.add(current)

            if current in self._components:
                stack.extend(self._components[current].dependencies)

        return False

    async def check_component_health(self, name: str) -> bool:
        """
        检查组件健康状态

        Args:
            name: 组件名称

        Returns:
            bool: 是否健康
        """
        if name not in self._components:
            return False

        component_info = self._components[name]
        health_status = "healthy"

        # 运行健康检查器
        if name in self._health_checkers:
            for checker in self._health_checkers[name]:
                try:
                    if asyncio.iscoroutinefunction(checker):
                        result = await checker()
                    else:
                        result = checker()

                    if not result:
                        health_status = "unhealthy"
                        break
                except Exception as e:
                    logger.error(f"❌ 健康检查器异常 ({name}): {e}")
                    health_status = "error"
                    break

        # 检查依赖组件健康状态
        for dep in component_info.dependencies:
            if not await self.check_component_health(dep):
                health_status = "dependency_unhealthy"
                break

        # 更新健康状态
        if component_info.health_status != health_status:
            old_status = component_info.health_status
            component_info.health_status = health_status
            logger.info(f"🏥 组件健康状态变更: {name} {old_status} → {health_status}")

        return health_status == "healthy"

    async def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        total_components = len(self._components)
        healthy_components = 0
        unhealthy_components = []

        for name in self._components:
            if await self.check_component_health(name):
                healthy_components += 1
            else:
                unhealthy_components.append(name)

        health_score = (healthy_components / total_components * 100) if total_components > 0 else 0

        return {
            "total_components": total_components,
            "healthy_components": healthy_components,
            "unhealthy_components": unhealthy_components,
            "health_score": health_score,
            "system_state": self._system_state,
            "uptime": time.time() - self._start_time
        }

    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图"""
        return {
            name: list(dependencies)
            for name, dependencies in self._components.items()
        }

    async def get_component_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取组件信息"""
        if name not in self._components:
            return None

        info = self._components[name]
        return {
            "name": info.name,
            "type": info.component_type,
            "state": info.state,
            "health_status": info.health_status,
            "dependencies": list(info.dependencies),
            "dependents": list(info.dependents),
            "last_activity": info.last_activity,
            "metadata": info.metadata
        }

    async def _register_coordination_handlers(self) -> None:
        """注册协调器事件处理器"""
        from .event_handler import EventHandler

        class ComponentStateHandler(EventHandler):
            def __init__(self, coordinator):
                super().__init__("ComponentStateHandler")
                self.coordinator = coordinator

            async def handle(self, event):
                if isinstance(event, ComponentStateChangedEvent):
                    await self.coordinator._handle_component_state_change(event)

        class ErrorHandler(EventHandler):
            def __init__(self, coordinator):
                super().__init__("ErrorHandler")
                self.coordinator = coordinator

            async def handle(self, event):
                if isinstance(event, ErrorEvent):
                    await self.coordinator._handle_system_error(event)

        # 注册处理器
        self._coordination_handlers.append(ComponentStateHandler(self))
        self._coordination_handlers.append(ErrorHandler(self))

        await self._event_bus.subscribe(ComponentStateChangedEvent, ComponentStateHandler(self))
        await self._event_bus.subscribe(ErrorEvent, ErrorHandler(self))

    async def _handle_component_state_change(self, event: ComponentStateChangedEvent) -> None:
        """处理组件状态变更事件"""
        logger.debug(f"🔄 组件状态变更: {event.component} {event.old_state} → {event.new_state}")

        # 检查是否需要启动依赖组件
        if event.new_state == "running":
            await self._start_dependent_components(event.component)

        # 检查是否需要停止依赖组件
        if event.new_state in ["stopped", "error"]:
            await self._check_dependent_components(event.component)

    async def _handle_system_error(self, event: ErrorEvent) -> None:
        """处理系统错误事件"""
        logger.error(f"🚨 系统错误 ({event.component}): {event.error_type}: {event.error_message}")

        # 检查是否需要紧急停止
        if event.priority == EventPriority.CRITICAL:
            logger.critical("🆘 检测到关键错误，准备紧急停止...")
            await self._emergency_shutdown(event.error_message)

    async def _start_dependent_components(self, component: str) -> None:
        """启动依赖组件"""
        if component not in self._components:
            return

        # 这里可以实现依赖组件的自动启动逻辑
        # 目前只记录日志
        for dep in self._components[component].dependents:
            logger.debug(f"🔗 依赖组件 {dep} 可以启动")

    async def _check_dependent_components(self, component: str) -> None:
        """检查并处理依赖组件"""
        if component not in self._components:
            return

        dependents = self._components[component].dependents.copy()
        for dependent in dependents:
            if dependent in self._components:
                component_info = self._components[dependent]
                if component_info.state not in ["stopped", "error"]:
                    logger.info(f"⏹️ 组件 {component} 状态变更，停止依赖组件: {dependent}")
                    await self.update_component_state(dependent, "stopped")

    async def _wait_for_components_shutdown(self) -> None:
        """等待所有组件停止"""
        max_wait_time = 30.0  # 最大等待30秒
        check_interval = 0.5
        waited_time = 0.0

        while waited_time < max_wait_time:
            all_stopped = all(
                info.state in ["stopped", "error"]
                for info in self._components.values()
            )

            if all_stopped:
                break

            await asyncio.sleep(check_interval)
            waited_time += check_interval

        if waited_time >= max_wait_time:
            logger.warning(f"⚠️ 等待组件停止超时 ({max_wait_time}s)")

    async def _emergency_shutdown(self, reason: str) -> None:
        """紧急停止"""
        logger.critical(f"🆘 紧急停止: {reason}")

        # 尝试优雅停止所有组件
        for name in list(self._components.keys()):
            await self.update_component_state(name, "stopped")

        # 设置错误状态
        self._system_state = "emergency_stopped"

    # 事件发布方法

    async def _publish_system_started_event(self) -> None:
        """发布系统启动事件"""
        event = SystemStartedEvent(
            source="SystemCoordinator",
            component="System",
            version="2.0.0",
            startup_time=time.time() - self._start_time
        )
        await self._event_bus.publish(event)

    async def _publish_system_shutdown_event(self) -> None:
        """发布系统关闭事件"""
        event = SystemShutdownEvent(
            source="SystemCoordinator",
            component="System",
            reason="normal",
            shutdown_time=time.time() - self._start_time
        )
        await self._event_bus.publish(event)

    async def _publish_component_state_changed_event(
        self,
        component_name: str,
        new_state: str,
        component_type: str,
        old_state: str = ""
    ) -> None:
        """发布组件状态变更事件"""
        event = ComponentStateChangedEvent(
            source="SystemCoordinator",
            component=component_name,
            old_state=old_state,
            new_state=new_state,
            state_type=component_type
        )
        await self._event_bus.publish(event)

    # 便捷方法

    async def publish_event(self, event: BaseEvent) -> None:
        """发布事件"""
        await self._event_bus.publish(event)

    async def publish_and_wait(self, event: BaseEvent, timeout: Optional[float] = None) -> None:
        """发布事件并等待处理"""
        await self._event_bus.publish_and_wait(event, timeout)


# 全局系统协调器实例
_global_coordinator = SystemCoordinator()


def get_global_coordinator() -> SystemCoordinator:
    """获取全局系统协调器"""
    return _global_coordinator


async def start_global_coordinator() -> None:
    """启动全局系统协调器"""
    await _global_coordinator.start()


async def stop_global_coordinator() -> None:
    """停止全局系统协调器"""
    await _global_coordinator.stop()