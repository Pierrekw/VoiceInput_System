#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建缺失的测量规范文件
"""

import os
import pandas as pd

def create_missing_specs():
    """创建缺失的测量规范文件"""
    print("🔧 创建缺失的测量规范文件")
    print("="*50)

    # 创建reports目录
    os.makedirs("reports", exist_ok=True)

    # 创建PART-A001的测量规范数据
    part_a001_spec_data = [
        [100, '半径1', 75.5, 85.8],
        [200, '半径2', 15.5, 30.5],
        [300, '半径3', 8.5, 12.5],
        [400, '半径4', 53.5, 57.5],
        [500, '直径1', 20.0, 25.0],
        [600, '直径2', 30.0, 35.0],
        [700, '高度1', 10.0, 15.0],
        [800, '高度2', 40.0, 45.0],
        [900, '宽度1', 25.0, 30.0],
        [1000, '宽度2', 35.0, 40.0],
    ]

    # 创建DataFrame
    spec_df = pd.DataFrame(part_a001_spec_data, columns=['标准序号', '标准内容', '下限', '上限'])

    # 保存为PART-A001_MeasureSpec.xlsx
    spec_filename = "reports/PART-A001_MeasureSpec.xlsx"
    spec_df.to_excel(spec_filename, index=False)

    print(f"✅ 创建测量规范文件: {spec_filename}")
    print(f"   包含 {len(part_a001_spec_data)} 条测量规范")

    # 显示创建的内容
    print(f"\n📋 创建的测量规范内容:")
    print(spec_df.to_string(index=False))

    # 检查文件是否创建成功
    if os.path.exists(spec_filename):
        file_size = os.path.getsize(spec_filename)
        print(f"\n📁 文件信息:")
        print(f"   文件大小: {file_size} 字节")
        print(f"   创建成功: ✅")
    else:
        print(f"\n❌ 文件创建失败")

    return spec_filename

if __name__ == "__main__":
    create_missing_specs()