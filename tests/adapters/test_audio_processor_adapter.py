# -*- coding: utf-8 -*-
"""
音频处理器适配器测试

测试AudioProcessorAdapter的功能和接口兼容性。
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio

from interfaces.audio_processor import AudioProcessorState, VoiceCommandType
from adapters.audio_processor_adapter import AudioProcessorAdapter


class TestAudioProcessorAdapter(unittest.TestCase):
    """音频处理器适配器测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟的AudioCapture实例
        self.mock_capture = Mock()
        self.mock_capture.state = "idle"
        self.mock_capture._model_loaded = False
        self.mock_capture.buffered_values = []
        self.mock_capture.tts = Mock()
        self.mock_capture.tts.get_tts_status.return_value = "on"

        # 创建适配器
        self.adapter = AudioProcessorAdapter(audio_capture=self.mock_capture)

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        # 验证适配器创建成功
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.wrapped_instance, self.mock_capture)

    def test_adapter_initialization_without_instance(self):
        """测试不提供实例时的初始化"""
        with patch('adapters.audio_processor_adapter.AudioCapture') as mock_capture_class:
            mock_instance = Mock()
            mock_capture_class.return_value = mock_instance

            adapter = AudioProcessorAdapter()

            # 验证创建了新的AudioCapture实例
            mock_capture_class.assert_called_once()
            self.assertEqual(adapter.wrapped_instance, mock_instance)

    def test_load_model_success(self):
        """测试成功加载模型"""
        # 设置mock返回值
        self.mock_capture.load_model.return_value = True
        self.mock_capture.model_path = "test_model"

        # 调用方法
        result = self.adapter.load_model("test_model")

        # 验证结果
        self.assertTrue(result)
        self.mock_capture.load_model.assert_called_once()

    def test_load_model_failure(self):
        """测试加载模型失败"""
        # 设置mock返回值
        self.mock_capture.load_model.return_value = False

        # 调用方法
        result = self.adapter.load_model("invalid_model")

        # 验证结果
        self.assertFalse(result)

    def test_unload_model(self):
        """测试卸载模型"""
        # 调用方法
        self.adapter.unload_model()

        # 验证方法被调用
        self.mock_capture.unload_model.assert_called_once()

    def test_is_model_loaded(self):
        """测试检查模型是否已加载"""
        # 设置mock返回值
        self.mock_capture._model_loaded = True

        # 调用方法
        result = self.adapter.is_model_loaded()

        # 验证结果
        self.assertTrue(result)

    def test_get_state(self):
        """测试获取状态"""
        # 测试不同状态
        test_cases = [
            ("idle", AudioProcessorState.IDLE),
            ("recording", AudioProcessorState.RECORDING),
            ("paused", AudioProcessorState.PAUSED),
            ("stopped", AudioProcessorState.STOPPED),
            ("unknown", AudioProcessorState.ERROR)
        ]

        for capture_state, expected_state in test_cases:
            with self.subTest(capture_state=capture_state):
                self.mock_capture.state = capture_state
                result = self.adapter.get_state()
                self.assertEqual(result, expected_state)

    def test_start_recognition_sync(self):
        """测试同步开始识别"""
        # 设置mock返回值
        expected_result = {
            "final": "test result",
            "buffered_values": [1.0, 2.0, 3.0],
            "collected_text": ["text1", "text2"],
            "session_data": [(1, 1.0, "text1")]
        }
        self.mock_capture.listen_realtime_vosk.return_value = expected_result

        # 设置回调
        callback_mock = Mock()
        self.adapter.set_callback(callback_mock)

        # 调用方法
        result = self.adapter.start_recognition()

        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_capture.set_callback.assert_called_once_with(callback_mock)

    def test_start_recognition_sync_error(self):
        """测试同步开始识别异常"""
        # 设置mock抛出异常
        self.mock_capture.listen_realtime_vosk.side_effect = Exception("Test error")

        # 调用方法
        result = self.adapter.start_recognition()

        # 验证错误处理
        self.assertIn("error", result)
        self.assertEqual(result["buffered_values"], [])

    @patch('asyncio.get_event_loop')
    def test_start_recognition_async(self, mock_get_event_loop):
        """测试异步开始识别"""
        # 设置mock异步执行
        mock_loop = Mock()
        mock_get_event_loop.return_value = mock_loop
        mock_loop.run_in_executor.return_value = {
            "final": "async result",
            "buffered_values": [1.5, 2.5],
            "collected_text": ["async_text"],
            "session_data": [(1, 1.5, "async_text")]
        }

        # 运行异步测试
        async def run_test():
            result = await self.adapter.start_recognition_async()
            return result

        # 执行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()

        # 验证结果
        self.assertEqual(result.final_text, "async result")
        self.assertEqual(result.buffered_values, [1.5, 2.5])

    def test_pause_recognition(self):
        """测试暂停识别"""
        # 调用方法
        self.adapter.pause_recognition()

        # 验证方法被调用
        self.mock_capture.pause.assert_called_once()

    def test_resume_recognition(self):
        """测试恢复识别"""
        # 调用方法
        self.adapter.resume_recognition()

        # 验证方法被调用
        self.mock_capture.resume.assert_called_once()

    def test_stop_recognition(self):
        """测试停止识别"""
        # 调用方法
        self.adapter.stop_recognition()

        # 验证方法被调用
        self.mock_capture.stop.assert_called_once()

    def test_set_callback(self):
        """测试设置回调"""
        # 创建回调函数
        callback = Mock()

        # 调用方法
        self.adapter.set_callback(callback)

        # 验证方法被调用
        self.mock_capture.set_callback.assert_called_once_with(callback)

    @patch('adapters.audio_processor_adapter.extract_measurements')
    def test_extract_measurements(self, mock_extract):
        """测试提取数值"""
        # 设置mock返回值
        mock_extract.return_value = [1.0, 2.0, 3.0]

        # 调用方法
        result = self.adapter.extract_measurements("二十五点五")

        # 验证结果
        self.assertEqual(result, [1.0, 2.0, 3.0])
        mock_extract.assert_called_once_with("二十五点五")

    def test_process_voice_commands(self):
        """测试处理语音命令"""
        # 设置mock返回值
        self.mock_capture._process_voice_commands.return_value = True

        # 测试暂停命令
        result = self.adapter.process_voice_commands("暂停录音")
        self.assertIsNotNone(result)
        self.assertEqual(result.command_type, VoiceCommandType.PAUSE)

        # 测试继续命令
        result = self.adapter.process_voice_commands("继续录音")
        self.assertIsNotNone(result)
        self.assertEqual(result.command_type, VoiceCommandType.RESUME)

        # 测试停止命令
        result = self.adapter.process_voice_commands("停止录音")
        self.assertIsNotNone(result)
        self.assertEqual(result.command_type, VoiceCommandType.STOP)

    def test_process_voice_commands_no_command(self):
        """测试处理非命令文本"""
        # 设置mock返回值
        self.mock_capture._process_voice_commands.return_value = False

        # 调用方法
        result = self.adapter.process_voice_commands("普通文本")

        # 验证结果
        self.assertIsNone(result)

    def test_get_buffered_values(self):
        """测试获取缓冲数值"""
        # 设置mock返回值
        test_values = [1.0, 2.0, 3.0]
        self.mock_capture.buffered_values = test_values

        # 调用方法
        result = self.adapter.get_buffered_values()

        # 验证结果
        self.assertEqual(result, test_values)

    def test_get_session_data(self):
        """测试获取会话数据"""
        # 设置mock返回值
        test_data = [(1, 1.0, "text1"), (2, 2.0, "text2")]
        mock_exporter = Mock()
        mock_exporter.get_session_data.return_value = test_data
        self.mock_capture._exporter = mock_exporter

        # 调用方法
        result = self.adapter.get_session_data()

        # 验证结果
        self.assertEqual(result, test_data)

    def test_clear_buffer(self):
        """测试清空缓冲区"""
        # 设置初始数据
        self.mock_capture.buffered_values = [1.0, 2.0]

        # 调用方法
        self.adapter.clear_buffer()

        # 验证缓冲区被清空
        self.assertEqual(len(self.mock_capture.buffered_values), 0)

    def test_set_audio_parameters(self):
        """测试设置音频参数"""
        # 调用方法
        self.adapter.set_audio_parameters(
            sample_rate=22050,
            chunk_size=4000,
            timeout_seconds=120
        )

        # 验证参数被设置
        self.assertEqual(self.mock_capture.sample_rate, 22050)
        self.assertEqual(self.mock_capture.audio_chunk_size, 4000)
        self.assertEqual(self.mock_capture.timeout_seconds, 120)

    def test_get_audio_parameters(self):
        """测试获取音频参数"""
        # 设置参数
        self.mock_capture.sample_rate = 22050
        self.mock_capture.audio_chunk_size = 4000
        self.mock_capture.timeout_seconds = 120
        self.mock_capture.model_path = "test_model"

        # 调用方法
        result = self.adapter.get_audio_parameters()

        # 验证结果
        expected = {
            "sample_rate": 22050,
            "chunk_size": 4000,
            "timeout_seconds": 120,
            "model_path": "test_model"
        }
        self.assertEqual(result, expected)

    def test_enable_tts(self):
        """测试启用TTS"""
        # 调用方法
        self.adapter.enable_tts()

        # 验证方法被调用
        self.mock_capture.enable_tts.assert_called_once()

    def test_disable_tts(self):
        """测试禁用TTS"""
        # 调用方法
        self.adapter.disable_tts()

        # 验证方法被调用
        self.mock_capture.disable_tts.assert_called_once()

    def test_toggle_tts(self):
        """测试切换TTS"""
        # 设置mock返回值
        self.mock_capture.get_tts_status.return_value = "off"

        # 调用方法
        result = self.adapter.toggle_tts()

        # 验证方法被调用
        self.mock_capture.toggle_tts.assert_called_once()
        self.assertFalse(result)  # 切换后状态为关闭

    def test_is_tts_enabled(self):
        """测试TTS状态"""
        # 测试启用状态
        self.mock_capture.get_tts_status.return_value = "on"
        self.assertTrue(self.adapter.is_tts_enabled())

        # 测试禁用状态
        self.mock_capture.get_tts_status.return_value = "off"
        self.assertFalse(self.adapter.is_tts_enabled())

    def test_speak_text(self):
        """测试TTS播报文本"""
        # 调用方法
        self.adapter.speak_text("测试文本")

        # 验证方法被调用
        self.mock_capture.tts.speak.assert_called_once_with("测试文本")

    def test_cleanup(self):
        """测试清理资源"""
        # 调用方法
        self.adapter.cleanup()

        # 验证方法被调用
        self.mock_capture.unload_model.assert_called_once()

    def test_get_diagnostics_info(self):
        """测试获取诊断信息"""
        # 设置状态
        self.mock_capture._model_loaded = True
        self.mock_capture.state = "recording"
        self.mock_capture.buffered_values = [1.0, 2.0]
        mock_exporter = Mock()
        mock_exporter.get_session_data.return_value = [(1, 1.0, "text")]
        self.mock_capture._exporter = mock_exporter

        # 调用方法
        result = self.adapter.get_diagnostics_info()

        # 验证结果
        expected_keys = {
            "state", "model_loaded", "tts_enabled", "audio_parameters",
            "buffered_values_count", "session_data_count"
        }
        self.assertTrue(set(result.keys()).issuperset(expected_keys))
        self.assertEqual(result["state"], "recording")
        self.assertTrue(result["model_loaded"])

    def test_adapter_repr(self):
        """测试适配器字符串表示"""
        # 设置状态
        self.mock_capture._model_loaded = True
        self.mock_capture.state = "recording"

        # 调用方法
        result = repr(self.adapter)

        # 验证结果
        self.assertIn("AudioProcessorAdapter", result)
        self.assertIn("state=recording", result)
        self.assertIn("model_loaded=True", result)


class TestAudioProcessorAdapterIntegration(unittest.TestCase):
    """音频处理器适配器集成测试"""

    def setUp(self):
        """测试前准备"""
        # 这个测试需要实际的AudioCapture类
        # 如果不可用，跳过测试
        try:
            from audio_capture_v import AudioCapture
            self.AudioCapture = AudioCapture
        except ImportError:
            self.skipTest("AudioCapture not available")

    def test_adapter_with_real_capture(self):
        """测试适配器与真实AudioCapture的集成"""
        # 创建真实的AudioCapture实例
        capture = self.AudioCapture(test_mode=True)

        # 创建适配器
        adapter = AudioProcessorAdapter(audio_capture=capture)

        # 验证基本功能
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.get_state(), AudioProcessorState.IDLE)
        self.assertFalse(adapter.is_model_loaded())

        # 测试参数设置
        adapter.set_audio_parameters(sample_rate=22050)
        params = adapter.get_audio_parameters()
        self.assertEqual(params["sample_rate"], 22050)

        # 清理
        adapter.cleanup()


if __name__ == '__main__':
    unittest.main()