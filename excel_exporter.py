# -*- coding: utf-8 -*-
# Excel Exporter Module - Optimized Version
from __future__ import annotations
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, Alignment
import threading
import logging
from typing import Any, List, Tuple, Union, Optional

# 新增：导入配置系统
from config_loader import config

logger = logging.getLogger(__name__)

class ExcelExporter:
    def __init__(self, filename: str = None):
        self._lock: threading.Lock = threading.Lock()
        # 使用配置文件中的文件名，如果未指定则使用默认值
        if filename is None:
            filename = config.get("excel.file_name", "measurement_data.xlsx")
        self.filename: str = filename
        # 使用配置系统获取是否包含原始语音的设置
        include_original = config.get("excel.formatting.include_original", True)
        
        # 根据header_language配置设置列名
        header_language = config.get("excel.formatting.header_language", "zh")
        if header_language == "en":
            self.columns: List[str] = ["ID", "Measurement", "Timestamp"]
        else:
            self.columns: List[str] = ["编号", "测量值", "时间戳"]
            
        # 根据配置决定是否添加原始语音列
        if include_original:
            if header_language == "en":
                self.columns.append("Original Text")
            else:
                self.columns.append("原始语音")
                
        self._last_id: int = 0
        self._initialize_last_id()
        # 新增：记录本次会话的所有数据
        self._session_data: List[Tuple[int, float, str]] = []

    @staticmethod
    def _float_cell(val: Any) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def _int_cell(val: Any) -> int:
        try:
            return int(ExcelExporter._float_cell(val))   # 先转 float 再 int，容忍 3.0
        except (ValueError, TypeError):
            return 0
       
    
    def _initialize_last_id(self) -> None:
        if os.path.exists(self.filename):
            try:
                workbook = load_workbook(self.filename, read_only=True)
                worksheet = workbook.active
                if worksheet is None:         
                    return                    
                max_row = worksheet.max_row
                if max_row > 1:
                    id_values: List[int] = []
                    for row in range(2, max_row + 1):
                        cell_value = worksheet.cell(row=row, column=1).value
                        if cell_value is not None:
                            try:
                                id_values.append(self._int_cell(cell_value))
                            except (ValueError, TypeError):
                                continue
                    self._last_id = max(id_values) if id_values else 0
                else:
                    self._last_id = 0
                workbook.close()
            except Exception as e:
                logger.error(f"使用openpyxl读取Excel文件时出错: {e}")
                try:
                    df = pd.read_excel(self.filename)
                    if not df.empty and "编号" in df.columns:
                        self._last_id = self._int_cell(df["编号"].max())
                    else:
                        self._last_id = 0
                except Exception as fallback_error:
                    logger.error(f"回退到pandas也失败: {fallback_error}")
                    self._last_id = 0

    def get_next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def create_new_file(self) -> None:
        df = pd.DataFrame(columns=self.columns)
        df.to_excel(self.filename, index=False)
        self.format_excel()  # ✅ 仅在此处格式化
        logger.info(f"创建并格式化新Excel文件: {self.filename}")

    def append_with_text(
            self,
            data: List[Tuple[float, str]],  # (数值, 原始语音文本)
            auto_generate_ids: bool = True
        ) -> List[Tuple[int, float, str]]:  # 返回 [(ID, 数值, 原始文本)]
            """
            新增方法：写入带原始语音文本的数据
            返回本次写入的所有记录（包含生成的ID）
            """
            if not data:
                logger.warning("没有数据可写入")
                return []
    
            with self._lock:
                try:
                    if not os.path.exists(self.filename):
                        self.create_new_file()
    
                    existing_data = pd.read_excel(self.filename)
                    
                    # 获取配置设置
                    include_original = config.get("excel.formatting.include_original", True)
                    auto_numbering = config.get("excel.formatting.auto_numbering", True)
                    include_timestamp = config.get("excel.formatting.include_timestamp", True)
                    
                    # 生成新记录
                    new_records = []
                    for val, original_text in data:
                        new_record = {}
                        
                        # 根据配置决定是否添加编号
                        if auto_numbering:
                            new_id = self.get_next_id()
                            new_record["编号"] = new_id
                            
                        # 添加测量值
                        new_record["测量值"] = self._float_cell(val)
                        
                        # 根据配置决定是否添加时间戳
                        if include_timestamp:
                            new_record["时间戳"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 根据配置决定是否添加原始语音字段
                        if include_original:
                            new_record["原始语音"] = original_text
                        
                        new_records.append(new_record)
                        
                        # 如果启用了自动编号，记录到会话数据
                        if auto_numbering:
                            self._session_data.append((new_id, self._float_cell(val), original_text))
                        else:
                            # 对于没有ID的情况，使用-1作为占位符
                            self._session_data.append((-1, self._float_cell(val), original_text))
    
                    # 合并数据
                    if existing_data.empty:
                        updated_data = pd.DataFrame(new_records)
                    else:
                        updated_data = pd.concat([existing_data, pd.DataFrame(new_records)], ignore_index=True)
    
                    updated_data.to_excel(self.filename, index=False)
                    
                    # 返回写入的记录列表
                    result = []
                    for _, r in pd.DataFrame(new_records).iterrows():
                        # 根据是否启用了自动编号来处理返回数据
                        if auto_numbering:
                            result.append((r["编号"], r["测量值"], r.get("原始语音", "")))
                        else:
                            # 对于没有ID的情况，使用-1作为占位符
                            result.append((-1, r["测量值"], r.get("原始语音", "")))
                    
                    logger.debug(f"成功写入 {len(result)} 条数据到 {self.filename}")
                    return result
    
                except Exception as e:
                    logger.error(f"写入Excel失败: {e}")
                    return []

    def append(
        self,
        data: Union[List[float], List[Tuple[int, float]]],
        auto_generate_ids: bool = True
    ) -> bool:
        if not data:
            logger.warning("没有数据可写入")
            return False

        if isinstance(data[0], (int, float)) and auto_generate_ids:
            start_id = self._last_id + 1 if self._last_id > 0 else 1
            data_pairs: List[Tuple[int, float]] = [(start_id + i, self._float_cell(v)) for i, v in enumerate(data)]
        elif isinstance(data[0], (list, tuple)) and len(data[0]) == 2:
            data_pairs = []
            for item in data:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    data_pairs.append((
                        self._int_cell(item[0]),
                        self._float_cell(item[1])
                    ))
        else:
            logger.error(f"无效的数据格式: {type(data[0])}，期望数值或(编号, 数值)对")
            return False

        return self._write_to_excel_core(data_pairs)

    # Backward compatibility
    def append_rows(self, values: List[float]) -> bool:
        return self.append(values, auto_generate_ids=True)

    def append_to_excel(self, data_pairs: List[Tuple[int, float]]) -> bool:
        return self.append(data_pairs, auto_generate_ids=False)

    def _write_to_excel_core(self, data_pairs: List[Tuple[int, float]]) -> bool:
        if not data_pairs:
            logger.warning("没有数据可写入")
            return False

        with self._lock:
            try:
                if not os.path.exists(self.filename):
                    self.create_new_file()

                existing_data = pd.read_excel(self.filename)
                
                # 获取配置设置
                include_original = config.get("excel.formatting.include_original", True)
                auto_numbering = config.get("excel.formatting.auto_numbering", True)
                include_timestamp = config.get("excel.formatting.include_timestamp", True)
                
                # 生成新数据记录
                new_data = []
                for nid, val in data_pairs:
                    record = {}
                    
                    # 根据配置决定是否添加编号
                    if auto_numbering:
                        record["编号"] = nid
                    
                    # 添加测量值
                    record["测量值"] = val
                    
                    # 根据配置决定是否添加时间戳
                    if include_timestamp:
                        record["时间戳"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 根据配置决定是否添加原始语音字段
                    if include_original:
                        record["原始语音"] = ""  # 兼容旧数据
                        
                    new_data.append(record)

                if existing_data.empty:
                    updated_data = pd.DataFrame(new_data)
                else:
                    updated_data = pd.concat([existing_data, pd.DataFrame(new_data)], ignore_index=True)

                updated_data.to_excel(self.filename, index=False)
                  
                if data_pairs and auto_numbering:
                    self._last_id = max(nid for nid, _ in data_pairs)

                logger.info(f"成功写入 {len(data_pairs)} 条数据到 {self.filename}")
                return True

            except Exception as e:
                logger.error(f"写入Excel失败: {e}")
                return False

    def format_excel(self) -> None:
        try:
            workbook = load_workbook(self.filename)
            worksheet = workbook.active
            if worksheet is None:
                return
            
            # 获取include_original配置
            include_original = config.get("excel.formatting.include_original", True)
            
            # 根据配置设置列宽
            column_widths = {'A': 10, 'B': 15, 'C': 20}
            if include_original:
                column_widths['D'] = 30  # 只有在包含原始语音时才设置D列宽
            
            for col_letter, width in column_widths.items():
                worksheet.column_dimensions[col_letter].width = width

            # Format header (row 1)
            header_font = Font(bold=True, size=12)
            header_alignment = Alignment(horizontal='center')
            for col in range(1, len(self.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.alignment = header_alignment

            workbook.save(self.filename)
            logger.info("Excel格式化完成")
        except Exception as e:
            logger.warning(f"Excel格式化失败: {e}")

    def get_existing_ids(self) -> List[int]:
        if not os.path.exists(self.filename):
            return []
        try:
            workbook = load_workbook(self.filename, read_only=True)
            worksheet = workbook.active
            if worksheet is None:
                workbook.close()
                return []
            existing_ids: List[int] = []
            for row in range(2, worksheet.max_row + 1):
                cell_value = worksheet.cell(row=row, column=1).value
                if cell_value is not None:
                    try:
                        existing_ids.append(self._int_cell(cell_value))
                    except (ValueError, TypeError):
                        continue
            workbook.close()
            return existing_ids
        except Exception as e:
            logger.error(f"使用openpyxl读取现有编号失败: {e}")
            try:
                df = pd.read_excel(self.filename)
                return df["编号"].tolist() if "编号" in df.columns else []
            except Exception as fallback_error:
                logger.error(f"回退到pandas也失败: {fallback_error}")
                return []

    def get_session_data(self) -> List[Tuple[int, float, str]]:
            """获取本次会话的所有数据"""
            return self._session_data.copy()
    
    def clear_session_data(self) -> None:
        """清空会话数据"""
        self._session_data.clear()

# 测试代码（保持不变，但修复日志配置）
if __name__ == '__main__':
    import tempfile, shutil
    logging.basicConfig(level=logging.INFO, format='%(message)s') # ✅ 测试时才配置日志
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test_data.xlsx")
    try:
        print("=== 开始优化模块自检 ===")
        exporter = ExcelExporter(filename=test_file)
        test_data: List[Tuple[int, float]] = [(1, 12.5), (2, 33.8), (3, 99.9)]
        print("\n[测试1] 统一接口 - 数据对写入")
        assert exporter.append(test_data, auto_generate_ids=False), "数据对写入失败"
        assert os.path.exists(test_file), "文件未创建"
        print("\n[测试2] 数据读取功能")
        df = pd.read_excel(test_file)
        assert len(df) == 3, "数据量不符"
        assert df['编号'].tolist() == [1, 2, 3], "编号数据错误"
        print("\n[测试3] 统一接口 - 数值列表写入")
        exporter.append([55.5, 77.7, 88.8], auto_generate_ids=True)
        updated_df = pd.read_excel(test_file)
        assert len(updated_df) == 6, "数值列表写入失败"
        print("\n✅ 所有测试通过！")
        print("生成的文件预览:")
        print(updated_df.head())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        shutil.rmtree(test_dir)