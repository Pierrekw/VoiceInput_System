# -*- coding: utf-8 -*-
"""
依赖注入容器异常类定义

定义了依赖注入容器相关的所有异常类型，提供清晰的错误信息和
调试支持。
"""
from typing import Optional

class DIContainerError(Exception):
    """
    依赖注入容器基础异常类

    所有DI容器相关的异常都继承自此类。
    """
    def __init__(self, message: str, service_type: Optional[str] = None):
        super().__init__(message)
        self.service_type = service_type
        self.message = message

    def __str__(self) -> str:
        if self.service_type:
            return f"{self.message} (Service: {self.service_type})"
        return self.message


class ServiceNotRegisteredError(DIContainerError):
    """
    服务未注册异常

    当尝试解析一个未注册的服务时抛出此异常。
    """
    def __init__(self, service_type: str):
        message = f"Service '{service_type}' is not registered"
        super().__init__(message, service_type)


class CircularDependencyError(DIContainerError):
    """
    循环依赖异常

    当检测到服务之间存在循环依赖时抛出此异常。
    """
    def __init__(self, dependency_chain: list):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)

    def __str__(self) -> str:
        return f"Circular dependency detected: {' -> '.join(self.dependency_chain)}"


class ServiceCreationError(DIContainerError):
    """
    服务创建异常

    当服务实例化过程中发生错误时抛出此异常。
    """
    def __init__(self, service_type: str, original_exception: Exception):
        self.original_exception = original_exception
        message = f"Failed to create service '{service_type}': {str(original_exception)}"
        super().__init__(message, service_type)

    def __str__(self) -> str:
        if self.service_type:
            return f"Failed to create service '{self.service_type}': {str(self.original_exception)}"
        return f"Service creation failed: {str(self.original_exception)}"


class InvalidServiceDescriptorError(DIContainerError):
    """
    无效服务描述符异常

    当服务描述符配置不正确时抛出此异常。
    """
    def __init__(self, message: str, service_type: Optional[str] = None):
        super().__init__(f"Invalid service descriptor: {message}", service_type)


class ServiceAlreadyRegisteredError(DIContainerError):
    """
    服务已注册异常

    当尝试注册一个已经注册的服务时抛出此异常。
    """
    def __init__(self, service_type: str):
        message = f"Service '{service_type}' is already registered"
        super().__init__(message, service_type)


class ContainerDisposedError(DIContainerError):
    """
    容器已释放异常

    当尝试在已释放的容器上执行操作时抛出此异常。
    """
    def __init__(self):
        message = "Container has been disposed and cannot be used"
        super().__init__(message)


class InvalidScopeError(DIContainerError):
    """
    无效作用域异常

    当服务的生命周期与当前作用域不匹配时抛出此异常。
    """
    def __init__(self, service_type: str, current_scope: str, required_scope: str):
        message = f"Service '{service_type}' requires scope '{required_scope}' but current scope is '{current_scope}'"
        super().__init__(message, service_type)


class ServiceConfigurationError(DIContainerError):
    """
    服务配置异常

    当服务配置不正确时抛出此异常。
    """
    def __init__(self, service_type: str, configuration_error: str):
        message = f"Service '{service_type}' configuration error: {configuration_error}"
        super().__init__(message, service_type)