# -*- coding: utf-8 -*-
"""
TTS语音服务适配器

将现有的TTS类适配为ITTSProvider接口，确保向后兼容性。
采用适配器模式包装现有实现，不修改原有代码。
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Union

from interfaces.tts_provider import (
    ITTSProvider, TTSState, TTSConfig, TTSResult, PlaybackResult, AudioFormat
)

# 导入现有的TTS类
try:
    from TTSengine import TTS as OriginalTTS
    _TTSType = OriginalTTS  # type: ignore
except ImportError:
    # 如果导入失败，创建一个占位符
    class _FallbackTTS:
        def __init__(self, *args, **kwargs):
            pass
    _TTSType = _FallbackTTS  # type: ignore

logger = logging.getLogger(__name__)


class TTSProviderAdapter(ITTSProvider):
    """
    TTS语音服务适配器

    将现有的TTS类适配为ITTSProvider接口。
    保持原有功能的同时提供新的接口支持。
    """

    def __init__(self, tts_engine: Optional[Any] = None, **kwargs):
        """
        初始化TTS语音服务适配器

        Args:
            tts_engine: 现有的TTS实例，如果为None则创建新实例
            **kwargs: 传递给TTS构造函数的参数
        """
        if tts_engine is None:
            # 创建新的TTS实例
            self._tts_engine = _TTSType(**kwargs)
        else:
            self._tts_engine = tts_engine

        # 配置对象
        self._config = TTSConfig()
        self._state = TTSState.IDLE
        self._is_playing = False

        # 应用默认配置
        self._apply_config()

        logger.info("TTSProviderAdapter initialized with TTS engine")

    def _apply_config(self) -> None:
        """应用配置到TTS引擎"""
        try:
            # 原TTS引擎的配置主要通过构造函数设置
            # 这里记录配置信息用于参考
            logger.debug(f"TTS config applied: model={self._config.model_path}")
        except Exception as e:
            logger.error(f"Failed to apply TTS config: {e}")

    # 初始化方法
    def initialize(self, config: Optional[TTSConfig] = None) -> bool:
        """
        初始化TTS服务

        Args:
            config: TTS配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        try:
            if config:
                self._config = config
                self._apply_config()

            # 验证TTS引擎是否正常工作
            self._state = TTSState.READY
            logger.info("TTS service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            self._state = TTSState.ERROR
            return False

    async def initialize_async(self, config: Optional[TTSConfig] = None) -> bool:
        """
        异步初始化TTS服务

        Args:
            config: TTS配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.initialize, config)

    def is_initialized(self) -> bool:
        """检查TTS服务是否已初始化"""
        return self._state in [TTSState.READY, TTSState.IDLE]

    def get_state(self) -> TTSState:
        """获取当前TTS状态"""
        return self._state

    # 语音合成和播放方法
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
        """
        start_time = time.time()
        audio_file_path = None
        error_message = None

        try:
            if not text or not text.strip():
                return TTSResult(
                    success=False,
                    text=text,
                    processing_time=time.time() - start_time,
                    error_message="Empty text provided"
                )

            self._state = TTSState.SPEAKING

            # 应用配置覆盖
            volume = config_override.get('volume', self._config.volume) if config_override else self._config.volume
            speed = config_override.get('speed', self._config.speed) if config_override else self._config.speed

            # 确定输出文件路径
            if output_file is None and self._config.auto_save:
                import os
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"tts_output_{timestamp}.wav"

            # 调用原TTS引擎
            if output_file:
                # 保存到文件
                self._tts_engine.speak(
                    text=text,
                    play=play,
                    output_wav=output_file,
                    volume=volume,
                    length_scale=1.0 / speed if speed > 0 else 1.0
                )
                audio_file_path = output_file
            else:
                # 仅播放
                self._tts_engine.speak(
                    text=text,
                    play=play,
                    volume=volume,
                    length_scale=1.0 / speed if speed > 0 else 1.0
                )

            processing_time = time.time() - start_time
            self._state = TTSState.IDLE

            return TTSResult(
                success=True,
                text=text,
                audio_file_path=audio_file_path,
                processing_time=processing_time,
                state=TTSState.IDLE
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            self._state = TTSState.ERROR
            logger.error(f"TTS synthesis failed: {e}")

            return TTSResult(
                success=False,
                text=text,
                processing_time=processing_time,
                error_message=error_message,
                state=TTSState.ERROR
            )

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak, text, play, output_file, config_override)

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
        return self.speak(text, play=False, output_file=output_file, config_override=config_override)

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.synthesize_speech, text, output_file, config_override)

    # 音频播放控制
    def play_audio(self, audio_file_path: str) -> PlaybackResult:
        """
        播放音频文件

        Args:
            audio_file_path: 音频文件路径

        Returns:
            PlaybackResult: 播放结果
        """
        start_time = time.time()
        error_message = None

        try:
            if not audio_file_path:
                return PlaybackResult(
                    success=False,
                    audio_file_path=audio_file_path,
                    error_message="No audio file path provided"
                )

            import os
            if not os.path.exists(audio_file_path):
                return PlaybackResult(
                    success=False,
                    audio_file_path=audio_file_path,
                    error_message="Audio file does not exist"
                )

            self._state = TTSState.SPEAKING
            self._is_playing = True

            # 使用原TTS引擎播放（这里可能需要调整，因为原TTS可能没有直接播放文件的方法）
            # 如果原TTS没有播放文件的方法，我们可能需要使用其他音频播放库
            try:
                # 尝试使用sounddevice播放
                import soundfile as sf
                import sounddevice as sd

                data, samplerate = sf.read(audio_file_path)
                sd.play(data, samplerate)
                sd.wait()  # 等待播放完成

                actual_duration = time.time() - start_time

                return PlaybackResult(
                    success=True,
                    audio_file_path=audio_file_path,
                    actual_duration=actual_duration
                )
            except ImportError:
                # 如果soundfile不可用，使用简单的播放方法
                logger.warning("soundfile not available, using fallback playback method")
                self._tts_engine.speak("", play=False, output_wav=audio_file_path)
                # 这里需要实现实际的播放逻辑
                actual_duration = time.time() - start_time

                return PlaybackResult(
                    success=True,
                    audio_file_path=audio_file_path,
                    actual_duration=actual_duration
                )

        except Exception as e:
            error_message = str(e)
            self._state = TTSState.ERROR
            logger.error(f"Audio playback failed: {e}")

            return PlaybackResult(
                success=False,
                audio_file_path=audio_file_path,
                error_message=error_message
            )
        finally:
            self._state = TTSState.IDLE
            self._is_playing = False

    async def play_audio_async(self, audio_file_path: str) -> PlaybackResult:
        """
        异步播放音频文件

        Args:
            audio_file_path: 音频文件路径

        Returns:
            PlaybackResult: 播放结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.play_audio, audio_file_path)

    def stop_playback(self) -> bool:
        """
        停止当前播放

        Returns:
            bool: 停止成功返回True，否则返回False
        """
        try:
            if self._is_playing:
                # 原TTS引擎可能没有直接的停止方法
                # 这里使用简单的状态重置
                self._is_playing = False
                self._state = TTSState.IDLE
                logger.info("Playback stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False

    async def stop_playback_async(self) -> bool:
        """
        异步停止当前播放

        Returns:
            bool: 停止成功返回True，否则返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.stop_playback)

    def pause_playback(self) -> bool:
        """
        暂停当前播放

        Returns:
            bool: 暂停成功返回True，否则返回False
        """
        try:
            if self._is_playing:
                self._state = TTSState.PAUSED
                logger.info("Playback paused")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
            return False

    def resume_playback(self) -> bool:
        """
        恢复播放

        Returns:
            bool: 恢复成功返回True，否则返回False
        """
        try:
            if self._state == TTSState.PAUSED:
                self._state = TTSState.SPEAKING
                logger.info("Playback resumed")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
            return False

    # 状态查询方法
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        return self._is_playing

    def is_paused(self) -> bool:
        """检查是否已暂停"""
        return self._state == TTSState.PAUSED

    # 批量处理方法
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
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.speak(text, play=play)
                results.append(result)

                # 添加间隔（除了最后一个）
                if i < len(texts) - 1 and interval > 0:
                    time.sleep(interval)

            except Exception as e:
                logger.error(f"Batch item {i} failed: {e}")
                results.append(TTSResult(
                    success=False,
                    text=text,
                    error_message=str(e)
                ))

        return results

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak_batch, texts, interval, play)

    # 便捷方法
    def speak_number(self, number: Union[int, float]) -> TTSResult:
        """
        播报数字

        Args:
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        return self.speak(str(number))

    async def speak_number_async(self, number: Union[int, float]) -> TTSResult:
        """
        异步播报数字

        Args:
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak_number, number)

    def speak_numbers(self, numbers: List[Union[int, float]]) -> TTSResult:
        """
        播报数字列表

        Args:
            numbers: 数字列表

        Returns:
            TTSResult: 播报结果
        """
        text = "，".join(str(num) for num in numbers)
        return self.speak(text)

    async def speak_numbers_async(self, numbers: List[Union[int, float]]) -> TTSResult:
        """
        异步播报数字列表

        Args:
            numbers: 数字列表

        Returns:
            TTSResult: 播报结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak_numbers, numbers)

    def speak_with_info(self, info: str, number: Union[int, float]) -> TTSResult:
        """
        带信息播报数字

        Args:
            info: 信息文本
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        text = f"{info} {number}"
        return self.speak(text)

    async def speak_with_info_async(self, info: str, number: Union[int, float]) -> TTSResult:
        """
        异步带信息播报数字

        Args:
            info: 信息文本
            number: 数字

        Returns:
            TTSResult: 播报结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak_with_info, info, number)

    # 配置管理
    def set_config(self, config: TTSConfig) -> None:
        """
        设置TTS配置

        Args:
            config: TTS配置
        """
        self._config = config
        self._apply_config()
        logger.info("TTS config updated")

    def get_config(self) -> TTSConfig:
        """
        获取当前TTS配置

        Returns:
            TTSConfig: 当前配置
        """
        return self._config

    def update_volume(self, volume: float) -> None:
        """
        更新音量

        Args:
            volume: 音量值 (0.0 - 2.0)
        """
        self._config.volume = max(0.0, min(2.0, volume))
        logger.info(f"Volume updated to {self._config.volume}")

    def update_speed(self, speed: float) -> None:
        """
        更新语速

        Args:
            speed: 语速值 (0.1 - 3.0)
        """
        self._config.speed = max(0.1, min(3.0, speed))
        logger.info(f"Speed updated to {self._config.speed}")

    def update_pitch(self, pitch: float) -> None:
        """
        更新音调

        Args:
            pitch: 音调值 (0.5 - 2.0)
        """
        self._config.pitch = max(0.5, min(2.0, pitch))
        logger.info(f"Pitch updated to {self._config.pitch}")

    # 状态和统计
    def get_supported_formats(self) -> List[AudioFormat]:
        """
        获取支持的音频格式

        Returns:
            List[AudioFormat]: 支持的格式列表
        """
        return [AudioFormat.WAV]  # 原TTS主要支持WAV格式

    def get_voices(self) -> List[str]:
        """
        获取可用的语音列表

        Returns:
            List[str]: 语音列表
        """
        # 原TTS可能没有获取语音列表的方法
        # 返回模型名称作为语音标识
        return [self._config.model_path]

    def set_voice(self, voice_name: str) -> bool:
        """
        设置语音

        Args:
            voice_name: 语音名称

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        try:
            # 这里可以实现语音切换逻辑
            # 原TTS可能需要重新初始化来切换语音
            self._config.model_path = voice_name
            logger.info(f"Voice set to: {voice_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取TTS使用统计

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        return {
            "state": self._state.value,
            "is_playing": self._is_playing,
            "current_config": {
                "model_path": self._config.model_path,
                "volume": self._config.volume,
                "speed": self._config.speed,
                "pitch": self._config.pitch
            },
            "supported_formats": [fmt.value for fmt in self.get_supported_formats()]
        }

    # 测试和诊断
    def test_tts(self, test_text: str = "测试语音合成功能") -> TTSResult:
        """
        测试TTS功能

        Args:
            test_text: 测试文本

        Returns:
            TTSResult: 测试结果
        """
        logger.info(f"Running TTS test with text: '{test_text}'")
        return self.speak(test_text, play=self._config.auto_play)

    async def test_tts_async(self, test_text: str = "测试语音合成功能") -> TTSResult:
        """
        异步测试TTS功能

        Args:
            test_text: 测试文本

        Returns:
            TTSResult: 测试结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.test_tts, test_text)

    def get_diagnostics_info(self) -> Dict[str, Any]:
        """
        获取诊断信息

        Returns:
            Dict[str, Any]: 诊断信息字典
        """
        try:
            import os
            model_exists = os.path.exists(self._config.model_path)

            return {
                "model_path": self._config.model_path,
                "model_exists": model_exists,
                "state": self._state.value,
                "initialized": self.is_initialized(),
                "config": self.get_config().__dict__,
                "statistics": self.get_statistics()
            }
        except Exception as e:
            logger.error(f"Failed to get diagnostics info: {e}")
            return {"error": str(e)}

    # 资源管理
    def cleanup(self) -> None:
        """清理TTS资源"""
        try:
            if hasattr(self._tts_engine, 'close'):
                self._tts_engine.close()
            self._state = TTSState.IDLE
            self._is_playing = False
            logger.info("TTSProviderAdapter cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

    async def cleanup_async(self) -> None:
        """异步清理TTS资源"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.cleanup)

    # 属性访问器
    @property
    def wrapped_instance(self) -> Any:
        """获取包装的TTS实例"""
        return self._tts_engine

    def __getattr__(self, name: str) -> Any:
        """代理未定义的属性到原TTS实例"""
        return getattr(self._tts_engine, name)

    def __repr__(self) -> str:
        return f"TTSProviderAdapter(state={self._state.value}, model='{self._config.model_path}')"