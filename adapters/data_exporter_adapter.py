# -*- coding: utf-8 -*-
"""
数据导出器适配器

将现有的ExcelExporter类适配为IDataExporter接口，确保向后兼容性。
采用适配器模式包装现有实现，不修改原有代码。
"""

import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional, Union
import time

from interfaces.data_exporter import (
    IDataExporter, ExportStatus, ExportRecord, ExportResult, ExportConfig, HeaderLanguage
)

# 导入现有的ExcelExporter类
try:
    from excel_exporter import ExcelExporter
except ImportError:
    # 如果导入失败，创建一个占位符
    class ExcelExporter:
        def __init__(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)


class DataExporterAdapter(IDataExporter):
    """
    数据导出器适配器

    将现有的ExcelExporter类适配为IDataExporter接口。
    保持原有功能的同时提供新的接口支持。
    """

    def __init__(self, excel_exporter: Optional[ExcelExporter] = None, **kwargs):
        """
        初始化数据导出器适配器

        Args:
            excel_exporter: 现有的ExcelExporter实例，如果为None则创建新实例
            **kwargs: 传递给ExcelExporter构造函数的参数
        """
        if excel_exporter is None:
            # 创建新的ExcelExporter实例
            self._excel_exporter = ExcelExporter(**kwargs)
        else:
            self._excel_exporter = excel_exporter

        # 配置对象
        self._config = ExportConfig()

        logger.info("DataExporterAdapter initialized with ExcelExporter")

    # 初始化方法
    def initialize(self, config: Optional[ExportConfig] = None) -> bool:
        """
        初始化导出器

        Args:
            config: 导出配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        if config:
            self._config = config
            # 将配置应用到ExcelExporter
            self._apply_config_to_excel_exporter()

        try:
            # 尝试访问文件以验证权限
            import os
            if not os.path.exists(self._config.file_name):
                self._excel_exporter.create_new_file()

            logger.info("DataExporterAdapter initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DataExporterAdapter: {e}")
            return False

    async def initialize_async(self, config: Optional[ExportConfig] = None) -> bool:
        """
        异步初始化导出器

        Args:
            config: 导出配置，如果为None则使用默认配置

        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.initialize, config)

    def _apply_config_to_excel_exporter(self) -> None:
        """将配置应用到ExcelExporter实例"""
        try:
            # ExcelExporter的大多数配置是通过构造函数设置的
            # 这里主要是为了保持一致性，实际配置在构造时已经应用
            logger.debug("Applied config to ExcelExporter")
        except Exception as e:
            logger.error(f"Failed to apply config: {e}")

    def is_initialized(self) -> bool:
        """检查导出器是否已初始化"""
        return self._excel_exporter is not None

    # 文件创建方法
    def create_new_file(self, file_path: Optional[str] = None) -> bool:
        """
        创建新的Excel文件

        Args:
            file_path: 文件路径，如果为None则使用配置中的路径

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            if file_path:
                # 临时设置文件路径
                original_filename = self._excel_exporter.filename
                self._excel_exporter.filename = file_path
                result = self._excel_exporter.create_new_file()
                self._excel_exporter.filename = original_filename
            else:
                result = self._excel_exporter.create_new_file()

            logger.info(f"Excel file created: {file_path or self._config.file_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to create Excel file: {e}")
            return False

    async def create_new_file_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步创建新的Excel文件

        Args:
            file_path: 文件路径，如果为None则使用配置中的路径

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_new_file, file_path)

    # 数据导出方法
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
        """
        start_time = time.time()
        exported_count = 0
        total_count = 0
        exported_records = []

        try:
            if not data:
                return ExportResult(
                    status=ExportStatus.SKIPPED,
                    exported_count=0,
                    total_count=0,
                    file_path=self._excel_exporter.filename,
                    processing_time=time.time() - start_time
                )

            total_count = len(data)

            # 转换数据格式
            if isinstance(data, list) and data:
                if isinstance(data[0], ExportRecord):
                    # ExportRecord格式
                    converted_data = [(record.id, record.value) for record in data]
                    session_data = [(record.id, record.value, record.original_text) for record in data]
                elif isinstance(data[0], (list, tuple)) and len(data[0]) == 2:
                    # (ID, 数值) 格式
                    converted_data = data
                    session_data = [(item[0], item[1], "") for item in data]
                else:
                    # 纯数值格式
                    converted_data = [(i + 1, value) for i, value in enumerate(data)]
                    session_data = [(i + 1, value, "") for i, value in enumerate(data)]
            else:
                converted_data = []
                session_data = []

            # 使用ExcelExporter的append方法
            if auto_generate_ids and isinstance(data, list) and data and isinstance(data[0], (int, float)):
                # 纯数值，自动生成ID
                success = self._excel_exporter.append(data, auto_generate_ids=True)
                if success:
                    exported_count = len(data)
                    # 获取会话数据
                    session_data = self._excel_exporter.get_session_data()
                    exported_records = [
                        ExportRecord(id=record[0], value=record[1], original_text=record[2])
                        for record in session_data[-len(data):]
                    ]
            else:
                # 使用现有的数据格式
                success = self._excel_exporter.append(converted_data, auto_generate_ids=False)
                if success:
                    exported_count = len(converted_data)
                    exported_records = [
                        ExportRecord(id=record[0], value=record[1], original_text=record[2])
                        for record in session_data
                    ]

            processing_time = time.time() - start_time
            status = ExportStatus.SUCCESS if success else ExportStatus.FAILED

            result = ExportResult(
                status=status,
                exported_count=exported_count,
                total_count=total_count,
                file_path=self._excel_exporter.filename,
                processing_time=processing_time,
                exported_records=exported_records
            )

            logger.info(f"Data export completed: {exported_count}/{total_count} records")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to export data: {e}")
            return ExportResult(
                status=ExportStatus.FAILED,
                exported_count=exported_count,
                total_count=total_count,
                file_path=self._excel_exporter.filename,
                processing_time=processing_time,
                error_message=str(e)
            )

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.append_data, data, auto_generate_ids)

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
        try:
            result = self._excel_exporter.append_with_text(data, auto_generate_ids)
            logger.info(f"Appended {len(result)} records with text")
            return result
        except Exception as e:
            logger.error(f"Failed to append data with text: {e}")
            return []

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.append_with_text, data, auto_generate_ids)

    # ID和会话数据管理
    def get_next_id(self) -> int:
        """获取下一个可用的ID"""
        try:
            return self._excel_exporter.get_next_id()
        except Exception as e:
            logger.error(f"Failed to get next ID: {e}")
            return 0

    def get_existing_ids(self) -> List[int]:
        """获取已存在的ID列表"""
        try:
            return self._excel_exporter.get_existing_ids()
        except Exception as e:
            logger.error(f"Failed to get existing IDs: {e}")
            return []

    def get_session_data(self) -> List[Tuple[int, float, str]]:
        """获取本次会话的所有数据"""
        try:
            return self._excel_exporter.get_session_data()
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return []

    def clear_session_data(self) -> None:
        """清空会话数据"""
        try:
            self._excel_exporter.clear_session_data()
            logger.info("Session data cleared")
        except Exception as e:
            logger.error(f"Failed to clear session data: {e}")

    # 文件格式化方法
    def format_excel(self, file_path: Optional[str] = None) -> bool:
        """
        格式化Excel文件

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 格式化成功返回True，失败返回False
        """
        try:
            if file_path and file_path != self._excel_exporter.filename:
                # 如果指定了不同的文件路径，需要重新创建格式化器
                # 这里简化处理，只格式化当前文件
                logger.warning("File path different from current, formatting current file")

            self._excel_exporter.format_excel()
            logger.info("Excel file formatted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to format Excel: {e}")
            return False

    async def format_excel_async(self, file_path: Optional[str] = None) -> bool:
        """
        异步格式化Excel文件

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 格式化成功返回True，失败返回False
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.format_excel, file_path)

    # 文件管理方法
    def file_exists(self, file_path: Optional[str] = None) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            bool: 文件存在返回True，否则返回False
        """
        import os
        target_path = file_path or self._excel_exporter.filename
        return os.path.exists(target_path)

    def get_file_info(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            Dict[str, Any]: 文件信息字典
        """
        import os
        from datetime import datetime

        target_path = file_path or self._excel_exporter.filename

        try:
            if os.path.exists(target_path):
                stat = os.stat(target_path)
                return {
                    "path": target_path,
                    "exists": True,
                    "size": stat.st_size,
                    "created_time": datetime.fromtimestamp(stat.st_ctime),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime),
                    "is_readable": os.access(target_path, os.R_OK),
                    "is_writable": os.access(target_path, os.W_OK)
                }
            else:
                return {
                    "path": target_path,
                    "exists": False
                }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {"path": target_path, "exists": False, "error": str(e)}

    def backup_file(self, file_path: Optional[str] = None) -> bool:
        """
        备份当前文件

        Args:
            file_path: 要备份的文件路径，如果为None则备份当前文件

        Returns:
            bool: 备份成功返回True，失败返回False
        """
        import shutil
        import os
        from datetime import datetime

        target_path = file_path or self._excel_exporter.filename

        try:
            if os.path.exists(target_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{target_path}.backup_{timestamp}"
                shutil.copy2(target_path, backup_path)
                logger.info(f"File backed up to: {backup_path}")
                return True
            else:
                logger.warning("Source file does not exist, cannot backup")
                return False
        except Exception as e:
            logger.error(f"Failed to backup file: {e}")
            return False

    # 配置管理
    def set_config(self, config: ExportConfig) -> None:
        """
        设置导出配置

        Args:
            config: 导出配置
        """
        self._config = config
        # 注意：大多数配置只能在创建时设置，这里主要用于一致性
        logger.info("Export config updated")

    def get_config(self) -> ExportConfig:
        """
        获取当前导出配置

        Returns:
            ExportConfig: 当前配置
        """
        return self._config

    def validate_data(self, data: Any) -> bool:
        """
        验证数据格式

        Args:
            data: 要验证的数据

        Returns:
            bool: 数据格式正确返回True，否则返回False
        """
        try:
            if not isinstance(data, (list, tuple)):
                return False

            if not data:
                return True  # 空数据是有效的

            # 检查数据元素格式
            if isinstance(data[0], ExportRecord):
                # ExportRecord列表
                return all(isinstance(item, ExportRecord) for item in data)
            elif isinstance(data[0], (list, tuple)):
                # 元组列表
                if len(data[0]) == 2:
                    # (ID, 数值) 或 (数值, 文本)
                    return all(
                        isinstance(item, (list, tuple)) and len(item) == 2
                        for item in data
                    )
                else:
                    return False
            elif isinstance(data[0], (int, float)):
                # 纯数值列表
                return all(isinstance(item, (int, float)) for item in data)
            else:
                return False

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False

    # 统计和分析方法
    def get_export_statistics(self) -> Dict[str, Any]:
        """
        获取导出统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            session_data = self.get_session_data()
            file_info = self.get_file_info()

            return {
                "session_records_count": len(session_data),
                "file_exists": file_info.get("exists", False),
                "file_size": file_info.get("size", 0),
                "current_config": {
                    "file_name": self._config.file_name,
                    "auto_numbering": self._config.auto_numbering,
                    "include_timestamp": self._config.include_timestamp,
                    "include_original": self._config.include_original,
                    "header_language": self._config.header_language.value
                }
            }
        except Exception as e:
            logger.error(f"Failed to get export statistics: {e}")
            return {"error": str(e)}

    def get_data_summary(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取数据摘要信息

        Args:
            file_path: 文件路径，如果为None则使用当前文件

        Returns:
            Dict[str, Any]: 数据摘要字典
        """
        try:
            # 这里可以添加读取Excel文件并分析数据的逻辑
            # 为了简化，返回基本信息
            file_info = self.get_file_info(file_path)
            session_data = self.get_session_data()

            if session_data:
                values = [record[1] for record in session_data if isinstance(record[1], (int, float))]
                return {
                    "total_records": len(session_data),
                    "numeric_values_count": len(values),
                    "min_value": min(values) if values else None,
                    "max_value": max(values) if values else None,
                    "avg_value": sum(values) / len(values) if values else None,
                    "file_info": file_info
                }
            else:
                return {
                    "total_records": 0,
                    "file_info": file_info
                }
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {"error": str(e)}

    # 批量操作方法
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
        results = []
        for i, batch in enumerate(data_batches):
            try:
                result = self.append_data(batch)
                results.append(result)
                logger.info(f"Batch {i+1}/{len(data_batches)} exported: {result.exported_count} records")
            except Exception as e:
                logger.error(f"Batch {i+1} failed: {e}")
                results.append(ExportResult(
                    status=ExportStatus.FAILED,
                    exported_count=0,
                    total_count=len(batch) if batch else 0,
                    file_path=self._excel_exporter.filename,
                    error_message=str(e)
                ))

        return results

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.batch_export, data_batches)

    # 资源管理
    def close(self) -> None:
        """关闭导出器，释放资源"""
        try:
            # ExcelExporter没有显式的close方法，这里主要用于清理适配器资源
            logger.info("DataExporterAdapter closed")
        except Exception as e:
            logger.error(f"Failed to close adapter: {e}")

    async def close_async(self) -> None:
        """异步关闭导出器，释放资源"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.close)

    # 属性访问器
    @property
    def wrapped_instance(self) -> ExcelExporter:
        """获取包装的ExcelExporter实例"""
        return self._excel_exporter

    def __getattr__(self, name: str) -> Any:
        """代理未定义的属性到原ExcelExporter实例"""
        return getattr(self._excel_exporter, name)

    def __repr__(self) -> str:
        return f"DataExporterAdapter(file='{self._excel_exporter.filename}', initialized={self.is_initialized()})"