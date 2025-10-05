# -*- coding: utf-8 -*-
"""
基础测试

测试核心功能，避免外部依赖。
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestBasicEventSystem(unittest.TestCase):
    """基础事件系统测试"""

    def test_event_imports(self):
        """测试事件模块导入"""
        try:
            from events import BaseEvent, EventPriority
            from events.event_types import AudioStreamStartedEvent
            from events.event_handler import EventHandler

            # 创建基本事件
            event = AudioStreamStartedEvent(
                source="Test",
                stream_id="test_stream",
                sample_rate=16000
            )

            self.assertEqual(event.source, "Test")
            self.assertEqual(event.stream_id, "test_stream")
            self.assertEqual(event.sample_rate, 16000)

        except ImportError as e:
            self.fail(f"导入事件模块失败: {e}")

    def test_event_handler_creation(self):
        """测试事件处理器创建"""
        try:
            from events.event_handler import EventHandler

            class TestHandler(EventHandler):
                def __init__(self):
                    super().__init__("TestHandler")

                async def handle(self, event):
                    pass

            handler = TestHandler()
            self.assertEqual(handler.name, "TestHandler")
            self.assertTrue(handler.enabled)

        except ImportError as e:
            self.fail(f"导入事件处理器失败: {e}")

    def test_system_coordinator_import(self):
        """测试系统协调器导入"""
        try:
            from events.system_coordinator import SystemCoordinator

            coordinator = SystemCoordinator()
            self.assertIsNotNone(coordinator)

        except ImportError as e:
            self.fail(f"导入系统协调器失败: {e}")


class TestBasicAsyncComponents(unittest.TestCase):
    """基础异步组件测试"""

    def test_interfaces_import(self):
        """测试接口模块导入"""
        try:
            from interfaces.audio_processor import RecognitionResult, VoiceCommand

            # 创建数据对象
            result = RecognitionResult(
                final_text="测试文本",
                processing_time=0.1
            )

            self.assertEqual(result.final_text, "测试文本")
            self.assertEqual(result.processing_time, 0.1)

        except ImportError as e:
            self.fail(f"导入接口模块失败: {e}")

    def test_container_import(self):
        """测试依赖注入容器导入"""
        try:
            from container.di_container import DIContainer

            container = DIContainer()
            self.assertIsNotNone(container)

        except ImportError as e:
            self.fail(f"导入依赖注入容器失败: {e}")


def run_basic_tests():
    """运行基础测试"""
    print("运行基础功能测试...")
    print("-" * 50)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBasicEventSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestBasicAsyncComponents))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    # 输出结果
    if result.wasSuccessful():
        print("基础功能测试通过!")
        return True
    else:
        print(f"基础功能测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)