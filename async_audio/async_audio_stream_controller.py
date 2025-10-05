# -*- coding: utf-8 -*-
"""
异步音频流控制器

提供精确的异步音频流控制，避免TTS回声问题。
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
import time


class StreamState(Enum):
    """音频流状态"""
    IDLE = "idle"
    ACTIVE = "active"
    MUTED = "muted"
    STOPPED = "stopped"


@dataclass
class StreamConfig:
    """音频流配置"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format_type: str = "int16"
    buffer_size: int = 8192


class AsyncAudioStreamController:
    """异步音频流控制器"""

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.state = StreamState.IDLE
        self.state_lock = asyncio.Lock()

        # 事件回调
        self.callbacks: Dict[str, List[Callable]] = {
            'on_data': [],
            'on_state_change': [],
            'on_mute': [],
            'on_unmute': []
        }

        # 性能监控
        self.metrics = {
            'chunks_processed': 0,
            'bytes_processed': 0,
            'last_activity': 0.0,
            'muted_duration': 0.0
        }

    async def start(self):
        """启动音频流"""
        async with self.state_lock:
            if self.state == StreamState.STOPPED:
                return False

            old_state = self.state
            self.state = StreamState.ACTIVE
            await self._notify_state_change(old_state, self.state)

        logging.info("🎤 音频流控制器已启动")
        return True

    async def stop(self):
        """停止音频流"""
        async with self.state_lock:
            old_state = self.state
            self.state = StreamState.STOPPED
            await self._notify_state_change(old_state, self.state)

        logging.info("🛑 音频流控制器已停止")

    async def mute(self, reason: str = "TTS播放"):
        """静音音频流"""
        async with self.state_lock:
            if self.state == StreamState.MUTED:
                return

            old_state = self.state
            self.state = StreamState.MUTED
            self.metrics['muted_duration'] = time.time()

            await self._notify_state_change(old_state, self.state)
            await self._notify_mute(reason)

        logging.info(f"🔇 音频流已静音: {reason}")

    async def unmute(self):
        """取消静音音频流"""
        async with self.state_lock:
            if self.state != StreamState.MUTED:
                return

            old_state = self.state
            self.state = StreamState.ACTIVE

            # 计算静音持续时间
            if self.metrics['muted_duration'] > 0:
                muted_duration = time.time() - self.metrics['muted_duration']
                self.metrics['muted_duration'] = 0
                logging.info(f"🎤 音频流静音持续时间: {muted_duration:.2f}秒")

            await self._notify_state_change(old_state, self.state)
            await self._notify_unmute()

        logging.info("🎤 音频流已恢复")

    def add_callback(self, event: str, callback: Callable):
        """添加事件回调"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable):
        """移除事件回调"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)

    async def process_audio_chunk(self, chunk: bytes) -> bool:
        """处理音频块"""
        async with self.state_lock:
            if self.state in [StreamState.STOPPED, StreamState.MUTED]:
                return False

            self.metrics['chunks_processed'] += 1
            self.metrics['bytes_processed'] += len(chunk)
            self.metrics['last_activity'] = time.time()

        # 调用数据回调
        for callback in self.callbacks['on_data']:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(chunk)
                else:
                    callback(chunk)
            except Exception as e:
                logging.error(f"音频数据回调错误: {e}")

        return True

    async def get_state(self) -> StreamState:
        """获取当前状态"""
        async with self.state_lock:
            return self.state

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()

    async def _notify_state_change(self, old_state: StreamState, new_state: StreamState):
        """通知状态变化"""
        for callback in self.callbacks['on_state_change']:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_state, new_state)
                else:
                    callback(old_state, new_state)
            except Exception as e:
                logging.error(f"状态变化通知错误: {e}")

    async def _notify_mute(self, reason: str):
        """通知静音事件"""
        for callback in self.callbacks['on_mute']:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason)
                else:
                    callback(reason)
            except Exception as e:
                logging.error(f"静音通知错误: {e}")

    async def _notify_unmute(self):
        """通知取消静音事件"""
        for callback in self.callbacks['on_unmute']:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logging.error(f"取消静音通知错误: {e}")


class AsyncAudioBuffer:
    """异步音频缓冲区"""

    def __init__(self, size: int = 8192):
        self.size = size
        self.buffer = bytearray()
        self.read_lock = asyncio.Lock()
        self.write_lock = asyncio.Lock()
        self.not_empty = asyncio.Event()
        self.not_full = asyncio.Event()

    async def write(self, data: bytes) -> int:
        """异步写入数据"""
        async with self.write_lock:
            # 等待缓冲区有空间
            while len(self.buffer) + len(data) > self.size:
                await self.not_full.wait()

            # 写入数据
            self.buffer.extend(data)
            bytes_written = len(data)

            # 通知有数据可读
            if bytes_written > 0:
                self.not_empty.set()

            # 如果缓冲区满了，通知写操作需要等待
            if len(self.buffer) >= self.size:
                self.not_full.clear()

        return bytes_written

    async def read(self, max_bytes: int = None) -> bytes:
        """异步读取数据"""
        async with self.read_lock:
            # 等待缓冲区有数据
            while len(self.buffer) == 0:
                await self.not_empty.wait()

            # 计算读取字节数
            if max_bytes is None or max_bytes > len(self.buffer):
                bytes_to_read = len(self.buffer)
            else:
                bytes_to_read = max_bytes

            # 读取数据
            data = bytes(self.buffer[:bytes_to_read])
            del self.buffer[:bytes_to_read]

            # 通知缓冲区有空间可写
            if len(self.buffer) < self.size:
                self.not_full.set()

            # 如果缓冲区空了，通知读操作需要等待
            if len(self.buffer) == 0:
                self.not_empty.clear()

        return data

    def size_available(self) -> int:
        """获取可用空间大小"""
        return self.size - len(self.buffer)

    def size_used(self) -> int:
        """获取已使用空间大小"""
        return len(self.buffer)


class TTSController:
    """TTS控制器 - 管理TTS播放和音频静音"""

    def __init__(self, audio_controller: AsyncAudioStreamController):
        self.audio_controller = audio_controller
        self.tts_queue = asyncio.Queue()
        self.is_running = False
        self.current_tts = None

    async def start(self):
        """启动TTS控制器"""
        self.is_running = True
        asyncio.create_task(self._tts_worker_loop())
        logging.info("🔊 TTS控制器已启动")

    async def stop(self):
        """停止TTS控制器"""
        self.is_running = False
        await self.tts_queue.put("__STOP__")
        logging.info("🔇 TTS控制器已停止")

    async def speak(self, text: str, priority: int = 0):
        """异步播放TTS"""
        await self.tts_queue.put((priority, time.time(), text))

    async def _tts_worker_loop(self):
        """TTS工作循环"""
        while self.is_running:
            try:
                # 获取TTS任务
                item = await self.tts_queue.get()

                if item == "__STOP__":
                    break

                priority, timestamp, text = item

                # 开始播放TTS
                await self._start_tts_playback(text)

                # 模拟TTS播放
                await self._simulate_tts_playback(text)

                # 结束播放TTS
                await self._end_tts_playback(text)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"TTS工作循环错误: {e}")

    async def _start_tts_playback(self, text: str):
        """开始TTS播放"""
        self.current_tts = text
        await self.audio_controller.mute(f"TTS播放: {text}")

        # 发布TTS开始事件
        try:
            from events.event_types import TTSPlaybackStartedEvent
            from main_production import ProductionVoiceSystem  # 避免循环导入
        except ImportError:
            pass

    async def _simulate_tts_playback(self, text: str):
        """模拟TTS播放（实际实现中应该集成真实的TTS引擎）"""
        # 估算播放时间（每个汉字约0.15秒）
        estimated_duration = len(text) * 0.15
        await asyncio.sleep(min(estimated_duration, 5.0))

    async def _end_tts_playback(self, text: str):
        """结束TTS播放"""
        # 短暂静音，避免立即被识别到
        await asyncio.sleep(0.05)
        await self.audio_controller.unmute()
        self.current_tts = None

        # 发布TTS结束事件
        try:
            from events.event_types import TTSPlaybackCompletedEvent
            from main_production import ProductionVoiceSystem
        except ImportError:
            pass

    def is_playing(self) -> bool:
        """检查是否正在播放TTS"""
        return self.current_tts is not None

    async def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """等待当前TTS播放完成"""
        start_time = time.time()

        while self.is_playing():
            if timeout and (time.time() - start_time) > timeout:
                return False
            await asyncio.sleep(0.01)

        return True