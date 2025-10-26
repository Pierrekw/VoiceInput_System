#!/usr/bin/env python3
"""
检查生成的Excel文件问题
分析文件命名和模板使用情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from openpyxl import load_workbook

def check_generated_file():
    """检查生成的文件"""
    print("🔍 检查生成的Excel文件问题")
    print("=" * 50)

    file_path = "reports/report_20251026_212804.xlsx"

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    print(f"📋 检查文件: {file_path}")
    print(f"📋 文件大小: {os.path.getsize(file_path)} bytes")

    # 检查文件内容
    try:
        df = pd.read_excel(file_path, header=None)
        print(f"📋 文件行数: {len(df)}")
        print(f"📋 文件列数: {len(df.columns)}")
        print("\n📋 文件内容:")
        for i in range(min(8, len(df))):
            row_content = []
            for j in range(min(10, len(df.columns))):
                val = df.iloc[i, j]
                if pd.isna(val):
                    row_content.append("None")
                else:
                    row_content.append(str(val)[:12])
            print(f"  行{i+1}: {' | '.join(row_content)}")

        # 检查是否使用了模板
        print("\n🔍 模板使用检查:")
        if len(df) >= 4:
            row1 = str(df.iloc[0, 0] or "")
            row2_1 = str(df.iloc[1, 0] or "")
            row4 = str(df.iloc[3, 0] or "")

            if "测量报告" in row1:
                print("✅ 第1行包含'测量报告' - 可能使用了模板")
            else:
                print("❌ 第1行不包含'测量报告' - 可能未使用模板")

            if "零件号" in row2_1:
                print("✅ 第2行包含'零件号' - 可能使用了模板")
            else:
                print("❌ 第2行不包含'零件号' - 可能未使用模板")

            if "标准序号" in row4:
                print("✅ 第4行包含'标准序号' - 可能使用了模板")
            else:
                print("❌ 第4行不包含'标准序号' - 可能未使用模板")

        # 检查文件命名规则
        print("\n🔍 文件命名检查:")
        filename = os.path.basename(file_path)
        expected_pattern = "Report_{part_no}_{batch_no}_{timestamp}"
        print(f"📋 当前文件名: {filename}")
        print(f"📋 期望格式: {expected_pattern}")

        if filename.startswith("report_"):
            print("❌ 文件名使用了'report_'前缀，应该是'Report_'")
        elif filename.startswith("Report_"):
            print("✅ 文件名使用了正确的'Report_'前缀")

        # 检查是否包含零件号和批次号
        if "_" in filename:
            parts = filename.split("_")
            if len(parts) >= 3:
                print(f"📋 文件名部分: {parts}")
                if parts[1] and parts[2]:
                    print("✅ 文件名包含零件号和批次号部分")
                else:
                    print("❌ 文件名缺少零件号或批次号部分")
            else:
                print("❌ 文件名格式不正确，应该包含至少3个下划线分隔的部分")
        else:
            print("❌ 文件名不包含下划线分隔")

    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

if __name__ == "__main__":
    check_generated_file()