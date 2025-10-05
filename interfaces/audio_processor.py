# -*- coding: utf-8 -*-
"""
音频处理器接口定义

IAudioProcessor定义了音频处理的核心抽象接口，包括语音识别、
数值提取、状态管理等功能。支持同步和异步两种模式。
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable, Dict, Any, Union
from enum import Enum
import asyncio


class AudioProcessorState(Enum):
    """音频处理器状态枚举"""
    IDLE = "idle"           # 空闲状态
    RECORDING = "recording" # 录音识别状态
    PAUSED = "paused"       # 暂停状态
    STOPPED = "stopped"     # 停止状态
    ERROR = "error"         # 错误状态


class VoiceCommandType(Enum):
    """语音命令类型枚举"""
    PAUSE = "pause"         # 暂停命令
    RESUME = "resume"       # 恢复命令
    STOP = "stop"          # 停止命令
    UNKNOWN = "unknown"     # 未知命令


class RecognitionResult:
    """语音识别结果数据类"""

    def __init__(
        self,
        final_text: str = "",
        buffered_values: List[float] = None,
        collected_text: List[str] = None,
        session_data: List[Tuple[int, float, str]] = None,
        recognition_count: int = 0,
        audio_frames: int = 0,
        processing_time: float = 0.0
    ):
        self.final_text = final_text
        self.buffered_values = buffered_values or []
        self.collected_text = collected_text or []
        self.session_data = session_data or []
        self.recognition_count = recognition_count
        self.audio_frames = audio_frames
        self.processing_time = processing_time

    def __repr__(self) -> str:
        return f"RecognitionResult(text='{self.final_text}', values={len(self.buffered_values)})"


class VoiceCommand:
    """语音命令数据类"""

    def __init__(
        self,
        command_type: VoiceCommandType,
        original_text: str,
        confidence: float = 1.0,
        timestamp: float = 0.0
    ):
        self.command_type = command_type
        self.original_text = original_text
        self.confidence = confidence
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return f"VoiceCommand(type={self.command_type.value}, text='{self.original_text}')"


class IAudioProcessor(ABC):
    """
    音频处理器接口

    定义了音频处理的核心功能，包括语音识别、数值提取、
    状态管理、TTS控制等。支持同步和异步两种调用模式。
    """

    @abstractmethod
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        加载语音识别模型

        Args:
            model_path: 模型文件路径，如果为None则使用默认路径

        Returns:
            bool: 加载成功返回True，失败返回False

        Raises:
            FileNotFoundError: 模型文件不存在
            RuntimeError: 模型加载失败
        """
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """
        卸载语音识别模型，释放内存资源
        """
        pass

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """
        检查模型是否已加载

        Returns:
            bool: 模型已加载返回True，否则返回False
        """
        pass

    @abstractmethod
    def get_state(self) -> AudioProcessorState:
        """
        获取当前处理器状态

        Returns:
            AudioProcessorState: 当前状态
        """
        pass

    @abstractmethod
    def start_recognition(self, callback: Optional[Callable[[List[float]], None]] = None) -> Dict[str, Any]:
        """
        开始语音识别（同步模式）

        Args:
            callback: 数值检测回调函数

        Returns:
            Dict[str, Any]: 识别结果字典

        Raises:
            RuntimeError: 模型未加载或状态错误
        """
        pass

    @abstractmethod
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

        Raises:
            RuntimeError: 模型未加载或状态错误
            asyncio.CancelledError: 操作被取消
        """
        pass

    @abstractmethod
    def pause_recognition(self) -> None:
        """
        暂停语音识别
        """
        pass

    @abstractmethod
    def resume_recognition(self) -> None:
        """
        恢复语音识别
        """
        pass

    @abstractmethod
    def stop_recognition(self) -> None:
        """
        停止语音识别
        """
        pass

    @abstractmethod
    def set_callback(self, callback: Callable[[List[float]], None]) -> None:
        """
        设置数值检测回调函数

        Args:
            callback: 回调函数，接收数值列表参数
        """
        pass

    @abstractmethod
    def extract_measurements(self, text: str) -> List[float]:
        """
        从文本中提取数值

        Args:
            text: 输入文本

        Returns:
            List[float]: 提取的数值列表
        """
        pass

    @abstractmethod
    def process_voice_commands(self, text: str) -> Optional[VoiceCommand]:
        """
        处理语音控制命令

        Args:
            text: 识别的文本

        Returns:
            Optional[VoiceCommand]: 识别的命令对象，如果不是命令则返回None
        """
        pass

    @abstractmethod
    def get_buffered_values(self) -> List[float]:
        """
        获取缓冲的数值列表

        Returns:
            List[float]: 缓冲的数值列表
        """
        pass

    @abstractmethod
    def get_session_data(self) -> List[Tuple[int, float, str]]:
        """
        获取本次会话的数据

        Returns:
            List[Tuple[int, float, str]]: 会话数据列表，格式为(ID, 数值, 原始文本)
        """
        pass

    @abstractmethod
    def clear_buffer(self) -> None:
        """
        清空数值缓冲区
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_audio_parameters(self) -> Dict[str, Any]:
        """
        获取当前音频处理参数

        Returns:
            Dict[str, Any]: 参数字典
        """
        pass

    # TTS相关方法
    @abstractmethod
    def enable_tts(self) -> None:
        """启用TTS功能"""
        pass

    @abstractmethod
    def disable_tts(self) -> None:
        """禁用TTS功能"""
        pass

    @abstractmethod
    def toggle_tts(self) -> bool:
        """
        切换TTS开关状态

        Returns:
            bool: 切换后的TTS状态，True表示开启
        """
        pass

    @abstractmethod
    def is_tts_enabled(self) -> bool:
        """
        获取TTS当前状态

        Returns:
            bool: TTS开启状态
        """
        pass

    @abstractmethod
    def speak_text(self, text: str) -> None:
        """
        TTS播报文本

        Args:
            text: 要播报的文本
        """
        pass

    @abstractmethod
    async def speak_text_async(self, text: str) -> None:
        """
        异步TTS播报文本

        Args:
            text: 要播报的文本
        """
        pass

    # 测试和诊断方法
    @abstractmethod
    def test_audio_pipeline(self) -> Dict[str, Any]:
        """
        测试音频处理管道

        Returns:
            Dict[str, Any]: 测试结果字典
        """
        pass

    @abstractmethod
    def get_diagnostics_info(self) -> Dict[str, Any]:
        """
        获取诊断信息

        Returns:
            Dict[str, Any]: 诊断信息字典
        """
        pass

    # 资源管理
    @abstractmethod
    def cleanup(self) -> None:
        """
        清理资源，释放内存和句柄
        """
        pass

    @abstractmethod
    async def cleanup_async(self) -> None:
        """
        异步清理资源
        """
        pass