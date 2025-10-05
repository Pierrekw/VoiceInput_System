# -*- coding: utf-8 -*-
"""
依赖注入容器核心实现

提供完整的依赖注入功能，包括服务注册、解析、生命周期管理等。
"""

from __future__ import annotations
from typing import Any, Dict, List, Type, TypeVar, Optional, Callable, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ForwardRef
    DIContainerRef = ForwardRef('DIContainer')
else:
    DIContainerRef = None
from uuid import uuid4
import threading
import weakref
from contextlib import contextmanager

from .service_registry import ServiceRegistry, ServiceDescriptor, ServiceLifetime
from .service_factory import (
    ServiceFactory, ReflectionFactory, DelegateFactory,
    InstanceFactory, SingletonFactory, ScopedFactory,
    create_reflection_factory, create_singleton_factory, create_scoped_factory
)
from .exceptions import (
    DIContainerError, ServiceNotRegisteredError, CircularDependencyError,
    ServiceCreationError, ContainerDisposedError, InvalidScopeError
)

T = TypeVar('T')


class DIScope:
    """
    依赖注入作用域

    管理作用域内的服务实例生命周期。
    """

    def __init__(self, scope_id: str, container: 'DIContainer'):
        """
        初始化作用域

        Args:
            scope_id: 作用域ID
            container: 父容器
        """
        self.scope_id = scope_id
        self.container = weakref.ref(container)
        self._scoped_instances: Dict[Type, Any] = {}
        self._disposed = False

    def get_scoped_instance(self, service_type: Type[T]) -> Optional[T]:
        """
        获取作用域内的实例

        Args:
            service_type: 服务类型

        Returns:
            Optional[T]: 实例，如果不存在则返回None
        """
        return self._scoped_instances.get(service_type)

    def set_scoped_instance(self, service_type: Type[T], instance: T) -> None:
        """
        设置作用域内的实例

        Args:
            service_type: 服务类型
            instance: 实例
        """
        if not self._disposed:
            self._scoped_instances[service_type] = instance

    def dispose(self) -> None:
        """释放作用域资源"""
        if not self._disposed:
            # 清理作用域内实例
            for instance in self._scoped_instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception:
                        pass  # 忽略清理过程中的异常

            self._scoped_instances.clear()
            self._disposed = True

    @property
    def is_disposed(self) -> bool:
        """检查是否已释放"""
        return self._disposed


class DIContainer:
    """
    依赖注入容器

    核心容器类，提供服务注册、解析、生命周期管理等功能。
    """

    def __init__(self):
        """初始化依赖注入容器"""
        self._registry = ServiceRegistry()
        self._singleton_instances: Dict[Type, Any] = {}
        self._scoped_factories: Dict[Type, ScopedFactory] = {}
        self._scopes: Dict[str, DIScope] = {}
        self._current_scope: Optional[str] = None
        self._lock = threading.RLock()
        self._disposed = False
        self._resolution_stack: List[Type] = []

        # 容器级别的服务注册
        self._register_container_services()

    def _register_container_services(self) -> None:
        """注册容器级别的服务"""
        # 注册容器自身
        self.register_instance(DIContainer, self)

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """
        注册瞬态服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法

        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        with self._lock:
            self._registry.register_transient(service_type, implementation_type, factory)
        return self

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """
        注册作用域服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法

        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        with self._lock:
            self._registry.register_scoped(service_type, implementation_type, factory)
        return self

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'DIContainer':
        """
        注册单例服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法
            instance: 预创建实例

        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        with self._lock:
            self._registry.register_singleton(service_type, implementation_type, factory, instance)

            # 如果提供了实例，立即缓存
            if instance is not None:
                self._singleton_instances[service_type] = instance

        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """
        注册实例（单例）

        Args:
            service_type: 服务类型
            instance: 实例

        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        return self.register_singleton(service_type, instance=instance)

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[Any], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> 'DIContainer':
        """
        注册工厂方法

        Args:
            service_type: 服务类型
            factory: 工厂方法
            lifetime: 生命周期

        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        with self._lock:
            self._registry.register_factory(service_type, factory, lifetime)
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务

        Args:
            service_type: 服务类型

        Returns:
            T: 服务实例

        Raises:
            ServiceNotRegisteredError: 服务未注册
            ServiceCreationError: 服务创建失败
            CircularDependencyError: 循环依赖
            ContainerDisposedError: 容器已释放
        """
        self._check_disposed()

        with self._lock:
            # 检查循环依赖
            if service_type in self._resolution_stack:
                chain = [t.__name__ for t in self._resolution_stack] + [service_type.__name__]
                raise CircularDependencyError(chain)

            # 获取服务描述符
            descriptor = self._registry.get_descriptor(service_type)
            if descriptor is None:
                raise ServiceNotRegisteredError(service_type.__name__)

            # 检查单例缓存
            if descriptor.is_singleton and service_type in self._singleton_instances:
                return self._singleton_instances[service_type]

            # 检查作用域缓存
            if descriptor.is_scoped and self._current_scope:
                scope = self._scopes.get(self._current_scope)
                if scope:
                    instance = scope.get_scoped_instance(service_type)
                    if instance is not None:
                        return instance

            # 创建新实例
            self._resolution_stack.append(service_type)
            try:
                instance = self._create_instance(descriptor)

                # 缓存实例
                if descriptor.is_singleton:
                    self._singleton_instances[service_type] = instance
                elif descriptor.is_scoped and self._current_scope:
                    scope = self._scopes.get(self._current_scope)
                    if scope:
                        scope.set_scoped_instance(service_type, instance)

                return instance
            finally:
                self._resolution_stack.pop()

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        创建服务实例

        Args:
            descriptor: 服务描述符

        Returns:
            Any: 创建的实例

        Raises:
            ServiceCreationError: 创建失败
        """
        try:
            # 如果有预创建实例，直接返回
            if descriptor.has_instance:
                return descriptor.instance

            # 创建工厂
            factory = self._create_factory(descriptor)

            # 创建实例
            return factory.create(self)

        except Exception as e:
            if isinstance(e, (ServiceCreationError, CircularDependencyError)):
                raise
            raise ServiceCreationError(descriptor.service_type.__name__, e)

    def _create_factory(self, descriptor: ServiceDescriptor) -> ServiceFactory:
        """
        创建服务工厂

        Args:
            descriptor: 服务描述符

        Returns:
            ServiceFactory: 服务工厂
        """
        if descriptor.has_factory:
            factory = DelegateFactory(descriptor.factory)
        elif descriptor.implementation_type:
            factory = ReflectionFactory(descriptor.implementation_type)
        else:
            raise ServiceCreationError(descriptor.service_type.__name__, Exception("No implementation or factory provided"))

        # 根据生命周期包装工厂
        if descriptor.is_singleton:
            return SingletonFactory(factory)
        elif descriptor.is_scoped:
            if descriptor.service_type not in self._scoped_factories:
                self._scoped_factories[descriptor.service_type] = ScopedFactory(factory)
            return self._scoped_factories[descriptor.service_type]
        else:
            return factory

    def is_registered(self, service_type: Type) -> bool:
        """
        检查服务是否已注册

        Args:
            service_type: 服务类型

        Returns:
            bool: 已注册返回True，否则返回False
        """
        with self._lock:
            return self._registry.is_registered(service_type)

    def get_current_scope_id(self) -> Optional[str]:
        """
        获取当前作用域ID

        Returns:
            Optional[str]: 当前作用域ID，如果没有则返回None
        """
        return self._current_scope

    @contextmanager
    def create_scope(self) -> None:
        """
        创建新的作用域

        Returns:
            DIContainer: 当前容器实例（支持链式调用）
        """
        scope_id = str(uuid4())
        scope = DIScope(scope_id, self)

        with self._lock:
            self._scopes[scope_id] = scope
            old_scope = self._current_scope
            self._current_scope = scope_id

        try:
            yield self
        finally:
            with self._lock:
                scope.dispose()
                del self._scopes[scope_id]
                self._current_scope = old_scope

    def clear_scope(self, scope_id: str) -> None:
        """
        清除指定作用域

        Args:
            scope_id: 作用域ID
        """
        with self._lock:
            if scope_id in self._scopes:
                self._scopes[scope_id].dispose()
                del self._scopes[scope_id]

    def get_registered_services(self) -> List[Type]:
        """
        获取所有已注册的服务类型

        Returns:
            List[Type]: 服务类型列表
        """
        with self._lock:
            return list(self._registry.get_all_descriptors().keys())

    def get_service_count(self) -> int:
        """
        获取已注册服务的数量

        Returns:
            int: 服务数量
        """
        with self._lock:
            return len(self._registry)

    def create_child_container(self) -> 'DIContainer':
        """
        创建子容器

        Returns:
            DIContainer: 子容器实例
        """
        child = DIContainer()
        # 复制父容器的注册（但不包括实例）
        with self._lock:
            for descriptor in self._registry:
                if not descriptor.has_instance:  # 不复制实例
                    # 重新注册服务，不复制实例
                    if descriptor.is_singleton:
                        child.register_singleton(
                            descriptor.service_type,
                            descriptor.implementation_type,
                            descriptor.factory
                        )
                    elif descriptor.is_scoped:
                        child.register_scoped(
                            descriptor.service_type,
                            descriptor.implementation_type,
                            descriptor.factory
                        )
                    else:
                        child.register_transient(
                            descriptor.service_type,
                            descriptor.implementation_type,
                            descriptor.factory
                        )
        return child

    def validate_registrations(self) -> List[str]:
        """
        验证所有服务注册

        Returns:
            List[str]: 验证错误列表，如果为空则表示验证通过
        """
        errors = []

        with self._lock:
            for descriptor in self._registry:
                try:
                    # 尝试创建工厂
                    factory = self._create_factory(descriptor)
                    if not factory.can_create():
                        errors.append(f"Service '{descriptor.service_type.__name__}': Factory cannot create instance")
                except Exception as e:
                    errors.append(f"Service '{descriptor.service_type.__name__}': {str(e)}")

        return errors

    def _check_disposed(self) -> None:
        """检查容器是否已释放"""
        if self._disposed:
            raise ContainerDisposedError()

    def dispose(self) -> None:
        """释放容器资源"""
        with self._lock:
            if not self._disposed:
                # 释放所有作用域
                for scope in self._scopes.values():
                    scope.dispose()
                self._scopes.clear()

                # 清理单例实例
                for instance in self._singleton_instances.values():
                    if hasattr(instance, 'dispose'):
                        try:
                            instance.dispose()
                        except Exception:
                            pass  # 忽略清理过程中的异常

                self._singleton_instances.clear()
                self._scoped_factories.clear()
                self._registry.clear()
                self._disposed = True

    @property
    def is_disposed(self) -> bool:
        """检查容器是否已释放"""
        return self._disposed

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.dispose()

    def __repr__(self) -> str:
        return f"DIContainer(services={len(self._registry)}, scopes={len(self._scopes)})"