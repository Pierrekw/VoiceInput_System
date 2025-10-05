# -*- coding: utf-8 -*-
"""
异步音频捕获模块

基于asyncio的现代异步音频处理系统，替代原有的threading实现。
提供非阻塞的音频流处理、语音识别和TTS播放功能。
"""

import asyncio
import logging
import time
from typing import List, Optional, Callable, Dict, Any, AsyncIterator
from collections import deque
from dataclasses import dataclass
from enum import Enum
import pyaudio
import numpy as np
from contextlib import asynccontextmanager

from interfaces.audio_processor import (
    IAudioProcessor, RecognitionResult, VoiceCommand,
    AudioProcessorState
)

logger = logging.getLogger(__name__)


class AsyncAudioProcessorState(Enum):
    """异步音频处理器状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AudioChunk:
    """音频数据块"""
    data: bytes
    timestamp: float
    size: int

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class RecognitionTask:
    """语音识别任务"""
    audio_chunk: AudioChunk
    task_id: str
    callback: Optional[Callable[[RecognitionResult], None]] = None


@dataclass
class TTSRequest:
    """TTS播放请求"""
    text: str
    task_id: str
    priority: int = 0
    callback: Optional[Callable[[bool], None]] = None


class AsyncAudioStream:
    """异步音频流管理器"""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 8000):
        """
        初始化异步音频流

        Args:
            sample_rate: 采样率
            chunk_size: 音频块大小
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.pyaudio = None
        self.stream = None
        self._is_active = False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def open(self):
        """打开音频流"""
        if self._is_active:
            return

        logger.debug("🎤 打开异步音频流...")

        # 在线程池中执行PyAudio初始化（PyAudio是同步的）
        self.pyaudio = await asyncio.to_thread(pyaudio.PyAudio)

        try:
            # 获取默认音频设备
            default_device = await asyncio.to_thread(self.pyaudio.get_default_input_device_info)
            logger.debug(f"🎧 使用音频设备: {default_device['name']}")

            # 创建音频流
            self.stream = await asyncio.to_thread(
                self.pyaudio.open,
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                start=True
            )

            self._is_active = True
            logger.debug("✅ 异步音频流创建成功")

        except Exception as e:
            logger.error(f"❌ 异步音频流创建失败: {e}")
            await self.close()
            raise

    async def close(self):
        """关闭音频流"""
        if not self._is_active:
            return

        logger.debug("🔇 关闭异步音频流...")

        try:
            if self.stream:
                await asyncio.to_thread(self.stream.stop_stream)
                await asyncio.to_thread(self.stream.close)
                self.stream = None

            if self.pyaudio:
                await asyncio.to_thread(self.pyaudio.terminate)
                self.pyaudio = None

            self._is_active = False
            logger.debug("✅ 异步音频流已关闭")

        except Exception as e:
            logger.error(f"❌ 关闭异步音频流失败: {e}")

    async def read_chunk(self) -> Optional[AudioChunk]:
        """异步读取音频数据块 - 优化版本"""
        if not self._is_active or not self.stream:
            return None

        try:
            # 优化：使用更小的超时和更快的响应
            # 在线程池中执行阻塞的音频读取，使用更短的超时
            data = await asyncio.wait_for(
                asyncio.to_thread(
                    self.stream.read,
                    self.chunk_size,
                    exception_on_overflow=False
                ),
                timeout=0.1  # 100ms超时，比原来的500ms快很多
            )

            return AudioChunk(
                data=data,
                timestamp=time.time(),
                size=len(data)
            )

        except asyncio.TimeoutError:
            # 超时是正常的，表示没有音频数据，减少日志频率
            if hasattr(self, '_timeout_count'):
                self._timeout_count += 1
            else:
                self._timeout_count = 1

            # 每100次超时才记录一次日志
            if self._timeout_count % 100 == 0:
                logger.debug(f"音频读取超时 #{self._timeout_count}，继续...")
            return None

        except Exception as e:
            logger.error(f"❌ 读取音频数据失败: {e}")
            return None

    @property
    def is_active(self) -> bool:
        """检查音频流是否活跃"""
        return bool(self._is_active and self.stream and self.stream.is_active())


class AsyncRecognizer:
    """异步语音识别器"""

    def __init__(self, model_path: Optional[str] = None):
        """
        初始化异步语音识别器

        Args:
            model_path: 语音模型路径
        """
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self._is_initialized = False

    async def initialize(self):
        """异步初始化识别器"""
        logger.debug(f"🧠 初始化异步语音识别器... current_state: _is_initialized={self._is_initialized}")
        if self._is_initialized:
            logger.debug("🧠 识别器已初始化，跳过")
            return

        logger.debug("🧠 开始初始化异步语音识别器...")

        try:
            # 在线程池中加载模型（Vosk是同步的）
            if self.model_path:
                logger.debug(f"🧠 加载模型: {self.model_path}")
                self.model = await asyncio.to_thread(
                    lambda: __import__('vosk').Model(self.model_path)
                )
                logger.debug(f"🧠 模型加载成功: {self.model is not None}")

                self.recognizer = await asyncio.to_thread(
                    lambda: __import__('vosk').KaldiRecognizer(self.model, 16000)
                )
                logger.debug(f"🧠 识别器创建成功: {self.recognizer is not None}")

            self._is_initialized = True
            logger.debug(f"✅ 异步语音识别器初始化成功: _is_initialized={self._is_initialized}, recognizer={self.recognizer is not None}")

        except Exception as e:
            logger.error(f"❌ 异步语音识别器初始化失败: {e}")
            self._is_initialized = False
            self.recognizer = None
            raise

    async def process_audio(self, audio_chunk: AudioChunk) -> Optional[str]:
        """异步处理音频数据"""
        if not self._is_initialized or not self.recognizer:
            return None

        try:
            # 验证音频数据
            if not audio_chunk or not audio_chunk.data:
                logger.debug("🔍 空音频块，跳过处理")
                return None

            if len(audio_chunk.data) == 0:
                logger.debug("🔍 音频数据长度为0，跳过处理")
                return None

            # 在线程池中执行语音识别
            result = await asyncio.to_thread(
                self.recognizer.AcceptWaveform,
                audio_chunk.data
            )

            if result:
                # 获取识别结果
                final_result = await asyncio.to_thread(
                    self.recognizer.Result
                )
                import json
                result_dict = json.loads(final_result)
                return result_dict.get('text', '')

        except Exception as e:
            logger.error(f"❌ 语音识别失败: {e}")
            logger.debug(f"🔍 音频块信息: size={len(audio_chunk.data) if audio_chunk else 0}, timestamp={audio_chunk.timestamp if audio_chunk else None}")
            # 不重新抛出异常，继续处理下一个音频块

        return None

    async def get_partial_result(self) -> Optional[str]:
        """获取部分识别结果"""
        if not self._is_initialized or not self.recognizer:
            return None

        try:
            partial_result = await asyncio.to_thread(
                self.recognizer.PartialResult
            )
            import json
            result_dict = json.loads(partial_result)
            return result_dict.get('partial', '')

        except Exception as e:
            logger.error(f"❌ 获取部分识别结果失败: {e}")

        return None

    async def get_final_result(self) -> Optional[str]:
        """获取最终识别结果"""
        logger.debug(f"🔍 get_final_result调用: _is_initialized={self._is_initialized}, recognizer={self.recognizer is not None}")

        # 检查事件循环是否还在运行
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("🔍 事件循环已关闭，无法获取最终结果")
            return None

        if not self._is_initialized or not self.recognizer:
            logger.debug(f"🔍 识别器未初始化: initialized={self._is_initialized}, recognizer_exists={self.recognizer is not None}")
            return None

        try:
            logger.debug("🔍 调用Vosk FinalResult...")
            final_result = await asyncio.to_thread(
                self.recognizer.FinalResult
            )
            logger.debug(f"🔍 Vosk FinalResult返回: '{final_result}'")
            import json
            result_dict = json.loads(final_result)
            text = result_dict.get('text', '')
            logger.debug(f"🔍 解析后的文本: '{text}'")
            return text

        except Exception as e:
            logger.error(f"❌ 获取最终识别结果失败: {e}")
            import traceback
            logger.debug(f"❌ 异常详情: {traceback.format_exc()}")

        return None

    @property
    def is_initialized(self) -> bool:
        """检查识别器是否已初始化"""
        logger.debug(f"🔍 检查识别器初始化状态: {self._is_initialized}")
        return self._is_initialized


class AsyncTTSPlayer:
    """异步TTS播放器"""

    def __init__(self):
        """初始化异步TTS播放器"""
        self._tts_engine = None
        self._play_queue: asyncio.Queue[TTSRequest] = asyncio.Queue()
        self._is_playing = False
        self._play_task: Optional[asyncio.Task] = None
        self._play_lock = asyncio.Lock()

    async def initialize(self):
        """初始化TTS引擎"""
        if self._tts_engine:
            return

        logger.debug("🔊 初始化异步TTS播放器...")

        try:
            # 导入并初始化TTS引擎
            from TTSengine import TTS
            self._tts_engine = await asyncio.to_thread(TTS)
            logger.debug("✅ 异步TTS播放器初始化成功")

        except Exception as e:
            logger.error(f"❌ 异步TTS播放器初始化失败: {e}")
            raise

    async def speak_async(self, text: str, priority: int = 0) -> bool:
        """异步语音播报"""
        if not self._tts_engine:
            return False

        request = TTSRequest(
            text=text,
            task_id=f"tts_{int(time.time() * 1000)}",
            priority=priority
        )

        await self._play_queue.put(request)

        # 启动播放任务
        if not self._play_task or self._play_task.done():
            self._play_task = asyncio.create_task(self._play_worker())

        return True

    async def _play_worker(self):
        """TTS播放工作协程"""
        logger.debug("🎵 启动TTS播放工作协程")

        try:
            while True:
                # 获取播放请求
                request = await self._play_queue.get()

                async with self._play_lock:
                    if self._is_playing:
                        logger.debug("⏸️  TTS正在播放，跳过请求")
                        continue

                    self._is_playing = True

                    try:
                        # 在线程池中执行TTS播放
                        await asyncio.to_thread(
                            self._tts_engine.speak,
                            request.text
                        )
                        logger.debug(f"✅ TTS播放完成: {request.text}")

                    except Exception as e:
                        logger.error(f"❌ TTS播放失败: {e}")

                    finally:
                        self._is_playing = False

        except asyncio.CancelledError:
            logger.debug("🛑 TTS播放工作协程被取消")

        except Exception as e:
            logger.error(f"❌ TTS播放工作协程异常: {e}")

    async def stop(self):
        """停止TTS播放"""
        if self._play_task and not self._play_task.done():
            self._play_task.cancel()
            try:
                await self._play_task
            except asyncio.CancelledError:
                pass

        # 清空播放队列
        while not self._play_queue.empty():
            try:
                self._play_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.debug("🛑 TTS播放器已停止")

    @property
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        return self._is_playing


class AsyncAudioCapture:
    """异步音频捕获器

    主要特性:
    - 完全异步的音频处理管道
    - 非阻塞的音频流读取
    - 并发的语音识别处理
    - 异步TTS播放支持
    - 事件驱动的状态管理
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 8000,
        model_path: Optional[str] = None,
        timeout_seconds: int = 30,
        test_mode: bool = False
    ):
        """
        初始化异步音频捕获器

        Args:
            sample_rate: 采样率
            chunk_size: 音频块大小
            model_path: 语音模型路径
            timeout_seconds: 超时时间
            test_mode: 测试模式
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model_path = model_path
        self.timeout_seconds = timeout_seconds
        self.test_mode = test_mode

        # 状态管理
        self._state = AsyncAudioProcessorState.IDLE
        self._state_lock = asyncio.Lock()

        # 事件控制
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()

        # 核心组件
        self.audio_stream = AsyncAudioStream(sample_rate, chunk_size)
        self.recognizer = AsyncRecognizer(model_path)
        self.tts_player = AsyncTTSPlayer()

        # 队列管理
        self._audio_queue: asyncio.Queue[AudioChunk] = asyncio.Queue(maxsize=100)
        self._recognition_queue: asyncio.Queue[RecognitionTask] = asyncio.Queue(maxsize=50)

        # 任务管理
        self._capture_task: Optional[asyncio.Task] = None
        self._recognition_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

        # 回调管理
        self._recognition_callbacks: List[Callable[[RecognitionResult], None]] = []
        self._state_change_callbacks: List[Callable[[AudioProcessorState], None]] = []

        # 统计信息
        self._stats: Dict[str, Any] = {
            'captured_chunks': 0,
            'recognized_texts': 0,
            'errors': 0,
            'start_time': None,  # float | None
            'last_activity': None,  # float | None
        }

        logger.info("🎤 AsyncAudioCapture initialized")

    async def initialize(self) -> bool:
        """异步初始化"""
        logger.info("🚀 初始化AsyncAudioCapture...")

        async with self._state_lock:
            if self._state != AsyncAudioProcessorState.IDLE:
                logger.warning(f"⚠️ 当前状态不是IDLE: {self._state}")
                return False

            await self._set_state(AsyncAudioProcessorState.INITIALIZING)

        try:
            # 初始化各个组件
            await self.audio_stream.open()
            await self.recognizer.initialize()
            await self.tts_player.initialize()

            await self._set_state(AsyncAudioProcessorState.IDLE)
            logger.info("✅ AsyncAudioCapture初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ AsyncAudioCapture初始化失败: {e}")
            await self._set_state(AsyncAudioProcessorState.ERROR)
            return False

    async def start_recognition(self) -> RecognitionResult:
        """开始语音识别"""
        logger.info("🎤 开始异步语音识别...")

        async with self._state_lock:
            if self._state not in [AsyncAudioProcessorState.IDLE, AsyncAudioProcessorState.STOPPED]:
                return RecognitionResult(
                    final_text=f"Invalid state for start: {self._state}",
                    processing_time=time.time()
                )

            await self._set_state(AsyncAudioProcessorState.RUNNING)

        try:
            # 重置事件
            self._stop_event.clear()
            self._pause_event.set()

            # 启动处理任务
            self._capture_task = asyncio.create_task(self._audio_capture_worker())
            self._recognition_task = asyncio.create_task(self._recognition_worker())
            self._monitor_task = asyncio.create_task(self._monitor_worker())

            # 更新统计信息
            self._stats['start_time'] = time.time()
            self._stats['last_activity'] = time.time()

            logger.info("✅ 异步语音识别已启动")
            return RecognitionResult(
                final_text="Recognition started successfully",
                processing_time=time.time()
            )

        except Exception as e:
            error_msg = f"Failed to start recognition: {str(e)}"
            logger.error(f"❌ 启动异步语音识别失败: {e}")
            await self._set_state(AsyncAudioProcessorState.ERROR)
            return RecognitionResult(
                final_text=error_msg,
                processing_time=time.time()
            )

    async def stop_recognition(self) -> RecognitionResult:
        """停止语音识别"""
        logger.info("🛑 停止异步语音识别...")

        async with self._state_lock:
            if self._state == AsyncAudioProcessorState.IDLE:
                return RecognitionResult(
                    final_text=f"Already stopped",
                    processing_time=time.time()                    
                )

            await self._set_state(AsyncAudioProcessorState.STOPPING)

        try:
            # 获取最终识别结果（在停止任务之前）
            final_text = "Recognition stopped successfully"
            try:
                logger.debug("🔍 尝试获取最终识别结果...")
                final_result = await self.recognizer.get_final_result()
                logger.debug(f"🔍 获得原始最终结果: '{final_result}'")
                if final_result and final_result.strip():
                    final_text = final_result.strip()
                    logger.info(f"✅ 获得最终识别结果: {final_text}")
                else:
                    logger.debug("🔍 最终结果为空或只有空白字符")
            except Exception as e:
                logger.error(f"❌ 获取最终识别结果失败: {e}")
                import traceback
                logger.debug(f"❌ 异常详情: {traceback.format_exc()}")

            # 设置停止事件
            self._stop_event.set()

            # 等待任务完成
            tasks = [t for t in [self._capture_task, self._recognition_task, self._monitor_task] if t and not t.done()]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            await self._set_state(AsyncAudioProcessorState.STOPPED)
            logger.info("✅ 异步语音识别已停止")

            return RecognitionResult(
                final_text=final_text,
                processing_time=time.time()

            )

        except Exception as e:
            error_msg = f"Failed to stop recognition: {str(e)}"
            logger.error(f"❌ 停止异步语音识别失败: {e}")
            await self._set_state(AsyncAudioProcessorState.ERROR)
            return RecognitionResult(
                final_text=error_msg,
                processing_time=time.time()                  
            )

    async def pause_recognition(self) -> bool:
        """暂停语音识别"""
        if self._state != AsyncAudioProcessorState.RUNNING:
            return False

        self._pause_event.clear()
        await self._set_state(AsyncAudioProcessorState.PAUSED)
        logger.info("⏸️ 语音识别已暂停")
        return True

    async def resume_recognition(self) -> bool:
        """恢复语音识别"""
        if self._state != AsyncAudioProcessorState.PAUSED:
            return False

        self._pause_event.set()
        await self._set_state(AsyncAudioProcessorState.RUNNING)
        logger.info("▶️ 语音识别已恢复")
        return True

    async def _audio_capture_worker(self):
        """音频采集工作协程"""
        logger.debug("🎙️ 启动音频采集工作协程")

        try:
            while not self._stop_event.is_set():
                # 检查暂停状态
                if not self._pause_event.is_set():
                    await asyncio.sleep(0.1)
                    continue

                # 读取音频数据
                audio_chunk = await self.audio_stream.read_chunk()
                if audio_chunk:
                    # 非阻塞入队
                    try:
                        self._audio_queue.put_nowait(audio_chunk)
                        self._stats['captured_chunks'] += 1
                        self._stats['last_activity'] = time.time()
                    except asyncio.QueueFull:
                        logger.warning("⚠️ 音频队列已满，丢弃音频块")

                await asyncio.sleep(0.01)  # 10ms休眠，类似同步系统的50ms但更快响应

        except asyncio.CancelledError:
            logger.debug("🛑 音频采集工作协程被取消")

        except Exception as e:
            logger.error(f"❌ 音频采集工作协程异常: {e}")
            self._stats['errors'] += 1

    async def _recognition_worker(self):
        """语音识别工作协程"""
        logger.debug("🧠 启动语音识别工作协程")

        try:
            while not self._stop_event.is_set():
                # 检查暂停状态
                if not self._pause_event.is_set():
                    await asyncio.sleep(0.1)
                    continue

                try:
                    # 获取音频数据 - 减少超时时间提高响应性
                    audio_chunk = await asyncio.wait_for(
                        self._audio_queue.get(),
                        timeout=0.1  # 100ms超时，更快响应
                    )

                    # 处理语音识别
                    text = await self.recognizer.process_audio(audio_chunk)

                    if text and text.strip():
                        # 创建识别结果
                        result = RecognitionResult(
                            final_text=text.strip(),
                            processing_time=time.time()                          
                            
                        )

                        # 调用回调
                        for callback in self._recognition_callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"❌ 识别回调执行失败: {e}")

                        self._stats['recognized_texts'] += 1
                        logger.debug(f"🗣️ 识别结果: {text}")

                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环
                    continue

                except Exception as e:
                    logger.error(f"❌ 语音识别处理失败: {e}")
                    self._stats['errors'] += 1

        except asyncio.CancelledError:
            logger.debug("🛑 语音识别工作协程被取消")

        except Exception as e:
            logger.error(f"❌ 语音识别工作协程异常: {e}")

    async def _monitor_worker(self):
        """监控工作协程"""
        logger.debug("👁️ 启动监控工作协程")

        try:
            while not self._stop_event.is_set():
                # 检查超时
                if self._stats['start_time']:
                    elapsed = time.time() - self._stats['start_time']
                    if elapsed > self.timeout_seconds:
                        logger.info(f"⏰ 识别超时 ({self.timeout_seconds}s)")
                        await self.stop_recognition()
                        break

                # 检查活动状态
                if self._stats['last_activity']:
                    inactive_time = time.time() - self._stats['last_activity']
                    if inactive_time > 10.0:  # 10秒无活动
                        logger.warning("⚠️ 长时间无音频活动")

                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.debug("🛑 监控工作协程被取消")

        except Exception as e:
            logger.error(f"❌ 监控工作协程异常: {e}")

    async def _set_state(self, new_state: AsyncAudioProcessorState):
        """设置状态"""
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            logger.debug(f"🔄 状态变更: {old_state} → {new_state}")

            # 调用状态变更回调
            for callback in self._state_change_callbacks:
                try:
                    # 转换为AudioProcessorState类型后再传递给回调
                    callback(self.get_state())
                except Exception as e:
                    logger.error(f"❌ 状态变更回调执行失败: {e}")

    def get_state(self) -> AudioProcessorState:
        """获取当前状态"""
        # 映射到接口状态枚举
        state_mapping = {
            AsyncAudioProcessorState.IDLE: AudioProcessorState.IDLE,
            AsyncAudioProcessorState.INITIALIZING: AudioProcessorState.IDLE,  # 映射到IDLE
            AsyncAudioProcessorState.RUNNING: AudioProcessorState.RECORDING,  # 使用RECORDING替代RUNNING
            AsyncAudioProcessorState.PAUSED: AudioProcessorState.PAUSED,
            AsyncAudioProcessorState.STOPPING: AudioProcessorState.STOPPED,   # 映射到STOPPED
            AsyncAudioProcessorState.STOPPED: AudioProcessorState.STOPPED,
            AsyncAudioProcessorState.ERROR: AudioProcessorState.ERROR,
        }

        return state_mapping.get(self._state, AudioProcessorState.IDLE)

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return (self._state != AsyncAudioProcessorState.IDLE and
                self.audio_stream.is_active and
                self.recognizer.is_initialized)

    def add_recognition_callback(self, callback: Callable[[RecognitionResult], None]):
        """添加识别结果回调"""
        self._recognition_callbacks.append(callback)

    def add_state_change_callback(self, callback: Callable[[AudioProcessorState], None]):
        """添加状态变更回调"""
        self._state_change_callbacks.append(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()

        if stats['start_time']:
            stats['running_time'] = time.time() - stats['start_time']
        else:
            stats['running_time'] = 0

        return stats

    async def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理AsyncAudioCapture资源...")

        try:
            # 停止识别
            if self._state in [AsyncAudioProcessorState.RUNNING, AsyncAudioProcessorState.PAUSED]:
                await self.stop_recognition()

            # 停止TTS播放
            await self.tts_player.stop()

            # 关闭音频流
            await self.audio_stream.close()

            logger.info("✅ AsyncAudioCapture资源清理完成")

        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


# 便捷函数
async def create_async_audio_capture(
    sample_rate: int = 16000,
    chunk_size: int = 8000,
    model_path: Optional[str] = None,
    timeout_seconds: int = 30,
    test_mode: bool = False
) -> AsyncAudioCapture:
    """创建异步音频捕获器的便捷函数"""
    capture = AsyncAudioCapture(
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        model_path=model_path,
        timeout_seconds=timeout_seconds,
        test_mode=test_mode
    )

    await capture.initialize()
    return capture