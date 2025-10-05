# -*- coding: utf-8 -*-
"""
服务工厂实现

提供不同类型的服务工厂实现，支持服务的创建和管理。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Type, TypeVar, Optional
from inspect import signature, Parameter
import inspect

from .exceptions import ServiceCreationError, CircularDependencyError

T = TypeVar('T')


class ServiceFactory(ABC):
    """
    服务工厂抽象基类

    定义了服务创建的通用接口。
    """

    @abstractmethod
    def create(self, container: 'DIContainer') -> Any:
        """
        创建服务实例

        Args:
            container: 依赖注入容器

        Returns:
            Any: 创建的服务实例
        """
        pass

    @abstractmethod
    def can_create(self) -> bool:
        """
        检查是否可以创建服务

        Returns:
            bool: 可以创建返回True，否则返回False
        """
        pass


class ReflectionFactory(ServiceFactory):
    """
    反射工厂

    使用反射机制自动分析构造函数参数并注入依赖。
    """

    def __init__(self, service_type: Type[T]):
        """
        初始化反射工厂

        Args:
            service_type: 要创建的服务类型
        """
        self.service_type = service_type
        self._constructor = None
        self._parameters = None
        self._analyze_constructor()

    def _analyze_constructor(self) -> None:
        """分析构造函数参数"""
        try:
            self._constructor = self.service_type.__init__
            sig = signature(self._constructor)
            self._parameters = [
                param for param in sig.parameters.values()
                if param.name != 'self' and param.kind == Parameter.POSITIONAL_OR_KEYWORD
            ]
        except Exception as e:
            raise ServiceCreationError(
                self.service_type.__name__,
                Exception(f"Failed to analyze constructor: {e}")
            )

    def create(self, container: 'DIContainer') -> T:
        """
        使用反射创建服务实例

        Args:
            container: 依赖注入容器

        Returns:
            T: 创建的服务实例

        Raises:
            ServiceCreationError: 创建失败
        """
        if not self.can_create():
            raise ServiceCreationError(self.service_type.__name__, Exception("Cannot create service"))

        try:
            # 解析构造函数参数
            args = []
            kwargs = {}

            for param in self._parameters:
                if param.annotation == Parameter.empty:
                    raise ServiceCreationError(
                        self.service_type.__name__,
                        Exception(f"Parameter '{param.name}' has no type annotation")
                    )

                dependency = container.resolve(param.annotation)
                if param.default == Parameter.empty:
                    args.append(dependency)
                else:
                    kwargs[param.name] = dependency

            # 创建实例
            instance = self.service_type(*args, **kwargs)
            return instance

        except Exception as e:
            if isinstance(e, ServiceCreationError):
                raise
            raise ServiceCreationError(self.service_type.__name__, e)

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return self._constructor is not None and self._parameters is not None


class DelegateFactory(ServiceFactory):
    """
    委托工厂

    使用委托函数或lambda表达式创建服务。
    """

    def __init__(self, factory_func: Callable[[Any], T]):
        """
        初始化委托工厂

        Args:
            factory_func: 工厂函数，接受容器参数并返回服务实例
        """
        self.factory_func = factory_func

    def create(self, container: 'DIContainer') -> T:
        """
        使用委托函数创建服务实例

        Args:
            container: 依赖注入容器

        Returns:
            T: 创建的服务实例

        Raises:
            ServiceCreationError: 创建失败
        """
        try:
            return self.factory_func(container)
        except Exception as e:
            raise ServiceCreationError("DelegateFactory", e)

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return callable(self.factory_func)


class InstanceFactory(ServiceFactory):
    """
    实例工厂

    直接返回预创建的实例。
    """

    def __init__(self, instance: T):
        """
        初始化实例工厂

        Args:
            instance: 预创建的实例
        """
        self.instance = instance

    def create(self, container: 'DIContainer') -> T:
        """
        返回预创建的实例

        Args:
            container: 依赖注入容器

        Returns:
            T: 服务实例
        """
        return self.instance

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return self.instance is not None


class SingletonFactory(ServiceFactory):
    """
    单例工厂

    确保只创建一个实例并缓存它。
    """

    def __init__(self, inner_factory: ServiceFactory):
        """
        初始化单例工厂

        Args:
            inner_factory: 内部工厂，用于创建实际实例
        """
        self.inner_factory = inner_factory
        self._instance: Optional[T] = None
        self._created = False

    def create(self, container: 'DIContainer') -> T:
        """
        创建或返回缓存的单例实例

        Args:
            container: 依赖注入容器

        Returns:
            T: 单例实例
        """
        if not self._created:
            self._instance = self.inner_factory.create(container)
            self._created = True
        return self._instance

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return self.inner_factory.can_create()

    def is_created(self) -> bool:
        """检查实例是否已创建"""
        return self._created

    def reset(self) -> None:
        """重置单例状态（主要用于测试）"""
        self._instance = None
        self._created = False


class ScopedFactory(ServiceFactory):
    """
    作用域工厂

    在同一个作用域内返回相同的实例。
    """

    def __init__(self, inner_factory: ServiceFactory):
        """
        初始化作用域工厂

        Args:
            inner_factory: 内部工厂，用于创建实际实例
        """
        self.inner_factory = inner_factory
        self._scoped_instances: Dict[str, Any] = {}

    def create(self, container: 'DIContainer') -> T:
        """
        在作用域内创建或返回缓存实例

        Args:
            container: 依赖注入容器

        Returns:
            T: 作用域实例
        """
        scope_id = container.get_current_scope_id()

        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = self.inner_factory.create(container)

        return self._scoped_instances[scope_id]

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return self.inner_factory.can_create()

    def clear_scope(self, scope_id: str) -> None:
        """清除指定作用域的实例"""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]

    def clear_all_scopes(self) -> None:
        """清除所有作用域的实例"""
        self._scoped_instances.clear()


class FactoryFactory(ServiceFactory):
    """
    工厂工厂

    创建工厂实例而不是服务实例本身。
    """

    def __init__(self, service_factory: ServiceFactory):
        """
        初始化工厂工厂

        Args:
            service_factory: 用于创建实际服务的工厂
        """
        self.service_factory = service_factory

    def create(self, container: 'DIContainer') -> Callable[[], T]:
        """
        创建工厂函数

        Args:
            container: 依赖注入容器

        Returns:
            Callable[[], T]: 工厂函数
        """
        def factory_func() -> T:
            return self.service_factory.create(container)

        return factory_func

    def can_create(self) -> bool:
        """检查是否可以创建服务"""
        return self.service_factory.can_create()


# 工厂创建辅助函数
def create_reflection_factory(service_type: Type[T]) -> ReflectionFactory:
    """
    创建反射工厂

    Args:
        service_type: 服务类型

    Returns:
        ReflectionFactory: 反射工厂实例
    """
    return ReflectionFactory(service_type)


def create_delegate_factory(factory_func: Callable[[Any], T]) -> DelegateFactory:
    """
    创建委托工厂

    Args:
        factory_func: 工厂函数

    Returns:
        DelegateFactory: 委托工厂实例
    """
    return DelegateFactory(factory_func)


def create_instance_factory(instance: T) -> InstanceFactory:
    """
    创建实例工厂

    Args:
        instance: 预创建实例

    Returns:
        InstanceFactory: 实例工厂实例
    """
    return InstanceFactory(instance)


def create_singleton_factory(inner_factory: ServiceFactory) -> SingletonFactory:
    """
    创建单例工厂

    Args:
        inner_factory: 内部工厂

    Returns:
        SingletonFactory: 单例工厂实例
    """
    return SingletonFactory(inner_factory)


def create_scoped_factory(inner_factory: ServiceFactory) -> ScopedFactory:
    """
    创建作用域工厂

    Args:
        inner_factory: 内部工厂

    Returns:
        ScopedFactory: 作用域工厂实例
    """
    return ScopedFactory(inner_factory)