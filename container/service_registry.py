# -*- coding: utf-8 -*-
"""
服务注册表和服务描述符

提供服务注册的核心数据结构和枚举类型。
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    TRANSIENT = "transient"     # 每次解析都创建新实例
    SCOPED = "scoped"           # 每个作用域创建一个实例
    SINGLETON = "singleton"     # 整个容器生命周期内只有一个实例


@dataclass
class ServiceDescriptor:
    """
    服务描述符

    描述一个服务的完整信息，包括类型、实现、生命周期等。
    """
    service_type: Type          # 服务接口类型
    implementation_type: Type   # 实现类型
    lifetime: ServiceLifetime   # 生命周期
    factory: Optional[Callable] = None    # 工厂方法
    instance: Optional[Any] = None        # 预创建实例（仅用于单例）
    dependencies: List[Type] = None       # 依赖类型列表

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    @property
    def has_factory(self) -> bool:
        """是否有工厂方法"""
        return self.factory is not None

    @property
    def has_instance(self) -> bool:
        """是否有预创建实例"""
        return self.instance is not None

    @property
    def is_singleton(self) -> bool:
        """是否为单例模式"""
        return self.lifetime == ServiceLifetime.SINGLETON

    @property
    def is_transient(self) -> bool:
        """是否为瞬态模式"""
        return self.lifetime == ServiceLifetime.TRANSIENT

    @property
    def is_scoped(self) -> bool:
        """是否为作用域模式"""
        return self.lifetime == ServiceLifetime.SCOPED

    def __str__(self) -> str:
        return f"ServiceDescriptor({self.service_type.__name__} -> {self.implementation_type.__name__}, {self.lifetime.value})"


class ServiceRegistry:
    """
    服务注册表

    管理所有已注册的服务描述符，提供注册和查询功能。
    """

    def __init__(self):
        """初始化服务注册表"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._named_services: Dict[str, Dict[Type, ServiceDescriptor]] = {}

    def register(
        self,
        service_type: Type[T],
        implementation_type: Type[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Callable[[], T] = None,
        instance: T = None,
        name: str = None
    ) -> 'ServiceRegistry':
        """
        注册服务

        Args:
            service_type: 服务接口类型
            implementation_type: 实现类型
            lifetime: 生命周期
            factory: 工厂方法
            instance: 预创建实例
            name: 服务名称（用于命名服务）

        Returns:
            ServiceRegistry: 返回自身以支持链式调用

        Raises:
            ValueError: 参数配置错误
            TypeError: 类型不匹配
        """
        # 参数验证
        if implementation_type is None and factory is None and instance is None:
            raise ValueError("At least one of implementation_type, factory, or instance must be provided")

        if implementation_type is not None and not issubclass(implementation_type, service_type):
            raise TypeError(f"Implementation type {implementation_type} must be a subclass of {service_type}")

        if instance is not None and not isinstance(instance, service_type):
            raise TypeError(f"Instance must be of type {service_type}")

        # 单例模式如果有实例则忽略工厂和实现类型
        if instance is not None:
            lifetime = ServiceLifetime.SINGLETON
            factory = None
            implementation_type = type(instance)

        # 创建服务描述符
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime,
            factory=factory,
            instance=instance
        )

        # 注册服务
        if name:
            if name not in self._named_services:
                self._named_services[name] = {}
            self._named_services[name][service_type] = descriptor
        else:
            self._services[service_type] = descriptor

        return self

    def register_transient(self, service_type: Type[T], implementation_type: Type[T] = None, factory: Callable[[], T] = None) -> 'ServiceRegistry':
        """
        注册瞬态服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法

        Returns:
            ServiceRegistry: 返回自身以支持链式调用
        """
        return self.register(service_type, implementation_type, ServiceLifetime.TRANSIENT, factory)

    def register_scoped(self, service_type: Type[T], implementation_type: Type[T] = None, factory: Callable[[], T] = None) -> 'ServiceRegistry':
        """
        注册作用域服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法

        Returns:
            ServiceRegistry: 返回自身以支持链式调用
        """
        return self.register(service_type, implementation_type, ServiceLifetime.SCOPED, factory)

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None,
        instance: T = None
    ) -> 'ServiceRegistry':
        """
        注册单例服务

        Args:
            service_type: 服务类型
            implementation_type: 实现类型
            factory: 工厂方法
            instance: 预创建实例

        Returns:
            ServiceRegistry: 返回自身以支持链式调用
        """
        return self.register(service_type, implementation_type, ServiceLifetime.SINGLETON, factory, instance)

    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceRegistry':
        """
        注册实例（单例）

        Args:
            service_type: 服务类型
            instance: 实例

        Returns:
            ServiceRegistry: 返回自身以支持链式调用
        """
        return self.register_singleton(service_type, instance=instance)

    def register_factory(self, service_type: Type[T], factory: Callable[[], T], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'ServiceRegistry':
        """
        注册工厂方法

        Args:
            service_type: 服务类型
            factory: 工厂方法
            lifetime: 生命周期

        Returns:
            ServiceRegistry: 返回自身以支持链式调用
        """
        return self.register(service_type, factory=factory, lifetime=lifetime)

    def get_descriptor(self, service_type: Type[T], name: str = None) -> Optional[ServiceDescriptor]:
        """
        获取服务描述符

        Args:
            service_type: 服务类型
            name: 服务名称

        Returns:
            Optional[ServiceDescriptor]: 服务描述符，如果未找到则返回None
        """
        if name:
            return self._named_services.get(name, {}).get(service_type)
        return self._services.get(service_type)

    def is_registered(self, service_type: Type, name: str = None) -> bool:
        """
        检查服务是否已注册

        Args:
            service_type: 服务类型
            name: 服务名称

        Returns:
            bool: 已注册返回True，否则返回False
        """
        return self.get_descriptor(service_type, name) is not None

    def get_all_descriptors(self) -> Dict[Type, ServiceDescriptor]:
        """
        获取所有服务描述符

        Returns:
            Dict[Type, ServiceDescriptor]: 所有服务描述符的字典
        """
        return self._services.copy()

    def get_descriptors_by_lifetime(self, lifetime: ServiceLifetime) -> List[ServiceDescriptor]:
        """
        根据生命周期获取服务描述符

        Args:
            lifetime: 生命周期

        Returns:
            List[ServiceDescriptor]: 匹配的服务描述符列表
        """
        return [desc for desc in self._services.values() if desc.lifetime == lifetime]

    def remove(self, service_type: Type, name: str = None) -> bool:
        """
        移除服务注册

        Args:
            service_type: 服务类型
            name: 服务名称

        Returns:
            bool: 移除成功返回True，服务不存在返回False
        """
        if name:
            if name in self._named_services and service_type in self._named_services[name]:
                del self._named_services[name][service_type]
                # 如果命名服务下没有其他服务，移除整个命名服务
                if not self._named_services[name]:
                    del self._named_services[name]
                return True
        else:
            if service_type in self._services:
                del self._services[service_type]
                return True
        return False

    def clear(self) -> None:
        """清空所有服务注册"""
        self._services.clear()
        self._named_services.clear()

    def __len__(self) -> int:
        """返回已注册服务的数量"""
        return len(self._services) + sum(len(services) for services in self._named_services.values())

    def __contains__(self, service_type: Type) -> bool:
        """检查服务类型是否已注册"""
        return service_type in self._services

    def __iter__(self):
        """迭代所有服务描述符"""
        return iter(self._services.values())