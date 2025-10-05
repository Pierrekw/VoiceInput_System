# -*- coding: utf-8 -*-
"""
事件驱动架构演示

展示完整的事件驱动音频处理系统，包括事件发布、订阅和处理。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from events import (
    AsyncEventBus, EventHandler, EventPriority,
    AudioStreamStartedEvent, AudioStreamStoppedEvent,
    AudioDataReceivedEvent, RecognitionStartedEvent,
    RecognitionCompletedEvent, RecognitionPartialEvent,
    TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent,
    ComponentStateChangedEvent, ErrorEvent,
    PerformanceMetricEvent, SystemStartedEvent, SystemShutdownEvent,
    create_error_event, create_metric_event
)
from events.system_coordinator import SystemCoordinator, get_global_coordinator
# from async_audio.event_driven_async_audio_capture import EventDrivenAsyncAudioCapture
# from async_audio.async_audio_capture import AsyncAudioCapture
# from audio_capture_v import AudioCapture

# 模拟导入，避免依赖问题
import asyncio
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoEventHandler(EventHandler):
    """演示事件处理器"""

    def __init__(self, name: str):
        super().__init__(name)
        self.received_events = []

    async def handle(self, event) -> None:
        """处理事件"""
        self.received_events.append(event)
        logger.info(f"📝 [{self.name}] 收到事件: {event.get_summary()}")


class AudioMetricsCollector(EventHandler):
    """音频指标收集器"""

    def __init__(self):
        super().__init__("AudioMetricsCollector")
        self.metrics = {
            "audio_chunks": 0,
            "recognition_count": 0,
            "tts_playbacks": 0,
            "errors": 0,
            "start_time": time.time()
        }

    async def handle(self, event) -> None:
        """收集指标"""
        if isinstance(event, AudioDataReceivedEvent):
            self.metrics["audio_chunks"] += 1
        elif isinstance(event, RecognitionCompletedEvent):
            self.metrics["recognition_count"] += 1
        elif isinstance(event, TTSPlaybackCompletedEvent):
            self.metrics["tts_playbacks"] += 1
        elif isinstance(event, ErrorEvent):
            self.metrics["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        uptime = time.time() - self.metrics["start_time"]
        return {
            **self.metrics,
            "uptime": uptime,
            "audio_chunks_per_sec": self.metrics["audio_chunks"] / max(1, uptime)
        }


class SystemHealthMonitor(EventHandler):
    """系统健康监控器"""

    def __init__(self, coordinator: SystemCoordinator):
        super().__init__("SystemHealthMonitor")
        self.coordinator = coordinator
        self.last_health_check = 0
        self.health_check_interval = 10.0  # 10秒检查一次

    async def handle(self, event) -> None:
        """监控系统健康状态"""
        current_time = time.time()

        # 定期健康检查
        if current_time - self.last_health_check > self.health_check_interval:
            await self._perform_health_check()
            self.last_health_check = current_time

        # 处理错误事件
        if isinstance(event, ErrorEvent):
            logger.warning(f"🚨 检测到错误: {event.get_summary()}")
            await self._handle_error(event)

    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        health = await self.coordinator.get_system_health()
        logger.info(f"🏥 系统健康状态: {health['health_score']:.1f}% "
                   f"({health['healthy_components']}/{health['total_components']} 组件健康)")

    async def _handle_error(self, error_event: ErrorEvent) -> None:
        """处理错误事件"""
        if error_event.priority == EventPriority.CRITICAL:
            logger.critical("🆘 检测到关键错误，可能需要紧急处理")


class PerformanceAnalyzer(EventHandler):
    """性能分析器"""

    def __init__(self):
        super().__init__("PerformanceAnalyzer")
        self.performance_data = []
        self.event_counts = {}

    async def handle(self, event) -> None:
        """分析性能"""
        # 记录事件类型
        event_type = event.event_type
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # 分析性能指标事件
        if isinstance(event, PerformanceMetricEvent):
            self.performance_data.append({
                "timestamp": time.time(),
                "metric_name": event.metric_name,
                "metric_value": event.metric_value,
                "component": event.component
            })

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_data:
            return {"message": "暂无性能数据"}

        # 计算平均性能指标
        metrics = {}
        for data in self.performance_data:
            name = data["metric_name"]
            value = data["metric_value"]
            if name not in metrics:
                metrics[name] = []
            metrics[name].append(value)

        avg_metrics = {name: sum(values) / len(values) for name, values in metrics.items()}

        return {
            "total_events": sum(self.event_counts.values()),
            "event_types": self.event_counts,
            "performance_metrics": avg_metrics,
            "data_points": len(self.performance_data)
        }


class MockEventDrivenAsyncAudioCapture:
    """模拟事件驱动音频捕获器"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.initialized = False

    async def initialize(self) -> bool:
        """模拟初始化"""
        await asyncio.sleep(0.1)  # 模拟初始化时间
        self.initialized = True
        return True

    async def cleanup(self) -> None:
        """模拟清理"""
        await asyncio.sleep(0.1)  # 模拟清理时间
        self.initialized = False


async def create_demo_audio_capture() -> MockEventDrivenAsyncAudioCapture:
    """创建演示用的音频捕获器"""
    logger.info("🎙️ 创建事件驱动音频捕获器...")

    capture = MockEventDrivenAsyncAudioCapture(
        sample_rate=16000,
        chunk_size=8000,
        model_path=None,  # 使用默认模型
        timeout_seconds=5,
        test_mode=True  # 测试模式
    )

    success = await capture.initialize()
    if not success:
        logger.error("❌ 音频捕获器初始化失败")
        return None

    logger.info("✅ 音频捕获器初始化成功")
    return capture


async def setup_event_system(coordinator: SystemCoordinator) -> Dict[str, Any]:
    """设置事件系统"""
    logger.info("⚙️ 设置事件系统...")

    # 创建事件处理器
    demo_handler = DemoEventHandler("DemoHandler")
    metrics_collector = AudioMetricsCollector()
    health_monitor = SystemHealthMonitor(coordinator)
    performance_analyzer = PerformanceAnalyzer()

    # 获取事件总线
    event_bus = coordinator._event_bus

    # 订阅各种事件
    await event_bus.subscribe(AudioStreamStartedEvent, demo_handler)
    await event_bus.subscribe(AudioStreamStoppedEvent, demo_handler)
    await event_bus.subscribe(RecognitionStartedEvent, demo_handler)
    await event_bus.subscribe(RecognitionCompletedEvent, demo_handler)
    await event_bus.subscribe(TTSPlaybackStartedEvent, demo_handler)
    await event_bus.subscribe(TTSPlaybackCompletedEvent, demo_handler)

    # 订阅指标事件
    await event_bus.subscribe(AudioDataReceivedEvent, metrics_collector)
    await event_bus.subscribe(RecognitionCompletedEvent, metrics_collector)
    await event_bus.subscribe(TTSPlaybackCompletedEvent, metrics_collector)
    await event_bus.subscribe(ErrorEvent, metrics_collector)

    # 订阅系统事件
    await event_bus.subscribe_all(health_monitor)
    await event_bus.subscribe(PerformanceMetricEvent, performance_analyzer)

    logger.info("✅ 事件系统设置完成")

    return {
        "demo_handler": demo_handler,
        "metrics_collector": metrics_collector,
        "health_monitor": health_monitor,
        "performance_analyzer": performance_analyzer
    }


async def simulate_audio_processing(capture: MockEventDrivenAsyncAudioCapture,
                                  event_bus: AsyncEventBus,
                                  duration: float = 30.0) -> None:
    """模拟音频处理流程"""
    logger.info(f"🎬 开始模拟音频处理 (持续 {duration}s)...")

    start_time = time.time()

    # 模拟音频流启动
    await event_bus.publish(AudioStreamStartedEvent(
        source="Demo",
        stream_id="demo_stream",
        sample_rate=16000
    ))

    # 模拟识别开始
    await event_bus.publish(RecognitionStartedEvent(
        source="Demo",
        recognizer_id="demo_recognizer",
        language="zh-CN"
    ))

    # 模拟持续的音频处理
    chunk_count = 0
    while time.time() - start_time < duration:
        # 模拟音频数据接收
        await event_bus.publish(AudioDataReceivedEvent(
            source="Demo",
            stream_id="demo_stream",
            audio_data=b"fake_audio_data",
            size=1024,
            sequence_number=chunk_count
        ))

        # 模拟部分识别结果
        if chunk_count % 10 == 0:
            await event_bus.publish(RecognitionPartialEvent(
                source="Demo",
                recognizer_id="demo_recognizer",
                partial_text=f"部分识别结果 {chunk_count // 10}",
                confidence=0.6
            ))

        # 模拟完整识别结果
        if chunk_count % 20 == 0 and chunk_count > 0:
            await event_bus.publish(RecognitionCompletedEvent(
                source="Demo",
                recognizer_id="demo_recognizer",
                text=f"识别完成的文本 {chunk_count // 20}",
                confidence=0.85,
                measurements=[chunk_count * 0.1, chunk_count * 0.2]
            ))

            # 模拟TTS播放
            await event_bus.publish(TTSPlaybackStartedEvent(
                source="Demo",
                player_id="demo_player",
                text=f"识别完成的文本 {chunk_count // 20}"
            ))

            # 模拟TTS播放完成
            await asyncio.sleep(0.1)  # 短暂延迟模拟播放时间
            await event_bus.publish(TTSPlaybackCompletedEvent(
                source="Demo",
                player_id="demo_player",
                text=f"识别完成的文本 {chunk_count // 20}",
                duration=0.1,
                success=True
            ))

        # 模拟性能指标
        if chunk_count % 30 == 0:
            await event_bus.publish(PerformanceMetricEvent(
                source="Demo",
                component="AudioProcessor",
                metric_name="processing_latency",
                metric_value=0.05,
                metric_unit="seconds"
            ))

        chunk_count += 1
        await asyncio.sleep(0.1)  # 100ms间隔

    # 模拟音频流停止
    await event_bus.publish(AudioStreamStoppedEvent(
        source="Demo",
        stream_id="demo_stream",
        reason="normal_completion",
        duration=duration
    ))

    logger.info(f"✅ 音频处理模拟完成 (处理了 {chunk_count} 个音频块)")


async def demonstrate_error_handling(event_bus: AsyncEventBus) -> None:
    """演示错误处理"""
    logger.info("🚨 演示错误处理...")

    # 模拟一般错误
    await event_bus.publish(create_error_event(
        source="Demo",
        component="AudioProcessor",
        error_type="processing_error",
        error_message="模拟处理错误"
    ))

    await asyncio.sleep(0.5)

    # 模拟关键错误
    await event_bus.publish(create_error_event(
        source="Demo",
        component="SystemCore",
        error_type="critical_failure",
        error_message="模拟关键错误",
        priority=EventPriority.CRITICAL
    ))

    logger.info("✅ 错误处理演示完成")


async def print_system_status(handlers: Dict[str, Any],
                            coordinator: SystemCoordinator) -> None:
    """打印系统状态"""
    logger.info("📊 打印系统状态...")

    # 打印处理器统计
    for name, handler in handlers.items():
        if hasattr(handler, 'received_events'):
            logger.info(f"  {name}: 处理了 {len(handler.received_events)} 个事件")
        elif hasattr(handler, 'get_metrics'):
            metrics = handler.get_metrics()
            logger.info(f"  {name}: {metrics}")
        elif hasattr(handler, 'get_performance_summary'):
            summary = handler.get_performance_summary()
            logger.info(f"  {name}: {summary}")

    # 打印协调器状态
    health = await coordinator.get_system_health()
    logger.info(f"  系统健康: {health['health_score']:.1f}%")

    # 打印事件总线指标
    event_metrics = coordinator._event_bus.get_metrics()
    logger.info(f"  事件总线: {event_metrics['events_published']} 个事件已发布, "
               f"{event_metrics['events_processed']} 个已处理")


async def main():
    """主演示函数"""
    logger.info("🚀 开始事件驱动架构演示...")

    try:
        # 1. 创建并启动系统协调器
        coordinator = get_global_coordinator()
        await coordinator.start()

        # 2. 注册音频捕获组件
        await coordinator.register_component(
            "AudioCapture",
            "EventDrivenAsyncAudioCapture",
            dependencies=["EventBus"]
        )

        # 3. 设置事件系统
        handlers = await setup_event_system(coordinator)

        # 4. 创建音频捕获器
        capture = await create_demo_audio_capture()
        if not capture:
            logger.error("❌ 无法创建音频捕获器，演示终止")
            return

        # 5. 更新组件状态
        await coordinator.update_component_state("AudioCapture", "initialized")
        await coordinator.update_component_state("AudioCapture", "running")

        # 6. 模拟音频处理
        await simulate_audio_processing(capture, coordinator._event_bus, duration=10.0)

        # 7. 演示错误处理
        await demonstrate_error_handling(coordinator._event_bus)

        # 8. 打印系统状态
        await print_system_status(handlers, coordinator)

        # 9. 清理资源
        logger.info("🧹 清理资源...")
        await coordinator.update_component_state("AudioCapture", "stopped")
        await capture.cleanup()
        await coordinator.stop()

        logger.info("✅ 事件驱动架构演示完成!")

    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())