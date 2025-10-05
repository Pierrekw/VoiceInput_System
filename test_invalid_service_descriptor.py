# 测试InvalidServiceDescriptorError异常是否正确导入和工作
from container import InvalidServiceDescriptorError
from container.service_registry import ServiceRegistry, ServiceLifetime
from typing import Protocol

# 定义一个测试接口
class ITestService:
    def test_method(self) -> str:
        raise NotImplementedError()

# 定义一个不符合接口的实现类
class InvalidImplementation:
    pass

# 创建服务注册表
registry = ServiceRegistry()

# 测试1: 尝试注册没有实现、工厂或实例的服务
print("测试1: 注册没有实现、工厂或实例的服务")
try:
    registry.register(ITestService)
except InvalidServiceDescriptorError as e:
    print(f"成功捕获异常: {e}")

# 测试2: 尝试注册类型不匹配的实现
print("\n测试2: 注册类型不匹配的实现")
try:
    registry.register(ITestService, InvalidImplementation)
except InvalidServiceDescriptorError as e:
    print(f"成功捕获异常: {e}")

print("\n测试完成!")