# -*- coding: utf-8 -*-
"""
音频处理器适配器

将现有的AudioCapture类适配为IAudioProcessor接口，确保向后兼容性。
采用适配器模式包装现有实现，不修改原有代码。
"""

import asyncio
import logging
from typing import List, Tuple, Optional, Callable, Dict, Any, Union

from interfaces.audio_processor import (
    IAudioProcessor, AudioProcessorState, VoiceCommandType,
    RecognitionResult, VoiceCommand
)

# 导入现有的AudioCapture类
try:
    from audio_capture_v import AudioCapture as OriginalAudioCapture
    _AudioCaptureType = OriginalAudioCapture  # type: ignore
except ImportError:
    # 如果导入失败，创建一个占位符
    class _FallbackAudioCapture:
        def __init__(self, *args, **kwargs):
            pass
    _AudioCaptureType = _FallbackAudioCapture  # type: ignore

logger = logging.getLogger(__name__)


class AudioProcessorAdapter(IAudioProcessor):
    """
    音频处理器适配器

    将现有的AudioCapture类适配为IAudioProcessor接口。
    保持原有功能的同时提供新的接口支持。
    """

    def __init__(self, audio_capture=None, **kwargs):
        """
        初始化音频处理器适配器

        Args:
            audio_capture: 现有的AudioCapture实例，如果为None则创建新实例
            **kwargs: 传递给AudioCapture构造函数的参数
        """
        if audio_capture is None:
            # 创建新的AudioCapture实例
            self._audio_capture = _AudioCaptureType(**kwargs)
        else:
            self._audio_capture = audio_capture

        # 回调函数存储
        self._callback = None

        logger.info("AudioProcessorAdapter initialized with AudioCapture")

    # 模型管理方法
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        加载语音识别模型

        Args:
            model_path: 模型文件路径，如果为None则使用默认路径

        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            if model_path:
                # 临时设置模型路径
                original_path = self._audio_capture.model_path
                self._audio_capture.model_path = model_path
                result = self._audio_capture.load_model()
                self._audio_capture.model_path = original_path
            else:
                result = self._audio_capture.load_model()

            logger.info(f"Model loading result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def unload_model(self) -> None:
        """卸载语音识别模型，释放内存资源"""
        try:
            self._audio_capture.unload_model()
            logger.info("Model unloaded successfully")
        except Exception as e:
            logger.error(f"Failed to unload model: {e}")

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return getattr(self._audio_capture, '_model_loaded', False)

    # 状态管理方法
    def get_state(self) -> AudioProcessorState:
        """获取当前处理器状态"""
        state_map = {
            'idle': AudioProcessorState.IDLE,
            'recording': AudioProcessorState.RECORDING,
            'paused': AudioProcessorState.PAUSED,
            'stopped': AudioProcessorState.STOPPED
        }

        current_state = getattr(self._audio_capture, 'state', 'idle')
        return state_map.get(current_state, AudioProcessorState.ERROR)

    # 语音识别方法
    def start_recognition(self, callback: Optional[Callable[[List[float]], None]] = None) -> Dict[str, Any]:
        """
        开始语音识别（同步模式）

        Args:
            callback: 数值检测回调函数

        Returns:
            Dict[str, Any]: 识别结果字典
        """
        if callback:
            self.set_callback(callback)

        try:
            result = self._audio_capture.listen_realtime_vosk()
            logger.info("Voice recognition completed successfully")
            return result
        except Exception as e:
            logger.error(f"Voice recognition failed: {e}")
            return {
                "final": "",
                "buffered_values": [],
                "collected_text": [],
                "session_data": [],
                "error": str(e)
            }

    async def start_recognition_async(
        self,
        callback: Optional[Callable[[List[float]], None]] = None
    ) -> RecognitionResult:
        """
        开始语音识别（异步模式）

        Args:
            callback: 数值检测回调函数

        Returns:
            RecognitionResult: 识别结果对象
        """
        if callback:
            self.set_callback(callback)

        # 在线程池中执行同步方法
        loop = asyncio.get_event_loop()
        try:
            result_dict = await loop.run_in_executor(None, self.start_recognition)

            # 转换为RecognitionResult对象
            return RecognitionResult(
                final_text=result_dict.get("final", ""),
                buffered_values=result_dict.get("buffered_values", []),
                collected_text=result_dict.get("collected_text", []),
                session_data=result_dict.get("session_data", []),
                recognition_count=len(result_dict.get("collected_text", [])),
                processing_time=0.0  # 原实现中没有时间统计
            )
        except Exception as e:
            logger.error(f"Async voice recognition failed: {e}")
            return RecognitionResult(
                final_text="",
                buffered_values=[],
                collected_text=[],
                session_data=[]
            )

    def pause_recognition(self) -> None:
        """暂停语音识别"""
        try:
            self._audio_capture.pause()
            logger.info("Voice recognition paused")
        except Exception as e:
            logger.error(f"Failed to pause recognition: {e}")

    def resume_recognition(self) -> None:
        """恢复语音识别"""
        try:
            self._audio_capture.resume()
            logger.info("Voice recognition resumed")
        except Exception as e:
            logger.error(f"Failed to resume recognition: {e}")

    def stop_recognition(self) -> None:
        """停止语音识别"""
        try:
            self._audio_capture.stop()
            logger.info("Voice recognition stopped")
        except Exception as e:
            logger.error(f"Failed to stop recognition: {e}")

    # 回调和数据处理方法
    def set_callback(self, callback: Callable[[List[float]], None]) -> None:
        """
        设置数值检测回调函数

        Args:
            callback: 回调函数，接收数值列表参数
        """
        self._callback = callback
        # 设置到原AudioCapture中
        self._audio_capture.set_callback(callback)

    def extract_measurements(self, text: str) -> List[float]:
        """
        从文本中提取数值

        Args:
            text: 输入文本

        Returns:
            List[float]: 提取的数值列表
        """
        try:
            from audio_capture_v import extract_measurements
            return extract_measurements(text)
        except Exception as e:
            logger.error(f"Failed to extract measurements from '{text}': {e}")
            return []

    def process_voice_commands(self, text: str) -> Optional[VoiceCommand]:
        """
        处理语音控制命令

        Args:
            text: 识别的文本

        Returns:
            Optional[VoiceCommand]: 识别的命令对象，如果不是命令则返回None
        """
        try:
            # 使用原AudioCapture的命令处理逻辑
            is_command = self._audio_capture._process_voice_commands(text)
            if not is_command:
                return None

            # 确定命令类型
            text_lower = text.lower()
            if any(word in text_lower for word in ["暂停", "pause"]):
                command_type = VoiceCommandType.PAUSE
            elif any(word in text_lower for word in ["继续", "恢复", "resume"]):
                command_type = VoiceCommandType.RESUME
            elif any(word in text_lower for word in ["停止", "结束", "stop"]):
                command_type = VoiceCommandType.STOP
            else:
                command_type = VoiceCommandType.UNKNOWN

            return VoiceCommand(
                command_type=command_type,
                original_text=text,
                confidence=1.0  # 原实现中没有置信度
            )
        except Exception as e:
            logger.error(f"Failed to process voice command '{text}': {e}")
            return None

    def get_buffered_values(self) -> List[float]:
        """获取缓冲的数值列表"""
        return list(self._audio_capture.buffered_values)

    def get_session_data(self) -> List[Tuple[int, float, str]]:
        """获取本次会话的数据"""
        try:
            if hasattr(self._audio_capture, '_exporter') and self._audio_capture._exporter:
                return self._audio_capture._exporter.get_session_data()
            return []
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return []

    def clear_buffer(self) -> None:
        """清空数值缓冲区"""
        try:
            self._audio_capture.buffered_values.clear()
            logger.info("Buffer cleared")
        except Exception as e:
            logger.error(f"Failed to clear buffer: {e}")

    # 参数配置方法
    def set_audio_parameters(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 8000,
        timeout_seconds: int = 60
    ) -> None:
        """
        设置音频处理参数

        Args:
            sample_rate: 采样率
            chunk_size: 音频块大小
            timeout_seconds: 超时时间
        """
        try:
            self._audio_capture.sample_rate = sample_rate
            self._audio_capture.audio_chunk_size = chunk_size
            self._audio_capture.timeout_seconds = timeout_seconds
            logger.info(f"Audio parameters updated: sr={sample_rate}, chunk={chunk_size}, timeout={timeout_seconds}")
        except Exception as e:
            logger.error(f"Failed to set audio parameters: {e}")

    def get_audio_parameters(self) -> Dict[str, Any]:
        """获取当前音频处理参数"""
        return {
            "sample_rate": getattr(self._audio_capture, 'sample_rate', 16000),
            "chunk_size": getattr(self._audio_capture, 'audio_chunk_size', 8000),
            "timeout_seconds": getattr(self._audio_capture, 'timeout_seconds', 60),
            "model_path": getattr(self._audio_capture, 'model_path', '')
        }

    # TTS相关方法
    def enable_tts(self) -> None:
        """启用TTS功能"""
        try:
            self._audio_capture.enable_tts()
            logger.info("TTS enabled")
        except Exception as e:
            logger.error(f"Failed to enable TTS: {e}")

    def disable_tts(self) -> None:
        """禁用TTS功能"""
        try:
            self._audio_capture.disable_tts()
            logger.info("TTS disabled")
        except Exception as e:
            logger.error(f"Failed to disable TTS: {e}")

    def toggle_tts(self) -> bool:
        """
        切换TTS开关状态

        Returns:
            bool: 切换后的TTS状态，True表示开启
        """
        try:
            self._audio_capture.toggle_tts()
            return self._audio_capture.get_tts_status() == "on"
        except Exception as e:
            logger.error(f"Failed to toggle TTS: {e}")
            return False

    def is_tts_enabled(self) -> bool:
        """获取TTS当前状态"""
        return getattr(self._audio_capture, 'get_tts_status', lambda: "off")() == "on"

    def speak_text(self, text: str) -> None:
        """
        TTS播报文本

        Args:
            text: 要播报的文本
        """
        try:
            if hasattr(self._audio_capture, 'tts') and self._audio_capture.tts:
                self._audio_capture.tts.speak(text)
                logger.info(f"TTS spoke: '{text}'")
        except Exception as e:
            logger.error(f"Failed to speak text '{text}': {e}")

    async def speak_text_async(self, text: str) -> None:
        """
        异步TTS播报文本

        Args:
            text: 要播报的文本
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.speak_text, text)
        except Exception as e:
            logger.error(f"Failed to speak text async '{text}': {e}")

    # 测试和诊断方法
    def test_audio_pipeline(self) -> Dict[str, Any]:
        """测试音频处理管道"""
        try:
            if hasattr(self._audio_capture, 'test_voice_recognition_pipeline'):
                return self._audio_capture.test_voice_recognition_pipeline()
            else:
                return {
                    "audio_input_working": False,
                    "model_loading_success": False,
                    "error": "Test method not available"
                }
        except Exception as e:
            logger.error(f"Audio pipeline test failed: {e}")
            return {
                "audio_input_working": False,
                "model_loading_success": False,
                "error": str(e)
            }

    def get_diagnostics_info(self) -> Dict[str, Any]:
        """获取诊断信息"""
        try:
            return {
                "state": self.get_state().value,
                "model_loaded": self.is_model_loaded(),
                "tts_enabled": self.is_tts_enabled(),
                "audio_parameters": self.get_audio_parameters(),
                "buffered_values_count": len(self.get_buffered_values()),
                "session_data_count": len(self.get_session_data())
            }
        except Exception as e:
            logger.error(f"Failed to get diagnostics info: {e}")
            return {"error": str(e)}

    # 资源管理
    def cleanup(self) -> None:
        """清理资源，释放内存和句柄"""
        try:
            self.unload_model()
            if hasattr(self._audio_capture, 'cleanup'):
                self._audio_capture.cleanup()
            logger.info("AudioProcessorAdapter cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

    async def cleanup_async(self) -> None:
        """异步清理资源"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.cleanup)

    # 属性访问器
    @property
    def wrapped_instance(self) -> Any:
        """获取包装的AudioCapture实例"""
        return self._audio_capture

    def __getattr__(self, name: str) -> Any:
        """代理未定义的属性到原AudioCapture实例"""
        return getattr(self._audio_capture, name)

    def __repr__(self) -> str:
        return f"AudioProcessorAdapter(state={self.get_state().value}, model_loaded={self.is_model_loaded()})"