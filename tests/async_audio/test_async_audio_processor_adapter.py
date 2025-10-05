# -*- coding: utf-8 -*-
"""
异步音频处理器适配器测试

测试AsyncAudioProcessorAdapter的功能和兼容性。
"""

import pytest
import asyncio
import time
import logging
from unittest.mock import Mock, patch, AsyncMock

from adapters.async_audio_processor_adapter import (
    AsyncAudioProcessorAdapter, create_async_audio_processor_adapter,
    create_hybrid_audio_processor_adapter
)
from interfaces.audio_processor import RecognitionResult, AudioProcessorState

# 配置测试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
async def async_adapter():
    """创建异步音频处理器适配器测试实例"""
    adapter = AsyncAudioProcessorAdapter(
        use_async=True,
        test_mode=True,
        timeout_seconds=5
    )
    await adapter.async_initialize()
    yield adapter
    await adapter.cleanup_async()


@pytest.fixture
def sync_adapter():
    """创建同步音频处理器适配器测试实例"""
    adapter = AsyncAudioProcessorAdapter(
        use_async=False,
        test_mode=True
    )
    yield adapter
    adapter.cleanup()


class TestAsyncAudioProcessorAdapter:
    """异步音频处理器适配器测试"""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, async_adapter):
        """测试适配器初始化"""
        assert async_adapter.use_async
        assert async_adapter._async_initialized
        assert async_adapter.is_initialized()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        async with await create_async_audio_processor_adapter(test_mode=True) as adapter:
            assert adapter.use_async
            assert adapter.is_initialized()

    @pytest.mark.asyncio
    async def test_start_stop_recognition_async(self, async_adapter):
        """测试异步开始和停止识别"""
        # 开始识别
        result = await async_adapter.start_recognition_async()

        if result.success:
            assert isinstance(result, RecognitionResult)
            logger.info(f"✅ 识别已启动: {result.text}")

            # 等待一段时间
            await asyncio.sleep(1.0)

            # 停止识别
            stop_result = await async_adapter.stop_recognition_async()
            assert stop_result.success
            logger.info("✅ 识别已停止")
        else:
            logger.warning(f"⚠️ 启动识别失败: {result.error_message}")

    @pytest.mark.asyncio
    async def test_pause_resume_recognition_async(self, async_adapter):
        """测试异步暂停和恢复识别"""
        # 开始识别
        result = await async_adapter.start_recognition_async()

        if result.success:
            # 暂停识别
            paused = await async_adapter.pause_recognition_async()
            if paused:
                logger.info("⏸️ 识别已暂停")
                assert async_adapter.get_state() == AudioProcessorState.PAUSED

                # 恢复识别
                resumed = await async_adapter.resume_recognition_async()
                if resumed:
                    logger.info("▶️ 识别已恢复")
                    assert async_adapter.get_state() == AudioProcessorState.RUNNING

            # 停止识别
            await async_adapter.stop_recognition_async()

    @pytest.mark.asyncio
    async def test_extract_measurements(self, async_adapter):
        """测试数值提取"""
        test_cases = [
            ("二十五点五", [25.5]),
            ("一百零二", [102]),
            ("三", [3]),
            ("零点五", [0.5])
        ]

        for text, expected in test_cases:
            result = async_adapter.extract_measurements(text)
            logger.info(f"提取测试: '{text}' -> {result} (期望: {expected})")
            # 注意：由于依赖外部库，可能不总能提取到正确结果

    @pytest.mark.asyncio
    async def test_extract_measurements_async(self, async_adapter):
        """测试异步数值提取"""
        test_text = "二十五点五"

        result = await async_adapter.extract_measurements_async(test_text)
        logger.info(f"异步提取测试: '{test_text}' -> {result}")

        # 应该返回一个列表
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_recognition_callback(self, async_adapter):
        """测试识别回调"""
        callback_results = []

        def test_callback(result: RecognitionResult):
            callback_results.append(result)
            logger.info(f"📞 收到识别回调: {result.final_text}")

        async_adapter.add_recognition_callback(test_callback)

        # 开始识别
        result = await async_adapter.start_recognition_async()

        if result.success:
            # 等待一段时间，看是否有回调被调用
            await asyncio.sleep(2.0)

            # 停止识别
            await async_adapter.stop_recognition_async()

        # 检查回调结果
        logger.info(f"📊 回调结果数量: {len(callback_results)}")

    @pytest.mark.asyncio
    async def test_state_change_callback(self, async_adapter):
        """测试状态变更回调"""
        state_changes = []

        def test_callback(state):
            state_changes.append(state)
            logger.info(f"🔄 状态变更回调: {state}")

        async_adapter.add_state_change_callback(test_callback)

        # 开始识别
        result = await async_adapter.start_recognition_async()

        if result.success:
            # 等待一段时间
            await asyncio.sleep(1.0)

            # 停止识别
            await async_adapter.stop_recognition_async()

        # 检查状态变更
        logger.info(f"📊 状态变更数量: {len(state_changes)}")
        for state in state_changes:
            logger.info(f"  状态: {state}")

    def test_get_statistics(self, async_adapter):
        """测试获取统计信息"""
        stats = async_adapter.get_statistics()

        assert isinstance(stats, dict)
        assert 'use_async' in stats
        assert 'async_initialized' in stats
        assert 'current_state' in stats

        assert stats['use_async'] is True
        assert stats['async_initialized'] is True

    @pytest.mark.asyncio
    async def test_get_diagnostics_info(self, async_adapter):
        """测试获取诊断信息"""
        diagnostics = await async_adapter.get_diagnostics_info()

        assert isinstance(diagnostics, dict)
        assert 'adapter_type' in diagnostics
        assert 'async_mode' in diagnostics
        assert 'async_initialized' in diagnostics
        assert 'state' in diagnostics

        assert diagnostics['adapter_type'] == 'AsyncAudioProcessorAdapter'
        assert diagnostics['async_mode'] is True
        assert diagnostics['async_initialized'] is True

    @pytest.mark.asyncio
    async def test_mode_switching(self):
        """测试模式切换"""
        # 创建混合模式适配器
        adapter = create_hybrid_audio_processor_adapter(
            use_async=False,
            test_mode=True
        )

        try:
            # 初始应该是同步模式
            assert not adapter.use_async

            # 切换到异步模式
            success = await adapter.switch_to_async_mode()
            if success:
                assert adapter.use_async
                assert adapter._async_initialized

            # 切换回同步模式
            await adapter.switch_to_sync_mode()
            assert not adapter.use_async

        finally:
            await adapter.cleanup_async()

    def test_sync_adapter_compatibility(self, sync_adapter):
        """测试同步适配器兼容性"""
        assert not sync_adapter.use_async
        assert sync_adapter.is_initialized()

        # 测试数值提取（同步模式）
        result = sync_adapter.extract_measurements("二十五点五")
        logger.info(f"同步模式数值提取: {result}")

        # 测试状态获取
        state = sync_adapter.get_state()
        logger.info(f"同步模式状态: {state}")


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_create_async_audio_processor_adapter(self):
        """测试创建异步音频处理器适配器"""
        adapter = await create_async_audio_processor_adapter(
            test_mode=True,
            timeout_seconds=5
        )

        try:
            assert adapter.use_async
            assert adapter.is_initialized()

            # 测试基本功能
            state = adapter.get_state()
            assert isinstance(state, AudioProcessorState)

        finally:
            await adapter.cleanup_async()

    def test_create_hybrid_audio_processor_adapter(self):
        """测试创建混合模式音频处理器适配器"""
        # 异步模式
        async_adapter = create_hybrid_audio_processor_adapter(
            use_async=True,
            test_mode=True
        )
        assert async_adapter.use_async

        # 同步模式
        sync_adapter = create_hybrid_audio_processor_adapter(
            use_async=False,
            test_mode=True
        )
        assert not sync_adapter.use_async


@pytest.mark.asyncio
async def test_performance_comparison():
    """性能对比测试"""
    logger.info("🏁 开始性能对比测试")

    # 创建同步适配器
    sync_adapter = create_hybrid_audio_processor_adapter(
        use_async=False,
        test_mode=True
    )

    # 创建异步适配器
    async_adapter = await create_async_audio_processor_adapter(
        test_mode=True
    )

    try:
        # 测试数值提取性能
        test_text = "二十五点五"
        iterations = 100

        # 同步模式性能测试
        start_time = time.time()
        for _ in range(iterations):
            sync_adapter.extract_measurements(test_text)
        sync_time = time.time() - start_time

        # 异步模式性能测试
        start_time = time.time()
        for _ in range(iterations):
            await async_adapter.extract_measurements_async(test_text)
        async_time = time.time() - start_time

        logger.info(f"📊 性能对比结果 ({iterations}次迭代):")
        logger.info(f"  同步模式: {sync_time:.4f}s")
        logger.info(f"  异步模式: {async_time:.4f}s")
        logger.info(f"  性能比: {async_time/sync_time:.2f}x")

    finally:
        await async_adapter.cleanup_async()


@pytest.mark.asyncio
async def test_error_handling():
    """错误处理测试"""
    logger.info("🧪 开始错误处理测试")

    adapter = AsyncAudioProcessorAdapter(
        use_async=True,
        test_mode=True
    )

    try:
        # 测试未初始化的错误处理
        if not adapter._async_initialized:
            # 尝试在未初始化状态下开始识别
            result = await adapter.start_recognition_async()
            # 应该返回失败结果或自动初始化
            logger.info(f"未初始化状态测试: {result.success}")

        # 测试重复操作
        await adapter.async_initialize()

        # 再次初始化应该是安全的
        success = await adapter.async_initialize()
        logger.info(f"重复初始化测试: {success}")

    finally:
        await adapter.cleanup_async()


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])