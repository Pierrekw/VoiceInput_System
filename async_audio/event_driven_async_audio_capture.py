# -*- coding: utf-8 -*-
"""
事件驱动的异步音频捕获器

将事件系统集成到AsyncAudioCapture中，实现事件驱动的音频处理。
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List

from events import (
    EventBus, AsyncEventBus, EventHandler,
    AudioStreamStartedEvent, AudioStreamStoppedEvent,
    AudioDataReceivedEvent, RecognitionStartedEvent,
    RecognitionCompletedEvent, RecognitionPartialEvent,
    TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent,
    ComponentStateChangedEvent, ErrorEvent,
    PerformanceMetricEvent, create_error_event
)
from .async_audio_capture import AsyncAudioCapture, AsyncAudioProcessorState

logger = logging.getLogger(__name__)


class EventDrivenAsyncAudioCapture(AsyncAudioCapture):
    """事件驱动的异步音频捕获器"""

    def __init__(
        self,
        event_bus: Optional[AsyncEventBus] = None,
        **kwargs
    ):
        """
        初始化事件驱动的异步音频捕获器

        Args:
            event_bus: 事件总线实例
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)
        self._event_bus = event_bus or AsyncEventBus()
        self._event_handlers: List[EventHandler] = []

    async def initialize(self) -> bool:
        """异步初始化"""
        logger.info("🚀 初始化事件驱动异步音频捕获器...")

        try:
            # 启动事件总线
            await self._event_bus.start()

            # 注册事件处理器
            await self._register_event_handlers()

            # 初始化基础组件
            success = await super().initialize()

            if success:
                # 发布初始化完成事件
                await self._publish_component_event("initialized")

            logger.info("✅ 事件驱动异步音频捕获器初始化完成")
            return success

        except Exception as e:
            logger.error(f"❌ 事件驱动异步音频捕获器初始化失败: {e}")
            await self._publish_error_event("initialization_failed", str(e))
            return False

    async def _register_event_handlers(self) -> None:
        """注册事件处理器"""
        logger.debug("📝 注册事件处理器...")

        # 创建处理器实例
        metrics_handler = AudioMetricsHandler(self)
        state_handler = AudioStateHandler(self)
        tts_handler = TTSEventHandler(self)

        # 注册处理器
        await self._event_bus.subscribe(AudioStreamStartedEvent, metrics_handler)
        await self._event_bus.subscribe(AudioStreamStoppedEvent, metrics_handler)
        await self._event_bus.subscribe(RecognitionCompletedEvent, metrics_handler)
        await self._event_bus.subscribe(RecognitionStartedEvent, state_handler)
        await self._event_bus.subscribe(RecognitionCompletedEvent, state_handler)
        await self._event_bus.subscribe(TTSPlaybackStartedEvent, tts_handler)
        await self._event_bus.subscribe(TTSPlaybackCompletedEvent, tts_handler)

        # 保存处理器引用
        self._event_handlers.extend([metrics_handler, state_handler, tts_handler])

        logger.debug(f"✅ 已注册 {len(self._event_handlers)} 个事件处理器")

    async def start_recognition(self) -> Dict[str, Any]:
        """开始语音识别（事件驱动版本）"""
        logger.info("🎤 开始事件驱动语音识别...")

        async with self._state_lock:
            if self._state not in [AsyncAudioProcessorState.IDLE, AsyncAudioProcessorState.STOPPED]:
                return {
                    "success": False,
                    "error_message": f"Invalid state for start: {self._state}",
                    "timestamp": time.time()
                }

            await self._set_state(AsyncAudioProcessorState.RUNNING)

        try:
            # 重置事件
            self._stop_event.clear()
            self._pause_event.set()

            # 发布识别开始事件
            await self._publish_recognition_started_event()

            # 启动处理任务
            self._capture_task = asyncio.create_task(self._audio_capture_worker())
            self._recognition_task = asyncio.create_task(self._recognition_worker())
            self._monitor_task = asyncio.create_task(self._monitor_worker())

            # 更新统计信息
            self._stats['start_time'] = time.time()
            self._stats['last_activity'] = time.time()

            logger.info("✅ 事件驱动语音识别已启动")
            return {
                "success": True,
                "text": "",
                "confidence": 1.0,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"❌ 启动事件驱动语音识别失败: {e}")
            await self._set_state(AsyncAudioProcessorState.ERROR)
            await self._publish_error_event("start_recognition_failed", str(e))
            return {
                "success": False,
                "error_message": str(e),
                "timestamp": time.time()
            }

    async def stop_recognition(self) -> Dict[str, Any]:
        """停止语音识别（事件驱动版本）"""
        logger.info("🛑 停止事件驱动语音识别...")

        async with self._state_lock:
            if self._state == AsyncAudioProcessorState.IDLE:
                return {
                    "success": True,
                    "text": "Already stopped",
                    "confidence": 1.0,
                    "timestamp": time.time()
                }

            await self._set_state(AsyncAudioProcessorState.STOPPING)

        try:
            # 设置停止事件
            self._stop_event.set()

            # 等待任务完成
            tasks = [t for t in [self._capture_task, self._recognition_task, self._monitor_task] if t and not t.done()]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            await self._set_state(AsyncAudioProcessorState.STOPPED)

            # 发布识别完成事件
            await self._publish_recognition_completed_event()

            logger.info("✅ 事件驱动语音识别已停止")
            return {
                "success": True,
                "text": "",
                "confidence": 1.0,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"❌ 停止事件驱动语音识别失败: {e}")
            await self._set_state(AsyncAudioProcessorState.ERROR)
            await self._publish_error_event("stop_recognition_failed", str(e))
            return {
                "success": False,
                "error_message": str(e),
                "timestamp": time.time()
            }

    async def _audio_capture_worker(self) -> None:
        """音频采集工作协程（事件驱动版本）"""
        logger.debug("🎙️ 启动事件驱动音频采集工作协程")

        try:
            while not self._stop_event.is_set():
                # 检查暂停状态
                if not self._pause_event.is_set():
                    await asyncio.sleep(0.1)
                    continue

                # 读取音频数据
                audio_chunk = await self.audio_stream.read_chunk()
                if audio_chunk:
                    # 发布音频数据事件
                    await self._publish_audio_data_event(audio_chunk)

                    # 非阻塞入队
                    try:
                        self._audio_queue.put_nowait(audio_chunk)
                        self._stats['captured_chunks'] += 1
                        self._stats['last_activity'] = time.time()
                    except asyncio.QueueFull:
                        logger.warning("⚠️ 音频队列已满，丢弃音频块")
                        await self._publish_error_event("audio_queue_full", "Audio queue is full")

                await asyncio.sleep(0.001)  # 短暂休眠避免CPU占用过高

        except Exception as e:
            logger.error(f"❌ 事件驱动音频采集工作协程异常: {e}")
            await self._publish_error_event("audio_capture_worker_error", str(e))

    async def _recognition_worker(self) -> None:
        """语音识别工作协程（事件驱动版本）"""
        logger.debug("🧠 启动事件驱动语音识别工作协程")

        try:
            while not self._stop_event.is_set():
                # 检查暂停状态
                if not self._pause_event.is_set():
                    await asyncio.sleep(0.1)
                    continue

                try:
                    # 获取音频数据
                    audio_chunk = await asyncio.wait_for(
                        self._audio_queue.get(),
                        timeout=1.0
                    )

                    # 发布部分识别结果事件
                    partial_text = await self.recognizer.get_partial_result()
                    if partial_text:
                        await self._publish_partial_recognition_event(partial_text)

                    # 处理语音识别
                    text = await self.recognizer.process_audio(audio_chunk)

                    if text and text.strip():
                        # 发布识别完成事件
                        await self._publish_recognition_completed_event(text)

                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环
                    continue

                except Exception as e:
                    logger.error(f"❌ 事件驱动语音识别处理失败: {e}")
                    self._stats['errors'] += 1

        except Exception as e:
            logger.error(f"❌ 事件驱动语音识别工作协程异常: {e}")
            await self._publish_error_event("recognition_worker_error", str(e))

    async def _monitor_worker(self) -> None:
        """监控工作协程（事件驱动版本）"""
        logger.debug("👁️ 启动事件驱动监控工作协程")

        try:
            last_metric_time = time.time()

            while not self._stop_event.is_set():
                current_time = time.time()

                # 检查超时
                if self._stats['start_time']:
                    elapsed = current_time - self._stats['start_time']
                    if elapsed > self.timeout_seconds:
                        logger.info(f"⏰ 识别超时 ({self.timeout_seconds}s)")
                        await self.stop_recognition()
                        break

                # 检查活动状态
                if self._stats['last_activity']:
                    inactive_time = current_time - self._stats['last_activity']
                    if inactive_time > 10.0:  # 10秒无活动
                        logger.warning("⚠️ 长时间无音频活动")

                # 定期发布性能指标事件
                if current_time - last_metric_time >= 5.0:  # 每5秒发布一次
                    await self._publish_performance_metrics()
                    last_metric_time = current_time

                await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"❌ 事件驱动监控工作协程异常: {e}")

    # 事件发布方法

    async def _publish_component_event(self, action: str) -> None:
        """发布组件事件"""
        event = ComponentStateChangedEvent(
            source="EventDrivenAsyncAudioCapture",
            component="AudioCapture",
            old_state="",
            new_state=action
        )
        await self._event_bus.publish(event)

    async def _publish_error_event(self, error_type: str, error_message: str) -> None:
        """发布错误事件"""
        event = ErrorEvent(
            source="EventDrivenAsyncAudioCapture",
            component="AudioCapture",
            error_type=error_type,
            error_message=error_message
        )
        await self._event_bus.publish(event)

    async def _publish_recognition_started_event(self) -> None:
        """发布识别开始事件"""
        event = RecognitionStartedEvent(
            source="EventDrivenAsyncAudioCapture",
            recognizer_id=f"recognizer_{int(time.time() * 1000)}",
            language="zh-CN"
        )
        await self._event_bus.publish(event)

    async def _publish_recognition_completed_event(self, text: str = "") -> None:
        """发布识别完成事件"""
        # 提取数值
        measurements = []
        if text:
            from .async_number_extractor import extract_measurements
            try:
                measurements = await extract_measurements(text)
            except Exception as e:
                logger.warning(f"⚠️ 提取数值失败: {e}")

        event = RecognitionCompletedEvent(
            source="EventDrivenAsyncAudioCapture",
            recognizer_id=f"recognizer_{int(time.time() * 1000)}",
            text=text,
            confidence=0.8,  # TODO: 实际计算置信度
            measurements=measurements
        )
        await self._event_bus.publish(event)

    async def _publish_partial_recognition_event(self, partial_text: str) -> None:
        """发布部分识别结果事件"""
        event = RecognitionPartialEvent(
            source="EventDrivenAsyncAudioCapture",
            recognizer_id=f"recognizer_{int(time.time() * 1000)}",
            partial_text=partial_text,
            confidence=0.5
        )
        await self._event_bus.publish(event)

    async def _publish_audio_data_event(self, audio_chunk) -> None:
        """发布音频数据事件"""
        event = AudioDataReceivedEvent(
            source="EventDrivenAsyncAudioCapture",
            stream_id="main_stream",
            audio_data=audio_chunk.data,
            size=audio_chunk.size,
            sequence_number=self._stats['captured_chunks']
        )
        await self._event_bus.publish(event)

    async def _publish_performance_metrics(self) -> None:
        """发布性能指标事件"""
        uptime = time.time() - (self._stats.get('start_time') or time.time())
        event = PerformanceMetricEvent(
            source="EventDrivenAsyncAudioCapture",
            component="AudioCapture",
            metric_name="processing_efficiency",
            metric_value=self._stats['captured_chunks'] / max(1, uptime),
            metric_unit="chunks/sec"
        )
        await self._event_bus.publish(event)

    async def cleanup(self) -> None:
        """清理资源"""
        logger.info("🧹 清理事件驱动异步音频捕获器资源...")

        try:
            # 停止识别
            if self._state in [AsyncAudioProcessorState.RUNNING, AsyncAudioProcessorState.PAUSED]:
                await self.stop_recognition()

            # 停止TTS播放
            await self.tts_player.stop()

            # 关闭音频流
            await self.audio_stream.close()

            # 停止事件总线
            await self._event_bus.stop()

            logger.info("✅ 事件驱动异步音频捕获器资源清理完成")

        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")


# 事件处理器类

class AudioMetricsHandler(EventHandler):
    """音频指标事件处理器"""

    def __init__(self, audio_capture):
        self.audio_capture = audio_capture

    async def handle(self, event):
        """处理指标事件"""
        if isinstance(event, PerformanceMetricEvent):
            logger.info(f"📊 音频指标: {event.metric_name} = {event.metric_value:.3f} {event.metric_unit}")


class AudioStateHandler(EventHandler):
    """音频状态事件处理器"""

    def __init__(self, audio_capture):
        self.audio_capture = audio_capture

    async def handle(self, event):
        """处理状态事件"""
        if isinstance(event, RecognitionStartedEvent):
            logger.info(f"🎤 识别已启动 (ID: {event.recognizer_id})")
        elif isinstance(event, RecognitionCompletedEvent):
            logger.info(f"🗣️ 识别完成: '{event.text}' (提取到 {len(event.measurements or [])} 个数值)")


class TTSEventHandler(EventHandler):
    """TTS事件处理器"""

    def __init__(self, audio_capture):
        self.audio_capture = audio_capture

    async def handle(self, event):
        """处理TTS事件"""
        if isinstance(event, TTSPlaybackStartedEvent):
            logger.info(f"🔊 TTS播放开始: '{event.text}'")
        elif isinstance(event, TTSPlaybackCompletedEvent):
            logger.info(f"🔇 TTS播放完成: '{event.text}' (耗时: {event.duration:.2f}s)")


# 便捷函数

async def create_event_driven_audio_capture(
    sample_rate: int = 16000,
    chunk_size: int = 8000,
    model_path: Optional[str] = None,
    timeout_seconds: int = 30,
    test_mode: bool = False,
    event_bus: Optional[AsyncEventBus] = None
) -> EventDrivenAsyncAudioCapture:
    """创建事件驱动的异步音频捕获器的便捷函数"""
    capture = EventDrivenAsyncAudioCapture(
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        model_path=model_path,
        timeout_seconds=timeout_seconds,
        test_mode=test_mode,
        event_bus=event_bus
    )

    await capture.initialize()
    return capture