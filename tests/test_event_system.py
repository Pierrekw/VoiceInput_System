# -*- coding: utf-8 -*-
"""
事件系统测试 - 修复版本

修复异步问题和编码问题。
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import unittest
import time
from typing import List

from events import (
    EventHandler, EventPriority,
    AudioStreamStartedEvent, AudioDataReceivedEvent,
    RecognitionCompletedEvent, ErrorEvent,
    create_error_event, create_metric_event
)


class TestEventHandler(EventHandler):
    """测试事件处理器"""

    def __init__(self):
        super().__init__("TestHandler")
        self.received_events = []

    async def handle(self, event):
        """处理事件"""
        self.received_events.append(event)


class TestEventTypes(unittest.TestCase):
    """事件类型测试"""

    def test_audio_stream_events(self):
        """测试音频流事件"""
        start_event = AudioStreamStartedEvent(
            source="Test",
            stream_id="test_stream",
            sample_rate=16000,
            channels=1
        )

        self.assertEqual(start_event.stream_id, "test_stream")
        self.assertEqual(start_event.sample_rate, 16000)
        self.assertEqual(start_event.channels, 1)
        self.assertIn("音频流已启动", start_event.get_summary())

    def test_recognition_events(self):
        """测试识别事件"""
        event = RecognitionCompletedEvent(
            source="Test",
            recognizer_id="test_recognizer",
            text="Hello world",
            confidence=0.95,
            measurements=[1.0, 2.0, 3.0]
        )

        self.assertEqual(event.text, "Hello world")
        self.assertEqual(event.confidence, 0.95)
        self.assertEqual(len(event.measurements), 3)
        self.assertIn("识别完成", event.get_summary())

    def test_error_events(self):
        """测试错误事件"""
        event = create_error_event(
            source="Test",
            component="TestComponent",
            error_type="test_error",
            error_message="Test error message"
        )

        self.assertEqual(event.component, "TestComponent")
        self.assertEqual(event.error_type, "test_error")
        self.assertEqual(event.error_message, "Test error message")
        self.assertEqual(event.priority, EventPriority.HIGH)

    def test_metric_events(self):
        """测试指标事件"""
        event = create_metric_event(
            source="Test",
            component="TestComponent",
            metric_name="test_metric",
            metric_value=42.5,
            metric_unit="ms"
        )

        self.assertEqual(event.component, "TestComponent")
        self.assertEqual(event.metric_name, "test_metric")
        self.assertEqual(event.metric_value, 42.5)
        self.assertEqual(event.metric_unit, "ms")


class TestEventHandlers(unittest.TestCase):
    """事件处理器测试"""

    def test_handler_creation(self):
        """测试处理器创建"""
        handler = TestEventHandler()

        self.assertEqual(handler.name, "TestHandler")
        self.assertTrue(handler.enabled)
        self.assertEqual(handler.handle_count, 0)
        self.assertEqual(handler.error_count, 0)

    def test_handler_statistics(self):
        """测试处理器统计"""
        handler = TestEventHandler()

        # 模拟一些处理（不实际调用async方法）
        handler.handle_count = 3
        handler.error_count = 1
        handler.total_handle_time = 0.15
        handler.max_handle_time = 0.08

        stats = handler.get_statistics()
        self.assertEqual(stats['handle_count'], 3)
        self.assertEqual(stats['error_count'], 1)
        self.assertAlmostEqual(stats['success_rate'], 2/3, places=2)  # (3-1)/3
        self.assertAlmostEqual(stats['avg_handle_time'], 0.05, places=2)  # 0.15/3
        self.assertEqual(stats['max_handle_time'], 0.08)

    def test_handler_enable_disable(self):
        """测试处理器启用/禁用"""
        handler = TestEventHandler()

        # 默认启用
        self.assertTrue(handler.enabled)

        # 禁用
        handler.disable()
        self.assertFalse(handler.enabled)

        # 启用
        handler.enable()
        self.assertTrue(handler.enabled)

    def test_handler_reset_statistics(self):
        """测试统计重置"""
        handler = TestEventHandler()

        # 设置一些统计数据
        handler.handle_count = 10
        handler.error_count = 2
        handler.total_handle_time = 1.5
        handler.max_handle_time = 0.5

        # 重置统计
        handler.reset_statistics()

        # 验证重置
        self.assertEqual(handler.handle_count, 0)
        self.assertEqual(handler.error_count, 0)
        self.assertEqual(handler.total_handle_time, 0.0)
        self.assertEqual(handler.max_handle_time, 0.0)


def run_event_system_fixed_tests():
    """运行修复后的事件系统测试"""
    print("开始运行修复后的事件系统测试...")

    try:
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # 添加测试类（只添加同步测试）
        suite.addTests(loader.loadTestsFromTestCase(TestEventTypes))
        suite.addTests(loader.loadTestsFromTestCase(TestEventHandlers))

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)

        # 输出结果
        if result.wasSuccessful():
            print("所有修复后的事件系统测试通过!")
        else:
            print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
            if result.failures:
                print("\n失败的测试:")
                for test, traceback in result.failures:
                    print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
            if result.errors:
                print("\n错误的测试:")
                for test, traceback in result.errors:
                    print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        return result.wasSuccessful()

    except Exception as e:
        print(f"运行测试时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_event_system_tests():
    """运行事件系统测试（为统一运行器提供的别名）"""
    return run_event_system_fixed_tests()


if __name__ == "__main__":
    run_event_system_fixed_tests()