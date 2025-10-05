# -*- coding: utf-8 -*-
"""
基础事件定义

定义事件驱动系统的基础事件类和枚举类型。
"""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, List


class EventPriority(Enum):
    """事件优先级枚举"""
    CRITICAL = 1    # 系统关键事件 (错误、系统启动/停止)
    HIGH = 2        # 高优先级事件 (用户操作、重要状态变更)
    NORMAL = 3      # 普通事件 (常规数据流、周期性事件)
    LOW = 4         # 低优先级事件 (日志、统计信息)


@dataclass
class EventMetadata:
    """事件元数据"""
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)

    def set_property(self, key: str, value: Any) -> None:
        """设置属性"""
        self.properties[key] = value


class BaseEvent(ABC):
    """基础事件抽象类"""

    def __init__(
        self,
        source: str,
        event_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[EventMetadata] = None
    ):
        """
        初始化基础事件

        Args:
            source: 事件源
            event_type: 事件类型
            data: 事件数据
            priority: 事件优先级
            metadata: 事件元数据
        """
        self.event_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.source = source
        self.event_type = event_type or self.__class__.__name__
        self.data = data or {}
        self.priority = priority
        self.metadata = metadata or EventMetadata()

    @abstractmethod
    def get_summary(self) -> str:
        """获取事件摘要"""
        pass

    def is_high_priority(self) -> bool:
        """检查是否为高优先级事件"""
        return self.priority in [EventPriority.CRITICAL, EventPriority.HIGH]

    def get_age(self) -> float:
        """获取事件年龄（秒）"""
        return time.time() - self.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "event_type": self.event_type,
            "data": self.data,
            "priority": self.priority.name,
            "metadata": {
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "tags": self.metadata.tags,
                "properties": self.metadata.properties
            }
        }

    def __str__(self) -> str:
        return f"{self.event_type}(id={self.event_id[:8]}, source={self.source}, priority={self.priority.name})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.__str__()}>"


class AudioEvent(BaseEvent):
    """音频事件基类"""

    def __init__(
        self,
        source: str,
        stream_id: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.stream_id = stream_id
        self.data["stream_id"] = stream_id


class SystemEvent(BaseEvent):
    """系统事件基类"""

    def __init__(
        self,
        source: str,
        component: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.component = component
        self.data["component"] = component


class RecognitionEvent(BaseEvent):
    """语音识别事件基类"""

    def __init__(
        self,
        source: str,
        recognizer_id: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.recognizer_id = recognizer_id
        self.data["recognizer_id"] = recognizer_id


class TTSEvent(BaseEvent):
    """TTS事件基类"""

    def __init__(
        self,
        source: str,
        player_id: str,
        text: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.player_id = player_id
        self.text = text
        self.data.update({
            "player_id": player_id,
            "text": text
        })


class ConfigurationEvent(BaseEvent):
    """配置事件基类"""

    def __init__(
        self,
        source: str,
        config_key: str,
        old_value: Any = None,
        new_value: Any = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.config_key = config_key
        self.old_value = old_value
        self.new_value = new_value
        self.data.update({
            "config_key": config_key,
            "old_value": old_value,
            "new_value": new_value
        })


class DataEvent(BaseEvent):
    """数据事件基类"""

    def __init__(
        self,
        source: str,
        data_type: str,
        data_content: Any,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(source, data=data, **kwargs)
        self.data_type = data_type
        self.data_content = data_content
        self.data.update({
            "data_type": data_type,
            "data_content": data_content
        })


# 事件创建便捷函数

def create_audio_event(
    event_class: type,
    source: str,
    stream_id: str,
    **kwargs
) -> AudioEvent:
    """创建音频事件的便捷函数"""
    return event_class(source=source, stream_id=stream_id, **kwargs)


def create_system_event(
    event_class: type,
    source: str,
    component: str,
    **kwargs
) -> SystemEvent:
    """创建系统事件的便捷函数"""
    return event_class(source=source, component=component, **kwargs)


def create_recognition_event(
    event_class: type,
    source: str,
    recognizer_id: str,
    **kwargs
) -> RecognitionEvent:
    """创建语音识别事件的便捷函数"""
    return event_class(source=source, recognizer_id=recognizer_id, **kwargs)


def create_tts_event(
    event_class: type,
    source: str,
    player_id: str,
    text: str,
    **kwargs
) -> TTSEvent:
    """创建TTS事件的便捷函数"""
    return event_class(source=source, player_id=player_id, text=text, **kwargs)