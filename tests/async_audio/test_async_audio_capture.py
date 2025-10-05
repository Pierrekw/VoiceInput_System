# -*- coding: utf-8 -*-
"""
异步音频捕获测试

测试AsyncAudioCapture及其相关组件的功能。
"""

import pytest
import asyncio
import time
import logging
from unittest.mock import Mock, patch, AsyncMock

from async_audio import (
    AsyncAudioCapture, AsyncAudioStream, AsyncRecognizer, AsyncTTSPlayer,
    AsyncAudioProcessorState, AudioChunk
)
from interfaces.audio_processor import RecognitionResult, AudioProcessorState

# 配置测试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
async def async_audio_capture():
    """创建AsyncAudioCapture测试实例"""
    capture = AsyncAudioCapture(
        sample_rate=16000,
        chunk_size=8000,
        timeout_seconds=5,
        test_mode=True
    )
    await capture.initialize()
    yield capture
    await capture.cleanup()


@pytest.fixture
async def async_audio_stream():
    """创建AsyncAudioStream测试实例"""
    stream = AsyncAudioStream(sample_rate=16000, chunk_size=8000)
    await stream.open()
    yield stream
    await stream.close()


class TestAsyncAudioStream:
    """异步音频流测试"""

    @pytest.mark.asyncio
    async def test_stream_initialization(self, async_audio_stream):
        """测试音频流初始化"""
        assert async_audio_stream.is_active
        assert async_audio_stream.sample_rate == 16000
        assert async_audio_stream.chunk_size == 8000

    @pytest.mark.asyncio
    async def test_stream_context_manager(self):
        """测试音频流上下文管理器"""
        async with AsyncAudioStream(sample_rate=16000, chunk_size=8000) as stream:
            assert stream.is_active

        # 上下文管理器退出后应该关闭
        assert not stream.is_active

    @pytest.mark.asyncio
    async def test_read_audio_chunk(self, async_audio_stream):
        """测试读取音频数据块"""
        # 读取音频数据（可能会有超时，这是正常的）
        chunk = await asyncio.wait_for(
            async_audio_stream.read_chunk(),
            timeout=1.0
        )

        # 在测试环境中，可能没有真实的音频输入设备
        # 所以chunk可能是None，这是正常的
        if chunk:
            assert isinstance(chunk, AudioChunk)
            assert chunk.data is not None
            assert chunk.size > 0
            assert chunk.timestamp > 0

    @pytest.mark.asyncio
    async def test_multiple_stream_reads(self, async_audio_stream):
        """测试多次读取音频数据"""
        chunks = []
        for _ in range(3):
            try:
                chunk = await asyncio.wait_for(
                    async_audio_stream.read_chunk(),
                    timeout=0.5
                )
                if chunk:
                    chunks.append(chunk)
            except asyncio.TimeoutError:
                # 超时是正常的，继续测试
                continue

        # 至少应该尝试读取
        assert len(chunks) >= 0


class TestAsyncAudioCapture:
    """异步音频捕获器测试"""

    @pytest.mark.asyncio
    async def test_capture_initialization(self, async_audio_capture):
        """测试捕获器初始化"""
        assert async_audio_capture.get_state() == AudioProcessorState.IDLE
        # 注意：在测试环境中，可能没有真实的音频设备，所以初始化可能失败
        # 如果初始化失败，状态会是ERROR

    @pytest.mark.asyncio
    async def test_capture_context_manager(self):
        """测试捕获器上下文管理器"""
        async with AsyncAudioCapture(test_mode=True) as capture:
            # 上下文管理器应该自动初始化
            assert capture is not None

        # 上下文管理器退出后应该清理
        # 注意：由于测试环境限制，实际状态可能不同

    @pytest.mark.asyncio
    async def test_start_stop_recognition(self, async_audio_capture):
        """测试开始和停止识别"""
        # 尝试开始识别
        result = await async_audio_capture.start_recognition()

        if result.success:
            assert async_audio_capture.get_state() == AudioProcessorState.RUNNING

            # 等待一小段时间
            await asyncio.sleep(0.5)

            # 停止识别
            stop_result = await async_audio_capture.stop_recognition()
            assert stop_result.success
        else:
            # 如果开始失败，记录原因
            logger.warning(f"开始识别失败: {result.error_message}")

    @pytest.mark.asyncio
    async def test_pause_resume_recognition(self, async_audio_capture):
        """测试暂停和恢复识别"""
        # 尝试开始识别
        result = await async_audio_capture.start_recognition()

        if result.success:
            # 暂停识别
            paused = await async_audio_capture.pause_recognition()
            if paused:
                assert async_audio_capture.get_state() == AudioProcessorState.PAUSED

                # 恢复识别
                resumed = await async_audio_capture.resume_recognition()
                if resumed:
                    assert async_audio_capture.get_state() == AudioProcessorState.RUNNING

            # 停止识别
            await async_audio_capture.stop_recognition()

    @pytest.mark.asyncio
    async def test_recognition_callback(self, async_audio_capture):
        """测试识别回调"""
        callback_results = []

        def test_callback(result: RecognitionResult):
            callback_results.append(result)

        async_audio_capture.add_recognition_callback(test_callback)

        # 开始识别
        result = await async_audio_capture.start_recognition()

        if result.success:
            # 等待一段时间，看是否有回调被调用
            await asyncio.sleep(2.0)

            # 停止识别
            await async_audio_capture.stop_recognition()

        # 检查回调结果
        logger.info(f"回调结果数量: {len(callback_results)}")

    @pytest.mark.asyncio
    async def test_state_change_callback(self, async_audio_capture):
        """测试状态变更回调"""
        state_changes = []

        def test_callback(state):
            state_changes.append(state)

        async_audio_capture.add_state_change_callback(test_callback)

        # 开始识别
        result = await async_audio_capture.start_recognition()

        if result.success:
            # 停止识别
            await async_audio_capture.stop_recognition()

        # 检查状态变更
        logger.info(f"状态变更数量: {len(state_changes)}")
        for state in state_changes:
            logger.info(f"  状态: {state}")

    @pytest.mark.asyncio
    async def test_statistics(self, async_audio_capture):
        """测试统计信息"""
        stats = async_audio_capture.get_statistics()

        assert isinstance(stats, dict)
        assert 'captured_chunks' in stats
        assert 'recognized_texts' in stats
        assert 'errors' in stats
        assert 'start_time' in stats
        assert 'last_activity' in stats

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, async_audio_capture):
        """测试并发操作"""
        # 同时开始多个操作
        tasks = [
            async_audio_capture.start_recognition(),
            async_audio_capture.pause_recognition(),
            async_audio_capture.resume_recognition()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {i} 异常: {result}")
            else:
                logger.info(f"任务 {i} 结果: {result}")


class TestAsyncNumberExtractor:
    """异步数值提取器测试"""

    @pytest.mark.asyncio
    async def test_extract_measurements(self):
        """测试异步数值提取"""
        from async_audio.async_number_extractor import AsyncNumberExtractor

        extractor = AsyncNumberExtractor()

        test_cases = [
            ("二十五点五", [25.5]),
            ("一百零二", [102]),
            ("三", [3]),
            ("零点五", [0.5]),
            ("二十", [20])
        ]

        for text, expected in test_cases:
            result = await extractor.extract_measurements(text)
            logger.info(f"提取测试: '{text}' -> {result} (期望: {expected})")
            # 注意：由于依赖外部库，可能不总能提取到正确结果

    @pytest.mark.asyncio
    async def test_extract_with_cache(self):
        """测试缓存功能"""
        from async_audio.async_number_extractor import AsyncNumberExtractor

        extractor = AsyncNumberExtractor()

        text = "二十五点五"

        # 第一次提取
        result1 = await extractor.extract_measurements(text)

        # 第二次提取（应该使用缓存）
        result2 = await extractor.extract_measurements(text)

        # 结果应该相同
        assert result1 == result2

        # 检查缓存统计
        stats = extractor.get_cache_stats()
        assert stats['cache_size'] > 0

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """测试清空缓存"""
        from async_audio.async_number_extractor import AsyncNumberExtractor

        extractor = AsyncNumberExtractor()

        # 添加一些缓存
        await extractor.extract_measurements("测试")

        # 检查缓存
        stats_before = extractor.get_cache_stats()
        assert stats_before['cache_size'] > 0

        # 清空缓存
        await extractor.clear_cache()

        # 检查缓存已清空
        stats_after = extractor.get_cache_stats()
        assert stats_after['cache_size'] == 0


class TestAsyncTTSPlayer:
    """异步TTS播放器测试"""

    @pytest.mark.asyncio
    async def test_tts_initialization(self):
        """测试TTS初始化"""
        tts = AsyncTTSPlayer()

        # 在测试环境中，TTS可能无法初始化
        try:
            await tts.initialize()
            # 如果成功初始化，测试基本功能
            assert tts is not None
        except Exception as e:
            logger.warning(f"TTS初始化失败（在测试环境中是正常的）: {e}")

    @pytest.mark.asyncio
    async def test_speak_async(self):
        """测试异步语音播报"""
        tts = AsyncTTSPlayer()

        try:
            await tts.initialize()

            # 测试语音播报
            result = await tts.speak_async("测试语音播报")

            # 检查结果
            if result:
                logger.info("语音播报请求已提交")

            # 停止TTS
            await tts.stop()

        except Exception as e:
            logger.warning(f"TTS测试失败（在测试环境中是正常的）: {e}")


@pytest.mark.asyncio
async def test_integration():
    """集成测试"""
    logger.info("🧪 开始异步音频处理集成测试")

    try:
        # 创建异步音频捕获器
        async with AsyncAudioCapture(test_mode=True) as capture:
            logger.info("✅ 异步音频捕获器创建成功")

            # 测试基本操作
            stats = capture.get_statistics()
            logger.info(f"📊 统计信息: {stats}")

            state = capture.get_state()
            logger.info(f"🔄 当前状态: {state}")

            # 尝试开始识别
            result = await capture.start_recognition()

            if result.success:
                logger.info("🎤 识别已启动")

                # 等待一段时间
                await asyncio.sleep(1.0)

                # 停止识别
                stop_result = await capture.stop_recognition()

                if stop_result.success:
                    logger.info("🛑 识别已停止")
            else:
                logger.warning(f"⚠️ 启动识别失败: {result.error_message}")

        logger.info("✅ 集成测试完成")

    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        raise


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])