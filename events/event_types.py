# -*- coding: utf-8 -*-
"""
具体事件类型定义

定义系统中使用的各种具体事件类型。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import time

from .base_event import (
    AudioEvent, SystemEvent, RecognitionEvent, TTSEvent,
    ConfigurationEvent, DataEvent, EventPriority
)


# 音频相关事件

@dataclass
class AudioStreamStartedEvent(AudioEvent):
    """音频流启动事件"""
    sample_rate: int = 16000
    channels: int = 1
    format_type: str = "int16"

    def __init__(self, source: str, stream_id: str, sample_rate: int = 16000, channels: int = 1, format_type: str = "int16", **kwargs):
        super().__init__(source, stream_id, **kwargs)
        self.sample_rate = sample_rate
        self.channels = channels
        self.format_type = format_type
        self.data.update({
            "sample_rate": sample_rate,
            "channels": channels,
            "format_type": format_type
        })

    def get_summary(self) -> str:
        return f"音频流已启动 (ID: {self.stream_id}, 采样率: {self.sample_rate}Hz)"


@dataclass
class AudioStreamStoppedEvent(AudioEvent):
    """音频流停止事件"""
    reason: Optional[str] = None
    duration: Optional[float] = None

    def __init__(self, source: str, stream_id: str, reason: Optional[str] = None, duration: Optional[float] = None, **kwargs):
        super().__init__(source, stream_id, **kwargs)
        self.reason = reason
        self.duration = duration
        self.data.update({
            "reason": reason,
            "duration": duration
        })

    def get_summary(self) -> str:
        return f"音频流已停止 (ID: {self.stream_id}, 原因: {self.reason})"


@dataclass
class AudioDataReceivedEvent(AudioEvent):
    """音频数据接收事件"""
    audio_data: bytes = b""
    size: int = 0
    sequence_number: int = 0

    def __init__(self, source: str, stream_id: str, audio_data: bytes = b"", size: int = 0, sequence_number: int = 0, **kwargs):
        super().__init__(source, stream_id, **kwargs)
        self.audio_data = audio_data
        self.size = size
        self.sequence_number = sequence_number
        self.data.update({
            "audio_data": audio_data,
            "size": size,
            "sequence_number": sequence_number
        })

    def get_summary(self) -> str:
        return f"接收音频数据 (流ID: {self.stream_id}, 大小: {self.size}字节)"


@dataclass
class AudioStreamErrorEvent(AudioEvent):
    """音频流错误事件"""
    error_code: Optional[str] = None
    error_message: str = ""

    def get_summary(self) -> str:
        return f"音频流错误 (流ID: {self.stream_id}): {self.error_message}"


# 语音识别相关事件

@dataclass
class RecognitionStartedEvent(RecognitionEvent):
    """语音识别启动事件"""
    model_path: Optional[str] = None
    language: str = "zh-CN"

    def __init__(self, source: str, recognizer_id: str, model_path: Optional[str] = None, language: str = "zh-CN", **kwargs):
        super().__init__(source, recognizer_id, **kwargs)
        self.model_path = model_path
        self.language = language
        self.data.update({
            "model_path": model_path,
            "language": language
        })

    def get_summary(self) -> str:
        return f"语音识别已启动 (ID: {self.recognizer_id}, 语言: {self.language})"


@dataclass
class RecognitionCompletedEvent(RecognitionEvent):
    """语音识别完成事件"""
    text: str = ""
    confidence: float = 0.0
    measurements: List[float] = None
    processing_time: float = 0.0

    def __init__(self, source: str, recognizer_id: str, text: str = "", confidence: float = 0.0, measurements: List[float] = None, processing_time: float = 0.0, **kwargs):
        super().__init__(source, recognizer_id, **kwargs)
        self.text = text
        self.confidence = confidence
        self.measurements = measurements or []
        self.processing_time = processing_time
        self.data.update({
            "text": text,
            "confidence": confidence,
            "measurements": self.measurements,
            "processing_time": processing_time
        })

    def get_summary(self) -> str:
        return f"识别完成: '{self.text}' (置信度: {self.confidence:.2f})"


@dataclass
class RecognitionPartialEvent(RecognitionEvent):
    """部分识别结果事件"""
    partial_text: str = ""
    confidence: float = 0.0

    def __init__(self, source: str, recognizer_id: str, partial_text: str = "", confidence: float = 0.0, **kwargs):
        super().__init__(source, recognizer_id, **kwargs)
        self.partial_text = partial_text
        self.confidence = confidence
        self.data.update({
            "partial_text": partial_text,
            "confidence": confidence
        })

    def get_summary(self) -> str:
        return f"部分识别: '{self.partial_text}' (置信度: {self.confidence:.2f})"


@dataclass
class RecognitionErrorEvent(RecognitionEvent):
    """语音识别错误事件"""
    error_type: str = ""
    error_message: str = ""
    error_code: Optional[str] = None

    def get_summary(self) -> str:
        return f"识别错误 (ID: {self.recognizer_id}): {self.error_message}"


# TTS相关事件

@dataclass
class TTSPlaybackStartedEvent(TTSEvent):
    """TTS播放开始事件"""
    voice_id: Optional[str] = None
    volume: float = 1.0

    def __init__(self, source: str, player_id: str, text: str, voice_id: Optional[str] = None, volume: float = 1.0, **kwargs):
        super().__init__(source, player_id, text, **kwargs)
        self.voice_id = voice_id
        self.volume = volume
        self.data.update({
            "voice_id": voice_id,
            "volume": volume
        })

    def get_summary(self) -> str:
        return f"TTS播放开始: '{self.text}' (播放器ID: {self.player_id})"


@dataclass
class TTSPlaybackCompletedEvent(TTSEvent):
    """TTS播放完成事件"""
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    def __init__(self, source: str, player_id: str, text: str, duration: float = 0.0, success: bool = True, error_message: Optional[str] = None, **kwargs):
        super().__init__(source, player_id, text, **kwargs)
        self.duration = duration
        self.success = success
        self.error_message = error_message
        self.data.update({
            "duration": duration,
            "success": success,
            "error_message": error_message
        })

    def get_summary(self) -> str:
        status = "成功" if self.success else "失败"
        return f"TTS播放{status}: '{self.text}' (耗时: {self.duration:.2f}s)"


@dataclass
class TTSErrorEvent(TTSEvent):
    """TTS错误事件"""
    error_type: str = ""
    error_message: str = ""

    def get_summary(self) -> str:
        return f"TTS错误 (播放器ID: {self.player_id}): {self.error_message}"


# 系统相关事件

@dataclass
class ComponentStateChangedEvent(SystemEvent):
    """组件状态变更事件"""
    old_state: str = ""
    new_state: str = ""
    state_type: str = "generic"

    def __init__(self, source: str, component: str, old_state: str = "", new_state: str = "", state_type: str = "generic", **kwargs):
        super().__init__(source, component, **kwargs)
        self.old_state = old_state
        self.new_state = new_state
        self.state_type = state_type
        self.data.update({
            "old_state": old_state,
            "new_state": new_state,
            "state_type": state_type
        })

    def get_summary(self) -> str:
        return f"组件状态变更 ({self.component}): {self.old_state} → {self.new_state}"


@dataclass
class SystemStartedEvent(SystemEvent):
    """系统启动事件"""
    version: str = ""
    startup_time: float = 0.0

    def __init__(self, source: str, component: str, version: str = "", startup_time: float = 0.0, **kwargs):
        super().__init__(source, component, **kwargs)
        self.version = version
        self.startup_time = startup_time
        self.data.update({
            "version": version,
            "startup_time": startup_time
        })

    def get_summary(self) -> str:
        return f"系统启动完成 (版本: {self.version}, 耗时: {self.startup_time:.2f}s)"


@dataclass
class SystemShutdownEvent(SystemEvent):
    """系统关闭事件"""
    reason: str = "normal"
    shutdown_time: float = 0.0

    def __init__(self, source: str, component: str, reason: str = "normal", shutdown_time: float = 0.0, **kwargs):
        super().__init__(source, component, **kwargs)
        self.reason = reason
        self.shutdown_time = shutdown_time
        self.data.update({
            "reason": reason,
            "shutdown_time": shutdown_time
        })

    def get_summary(self) -> str:
        return f"系统关闭 (原因: {self.reason}, 耗时: {self.shutdown_time:.2f}s)"


@dataclass
class ErrorEvent(SystemEvent):
    """错误事件"""
    error_type: str = ""
    error_message: str = ""
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None

    def __init__(self, source: str, component: str, error_type: str = "", error_message: str = "", exception: Optional[Exception] = None, **kwargs):
        super().__init__(source, component, **kwargs)
        self.error_type = error_type
        self.error_message = error_message
        self.exception = exception
        self.data.update({
            "error_type": error_type,
            "error_message": error_message
        })
        if self.priority == EventPriority.NORMAL:
            self.priority = EventPriority.HIGH

    def get_summary(self) -> str:
        return f"系统错误 ({self.component}): {self.error_type}: {self.error_message}"


@dataclass
class PerformanceMetricEvent(SystemEvent):
    """性能指标事件"""
    metric_name: str = ""
    metric_value: float = 0.0
    metric_unit: str = ""
    timestamp: float = 0.0

    def __init__(self, source: str, component: str, metric_name: str = "", metric_value: float = 0.0, metric_unit: str = "", timestamp: float = 0.0, **kwargs):
        super().__init__(source, component, **kwargs)
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.metric_unit = metric_unit
        self.timestamp = timestamp or time.time()
        self.data.update({
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": metric_unit,
            "timestamp": self.timestamp
        })

    def get_summary(self) -> str:
        return f"性能指标 ({self.component}): {self.metric_name} = {self.metric_value} {self.metric_unit}"


# 配置相关事件

@dataclass
class ConfigurationLoadedEvent(ConfigurationEvent):
    """配置加载事件"""
    config_file: str = ""
    config_count: int = 0

    def get_summary(self) -> str:
        return f"配置加载完成: {self.config_file} ({self.config_count}项配置)"


@dataclass
class ConfigurationChangedEvent(ConfigurationEvent):
    """配置变更事件"""
    changed_by: str = "system"

    def get_summary(self) -> str:
        return f"配置变更: {self.config_key} = {self.new_value} (由{self.changed_by}修改)"


# 数据相关事件

@dataclass
class DataExportStartedEvent(DataEvent):
    """数据导出开始事件"""
    export_type: str = ""
    destination: str = ""
    record_count: int = 0

    def get_summary(self) -> str:
        return f"数据导出开始: {self.export_type} → {self.destination} ({self.record_count}条记录)"


@dataclass
class DataExportCompletedEvent(DataEvent):
    """数据导出完成事件"""
    export_type: str = ""
    success: bool = True
    exported_count: int = 0
    error_message: Optional[str] = None

    def get_summary(self) -> str:
        status = "成功" if self.success else "失败"
        return f"数据导出{status}: {self.export_type} ({self.exported_count}条记录)"


@dataclass
class MeasurementExtractedEvent(DataEvent):
    """数值提取事件"""
    source_text: str = ""
    extracted_values: List[float] = None
    extraction_method: str = ""

    def get_summary(self) -> str:
        values_str = ", ".join(map(str, self.extracted_values or []))
        return f"数值提取: '{self.source_text}' → [{values_str}]"


# 用户交互事件

@dataclass
class UserCommandEvent(SystemEvent):
    """用户命令事件"""
    command: str = ""
    parameters: Dict[str, Any] = None

    def get_summary(self) -> str:
        params_str = str(self.parameters) if self.parameters else ""
        return f"用户命令: {self.command} {params_str}"


@dataclass
class VoiceCommandEvent(UserCommandEvent):
    """语音命令事件"""
    command_text: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0

    def __init__(self, source: str, command: str, timestamp: float = 0.0, command_text: str = "", confidence: float = 0.0, **kwargs):
        super().__init__(source, "VoiceCommand", command, **kwargs)
        self.command = command
        self.command_text = command_text or command
        self.confidence = confidence
        self.timestamp = timestamp or time.time()
        self.data.update({
            "command": command,
            "command_text": self.command_text,
            "confidence": confidence,
            "timestamp": self.timestamp
        })

    def get_summary(self) -> str:
        return f"语音命令: '{self.command_text}' (置信度: {self.confidence:.2f})"


@dataclass
class KeyboardPressEvent(UserCommandEvent):
    """键盘按键事件"""
    key: str = ""
    timestamp: float = 0.0

    def __init__(self, source: str, key: str, timestamp: float = 0.0, **kwargs):
        super().__init__(source, "Keyboard", f"key_press_{key}", **kwargs)
        self.key = key
        self.timestamp = timestamp or time.time()
        self.data.update({
            "key": key,
            "timestamp": self.timestamp
        })

    def get_summary(self) -> str:
        return f"键盘按键: '{self.key}'"


# 事件工厂函数

def create_error_event(
    source: str,
    component: str,
    error_type: str,
    error_message: str,
    exception: Optional[Exception] = None,
    **kwargs
) -> ErrorEvent:
    """创建错误事件的便捷函数"""
    # 如果没有指定优先级，默认为HIGH
    if 'priority' not in kwargs:
        kwargs['priority'] = EventPriority.HIGH

    return ErrorEvent(
        source=source,
        component=component,
        error_type=error_type,
        error_message=error_message,
        exception=exception,
        **kwargs
    )


def create_metric_event(
    source: str,
    component: str,
    metric_name: str,
    metric_value: float,
    metric_unit: str = "",
    **kwargs
) -> PerformanceMetricEvent:
    """创建性能指标事件的便捷函数"""
    return PerformanceMetricEvent(
        source=source,
        component=component,
        metric_name=metric_name,
        metric_value=metric_value,
        metric_unit=metric_unit,
        **kwargs
    )