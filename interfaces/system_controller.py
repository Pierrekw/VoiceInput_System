# -*- coding: utf-8 -*-
"""
系统控制器接口定义

ISystemController定义了系统控制的抽象接口，负责协调各个组件、
管理生命周期、处理事件等。提供同步和异步两种调用模式。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
import asyncio

from .audio_processor import IAudioProcessor, AudioProcessorState
from .data_exporter import IDataExporter
from .tts_provider import ITTSProvider
from .config_provider import IConfigProvider


class SystemState(Enum):
    """系统状态枚举"""
    UNINITIALIZED = "uninitialized"   # 未初始化
    INITIALIZING = "initializing"     # 初始化中
    READY = "ready"                  # 就绪
    STARTING = "starting"            # 启动中
    RUNNING = "running"              # 运行中
    PAUSING = "pausing"              # 暂停中
    PAUSED = "paused"                # 已暂停
    STOPPING = "stopping"            # 停止中
    STOPPED = "stopped"              # 已停止
    ERROR = "error"                  # 错误状态
    SHUTTING_DOWN = "shutting_down"  # 关闭中
    SHUTDOWN = "shutdown"            # 已关闭


class EventType(Enum):
    """事件类型枚举"""
    SYSTEM_STATE_CHANGED = "system_state_changed"
    AUDIO_PROCESSOR_CHANGED = "audio_processor_changed"
    DATA_EXPORTER_CHANGED = "data_exporter_changed"
    TTS_PROVIDER_CHANGED = "tts_provider_changed"
    CONFIG_CHANGED = "config_changed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"
    INFO_OCCURRED = "info_occurred"


@dataclass
class SystemEvent:
    """系统事件数据类"""
    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
    message: str = ""

    def __repr__(self) -> str:
        return f"SystemEvent(type={self.event_type.value}, source='{self.source}')"


@dataclass
class SystemInfo:
    """系统信息数据类"""
    state: SystemState
    version: str
    uptime: float
    audio_processor_state: Optional[AudioProcessorState] = None
    components_status: Dict[str, bool] = None
    last_error: Optional[str] = None
    performance_metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.components_status is None:
            self.components_status = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}

    def __repr__(self) -> str:
        return f"SystemInfo(state={self.state.value}, uptime={self.uptime:.1f}s)"


@dataclass
class ComponentConfig:
    """组件配置数据类"""
    audio_processor: Optional[Dict[str, Any]] = None
    data_exporter: Optional[Dict[str, Any]] = None
    tts_provider: Optional[Dict[str, Any]] = None
    config_provider: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # 确保所有配置字典都不为None
        if self.audio_processor is None:
            self.audio_processor = {}
        if self.data_exporter is None:
            self.data_exporter = {}
        if self.tts_provider is None:
            self.tts_provider = {}
        if self.config_provider is None:
            self.config_provider = {}


class ISystemController(ABC):
    """
    系统控制器接口

    定义了系统控制的核心功能，包括组件管理、生命周期控制、
    事件处理、状态管理等。提供同步和异步两种调用模式。
    """

    @abstractmethod
    def initialize(self, config: Optional[ComponentConfig] = None) -> bool:
        """
        初始化系统控制器

        Args:
            config: 组件配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False

        Raises:
            RuntimeError: 系统已经初始化或初始化失败
        """
        pass

    @abstractmethod
    async def initialize_async(self, config: Optional[ComponentConfig] = None) -> bool:
        """
        异步初始化系统控制器

        Args:
            config: 组件配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查系统是否已初始化

        Returns:
            bool: 已初始化返回True，否则返回False
        """
        pass

    @abstractmethod
    def get_state(self) -> SystemState:
        """
        获取当前系统状态

        Returns:
            SystemState: 当前状态
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """
        启动系统

        Returns:
            bool: 启动成功返回True，失败返回False

        Raises:
            RuntimeError: 系统未初始化或状态不正确
        """
        pass

    @abstractmethod
    async def start_async(self) -> bool:
        """
        异步启动系统

        Returns:
            bool: 启动成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        停止系统

        Returns:
            bool: 停止成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def stop_async(self) -> bool:
        """
        异步停止系统

        Returns:
            bool: 停止成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def pause(self) -> bool:
        """
        暂停系统

        Returns:
            bool: 暂停成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def resume(self) -> bool:
        """
        恢复系统

        Returns:
            bool: 恢复成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        关闭系统

        Returns:
            bool: 关闭成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def shutdown_async(self) -> bool:
        """
        异步关闭系统

        Returns:
            bool: 关闭成功返回True，失败返回False
        """
        pass

    # 组件管理
    @abstractmethod
    def set_audio_processor(self, processor: IAudioProcessor) -> None:
        """
        设置音频处理器

        Args:
            processor: 音频处理器实例
        """
        pass

    @abstractmethod
    def get_audio_processor(self) -> Optional[IAudioProcessor]:
        """
        获取音频处理器

        Returns:
            Optional[IAudioProcessor]: 音频处理器实例，如果未设置则返回None
        """
        pass

    @abstractmethod
    def set_data_exporter(self, exporter: IDataExporter) -> None:
        """
        设置数据导出器

        Args:
            exporter: 数据导出器实例
        """
        pass

    @abstractmethod
    def get_data_exporter(self) -> Optional[IDataExporter]:
        """
        获取数据导出器

        Returns:
            Optional[IDataExporter]: 数据导出器实例，如果未设置则返回None
        """
        pass

    @abstractmethod
    def set_tts_provider(self, provider: ITTSProvider) -> None:
        """
        设置TTS语音服务

        Args:
            provider: TTS服务实例
        """
        pass

    @abstractmethod
    def get_tts_provider(self) -> Optional[ITTSProvider]:
        """
        获取TTS语音服务

        Returns:
            Optional[ITTSProvider]: TTS服务实例，如果未设置则返回None
        """
        pass

    @abstractmethod
    def set_config_provider(self, provider: IConfigProvider) -> None:
        """
        设置配置提供者

        Args:
            provider: 配置提供者实例
        """
        pass

    @abstractmethod
    def get_config_provider(self) -> Optional[IConfigProvider]:
        """
        获取配置提供者

        Returns:
            Optional[IConfigProvider]: 配置提供者实例，如果未设置则返回None
        """
        pass

    # 事件管理
    @abstractmethod
    def subscribe(self, event_type: EventType, callback: Callable[[SystemEvent], None]) -> str:
        """
        订阅系统事件

        Args:
            event_type: 事件类型
            callback: 事件回调函数

        Returns:
            str: 订阅ID
        """
        pass

    @abstractmethod
    async def subscribe_async(self, event_type: EventType, callback: Callable[[SystemEvent], None]) -> str:
        """
        异步订阅系统事件

        Args:
            event_type: 事件类型
            callback: 事件回调函数

        Returns:
            str: 订阅ID
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅事件

        Args:
            subscription_id: 订阅ID

        Returns:
            bool: 取消成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def publish_event(self, event: SystemEvent) -> None:
        """
        发布系统事件

        Args:
            event: 系统事件
        """
        pass

    @abstractmethod
    async def publish_event_async(self, event: SystemEvent) -> None:
        """
        异步发布系统事件

        Args:
            event: 系统事件
        """
        pass

    # 系统信息和统计
    @abstractmethod
    def get_system_info(self) -> SystemInfo:
        """
        获取系统信息

        Returns:
            SystemInfo: 系统信息
        """
        pass

    @abstractmethod
    async def get_system_info_async(self) -> SystemInfo:
        """
        异步获取系统信息

        Returns:
            SystemInfo: 系统信息
        """
        pass

    @abstractmethod
    def get_component_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有组件状态

        Returns:
            Dict[str, Dict[str, Any]]: 组件状态字典
        """
        pass

    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        获取性能指标

        Returns:
            Dict[str, float]: 性能指标字典
        """
        pass

    @abstractmethod
    def get_error_history(self, limit: int = 100) -> List[SystemEvent]:
        """
        获取错误历史

        Args:
            limit: 返回的错误数量限制

        Returns:
            List[SystemEvent]: 错误事件列表
        """
        pass

    # 配置管理
    @abstractmethod
    def update_component_config(self, component: str, config: Dict[str, Any]) -> bool:
        """
        更新组件配置

        Args:
            component: 组件名称
            config: 配置字典

        Returns:
            bool: 更新成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """
        获取组件配置

        Args:
            component: 组件名称

        Returns:
            Dict[str, Any]: 配置字典
        """
        pass

    # 健康检查和诊断
    @abstractmethod
    def health_check(self) -> Dict[str, bool]:
        """
        系统健康检查

        Returns:
            Dict[str, bool]: 健康状态字典
        """
        pass

    @abstractmethod
    async def health_check_async(self) -> Dict[str, bool]:
        """
        异步系统健康检查

        Returns:
            Dict[str, bool]: 健康状态字典
        """
        pass

    @abstractmethod
    def run_diagnostics(self) -> Dict[str, Any]:
        """
        运行系统诊断

        Returns:
            Dict[str, Any]: 诊断结果字典
        """
        pass

    @abstractmethod
    async def run_diagnostics_async(self) -> Dict[str, Any]:
        """
        异步运行系统诊断

        Returns:
            Dict[str, Any]: 诊断结果字典
        """
        pass

    # 任务管理
    @abstractmethod
    def schedule_task(self, task: Callable, delay: float = 0.0) -> str:
        """
        调度任务

        Args:
            task: 要执行的任务函数
            delay: 延迟执行时间（秒）

        Returns:
            str: 任务ID
        """
        pass

    @abstractmethod
    async def schedule_task_async(self, task: Callable, delay: float = 0.0) -> str:
        """
        异步调度任务

        Args:
            task: 要执行的任务函数
            delay: 延迟执行时间（秒）

        Returns:
            str: 任务ID
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 取消成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def get_active_tasks(self) -> List[str]:
        """
        获取活跃任务列表

        Returns:
            List[str]: 任务ID列表
        """
        pass

    # 日志和监控
    @abstractmethod
    def set_log_level(self, level: str) -> None:
        """
        设置日志级别

        Args:
            level: 日志级别
        """
        pass

    @abstractmethod
    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> List[str]:
        """
        获取系统日志

        Args:
            level: 日志级别过滤
            limit: 返回的日志数量限制

        Returns:
            List[str]: 日志条目列表
        """
        pass

    @abstractmethod
    def export_logs(self, file_path: str, format: str = "txt") -> bool:
        """
        导出系统日志

        Args:
            file_path: 导出文件路径
            format: 导出格式

        Returns:
            bool: 导出成功返回True，失败返回False
        """
        pass

    # 系统控制
    @abstractmethod
    def restart_component(self, component: str) -> bool:
        """
        重启组件

        Args:
            component: 组件名称

        Returns:
            bool: 重启成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def restart_component_async(self, component: str) -> bool:
        """
        异步重启组件

        Args:
            component: 组件名称

        Returns:
            bool: 重启成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def reload_configuration(self) -> bool:
        """
        重新加载配置

        Returns:
            bool: 重载成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def reload_configuration_async(self) -> bool:
        """
        异步重新加载配置

        Returns:
            bool: 重载成功返回True，失败返回False
        """
        pass

    # 资源管理
    @abstractmethod
    def cleanup(self) -> None:
        """
        清理系统资源
        """
        pass

    @abstractmethod
    async def cleanup_async(self) -> None:
        """
        异步清理系统资源
        """
        pass

    @abstractmethod
    def force_cleanup(self) -> None:
        """
        强制清理系统资源（紧急情况使用）
        """
        pass