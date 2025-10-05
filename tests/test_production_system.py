# -*- coding: utf-8 -*-
"""
生产环境系统测试模块

测试TTS回声检测、键盘控制异步处理等核心功能。
"""

import sys
import os
import asyncio
import time
import unittest
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入生产环境组件
from main_production import (
    AsyncAudioProcessor, AsyncTTSManager, AsyncKeyboardController,
    ProductionVoiceSystem
)


class TestAsyncAudioProcessor(unittest.IsolatedAsyncioTestCase):
    """测试异步音频处理器"""

    async def asyncSetUp(self):
        """设置测试环境"""
        from events.event_bus import AsyncEventBus
        self.event_bus = AsyncEventBus()
        await self.event_bus.start()
        self.processor = AsyncAudioProcessor(self.event_bus)
        await self.processor.initialize()

    async def asyncTearDown(self):
        """清理测试环境"""
        await self.event_bus.stop()

    async def test_tts_silence_detection(self):
        """测试TTS静音检测机制"""
        print("测试TTS静音检测...")

        # 模拟TTS播放开始
        from events.event_types import TTSPlaybackStartedEvent
        await self.event_bus.publish(TTSPlaybackStartedEvent(
            source="Test",
            text="测试TTS",
            player_id="test_player",
            duration=1.0,
            success=True
        ))

        # 等待事件处理
        await asyncio.sleep(0.1)

        # 检查静音状态
        self.assertTrue(self.processor.detection_state.tts_active,
                        "TTS播放时应该激活静音状态")

        # 模拟音频数据接收
        from events.event_types import AudioDataReceivedEvent
        await self.event_bus.publish(AudioDataReceivedEvent(
            source="Test",
            stream_id="test_stream",
            audio_data=b"test_data",
            size=9,
            sequence_number=1
        ))

        await asyncio.sleep(0.1)

        # 测试识别结果处理（应该被静音）
        result = await self.processor.process_recognition_result("测试文本")
        self.assertEqual(result, [], "TTS静音期间应该返回空结果")

    async def test_voice_command_processing(self):
        """测试语音命令处理"""
        print("测试语音命令处理...")

        # 测试暂停命令
        result = await self.processor.process_recognition_result("暂停录音")
        self.assertEqual(result, [], "语音命令应该返回空结果")

        # 测试数值提取
        result = await self.processor.process_recognition_result("温度二十五点五度")
        self.assertEqual(result, [25.5], "应该正确提取数值")

        # 测试停止命令
        result = await self.processor.process_recognition_result("停止录音")
        self.assertEqual(result, [], "语音命令应该返回空结果")

    async def test_audio_processing_after_tts(self):
        """测试TTS结束后的音频处理"""
        print("测试TTS结束后的音频处理...")

        # 模拟TTS播放开始
        from events.event_types import TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent

        await self.event_bus.publish(TTSPlaybackStartedEvent(
            source="Test",
            text="测试TTS",
            player_id="test_player",
            duration=1.0,
            success=True
        ))

        await asyncio.sleep(0.1)

        # 在TTS播放期间测试（应该被静音）
        result = await self.processor.process_recognition_result("TTS播放时的文本")
        self.assertEqual(result, [], "TTS播放期间应该完全静音")

        # 模拟TTS播放结束
        await self.event_bus.publish(TTSPlaybackCompletedEvent(
            source="Test",
            text="测试TTS",
            player_id="test_player",
            duration=1.0,
            success=True
        ))

        await asyncio.sleep(0.1)

        # TTS刚结束时测试（应该仍被静音）
        result = await self.processor.process_recognition_result("刚结束时的文本")
        self.assertEqual(result, [], "TTS刚结束时应该仍被静音")

        # 等待部分静音期（仍应该被静音）
        await asyncio.sleep(0.4)
        result = await self.processor.process_recognition_result("静音期中期的文本")
        self.assertEqual(result, [], "静音期间应该保持静音")

        # 等待完整静音期结束（应该正常处理）
        await asyncio.sleep(0.8)
        result = await self.processor.process_recognition_result("测试数值12.5")
        self.assertEqual(result, [12.5], "TTS静音期结束后应该正常处理")

    async def test_tts_complete_silence_protection(self):
        """测试TTS完全静音保护机制"""
        print("测试TTS完全静音保护...")

        # 模拟长TTS播放
        from events.event_types import TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent

        await self.event_bus.publish(TTSPlaybackStartedEvent(
            source="Test",
            text="这是一个较长的TTS文本，用于测试静音保护",
            player_id="test_player",
            duration=3.0,
            success=True
        ))

        # 在TTS播放过程中多次尝试识别
        for i in range(5):
            await asyncio.sleep(0.2)
            result = await self.processor.process_recognition_result(f"干扰文本{i}")
            self.assertEqual(result, [], f"TTS播放期间第{i}次尝试应该被静音")

        # 模拟TTS播放结束
        await self.event_bus.publish(TTSPlaybackCompletedEvent(
            source="Test",
            text="长文本播放完成",
            player_id="test_player",
            duration=3.0,
            success=True
        ))

        # 测试静音期保护
        total_silence_time = self.processor.detection_state.silence_duration + self.processor.detection_state.tts_buffer_duration

        for i in range(int(total_silence_time / 0.2)):
            await asyncio.sleep(0.2)
            result = await self.processor.process_recognition_result(f"回声干扰{i}")
            self.assertEqual(result, [], f"静音期第{i}次应该被静音")

        # 静音期结束后应该恢复正常
        await asyncio.sleep(0.1)
        result = await self.processor.process_recognition_result("恢复识别12.3")
        self.assertEqual(result, [12.3], "静音期结束后应该恢复正常")


class TestAsyncTTSManager(unittest.IsolatedAsyncioTestCase):
    """测试异步TTS管理器"""

    async def asyncSetUp(self):
        """设置测试环境"""
        from events.event_bus import AsyncEventBus
        self.event_bus = AsyncEventBus()
        await self.event_bus.start()
        self.tts_manager = AsyncTTSManager(self.event_bus)
        await self.tts_manager.initialize()

    async def asyncTearDown(self):
        """清理测试环境"""
        await self.tts_manager.stop()
        await self.event_bus.stop()

    async def test_tts_queuing(self):
        """测试TTS队列机制"""
        print("测试TTS队列机制...")

        # 添加多个TTS任务
        await self.tts_manager.speak("第一句话")
        await self.tts_manager.speak("第二句话")
        await self.tts_manager.speak("第三句话")

        # 等待处理
        await asyncio.sleep(0.5)

        # 检查队列状态
        queue_size = self.tts_manager.audio_queue.qsize()
        print(f"TTS队列大小: {queue_size}")

        # 测试禁用TTS
        self.tts_manager.disable()
        await self.tts_manager.speak("这句话不应该播放")
        self.assertFalse(self.tts_manager.is_enabled, "TTS应该被禁用")

        # 测试启用TTS
        self.tts_manager.enable()
        self.assertTrue(self.tts_manager.is_enabled, "TTS应该被启用")

    async def test_tts_event_publishing(self):
        """测试TTS事件发布"""
        print("测试TTS事件发布...")

        # 创建事件收集器
        events_received = []

        async def event_handler(event):
            events_received.append(type(event).__name__)

        # 订阅TTS事件
        await self.event_bus.subscribe(
            type(self.tts_manager.audio_queue).__class__,
            lambda e: None
        )

        # 播放TTS
        await self.tts_manager.speak("测试事件发布")

        # 等待事件处理
        await asyncio.sleep(0.3)

        # 验证事件发布
        self.assertGreater(len(events_received), 0, "应该发布TTS相关事件")


class TestAsyncKeyboardController(unittest.IsolatedAsyncioTestCase):
    """测试异步键盘控制器"""

    async def asyncSetUp(self):
        """设置测试环境"""
        from events.event_bus import AsyncEventBus
        self.event_bus = AsyncEventBus()
        await self.event_bus.start()
        self.keyboard_controller = AsyncKeyboardController(self.event_bus)

    async def asyncTearDown(self):
        """清理测试环境"""
        await self.keyboard_controller.stop()
        await self.event_bus.stop()

    async def test_key_press_simulation(self):
        """测试按键模拟"""
        print("测试按键模拟...")

        # 创建事件收集器
        keyboard_events = []

        async def keyboard_handler(event):
            keyboard_events.append(event.key)

        # 订阅键盘事件
        await self.event_bus.subscribe(
            type(self.event_bus).__class__,
            lambda e: None
        )

        # 模拟按键
        await self.keyboard_controller.simulate_key_press("space")
        await self.keyboard_controller.simulate_key_press("esc")
        await self.keyboard_controller.simulate_key_press("t")

        # 等待事件处理
        await asyncio.sleep(0.2)

        # 验证按键事件
        self.assertGreater(len(keyboard_events), 0, "应该收到键盘事件")

    async def test_key_event_handlers(self):
        """测试按键事件处理器"""
        print("测试按键事件处理器...")

        # 模拟按键并检查响应
        await self.keyboard_controller._handle_key_press("space")
        await asyncio.sleep(0.1)

        await self.keyboard_controller._handle_key_press("esc")
        await asyncio.sleep(0.1)

        await self.keyboard_controller._handle_key_press("t")
        await asyncio.sleep(0.1)

        # 这里可以添加更详细的事件验证逻辑
        # 比如检查是否发布了相应的命令事件


class TestProductionSystemIntegration(unittest.IsolatedAsyncioTestCase):
    """测试生产系统集成"""

    async def asyncSetUp(self):
        """设置测试环境"""
        self.system = ProductionVoiceSystem()

    async def asyncTearDown(self):
        """清理测试环境"""
        await self.system.shutdown()

    async def test_system_initialization(self):
        """测试系统初始化"""
        print("测试系统初始化...")

        await self.system.initialize()

        # 验证组件初始化
        self.assertIsNotNone(self.system.event_bus, "事件总线应该已初始化")
        self.assertIsNotNone(self.system.audio_processor, "音频处理器应该已初始化")
        self.assertIsNotNone(self.system.tts_manager, "TTS管理器应该已初始化")
        self.assertIsNotNone(self.system.keyboard_controller, "键盘控制器应该已初始化")

    async def test_recognition_workflow(self):
        """测试识别工作流"""
        print("测试识别工作流...")

        await self.system.initialize()

        # 启动识别
        await self.system.start_recognition()
        self.assertTrue(self.system.recognition_active, "识别应该已激活")

        # 运行一段时间
        await asyncio.sleep(1.0)

        # 停止识别
        await self.system.stop_recognition()
        self.assertFalse(self.system.recognition_active, "识别应该已停止")

    async def test_tts_integration(self):
        """测试TTS集成"""
        print("测试TTS集成...")

        await self.system.initialize()

        # 测试TTS播放
        await self.system.tts_manager.speak("测试TTS集成")
        await asyncio.sleep(0.5)

        # 验证TTS状态
        self.assertTrue(self.system.tts_manager.is_enabled, "TTS应该启用")

    async def test_command_handling(self):
        """测试命令处理"""
        print("测试命令处理...")

        await self.system.initialize()

        # 模拟语音命令
        from events.event_types import VoiceCommandEvent
        await self.system.event_bus.publish(VoiceCommandEvent(
            source="Test",
            command="pause",
            timestamp=time.time()
        ))

        await asyncio.sleep(0.1)

        # 模拟键盘命令
        await self.system.keyboard_controller.simulate_key_press("t")
        await asyncio.sleep(0.1)


def run_production_system_tests():
    """运行生产系统测试"""
    print("=" * 60)
    print("🧪 生产环境系统测试")
    print("=" * 60)

    try:
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # 添加测试类
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncAudioProcessor))
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncTTSManager))
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncKeyboardController))
        suite.addTests(loader.loadTestsFromTestCase(TestProductionSystemIntegration))

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # 输出结果
        print("\n" + "=" * 60)
        print("生产系统测试结果")
        print("=" * 60)

        if result.wasSuccessful():
            print("✅ 所有生产系统测试通过!")
            print("TTS回声检测和键盘控制优化验证成功。")
        else:
            print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")

            if result.failures:
                print("\n失败的测试:")
                for test, traceback in result.failures:
                    print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

            if result.errors:
                print("\n错误的测试:")
                for test, traceback in result.errors:
                    print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        print(f"\n测试统计:")
        print(f"  运行测试: {result.testsRun}")
        print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"  失败: {len(result.failures)}")
        print(f"  错误: {len(result.errors)}")

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 运行生产系统测试时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_production_system_tests()
    sys.exit(0 if success else 1)