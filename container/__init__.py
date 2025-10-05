# -*- coding: utf-8 -*-
"""
Voice Input System - 依赖注入容器模块

本模块提供依赖注入功能，支持服务的注册、解析和生命周期管理。
为系统解耦和组件化架构提供基础设施。

主要组件:
- DIContainer: 核心依赖注入容器
- ServiceRegistry: 服务注册表
- ServiceLifetime: 服务生命周期枚举
- ServiceDescriptor: 服务描述符
"""

from .di_container import DIContainer
from .service_registry import ServiceRegistry, ServiceDescriptor, ServiceLifetime
from .service_factory import ServiceFactory, InstanceFactory, SingletonFactory
from .exceptions import (
    DIContainerError,
    ServiceNotRegisteredError,
    CircularDependencyError,
    ServiceCreationError,
    InvalidServiceDescriptorError
)

__all__ = [
    # 核心容器
    "DIContainer",

    # 服务注册
    "ServiceRegistry",
    "ServiceDescriptor",
    "ServiceLifetime",

    # 工厂模式
    "ServiceFactory",
    "InstanceFactory",
    "SingletonFactory",

    # 异常类
    "DIContainerError",
    "ServiceNotRegisteredError",
    "CircularDependencyError",
    "ServiceCreationError",
    "InvalidServiceDescriptorError"
]

__version__ = "1.0.0"
__author__ = "Voice Input System Team"