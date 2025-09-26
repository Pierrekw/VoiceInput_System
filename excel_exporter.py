import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # 只显示消息本身
    handlers=[logging.StreamHandler()]
)

class ExcelExporter:
    def __init__(self, filename="measurement_data.xlsx"):
        self.filename = filename
        self.columns = ["编号", "测量值", "时间戳"]
    
    def create_new_file(self):
        """创建新的Excel文件"""
        df = pd.DataFrame(columns=self.columns)
        df.to_excel(self.filename, index=False)
        logging.info(f"创建新的Excel文件: {self.filename}")
    
    def append_to_excel(self, data_pairs):
        """追加数据到Excel文件"""
        if not data_pairs:
            logging.warning("没有数据可写入")
            return False
        
        try:
            # 检查文件是否存在
            if not os.path.exists(self.filename):
                self.create_new_file()
            
            # 读取现有数据
            existing_data = pd.read_excel(self.filename)
            
            # 准备新数据
            new_data = []
            for number_id, value in data_pairs:
                new_data.append({
                    "编号": int(number_id),
                    "测量值": float(value),
                    "时间戳": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # 合并数据
            if existing_data.empty:  # 如果原数据为空，直接使用新数据
                updated_data = pd.DataFrame(new_data)
            else:
                updated_data = pd.concat([existing_data, pd.DataFrame(new_data)], ignore_index=True)
            
            # 保存到Excel
            updated_data.to_excel(self.filename, index=False)
            
            # 格式化Excel
            self.format_excel()
            
            logging.info(f"成功写入 {len(data_pairs)} 条数据到 {self.filename}")
            return True
            
        except Exception as e:
            logging.error(f"写入Excel失败: {e}")
            return False
    
    def format_excel(self):
        """格式化Excel文件"""
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
        """获取已存在的编号列表"""
        if not os.path.exists(self.filename):
            return []
        
        try:
            df = pd.read_excel(self.filename)
            return df["编号"].tolist() if "编号" in df.columns else []
        except Exception as e:
            logging.error(f"读取现有编号失败: {e}")
            return []
            
            
if __name__ == '__main__':
    """模块自查代码（优化版）"""
    import os
    import tempfile
    import shutil
    import pandas as pd

    # 配置简洁日志
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # 创建临时环境
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test_data.xlsx")
    
    try:
        print("=== 开始模块自检 ===")
        exporter = ExcelExporter(filename=test_file)
        
        # 测试数据
        test_data = [('1', 12.5), ('2', 33.8), ('3', 99.9)]
        
        # 测试写入功能
        print("\n[测试1] 数据写入功能")
        assert exporter.append_to_excel(test_data), "数据写入失败"
        assert os.path.exists(test_file), "文件未创建"
        
        # 测试读取功能
        print("\n[测试2] 数据读取功能")
        df = pd.read_excel(test_file)
        assert len(df) == 3, "数据量不符"
        assert df['编号'].tolist() == [1, 2, 3], "编号数据错误"
        
        # 测试追加功能
        print("\n[测试3] 数据追加功能")
        exporter.append_to_excel([('4', 55.5)])
        updated_df = pd.read_excel(test_file)
        assert len(updated_df) == 4, "追加数据失败"
        
        print("\n✅ 所有测试通过！")
        print("生成的文件预览:")
        print(updated_df.head())
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        shutil.rmtree(test_dir)