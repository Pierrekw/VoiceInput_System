# -*- coding: utf-8 -*-
# Excel Exporter Module / Excel导出模块
# Handles measurement data export to Excel files with formatting
# 处理测量数据导出到Excel文件，包含格式化功能

import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Only show message itself / 只显示消息本身
    handlers=[logging.StreamHandler()]  # Console output / 控制台输出
)

class ExcelExporter:
    """
    Excel Exporter Class / Excel导出类
    Handles measurement data export to Excel files with formatting and auto-numbering
    处理测量数据导出到Excel文件，包含格式化和自动编号功能
    """

    def __init__(self, filename="measurement_data.xlsx"):
        """
        Initialize Excel exporter with filename and column structure
        初始化Excel导出器，设置文件名和列结构
        """
        self.filename = filename
        self.columns = ["编号", "测量值", "时间戳"]  # ID, Measurement Value, Timestamp / 编号，测量值，时间戳

    def create_new_file(self):
        """
        Create new Excel file with headers / 创建新的Excel文件（包含表头）
        """
        df = pd.DataFrame(columns=self.columns)
        df.to_excel(self.filename, index=False)
        logging.info(f"创建新的Excel文件: {self.filename}")  # Create new Excel file / 创建新的Excel文件
    
    def append(self, data, auto_generate_ids=True):
        """
        Unified data append interface - intelligently handles two input types
        统一的数据追加接口 - 智能处理两种输入类型

        Args:
            data: Can be one of two formats / 可以是以下两种格式之一：
                  - [12.5, 33.8, 99.9] - Value list (used by AudioCapture) / 数值列表（AudioCapture使用）
                  - [(1, 12.5), (2, 33.8)] - (ID, Value) pairs list (direct call) / (ID, 数值)对列表（直接调用）
            auto_generate_ids: Whether to auto-generate IDs (needed for value lists, not for tuple lists) / 是否自动编号（数值列表需要，元组列表不需要）

        Returns:
            bool: Returns True on successful write, False on failure / 写入成功返回True，失败返回False
        """
        if not data:
            logging.warning("没有数据可写入")  # No data to write / 没有数据可写入
            return False

        # Data type detection and conversion / 数据类型检测和转换
        if isinstance(data[0], (int, float)) and auto_generate_ids:
            # Case 1: Value list [12.5, 33.8, 99.9] / 情况1: 数值列表 [12.5, 33.8, 99.9]
            # Get existing IDs and generate new ones / 获取现有编号，生成新编号
            existing_ids = self.get_existing_ids()
            start_id = max(existing_ids) + 1 if existing_ids else 1

            # Create data pairs: (ID, Value) / 创建数据对：(编号, 数值)
            data_pairs = []
            for i, value in enumerate(data):
                data_pairs.append((start_id + i, float(value)))

        elif isinstance(data[0], (list, tuple)) and len(data[0]) == 2:
            # Case 2: (ID, Value) pairs list [(1, 12.5), (2, 33.8)] / 情况2: (ID, 数值)对列表 [(1, 12.5), (2, 33.8)]
            data_pairs = [(int(item[0]), float(item[1])) for item in data]

        else:
            logging.error(f"无效的数据格式: {type(data[0])}，期望数值或(编号, 数值)对")  # Invalid data format / 无效的数据格式
            return False

        # Call core Excel writing logic / 调用核心的Excel写入逻辑
        return self._write_to_excel_core(data_pairs)
    
    # Backward compatibility methods (deprecated, recommend using unified append() method)
    # 向后兼容的方法（已弃用，建议使用统一的 append() 方法）
    def append_rows(self, values):
        """Compatible with AudioCapture old interface - recommend using append(values) / 兼容AudioCapture的旧接口 - 推荐使用 append(values)"""
        return self.append(values, auto_generate_ids=True)

    def append_to_excel(self, data_pairs):
        """Compatible with direct call old interface - recommend using append(data_pairs, auto_generate_ids=False) / 兼容直接调用的旧接口 - 推荐使用 append(data_pairs, auto_generate_ids=False)"""
        return self.append(data_pairs, auto_generate_ids=False)
    
    def _write_to_excel_core(self, data_pairs):
        """
        Core Excel writing logic - process data pairs and write to Excel file
        核心的Excel写入逻辑 - 处理数据对并写入Excel文件
        """
        if not data_pairs:
            logging.warning("没有数据可写入")
            return False
        
        try:
            # Check if file exists / 检查文件是否存在
            if not os.path.exists(self.filename):
                self.create_new_file()  # Create new file if not exists / 文件不存在时创建新文件

            # Read existing data / 读取现有数据
            existing_data = pd.read_excel(self.filename)

            # Prepare new data / 准备新数据
            new_data = []
            for number_id, value in data_pairs:
                new_data.append({
                    "编号": int(number_id),  # ID number / 编号
                    "测量值": float(value),  # Measurement value / 测量值
                    "时间戳": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp / 时间戳
                })

            # Merge data / 合并数据
            if existing_data.empty:  # If original data is empty, use new data directly / 如果原数据为空，直接使用新数据
                updated_data = pd.DataFrame(new_data)
            else:
                updated_data = pd.concat([existing_data, pd.DataFrame(new_data)], ignore_index=True)

            # Save to Excel / 保存到Excel
            updated_data.to_excel(self.filename, index=False)

            # Format Excel / 格式化Excel
            self.format_excel()

            logging.info(f"成功写入 {len(data_pairs)} 条数据到 {self.filename}")  # Successfully wrote X records to file / 成功写入X条数据到文件
            return True

        except Exception as e:
            logging.error(f"写入Excel失败: {e}")  # Failed to write Excel / 写入Excel失败
            return False
    
    def format_excel(self):
        """
        Format Excel file with professional styling / 格式化Excel文件（专业样式）
        """
        try:
            workbook = load_workbook(self.filename)
            worksheet = workbook.active

            # Set column widths / 设置列宽
            column_widths = {'A': 10, 'B': 15, 'C': 20}  # ID, Value, Timestamp / 编号，测量值，时间戳
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

            # Set header row styles / 设置标题行样式
            header_font = Font(bold=True, size=12)  # Bold, size 12 / 粗体，12号字体
            header_alignment = Alignment(horizontal='center')  # Center alignment / 居中对齐

            for col in range(1, len(self.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.alignment = header_alignment

            # Save formatted file / 保存格式化后的文件
            workbook.save(self.filename)
            logging.info("Excel格式化完成")  # Excel formatting completed / Excel格式化完成

        except Exception as e:
            logging.warning(f"Excel格式化失败: {e}")  # Excel formatting failed / Excel格式化失败
        try:
            workbook = load_workbook(self.filename)
            worksheet = workbook.active
            
            # 设置列宽
            column_widths = {'A': 10, 'B': 15, 'C': 20}
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # 设置标题行样式
            header_font = Font(bold=True, size=12)
            header_alignment = Alignment(horizontal='center')
            
            for col in range(1, len(self.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.alignment = header_alignment
            
            workbook.save(self.filename)
            logging.info("Excel格式化完成")
            
        except Exception as e:
            logging.warning(f"Excel格式化失败: {e}")
    
    def get_existing_ids(self):
        """
        Get list of existing data IDs / 获取已存在的编号列表
        """
        if not os.path.exists(self.filename):
            return []  # Return empty list if file doesn't exist / 文件不存在返回空列表
        
        try:
            df = pd.read_excel(self.filename)
            return df["编号"].tolist() if "编号" in df.columns else []  # Return ID list if ID column exists / 如果编号列存在返回编号列表
        except Exception as e:
            logging.error(f"读取现有编号失败: {e}")  # Failed to read existing IDs / 读取现有编号失败
            return []
            
            
if __name__ == '__main__':
    """
    Module self-test code (optimized version) / 模块自查代码（优化版）
    Tests Excel export functionality with various data types and scenarios
    使用各种数据类型和场景测试Excel导出功能
    """
    import os
    import tempfile
    import shutil
    import pandas as pd

    # Configure simple logging / 配置简洁日志
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # 创建临时环境
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test_data.xlsx")
    
    try:
        print("=== 开始模块自检 ===")
        exporter = ExcelExporter(filename=test_file)
        
        # 测试数据
        test_data = [('1', 12.5), ('2', 33.8), ('3', 99.9)]
        
        # 测试统一接口 - 使用数据对（auto_generate_ids=False）
        print("\n[测试1] 统一接口 - 数据对写入")
        assert exporter.append(test_data, auto_generate_ids=False), "数据对写入失败"
        assert os.path.exists(test_file), "文件未创建"
        
        # 测试读取功能
        print("\n[测试2] 数据读取功能")
        df = pd.read_excel(test_file)
        assert len(df) == 3, "数据量不符"
        assert df['编号'].tolist() == [1, 2, 3], "编号数据错误"
        
        # 测试统一接口 - 数值列表（auto_generate_ids=True）
        print("\n[测试3] 统一接口 - 数值列表写入")
        exporter.append([55.5, 77.7, 88.8], auto_generate_ids=True)
        updated_df = pd.read_excel(test_file)
        assert len(updated_df) == 6, "数值列表写入失败"  # 原有3条 + 新增3条
        
        print("\n✅ 所有测试通过！")
        print("生成的文件预览:")
        print(updated_df.head())
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        shutil.rmtree(test_dir)