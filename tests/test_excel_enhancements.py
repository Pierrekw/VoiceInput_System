#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel增强功能测试脚本
独立测试双ID系统、模板复制、删除功能等核心功能
"""

import sys
import os
import time
import random
import logging
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_exporter import ExcelExporter
from logging_utils import LoggingManager

def test_excel_enhancements():
    """测试Excel增强功能的完整流程"""

    # 设置日志
    logger = LoggingManager.get_logger(
        name='test_excel',
        level=logging.INFO,
        console_level=logging.INFO,
        log_to_console=True,
        log_to_file=True
    )

    print("="*80)
    print("🧪 开始测试Excel增强功能")
    print("="*80)

    # 1. 测试数据准备
    test_data = [
        (12.5, "十二点五", "12.5"),
        ("OK", "好的", "OK"),
        (99.8, "九十九点八", "99.8"),
        (15.2, "十五点二", "15.2"),
        ("NOK", "不行", "NOK"),
        (22.1, "二十二点一", "22.1")
    ]

    part_no = "TEST001"
    batch_no = "B202501"
    inspector = "张三"

    # 2. 创建测试ExcelExporter
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_filename = f"reports/test_{timestamp}.xlsx"

    print(f"\n📁 测试文件: {test_filename}")
    print(f"📊 测试数据: {len(test_data)} 条")

    try:
        # 初始化ExcelExporter
        exporter = ExcelExporter(filename=test_filename)

        # 3. 测试模板复制
        print("\n1️⃣ 测试模板复制功能...")
        success = exporter.create_from_template(part_no, batch_no, inspector)
        if success:
            print("✅ 模板复制成功")
        else:
            print("❌ 模板复制失败，使用默认方式")

        # 4. 测试数据写入
        print("\n2️⃣ 测试初始数据写入（3条）...")
        initial_data = test_data[:3]
        results = exporter.append_with_text(initial_data)

        print(f"写入结果:")
        for voice_id, value, original in results:
            print(f"  Voice ID: {voice_id}, 值: {value}, 原文: {original}")

        # 5. 测试删除功能
        print("\n3️⃣ 测试删除功能（删除Voice ID 2）...")
        delete_success = exporter.delete_row_by_voice_id(2)
        if delete_success:
            print("✅ 删除成功")
        else:
            print("❌ 删除失败")

        # 6. 测试继续写入数据
        print("\n4️⃣ 测试继续写入数据（2条）...")
        continue_data = test_data[3:5]
        continue_results = exporter.append_with_text(continue_data)

        print(f"继续写入结果:")
        for voice_id, value, original in continue_results:
            print(f"  Voice ID: {voice_id}, 值: {value}, 原文: {original}")

        # 7. 测试再次删除
        print("\n5️⃣ 测试再次删除（删除Voice ID 1）...")
        delete_success2 = exporter.delete_row_by_voice_id(1)
        if delete_success2:
            print("✅ 删除成功")
        else:
            print("❌ 删除失败")

        # 8. 测试最后写入
        print("\n6️⃣ 测试最后写入数据（1条）...")
        final_data = test_data[5:]
        final_results = exporter.append_with_text(final_data)

        print(f"最后写入结果:")
        for voice_id, value, original in final_results:
            print(f"  Voice ID: {voice_id}, 值: {value}, 原文: {original}")

        # 9. 测试重新编号
        print("\n7️⃣ 测试Excel重新编号...")
        exporter.renumber_excel_ids()
        print("✅ 重新编号完成")

        # 10. 验证最终结果
        print("\n8️⃣ 验证最终结果...")
        verify_results(exporter)

        # 11. 内存状态检查
        print("\n9️⃣ 内存状态检查...")
        check_memory_state(exporter)

        print(f"\n✅ 测试完成！文件保存在: {test_filename}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def verify_results(exporter):
    """验证Excel文件内容"""
    try:
        import pandas as pd

        # 读取Excel文件
        df = pd.read_excel(exporter.filename)

        print(f"📊 Excel文件内容:")
        print(f"   总行数: {len(df)}")
        print(f"   列名: {df.columns.tolist()}")

        if not df.empty:
            print(f"\n📋 详细数据:")
            for index, row in df.iterrows():
                row_num = index + 4  # Excel行号（从第4行开始）
                print(f"   行{row_num}: ", end="")

                # 显示各列数据
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):
                        print(f"{col}={value} ", end="")
                print()

        # 检查关键列
        if '语音录入编号' in df.columns:
            voice_ids = df['语音录入编号'].dropna().tolist()
            print(f"\n🔢 语音录入ID: {voice_ids}")

        if 'Excel编号' in df.columns:
            excel_ids = df['Excel编号'].dropna().tolist()
            print(f"📊 Excel编号: {excel_ids}")

        # 验证删除的ID是否不在文件中
        deleted_ids = exporter.deleted_voice_ids
        print(f"🗑️ 已删除的ID: {deleted_ids}")

        # 检查删除的ID是否真的不在文件中
        if '语音录入编号' in df.columns:
            existing_voice_ids = set(df['语音录入编号'].dropna().astype(int).tolist())
            missing_deleted = deleted_ids - existing_voice_ids
            if missing_deleted == deleted_ids:
                print("✅ 删除的ID已正确从文件中移除")
            else:
                print(f"❌ 删除的ID仍有部分在文件中: {missing_deleted}")

    except Exception as e:
        print(f"❌ 验证失败: {e}")

def check_memory_state(exporter):
    """检查内存状态"""
    print(f"🧠 内存状态:")
    print(f"   voice_id_counter: {exporter.voice_id_counter}")
    print(f"   next_insert_row: {exporter.next_insert_row}")
    print(f"   active_record_count: {exporter.active_record_count}")
    print(f"   deleted_voice_ids: {exporter.deleted_voice_ids}")
    print(f"   voice_id_to_row 映射: {exporter.voice_id_to_row}")

    # 验证映射一致性
    total_records = len(exporter.voice_id_to_row) + len(exporter.deleted_voice_ids)
    if total_records == exporter.voice_id_counter:
        print("✅ 内存映射一致性正确")
    else:
        print(f"❌ 内存映射不一致: 总记录数{total_records} != 计数器{exporter.voice_id_counter}")

if __name__ == "__main__":
    test_excel_enhancements()