#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建干净的Excel模板
"""

import pandas as pd

def create_clean_template():
    """创建干净的测量报告模板"""

    # 创建模板数据
    template_data = [
        ["标准序号", "标准内容", "下限", "上限", "测量值", "判断结果", "偏差", "time", "语音录入编号"],
        [100, "半径1", 75.5, 85.8, "", "", "", "", ""],
        [200, "半径2", 15.5, 30.5, "", "", "", "", ""],
        [300, "半径3", 8.5, 12.5, "", "", "", "", ""],
        [400, "半径4", 53.5, 57.5, "", "", "", "", ""],
    ]

    # 创建DataFrame
    df = pd.DataFrame(template_data)

    # 保存为Excel文件
    template_path = "reports/clean_measure_template.xlsx"
    df.to_excel(template_path, index=False, header=False)

    print(f"✅ 创建干净模板: {template_path}")

    # 验证文件
    df_check = pd.read_excel(template_path, header=None)
    print(f"📋 模板内容验证:")
    for idx, row in df_check.iterrows():
        print(f"   行{idx+1}: {list(row)}")

if __name__ == "__main__":
    create_clean_template()