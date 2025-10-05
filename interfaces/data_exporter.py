# -*- coding: utf-8 -*-
"""
数据导出器接口定义

IDataExporter定义了数据导出的抽象接口，主要用于Excel数据导出功能。
支持同步和异步两种模式，提供了灵活的数据写入和格式化选项。
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
import asyncio


class ExportStatus(Enum):
    """导出状态枚举"""
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    PARTIAL = "partial"       # 部分成功
    SKIPPED = "skipped"       # 跳过
    ERROR = "error"          # 错误


class HeaderLanguage(Enum):
    """表头语言枚举"""
    CHINESE = "zh"           # 中文
    ENGLISH = "en"           # 英文


@dataclass
class ExportRecord:
    """导出记录数据类"""
    id: int
    value: float
    original_text: str
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            import datetime
            self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ExportResult:
    """导出结果数据类"""
    status: ExportStatus
    exported_count: int
    total_count: int
    file_path: str
    processing_time: float = 0.0
    error_message: Optional[str] = None
    exported_records: List[ExportRecord] = None

    def __post_init__(self):
        if self.exported_records is None:
            self.exported_records = []

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.exported_count / self.total_count

    def __repr__(self) -> str:
        return f"ExportResult(status={self.status.value}, {self.exported_count}/{self.total_count})"


@dataclass
class ExportConfig:
    """导出配置数据类"""
    file_name: str = "measurement_data.xlsx"
    auto_numbering: bool = True
    include_timestamp: bool = True
    include_original: bool = True
    header_language: HeaderLanguage = HeaderLanguage.CHINESE
    auto_format: bool = True

    # 列宽配置
    column_widths: Dict[str, int] = None

    def __post_init__(self):
        if self.column_widths is None:
            self.column_widths = {
                'A': 10,  # ID列
                'B': 15,  # 测量值列
                'C': 20,  # 时间戳列
                'D': 30   # 原始文本列
            }


class IDataExporter(ABC):
    """
    数据导出器接口

    定义了数据导出的核心功能，包括Excel文件创建、数据写入、
    格式化处理等。支持同步和异步两种调用模式。
    """

    @abstractmethod
    def initialize(self, config: Optional[ExportConfig] = None) -> bool:
        """
        初始化导出器

        Args:
            config: 导出配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False

        Raises:
            FileNotFoundError: 目录不存在
            PermissionError: 文件权限不足
        """
        pass

    @abstractmethod
    async def initialize_async(self, config: Optional[ExportConfig] = None) -> bool:
        """
        异步初始化导出器

        Args:
            config: 导出配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def create_new_file(self, file_path: Optional[str] = None) -> bool:
        """
        创建新的Excel文件

        Args:
            file_path: 文件路径，如果为None则使用配置中的路径

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def create_new_file_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步创建新的Excel文件

        Args:
            file_path: 文件路径，如果为None则使用配置中的路径

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def append_data(
        self,
        data: Union[List[float], List[Tuple[int, float]], List[ExportRecord]],
        auto_generate_ids: bool = True
    ) -> ExportResult:
        """
        追加数据到Excel文件

        Args:
            data: 要导出的数据，支持多种格式
            auto_generate_ids: 是否自动生成ID

        Returns:
            ExportResult: 导出结果

        Raises:
            FileNotFoundError: Excel文件不存在
            PermissionError: 文件被占用
            ValueError: 数据格式错误
        """
        pass

    @abstractmethod
    async def append_data_async(
        self,
        data: Union[List[float], List[Tuple[int, float]], List[ExportRecord]],
        auto_generate_ids: bool = True
    ) -> ExportResult:
        """
        异步追加数据到Excel文件

        Args:
            data: 要导出的数据，支持多种格式
            auto_generate_ids: 是否自动生成ID

        Returns:
            ExportResult: 导出结果
        """
        pass

    @abstractmethod
    def append_with_text(
        self,
        data: List[Tuple[float, str]],  # (数值, 原始文本)
        auto_generate_ids: bool = True
    ) -> List[Tuple[int, float, str]]:
        """
        追加带原始文本的数据

        Args:
            data: 数据列表，格式为[(数值, 原始文本)]
            auto_generate_ids: 是否自动生成ID

        Returns:
            List[Tuple[int, float, str]]: 写入的记录列表，格式为(ID, 数值, 原始文本)
        """
        pass

    @abstractmethod
    async def append_with_text_async(
        self,
        data: List[Tuple[float, str]],  # (数值, 原始文本)
        auto_generate_ids: bool = True
    ) -> List[Tuple[int, float, str]]:
        """
        异步追加带原始文本的数据

        Args:
            data: 数据列表，格式为[(数值, 原始文本)]
            auto_generate_ids: 是否自动生成ID

        Returns:
            List[Tuple[int, float, str]]: 写入的记录列表，格式为(ID, 数值, 原始文本)
        """
        pass

    @abstractmethod
    def get_next_id(self) -> int:
        """
        获取下一个可用的ID

        Returns:
            int: 下一个ID
        """
        pass

    @abstractmethod
    def get_existing_ids(self) -> List[int]:
        """
        获取已存在的ID列表

        Returns:
            List[int]: 已存在的ID列表
        """
        pass

    @abstractmethod
    def get_session_data(self) -> List[Tuple[int, float, str]]:
        """
        获取本次会话的所有数据

        Returns:
            List[Tuple[int, float, str]]: 会话数据列表
        """
        pass

    @abstractmethod
    def clear_session_data(self) -> None:
        """清空会话数据"""
        pass

    @abstractmethod
    def format_excel(self, file_path: Optional[str] = None) -> bool:
        """
        格式化Excel文件

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 格式化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def format_excel_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步格式化Excel文件

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 格式化成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: Optional[str] = None) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 文件存在返回True，否则返回False
        """
        pass

    @abstractmethod
    def get_file_info(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            Dict[str, Any]: 文件信息字典
        """
        pass

    @abstractmethod
    def backup_file(self, file_path: Optional[str] = None) -> bool:
        """
        备份当前文件

        Args:
            file_path: 要备份的文件路径，如果为None则备份当前文件

        Returns:
            bool: 备份成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def set_config(self, config: ExportConfig) -> None:
        """
        设置导出配置

        Args:
            config: 导出配置
        """
        pass

    @abstractmethod
    def get_config(self) -> ExportConfig:
        """
        获取当前导出配置

        Returns:
            ExportConfig: 当前配置
        """
        pass

    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """
        验证数据格式

        Args:
            data: 要验证的数据

        Returns:
            bool: 数据格式正确返回True，否则返回False
        """
        pass

    # 统计和分析方法
    @abstractmethod
    def get_export_statistics(self) -> Dict[str, Any]:
        """
        获取导出统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        pass

    @abstractmethod
    def get_data_summary(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取数据摘要信息

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            Dict[str, Any]: 数据摘要字典
        """
        pass

    # 批量操作方法
    @abstractmethod
    def batch_export(
        self,
        data_batches: List[Union[List[float], List[Tuple[int, float]], List[ExportRecord]]]
    ) -> List[ExportResult]:
        """
        批量导出数据

        Args:
            data_batches: 数据批次列表

        Returns:
            List[ExportResult]: 每个批次的导出结果列表
        """
        pass

    @abstractmethod
    async def batch_export_async(
        self,
        data_batches: List[Union[List[float], List[Tuple[int, float]], List[ExportRecord]]]
    ) -> List[ExportResult]:
        """
        异步批量导出数据

        Args:
            data_batches: 数据批次列表

        Returns:
            List[ExportResult]: 每个批次的导出结果列表
        """
        pass

    # 资源管理
    @abstractmethod
    def close(self) -> None:
        """
        关闭导出器，释放资源
        """
        pass

    @abstractmethod
    async def close_async(self) -> None:
        """
        异步关闭导出器，释放资源
        """
        pass