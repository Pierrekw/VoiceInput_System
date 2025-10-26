#!/usr/bin/env python3
"""
测试模板使用情况
检查系统是否能正确使用模板创建报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_utils import ExcelExporterEnhanced as ExcelExporter
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_template_usage():
    """测试模板使用情况"""
    print("🔍 测试Excel模板使用情况")
    print("=" * 50)

    # 创建Excel导出器
    exporter = ExcelExporter("test_template_usage.xlsx")

    print(f"📋 模板路径: {exporter.template_path}")
    print(f"📋 模板文件存在: {os.path.exists(exporter.template_path)}")

    if os.path.exists(exporter.template_path):
        print("✅ 模板文件存在，尝试使用模板创建...")
        success = exporter.create_from_template("TEST-PART", "B001", "测试员")
        print(f"📊 模板创建结果: {success}")

        if success:
            print("✅ 模板使用成功！")
            # 检查生成的文件结构
            if os.path.exists(exporter.filename):
                import pandas as pd
                df = pd.read_excel(exporter.filename, header=None)
                print(f"📋 生成文件行数: {len(df)}")
                print("📋 前5行内容:")
                for i in range(min(5, len(df))):
                    print(f"  行{i+1}: {df.iloc[i].tolist()}")
        else:
            print("❌ 模板使用失败！")
    else:
        print("❌ 模板文件不存在，尝试使用默认方式创建...")
        exporter.create_new_file()
        print("✅ 默认方式创建完成")

        # 检查生成的文件结构
        if os.path.exists(exporter.filename):
            import pandas as pd
            df = pd.read_excel(exporter.filename, header=None)
            print(f"📋 生成文件行数: {len(df)}")
            print("📋 前5行内容:")
            for i in range(min(5, len(df))):
                print(f"  行{i+1}: {df.iloc[i].tolist()}")

if __name__ == "__main__":
    test_template_usage()