#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试模板创建功能
"""

import os
import sys
import pandas as pd

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from excel_exporter_enhanced import ExcelExporterEnhanced

def test_template_direct():
    """直接测试模板创建功能"""
    print("🎯 直接测试模板创建功能")
    print("="*60)

    # 创建测量规范文件
    spec_data = [
        [100, '半径1', 75.5, 85.8],
        [200, '半径2', 15.5, 30.5],
        [300, '半径3', 8.5, 12.5],
    ]

    spec_df = pd.DataFrame(spec_data, columns=['标准序号', '标准内容', '下限', '上限'])
    spec_filename = "reports/DIRECT-TEST_MeasureSpec.xlsx"

    os.makedirs("reports", exist_ok=True)
    spec_df.to_excel(spec_filename, index=False)

    # 创建导出器，使用模板创建
    exporter = ExcelExporterEnhanced(
        filename="reports/direct_template_test.xlsx",
        part_no="DIRECT-TEST",
        batch_no="B001",
        inspector="直接测试"
    )

    print("📝 1. 使用模板创建文件...")
    success = exporter.create_from_template("DIRECT-TEST", "B001", "直接测试")
    print(f"   模板创建结果: {success}")

    print(f"📝 2. 写入测试数据...")
    test_scenarios = [
        (100, 80.0, "半径1 八十"),
        (200, 25.0, "半径2 二十五"),
        (300, 11.0, "半径3 十一"),
    ]

    for standard_id, value, text in test_scenarios:
        exporter.current_standard_id = standard_id
        test_data = [(value, text, text)]
        results = exporter.append_with_text(test_data)
        print(f"   标准序号{standard_id}: 值{value} -> 写入结果: {results}")

    print("🔧 3. 执行最终格式化...")
    success = exporter.finalize_excel_file()
    print(f"   格式化结果: {success}")

    if success and os.path.exists(exporter.filename):
        print(f"\n📋 4. 验证结果:")
        df = pd.read_excel(exporter.filename)
        print(f"   Excel文件包含 {len(df)} 行数据")

        for idx, row in df.iterrows():
            print(f"   行{idx+1}: {dict(row)}")

        # 清理文件
        os.remove(exporter.filename)
        print(f"\n🧹 已清理测试文件")

    # 清理测量规范文件
    if os.path.exists(spec_filename):
        os.remove(spec_filename)
        print(f"🧹 已清理测量规范文件")

if __name__ == "__main__":
    test_template_direct()