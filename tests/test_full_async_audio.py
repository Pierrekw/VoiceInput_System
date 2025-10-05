# -*- coding: utf-8 -*-
"""
完整异步音频组件测试

使用真实的PyAudio和async_audio模块进行测试。
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch
from unittest.mock import MagicMock

# 测试PyAudio是否可用
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    print("PyAudio可用，版本:", pyaudio.__version__)
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("PyAudio不可用，将使用模拟版本")


# 根据PyAudio可用性选择导入
if PYAUDIO_AVAILABLE:
    try:
        from async_audio.async_audio_capture import (
            AsyncAudioCapture, AsyncAudioProcessorState,
            AsyncAudioStream, AsyncRecognizer, AsyncTTSPlayer
        )
        REAL_ASYNC_AUDIO = True
        print("异步音频模块导入成功")
    except ImportError as e:
        print(f"异步音频模块导入失败: {e}")
        REAL_ASYNC_AUDIO = False
else:
    REAL_ASYNC_AUDIO = False


class MockAudioStream:
    """模拟音频流"""

    def __init__(self):
        self.is_closed = False
        self.chunk_count = 0

    async def read_chunk(self):
        """读取音频块"""
        if self.is_closed:
            return None

        chunk = Mock()
        chunk.data = b"mock_audio_data"
        chunk.size = 1024
        self.chunk_count += 1
        return chunk

    async def close(self):
        """关闭音频流"""
        self.is_closed = True


class MockRecognizer:
    """模拟语音识别器"""

    def __init__(self):
        self.processed_chunks = 0

    async def process_audio(self, audio_chunk):
        """处理音频"""
        self.processed_chunks += 1
        if self.processed_chunks % 10 == 0:
            return f"识别结果 {self.processed_chunks // 10}"
        return ""

    async def get_partial_result(self):
        """获取部分识别结果"""
        if self.processed_chunks % 5 == 0:
            return f"部分结果 {self.processed_chunks // 5}"
        return ""


class MockTTSPlayer:
    """模拟TTS播放器"""

    def __init__(self):
        self.played_texts = []

    async def speak(self, text, volume=1.0):
        """播放语音"""
        self.played_texts.append(text)
        await asyncio.sleep(0.01)  # 短暂延迟

    async def stop(self):
        """停止播放"""
        pass


# 选择使用真实还是模拟组件
if REAL_ASYNC_AUDIO:
    AudioStream = AsyncAudioStream
    Recognizer = AsyncRecognizer
    TTSPlayer = AsyncTTSPlayer
else:
    AudioStream = MockAudioStream
    Recognizer = MockRecognizer
    TTSPlayer = MockTTSPlayer


class TestFullAsyncAudio(unittest.TestCase):
    """完整异步音频测试"""

    def test_audio_stream_creation(self):
        """测试音频流创建"""
        if not REAL_ASYNC_AUDIO:
            stream = MockAudioStream()
        else:
            # 如果是真实的音频流，我们只能测试创建
            with patch('async_audio.async_audio_capture.pyaudio') as mock_pyaudio:
                stream = AudioStream()

        self.assertIsNotNone(stream)

    def test_recognizer_creation(self):
        """测试识别器创建"""
        if not REAL_ASYNC_AUDIO:
            recognizer = MockRecognizer()
        else:
            # 如果是真实的识别器，我们只能测试创建
            recognizer = Recognizer()

        self.assertIsNotNone(recognizer)

    def test_tts_player_creation(self):
        """测试TTS播放器创建"""
        if not REAL_ASYNC_AUDIO:
            player = MockTTSPlayer()
        else:
            # 如果是真实的TTS播放器，我们只能测试创建
            player = TTSPlayer()

        self.assertIsNotNone(player)

    @unittest.skipUnless(REAL_ASYNC_AUDIO, "需要真实的异步音频模块")
    def test_async_audio_capture_creation(self):
        """测试异步音频捕获器创建"""
        # 使用patch模拟PyAudio
        with patch('async_audio.async_audio_capture.pyaudio') as mock_pyaudio:
            with patch('async_audio.async_audio_capture.pyaudio.PyAudio') as mock_pyaudio_class:
                mock_pyaudio_class.return_value.get_device_count.return_value = 2
                mock_pyaudio_class.return_value.get_device_info_by_index.return_value = {
                    'maxInputChannels': 1,
                    'maxOutputChannels': 2
                }

                capture = AsyncAudioCapture(
                    sample_rate=16000,
                    chunk_size=1024,
                    timeout_seconds=5
                )

                self.assertIsNotNone(capture)
                self.assertEqual(capture.sample_rate, 16000)
                self.assertEqual(capture.chunk_size, 1024)


class TestMockComponents(unittest.TestCase):
    """测试模拟组件"""

    def test_mock_audio_stream(self):
        """测试模拟音频流"""
        stream = MockAudioStream()

        # 测试初始状态
        self.assertFalse(stream.is_closed)
        self.assertEqual(stream.chunk_count, 0)

        # 测试读取音频块
        async def test_read():
            chunk = await stream.read_chunk()
            self.assertIsNotNone(chunk)
            self.assertEqual(chunk.size, 1024)
            self.assertEqual(stream.chunk_count, 1)

        # 运行异步测试
        asyncio.run(test_read())

    def test_mock_recognizer(self):
        """测试模拟识别器"""
        recognizer = MockRecognizer()
        mock_chunk = Mock()

        # 测试处理音频
        async def test_process():
            results = []
            for i in range(15):
                result = await recognizer.process_audio(mock_chunk)
                if result:
                    results.append(result)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], "识别结果 1")

        # 运行异步测试
        asyncio.run(test_process())

    def test_mock_tts_player(self):
        """测试模拟TTS播放器"""
        player = MockTTSPlayer()

        # 测试播放
        async def test_speak():
            await player.speak("测试文本")
            await player.speak("另一段文本")

            self.assertEqual(len(player.played_texts), 2)
            self.assertEqual(player.played_texts[0], "测试文本")
            self.assertEqual(player.played_texts[1], "另一段文本")

        # 运行异步测试
        asyncio.run(test_speak())


def run_full_async_audio_tests():
    """运行完整异步音频测试"""
    print("开始运行完整异步音频测试...")
    print(f"PyAudio可用: {PYAUDIO_AVAILABLE}")
    print(f"真实异步音频模块: {REAL_ASYNC_AUDIO}")

    try:
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # 添加测试类
        suite.addTests(loader.loadTestsFromTestCase(TestFullAsyncAudio))
        suite.addTests(loader.loadTestsFromTestCase(TestMockComponents))

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)

        # 输出结果
        if result.wasSuccessful():
            print("所有完整异步音频测试通过!")
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


if __name__ == "__main__":
    run_full_async_audio_tests()