# -*- coding: utf-8 -*-
"""
TTS语音服务接口定义

ITTSProvider定义了文本转语音服务的抽象接口，支持语音合成、
播放控制、音质调节等功能。提供同步和异步两种调用模式。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass
import asyncio


class TTSState(Enum):
    """TTS状态枚举"""
    IDLE = "idle"           # 空闲状态
    READY = "ready"         # 准备就绪
    SPEAKING = "speaking"   # 正在播放
    PAUSED = "paused"       # 暂停状态
    ERROR = "error"         # 错误状态
    LOADING = "loading"     # 模型加载中


class AudioFormat(Enum):
    """音频格式枚举"""
    WAV = "wav"             # WAV格式
    MP3 = "mp3"             # MP3格式
    FLAC = "flac"           # FLAC格式
    OGG = "ogg"             # OGG格式


@dataclass
class TTSConfig:
    """TTS配置数据类"""
    model_path: str = "model/tts/zh_CN-huayan-medium.onnx"
    sample_rate: int = 22050
    volume: float = 1.0
    speed: float = 1.0
    pitch: float = 1.0

    # 语音参数
    noise_scale: float = 0.667
    noise_w_scale: float = 0.8
    length_scale: float = 1.0

    # 输出设置
    output_format: AudioFormat = AudioFormat.WAV
    output_directory: str = "WaveOutput"
    auto_play: bool = True
    auto_save: bool = False

    def __post_init__(self):
        # 参数验证
        if not 0.0 <= self.volume <= 2.0:
            raise ValueError("Volume must be between 0.0 and 2.0")
        if not 0.1 <= self.speed <= 3.0:
            raise ValueError("Speed must be between 0.1 and 3.0")
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError("Pitch must be between 0.5 and 2.0")


@dataclass
class TTSResult:
    """TTS处理结果数据类"""
    success: bool
    text: str
    audio_file_path: Optional[str] = None
    processing_time: float = 0.0
    audio_duration: float = 0.0
    error_message: Optional[str] = None
    state: TTSState = TTSState.IDLE

    def __repr__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"TTSResult({status} '{self.text[:20]}...' duration={self.audio_duration:.2f}s)"


@dataclass
class PlaybackResult:
    """播放结果数据类"""
    success: bool
    audio_file_path: str
    actual_duration: float = 0.0
    error_message: Optional[str] = None
    interrupted: bool = False

    def __repr__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"PlaybackResult({status} duration={self.actual_duration:.2f}s)"


class ITTSProvider(ABC):
    """
    TTS语音服务接口

    定义了文本转语音的核心功能，包括语音合成、播放控制、
    音质调节等。支持同步和异步两种调用模式。
    """

    @abstractmethod
    def initialize(self, config: Optional[TTSConfig] = None) -> bool:
        """
        初始化TTS服务

        Args:
            config: TTS配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False

        Raises:
            FileNotFoundError: 模型文件不存在
            RuntimeError: TTS引擎初始化失败
        """
        pass

    @abstractmethod
    async def initialize_async(self, config: Optional[TTSConfig] = None) -> bool:
        """
        异步初始化TTS服务

        Args:
            config: TTS配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查TTS服务是否已初始化

        Returns:
            bool: 已初始化返回True，否则返回False
        """
        pass

    @abstractmethod
    def get_state(self) -> TTSState:
        """
        获取当前TTS状态

        Returns:
            TTSState: 当前状态
        """
        pass

    @abstractmethod
    def speak(
        self,
        text: str,
        play: bool = True,
        output_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> TTSResult:
        """
        文本转语音并播放（同步模式）

        Args:
            text: 要转换的文本
            play: 是否自动播放
            output_file: 输出文件路径，如果为None则使用配置中的设置
            config_override: 配置覆盖参数

        Returns:
            TTSResult: TTS处理结果

        Raises:
            RuntimeError: TTS未初始化或播放失败
            ValueError: 文本为空或格式错误
        """
        pass

    @abstractmethod
    async def speak_async(
        self,
        text: str,
        play: bool = True,
        output_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> TTSResult:
        """
        异步文本转语音并播放

        Args:
            text: 要转换的文本
            play: 是否自动播放
            output_file: 输出文件路径，如果为None则使用配置中的设置
            config_override: 配置覆盖参数

        Returns:
            TTSResult: TTS处理结果
        """
        pass

    @abstractmethod
    def synthesize_speech(
        self,
        text: str,
        output_file: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> TTSResult:
        """
        仅合成语音，不播放

        Args:
            text: 要转换的文本
            output_file: 输出文件路径
            config_override: 配置覆盖参数

        Returns:
            TTSResult: 合成结果
        """
        pass

    @abstractmethod
    async def synthesize_speech_async(
        self,
        text: str,
        output_file: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> TTSResult:
        """
        异步合成语音，不播放

        Args:
            text: 要转换的文本
            output_file: 输出文件路径
            config_override: 配置覆盖参数

        Returns:
            TTSResult: 合成结果
        """
        pass

    @abstractmethod
    def play_audio(self, audio_file_path: str) -> PlaybackResult:
        """
        播放音频文件

        Args:
            audio_file_path: 音频文件路径

        Returns:
            PlaybackResult: 播放结果

        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: 播放失败
        """
        pass

    @abstractmethod
    async def play_audio_async(self, audio_file_path: str) -> PlaybackResult:
        """
        异步播放音频文件

        Args:
            audio_file_path: 音频文件路径

        Returns:
            PlaybackResult: 播放结果
        """
        pass

    @abstractmethod
    def stop_playback(self) -> bool:
        """
        停止当前播放

        Returns:
            bool: 停止成功返回True，否则返回False
        """
        pass

    @abstractmethod
    async def stop_playback_async(self) -> bool:
        """
        异步停止当前播放

        Returns:
            bool: 停止成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def pause_playback(self) -> bool:
        """
        暂停当前播放

        Returns:
            bool: 暂停成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def resume_playback(self) -> bool:
        """
        恢复播放

        Returns:
            bool: 恢复成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        """
        检查是否正在播放

        Returns:
            bool: 正在播放返回True，否则返回False
        """
        pass

    @abstractmethod
    def is_paused(self) -> bool:
        """
        检查是否已暂停

        Returns:
            bool: 已暂停返回True，否则返回False
        """
        pass

    # 批量处理方法
    @abstractmethod
    def speak_batch(
        self,
        texts: List[str],
        interval: float = 0.5,
        play: bool = True
    ) -> List[TTSResult]:
        """
        批量文本转语音

        Args:
            texts: 文本列表
            interval: 播放间隔（秒）
            play: 是否自动播放

        Returns:
            List[TTSResult]: 处理结果列表
        """
        pass

    @abstractmethod
    async def speak_batch_async(
        self,
        texts: List[str],
        interval: float = 0.5,
        play: bool = True
    ) -> List[TTSResult]:
        """
        异步批量文本转语音

        Args:
            texts: 文本列表
            interval: 播放间隔（秒）
            play: 是否自动播放

        Returns:
            List[TTSResult]: 处理结果列表
        """
        pass

    # 便捷方法
    @abstractmethod
    def speak_number(self, number: Union[int, float]) -> TTSResult:
        """
        播报数字

        Args:
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        pass

    @abstractmethod
    async def speak_number_async(self, number: Union[int, float]) -> TTSResult:
        """
        异步播报数字

        Args:
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        pass

    @abstractmethod
    def speak_numbers(self, numbers: List[Union[int, float]]) -> TTSResult:
        """
        播报数字列表

        Args:
            numbers: 数字列表

        Returns:
            TTSResult: 播报结果
        """
        pass

    @abstractmethod
    async def speak_numbers_async(self, numbers: List[Union[int, float]]) -> TTSResult:
        """
        异步播报数字列表

        Args:
            numbers: 数字列表

        Returns:
            TTSResult: 播报结果
        """
        pass

    @abstractmethod
    def speak_with_info(self, info: str, number: Union[int, float]) -> TTSResult:
        """
        带信息播报数字

        Args:
            info: 信息文本
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        pass

    @abstractmethod
    async def speak_with_info_async(self, info: str, number: Union[int, float]) -> TTSResult:
        """
        异步带信息播报数字

        Args:
            info: 信息文本
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        pass

    # 配置管理
    @abstractmethod
    def set_config(self, config: TTSConfig) -> None:
        """
        设置TTS配置

        Args:
            config: TTS配置
        """
        pass

    @abstractmethod
    def get_config(self) -> TTSConfig:
        """
        获取当前TTS配置

        Returns:
            TTSConfig: 当前配置
        """
        pass

    @abstractmethod
    def update_volume(self, volume: float) -> None:
        """
        更新音量

        Args:
            volume: 音量值 (0.0 - 2.0)
        """
        pass

    @abstractmethod
    def update_speed(self, speed: float) -> None:
        """
        更新语速

        Args:
            speed: 语速值 (0.1 - 3.0)
        """
        pass

    @abstractmethod
    def update_pitch(self, pitch: float) -> None:
        """
        更新音调

        Args:
            pitch: 音调值 (0.5 - 2.0)
        """
        pass

    # 状态和统计
    @abstractmethod
    def get_supported_formats(self) -> List[AudioFormat]:
        """
        获取支持的音频格式

        Returns:
            List[AudioFormat]: 支持的格式列表
        """
        pass

    @abstractmethod
    def get_voices(self) -> List[str]:
        """
        获取可用的语音列表

        Returns:
            List[str]: 语音列表
        """
        pass

    @abstractmethod
    def set_voice(self, voice_name: str) -> bool:
        """
        设置语音

        Args:
            voice_name: 语音名称

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取TTS使用统计

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        pass

    # 测试和诊断
    @abstractmethod
    def test_tts(self, test_text: str = "测试语音合成功能") -> TTSResult:
        """
        测试TTS功能

        Args:
            test_text: 测试文本

        Returns:
            TTSResult: 测试结果
        """
        pass

    @abstractmethod
    async def test_tts_async(self, test_text: str = "测试语音合成功能") -> TTSResult:
        """
        异步测试TTS功能

        Args:
            test_text: 测试文本

        Returns:
            TTSResult: 测试结果
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
        清理TTS资源
        """
        pass

    @abstractmethod
    async def cleanup_async(self) -> None:
        """
        异步清理TTS资源
        """
        pass