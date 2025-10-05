# -*- coding: utf-8 -*-
"""
异步音频处理器适配器

将AsyncAudioCapture适配为IAudioProcessor接口，提供完整的异步功能支持。
同时保持与现有AudioCapture的兼容性，支持渐进式迁移。
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Callable, Tuple

from interfaces.audio_processor import (
    IAudioProcessor, RecognitionResult, VoiceCommand, VoiceCommandType,
    AudioProcessorState
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from async_audio import AsyncAudioCapture, create_async_audio_capture
from async_audio.async_number_extractor import extract_measurements
from audio_capture_v import AudioCapture

logger = logging.getLogger(__name__)


class AsyncAudioProcessorAdapter(IAudioProcessor):
    """
    异步音频处理器适配器

    特性:
    - 完全异步的音频处理
    - 与同步接口的兼容性
    - 高性能的并发处理
    - 事件驱动的状态管理
    """

    def __init__(
        self,
        async_capture: Optional[AsyncAudioCapture] = None,
        sync_capture: Optional[AudioCapture] = None,
        use_async: bool = True,
        **kwargs
    ):
        """
        初始化异步音频处理器适配器

        Args:
            async_capture: 现有的AsyncAudioCapture实例
            sync_capture: 现有的AudioCapture实例（兼容性）
            use_async: 是否使用异步模式
            **kwargs: 传递给AudioCapture构造函数的参数
        """
        self.use_async = use_async
        self._kwargs = kwargs

        # 过滤参数，只传递AudioCapture支持的参数
        sync_kwargs = {}
        async_kwargs = {}

        # 支持的参数映射
        supported_sync_params = ['timeout_seconds', 'model_path', 'test_mode', 'device_index']
        supported_async_params = ['sample_rate', 'chunk_size', 'model_path', 'timeout_seconds', 'test_mode']

        for key, value in kwargs.items():
            if key in supported_sync_params:
                sync_kwargs[key] = value
            if key in supported_async_params:
                async_kwargs[key] = value

        # 异步处理器
        if async_capture:
            self._async_capture = async_capture
        else:
            self._async_capture = AsyncAudioCapture(**async_kwargs)

        # 同步处理器（兼容性）
        if sync_capture:
            self._sync_capture = sync_capture
        else:
            self._sync_capture = AudioCapture(**sync_kwargs)

        # 回调管理
        self._recognition_callbacks: List[Callable[[RecognitionResult], None]] = []
        self._state_change_callbacks: List[Callable[[AudioProcessorState], None]] = []

        # 状态缓存
        self._last_state: AudioProcessorState = AudioProcessorState.IDLE
        self._state_lock = asyncio.Lock()

        # 异步初始化状态
        self._async_initialized = False

        logger.info(f"AsyncAudioProcessorAdapter initialized (async_mode: {use_async})")

    async def async_initialize(self) -> bool:
        """异步初始化"""
        if not self.use_async or self._async_initialized:
            return True

        logger.info("🚀 初始化异步音频处理器...")

        try:
            # 初始化异步处理器
            success = await self._async_capture.initialize()

            if success:
                # 设置回调
                self._async_capture.add_recognition_callback(self._on_recognition_result)
                self._async_capture.add_state_change_callback(self._on_state_change)

                self._async_initialized = True
                logger.info("✅ 异步音频处理器初始化成功")

            return success

        except Exception as e:
            logger.error(f"❌ 异步音频处理器初始化失败: {e}")
            return False

    # IAudioProcessor 接口实现

    async def start_recognition_async(self, callback: Optional[Callable[[List[float]], None]] = None) -> RecognitionResult:
        """异步开始语音识别"""
        # 存储回调函数（如果提供）
        if callback:
            self.set_callback(callback)
        if not self.use_async:
            # 同步模式的异步包装
            # 将listen_realtime_vosk返回的字典转换为RecognitionResult对象
            result_dict = await asyncio.to_thread(self._sync_capture.listen_realtime_vosk)
            # 确保获取的值具有正确的类型
            final_text = str(result_dict.get('text', ''))
            
            # 确保buffered_values是List[float]
            raw_values = result_dict.get('values', [])
            buffered_values: List[float] = []
            if isinstance(raw_values, list):
                for val in raw_values:
                    # 只尝试转换可以转换为float的类型
                    if isinstance(val, (int, float, str)):
                        try:
                            buffered_values.append(float(val))
                        except (ValueError, TypeError):
                            pass
            
            # 确保collected_text是List[str]
            raw_texts = result_dict.get('collected_text', [])
            collected_text: List[str] = []
            if isinstance(raw_texts, list):
                for text in raw_texts:
                    try:
                        collected_text.append(str(text))
                    except (ValueError, TypeError):
                        pass
            
            # 确保session_data是List[Tuple[int, float, str]]
            raw_session_data = result_dict.get('session_data', [])
            session_data: List[Tuple[int, float, str]] = []
            if isinstance(raw_session_data, list):
                for item in raw_session_data:
                    try:
                        if isinstance(item, tuple) and len(item) == 3:
                            # 尝试转换为正确的类型
                            timestamp = int(item[0])
                            value = float(item[1])
                            text = str(item[2])
                            session_data.append((timestamp, value, text))
                    except (ValueError, TypeError, IndexError):
                        pass
            
            # 确保数值类型正确 - 先获取值并确保它是可转换的类型
            recognition_count_val = result_dict.get('recognition_count', 0)
            recognition_count = 0
            if isinstance(recognition_count_val, (int, float, str)):
                try:
                    recognition_count = int(recognition_count_val)
                except (ValueError, TypeError):
                    pass
            
            audio_frames_val = result_dict.get('audio_frames', 0)
            audio_frames = 0
            if isinstance(audio_frames_val, (int, float, str)):
                try:
                    audio_frames = int(audio_frames_val)
                except (ValueError, TypeError):
                    pass
            
            processing_time_val = result_dict.get('processing_time', 0.0)
            processing_time = 0.0
            if isinstance(processing_time_val, (int, float, str)):
                try:
                    processing_time = float(processing_time_val)
                except (ValueError, TypeError):
                    pass
            
            return RecognitionResult(
                final_text=final_text,
                buffered_values=buffered_values,
                collected_text=collected_text,
                session_data=session_data,
                recognition_count=recognition_count,
                audio_frames=audio_frames,
                processing_time=processing_time
            )

        # 确保异步处理器已初始化
        if not await self.async_initialize():
            return RecognitionResult(
                final_text="",
                session_data=[],
                processing_time=0.0
            )

        return await self._async_capture.start_recognition()

    async def stop_recognition_async(self) -> RecognitionResult:
        """异步停止语音识别"""
        if not self.use_async:
            # 同步模式的异步包装
            # TODO: 实现同步停止逻辑
            return RecognitionResult(
                final_text="Stop sync recognition",
                session_data=[],
                processing_time=0.0
            )

        return await self._async_capture.stop_recognition()

    async def pause_recognition_async(self) -> bool:
        """异步暂停语音识别"""
        if not self.use_async:
            return False  # 同步模式暂不支持暂停

        return await self._async_capture.pause_recognition()

    async def resume_recognition_async(self) -> bool:
        """异步恢复语音识别"""
        if not self.use_async:
            return False  # 同步模式暂不支持恢复

        return await self._async_capture.resume_recognition()

    def extract_measurements(self, text: str) -> List[float]:
        """提取数值（同步接口）"""
        try:
            # 如果是异步模式，尝试使用异步提取器的同步版本
            if self.use_async:
                # 使用asyncio.run在同步上下文中运行异步函数
                try:
                    # 注意：这只能在非异步上下文中使用
                    if not asyncio.get_event_loop().is_running():
                        return asyncio.run(extract_measurements(text))
                except RuntimeError:
                    # 如果已有事件循环在运行，回退到同步版本
                    pass

            # 回退到同步版本的数值提取
            # 由于extract_measurements是异步函数，需要在同步环境中使用run来执行
            def sync_wrapper():
                try:
                    # 检查是否有正在运行的事件循环
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，使用创建任务的方式
                        future = asyncio.run_coroutine_threadsafe(extract_measurements(text), loop)
                        return future.result()
                    else:
                        # 如果没有运行的事件循环，直接运行
                        return asyncio.run(extract_measurements(text))
                except RuntimeError:
                    # 无法获取事件循环，创建一个新的
                    return asyncio.run(extract_measurements(text))
                except Exception as e:
                    logger.error(f"❌ 数值提取包装失败: {e}")
                    return []
            
            return sync_wrapper()

        except Exception as e:
            logger.error(f"❌ 数值提取失败: {e}")
            return []

    async def extract_measurements_async(self, text: str) -> List[float]:
        """异步提取数值"""
        if self.use_async:
            return await extract_measurements(text)
        else:
            # 同步模式的异步包装
            # 由于extract_measurements是异步函数，需要在同步环境中使用run来执行
            def sync_wrapper():
                try:
                    # 检查是否有正在运行的事件循环
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，使用创建任务的方式
                        future = asyncio.run_coroutine_threadsafe(extract_measurements(text), loop)
                        return future.result()
                    else:
                        # 如果没有运行的事件循环，直接运行
                        return asyncio.run(extract_measurements(text))
                except RuntimeError:
                    # 无法获取事件循环，创建一个新的
                    return asyncio.run(extract_measurements(text))
            
            return await asyncio.to_thread(sync_wrapper)

    def get_state(self) -> AudioProcessorState:
        """获取当前状态"""
        if self.use_async and self._async_initialized:
            return self._async_capture.get_state()
        else:
            # 映射同步状态到接口状态
            sync_state = self._sync_capture.state
            state_mapping = {
                "idle": AudioProcessorState.IDLE,
                "running": AudioProcessorState.RECORDING,  # 使用RECORDING替代RUNNING
                "paused": AudioProcessorState.PAUSED,
                "stopped": AudioProcessorState.STOPPED
            }
            return state_mapping.get(sync_state, AudioProcessorState.IDLE)

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        if self.use_async:
            return self._async_initialized
        else:
            # 同步模式没有明确的初始化状态
            return True

    def add_recognition_callback(self, callback: Callable[[RecognitionResult], None]):
        """添加识别结果回调"""
        self._recognition_callbacks.append(callback)

        # 如果是异步模式且已初始化，也添加到异步处理器
        if self.use_async and self._async_initialized:
            self._async_capture.add_recognition_callback(callback)

    def add_state_change_callback(self, callback: Callable[[AudioProcessorState], None]):
        """添加状态变更回调"""
        self._state_change_callbacks.append(callback)

        # 如果是异步模式且已初始化，也添加到异步处理器
        if self.use_async and self._async_initialized:
            self._async_capture.add_state_change_callback(callback)

    # 扩展功能

    def set_async_mode(self, use_async: bool):
        """设置异步模式"""
        if use_async != self.use_async:
            logger.info(f"🔄 切换异步模式: {self.use_async} → {use_async}")
            self.use_async = use_async

            # 如果切换到异步模式，触发初始化
            if use_async and not self._async_initialized:
                # 注意：这里不能直接await，需要在异步上下文中调用
                logger.info("⚠️ 需要在异步上下文中调用 async_initialize()")

    async def switch_to_async_mode(self) -> bool:
        """切换到异步模式（异步方法）"""
        if not self.use_async:
            self.set_async_mode(True)
            return await self.async_initialize()
        return self._async_initialized

    async def switch_to_sync_mode(self) -> bool:
        """切换到同步模式（异步方法）"""
        if self.use_async:
            # 停止异步处理器
            if self._async_initialized:
                await self._async_capture.stop_recognition()
                await self._async_capture.cleanup()
                self._async_initialized = False

            self.set_async_mode(False)
            return True
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "use_async": self.use_async,
            "async_initialized": self._async_initialized,
            "current_state": self.get_state().name
        }

        if self.use_async and self._async_initialized:
            async_stats = self._async_capture.get_statistics()
            stats["async_stats"] = async_stats

        return stats

    def get_diagnostics_info(self) -> Dict[str, Any]:
        """获取诊断信息"""
        diagnostics = {
            "adapter_type": "AsyncAudioProcessorAdapter",
            "async_mode": self.use_async,
            "async_initialized": self._async_initialized,
            "state": self.get_state().name,
            "callback_count": len(self._recognition_callbacks) + len(self._state_change_callbacks)
        }

        if self.use_async and self._async_initialized:
            # 在同步方法中获取异步处理器的诊断信息
            # 注意：这里假设get_statistics是同步方法，如果是异步的需要额外处理
            try:
                async_diagnostics = self._async_capture.get_statistics()
                diagnostics["async_details"] = async_diagnostics
            except Exception:
                # 如果获取失败，记录错误但不影响整体功能
                diagnostics["async_details"] = {"error": "Failed to get async diagnostics"}

        return diagnostics

    # 内部回调处理

    def _on_recognition_result(self, result: RecognitionResult):
        """处理识别结果回调"""
        # 调用所有注册的回调
        for callback in self._recognition_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"❌ 识别回调执行失败: {e}")

    def _on_state_change(self, new_state):
        """处理状态变更回调"""
        # 调用所有注册的回调
        for callback in self._state_change_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                logger.error(f"❌ 状态变更回调执行失败: {e}")

    # 资源管理

    async def cleanup_async(self):
        """异步清理资源"""
        logger.info("🧹 清理异步音频处理器适配器...")

        try:
            # 清理异步处理器
            if self.use_async and self._async_initialized:
                await self._async_capture.cleanup()
                self._async_initialized = False

            # 清理同步处理器
            if hasattr(self._sync_capture, 'cleanup'):
                self._sync_capture.cleanup()

            logger.info("✅ 异步音频处理器适配器清理完成")

        except Exception as e:
            logger.error(f"❌ 异步音频处理器适配器清理失败: {e}")

    # IAudioProcessor 接口实现 - 完整方法集

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """加载语音识别模型"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(self._async_load_model(model_path))
                    return True
                else:
                    # 如果没有事件循环，运行异步方法
                    return loop.run_until_complete(self._async_load_model(model_path))
            except RuntimeError:
                # 如果无法获取事件循环，回退到同步模式
                # AudioCapture.load_model方法没有参数
                return self._sync_capture.load_model()
        else:
            # 同步模式
            # AudioCapture.load_model方法没有参数
            return self._sync_capture.load_model()

    async def _async_load_model(self, model_path: Optional[str] = None) -> bool:
        """异步加载模型"""
        if not self.use_async or not self._async_initialized:
            return False

        try:
            # 在线程池中执行模型加载
            # AudioCapture.load_model方法没有参数
            success = await asyncio.to_thread(
                self._sync_capture.load_model
            )
            return success
        except Exception as e:
            logger.error(f"❌ 异步加载模型失败: {e}")
            return False

    def unload_model(self) -> None:
        """卸载语音识别模型，释放内存资源"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._async_unload_model())
                else:
                    loop.run_until_complete(self._async_unload_model())
            except RuntimeError:
                self._sync_capture.unload_model()
        else:
            self._sync_capture.unload_model()

    async def _async_unload_model(self) -> None:
        """异步卸载模型"""
        if not self.use_async or not self._async_initialized:
            return

        try:
            await asyncio.to_thread(self._sync_capture.unload_model)
        except Exception as e:
            logger.error(f"❌ 异步卸载模型失败: {e}")

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步检查
            return self._async_capture.recognizer.is_initialized
        else:
            # 同步模式
            return hasattr(self._sync_capture, 'recognizer') and self._sync_capture.recognizer is not None

    def start_recognition(self, callback: Optional[Callable[[List[float]], None]] = None) -> Dict[str, Any]:
        """开始语音识别（同步模式）"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，返回错误信息
                    return {
                        "success": False,
                        "error": "Cannot use sync method when async mode is enabled and event loop is running",
                        "timestamp": time.time()
                    }
                else:
                    # 如果没有事件循环，运行异步方法
                    result = loop.run_until_complete(self.start_recognition_async())
                    # RecognitionResult类没有success、text、error_message和timestamp属性
                    # 使用正确的属性来构建返回值
                    return {
                        "success": True,  # 假设识别成功
                        "text": result.final_text,
                        "error": None,  # 无法从RecognitionResult中直接获取错误信息
                        "timestamp": time.time()  # 使用当前时间戳
                    }
            except RuntimeError:
                # 如果无法获取事件循环，回退到同步模式
                return self._sync_capture.listen_realtime_vosk()
        else:
            # 同步模式
            return self._sync_capture.listen_realtime_vosk()

    def pause_recognition(self) -> None:
        """暂停语音识别"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.pause_recognition_async())
                else:
                    loop.run_until_complete(self.pause_recognition_async())
            except RuntimeError:
                pass  # 静默处理
        else:
            # 同步模式可能不支持暂停
            pass

    def resume_recognition(self) -> None:
        """恢复语音识别"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.resume_recognition_async())
                else:
                    loop.run_until_complete(self.resume_recognition_async())
            except RuntimeError:
                pass  # 静默处理
        else:
            # 同步模式可能不支持恢复
            pass

    def stop_recognition(self) -> None:
        """停止语音识别"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.stop_recognition_async())
                else:
                    loop.run_until_complete(self.stop_recognition_async())
            except RuntimeError:
                pass  # 静默处理
        else:
            # 同步模式
            if hasattr(self._sync_capture, 'state') and self._sync_capture.state == "running":
                self._sync_capture.state = "stopped"

    def set_callback(self, callback: Callable[[List[float]], None]) -> None:
        """设置数值检测回调函数"""
        # 转换为RecognitionResult回调
        def converted_callback(result: RecognitionResult):
            # RecognitionResult没有success和text属性，使用正确的属性
            if result.final_text and self.use_async:
                # 提取数值
                measurements = self.extract_measurements(result.final_text)
                if measurements:
                    callback(measurements)

        self.add_recognition_callback(converted_callback)

        # 同时设置到同步处理器
        if hasattr(self._sync_capture, 'set_callback'):
            self._sync_capture.set_callback(callback)

    def process_voice_commands(self, text: str) -> Optional[VoiceCommand]:
        """处理语音控制命令"""
        try:
            # 简单的语音命令识别
            text_lower = text.lower().strip()

            # 停止命令
            if any(keyword in text_lower for keyword in ['停止', '结束', '停止识别']):
                return VoiceCommand(
                    command_type=VoiceCommandType.STOP,
                    original_text=text,
                    confidence=0.9
                )

            # 暂停命令
            elif any(keyword in text_lower for keyword in ['暂停', '暂停识别']):
                return VoiceCommand(
                    command_type=VoiceCommandType.PAUSE,
                    original_text=text,
                    confidence=0.9
                )

            # 恢复命令
            elif any(keyword in text_lower for keyword in ['继续', '恢复', '恢复识别']):
                return VoiceCommand(
                    command_type=VoiceCommandType.RESUME,
                    original_text=text,
                    confidence=0.9
                )

            # 清空命令 - 使用UNKNOWN类型，因为VoiceCommandType中没有CLEAR枚举
            elif any(keyword in text_lower for keyword in ['清空', '清除', '清空数据']):
                return VoiceCommand(
                    command_type=VoiceCommandType.UNKNOWN,
                    original_text=text,
                    confidence=0.8
                )

            return None

        except Exception as e:
            logger.error(f"❌ 处理语音命令失败: {e}")
            return None

    def get_buffered_values(self) -> List[float]:
        """获取缓冲的数值列表"""
        if self.use_async and self._async_initialized:
            # 从异步处理器的统计信息中获取
            stats = self._async_capture.get_statistics()
            # 这里需要实现实际的缓冲区管理
            # 目前返回空列表
            return []
        else:
            # 同步模式
            if hasattr(self._sync_capture, 'buffered_values'):
                # 确保返回的是list类型，即使原始类型是deque
                return list(self._sync_capture.buffered_values)
            return []

    def get_session_data(self) -> List[Tuple[int, float, str]]:
        """获取本次会话的数据"""
        if self.use_async and self._async_initialized:
            # 从异步处理器的会话数据中获取
            # 这里需要实现实际的会话数据管理
            # 目前返回空列表
            return []
        else:
            # 同步模式
            if hasattr(self._sync_capture, 'session_data'):
                return self._sync_capture.session_data
            return []

    def clear_buffer(self) -> None:
        """清空数值缓冲区"""
        if self.use_async and self._async_initialized:
            # 清空异步处理器的缓冲区
            # 这里需要实现实际的缓冲区清理
            pass
        else:
            # 同步模式
            if hasattr(self._sync_capture, 'clear_buffer'):
                self._sync_capture.clear_buffer()

    def set_audio_parameters(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 8000,
        channels: int = 1,
        format_type: str = "int16"
    ) -> None:
        """设置音频处理参数"""
        if self.use_async and self._async_initialized:
            # 异步模式参数设置
            logger.warning("⚠️ 异步模式下运行时参数更改需要重新初始化")
            # 记录新参数，下次初始化时使用
            self._kwargs.update({
                'sample_rate': sample_rate,
                'chunk_size': chunk_size,
                'channels': channels,
                'format_type': format_type
            })
        else:
            # 同步模式参数设置
            if hasattr(self._sync_capture, 'set_audio_parameters'):
                self._sync_capture.set_audio_parameters(
                    sample_rate=sample_rate,
                    chunk_size=chunk_size,
                    channels=channels,
                    format_type=format_type
                )

    def get_audio_parameters(self) -> Dict[str, Any]:
        """获取当前音频处理参数"""
        if self.use_async and self._async_initialized:
            # 异步模式参数获取
            return {
                'sample_rate': self._async_capture.sample_rate,
                'chunk_size': self._async_capture.chunk_size,
                'model_path': self._async_capture.model_path,
                'timeout_seconds': self._async_capture.timeout_seconds,
                'test_mode': self._async_capture.test_mode
            }
        else:
            # 同步模式参数获取
            params = {
                'timeout_seconds': self._sync_capture.timeout_seconds
            }
            if hasattr(self._sync_capture, 'audio_chunk_size'):
                params['chunk_size'] = self._sync_capture.audio_chunk_size
            return params

    # TTS相关方法

    def enable_tts(self) -> None:
        """启用TTS功能"""
        if self.use_async and self._async_initialized:
            # 异步模式启用TTS
            logger.info("🔊 启用异步TTS功能")
            # 这里需要实现实际的TTS启用逻辑
        else:
            # 同步模式启用TTS
            if hasattr(self._sync_capture, 'enable_tts'):
                self._sync_capture.enable_tts()

    def disable_tts(self) -> None:
        """禁用TTS功能"""
        if self.use_async and self._async_initialized:
            # 异步模式禁用TTS
            logger.info("🔇 禁用异步TTS功能")
            # 这里需要实现实际的TTS禁用逻辑
        else:
            # 同步模式禁用TTS
            if hasattr(self._sync_capture, 'disable_tts'):
                self._sync_capture.disable_tts()

    def toggle_tts(self) -> bool:
        """切换TTS开关状态"""
        if self.use_async and self._async_initialized:
            # 异步模式切换TTS
            current_state = self.is_tts_enabled()
            if current_state:
                self.disable_tts()
            else:
                self.enable_tts()
            return not current_state
        else:
            # 同步模式切换TTS
            if hasattr(self._sync_capture, 'toggle_tts'):
                try:
                    self._sync_capture.toggle_tts()
                    return True
                except Exception as e:
                    logger.error(f"❌ 同步模式切换TTS失败: {e}")
                    return False
            return False

    def is_tts_enabled(self) -> bool:
        """获取TTS当前状态"""
        if self.use_async and self._async_initialized:
            # 异步模式TTS状态
            # 这里需要实现实际的TTS状态检查
            return False  # 默认禁用
        else:
            # 同步模式TTS状态
            if hasattr(self._sync_capture, 'is_tts_enabled'):
                return self._sync_capture.is_tts_enabled()
            return False

    def speak_text(self, text: str) -> None:
        """TTS播报文本"""
        if self.use_async and self._async_initialized:
            # 异步模式的同步包装
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(self.speak_text_async(text))
                else:
                    # 如果没有事件循环，运行异步方法
                    loop.run_until_complete(self.speak_text_async(text))
            except RuntimeError:
                # 如果无法获取事件循环，回退到同步模式
                if hasattr(self._sync_capture, 'speak_text'):
                    self._sync_capture.speak_text(text)
        else:
            # 同步模式
            if hasattr(self._sync_capture, 'speak_text'):
                self._sync_capture.speak_text(text)

    async def speak_text_async(self, text: str) -> None:
        """异步TTS播报文本"""
        if self.use_async and self._async_initialized:
            # 异步模式TTS播报
            try:
                success = await self._async_capture.tts_player.speak_async(text)
                if not success:
                    logger.warning(f"⚠️ TTS播报失败: {text}")
            except Exception as e:
                logger.error(f"❌ 异步TTS播报失败: {e}")
        else:
            # 同步模式的异步包装
            await asyncio.to_thread(self.speak_text, text)

    def test_audio_pipeline(self) -> Dict[str, Any]:
        """测试音频处理管道"""
        test_results: Dict[str, Any] = {
            "adapter_type": "AsyncAudioProcessorAdapter",
            "async_mode": self.use_async,
            "test_time": time.time(),
            "tests": {}
        }
        # 明确指定tests是字典类型
        tests: Dict[str, Dict[str, Any]] = test_results["tests"]

        try:
            # 测试数值提取
            test_text = "二十五点五"
            measurements = self.extract_measurements(test_text)
            tests["number_extraction"] = {
                "input": test_text,
                "output": measurements,
                "success": len(measurements) > 0
            }

            # 测试状态获取
            state = self.get_state()
            tests["state_check"] = {
                "state": state.name,
                "success": True
            }

            # 测试音频参数
            params = self.get_audio_parameters()
            tests["audio_parameters"] = {
                "parameters": params,
                "success": len(params) > 0
            }

            # 测试TTS状态
            tts_enabled = self.is_tts_enabled()
            tests["tts_status"] = {
                "enabled": tts_enabled,
                "success": True
            }

            # 异步模式额外测试
            if self.use_async and self._async_initialized:
                stats = self._async_capture.get_statistics()
                tests["async_stats"] = {
                    "statistics": stats,
                    "success": True
                }

            test_results["overall_success"] = all(
                test["success"] for test in tests.values()
            )

        except Exception as e:
            test_results["error"] = str(e)
            test_results["overall_success"] = False

        return test_results

    def cleanup(self):
        """同步清理资源（兼容性）"""
        try:
            # 检查是否有事件循环在运行
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果有事件循环在运行，创建清理任务
                    asyncio.create_task(self.cleanup_async())
                else:
                    # 如果没有事件循环，运行清理
                    loop.run_until_complete(self.cleanup_async())
            except RuntimeError:
                # 如果没有事件循环，创建新的来执行清理
                asyncio.run(self.cleanup_async())

        except Exception as e:
            logger.error(f"❌ 同步清理失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.async_initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup_async()


# 便捷函数

async def create_async_audio_processor_adapter(
    sample_rate: int = 16000,
    chunk_size: int = 8000,
    model_path: Optional[str] = None,
    timeout_seconds: int = 30,
    test_mode: bool = False,
    **kwargs
) -> AsyncAudioProcessorAdapter:
    """创建异步音频处理器适配器的便捷函数"""
    adapter = AsyncAudioProcessorAdapter(
        use_async=True,
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        model_path=model_path,
        timeout_seconds=timeout_seconds,
        test_mode=test_mode,
        **kwargs
    )

    await adapter.async_initialize()
    return adapter


def create_hybrid_audio_processor_adapter(
    use_async: bool = True,
    **kwargs
) -> AsyncAudioProcessorAdapter:
    """创建混合模式音频处理器适配器的便捷函数"""
    return AsyncAudioProcessorAdapter(
        use_async=use_async,
        **kwargs
    )