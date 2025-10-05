#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步数据导出器功能
"""

import asyncio
import sys
import os
from typing import List, Tuple

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_async_excel_exporter():
    """测试异步Excel导出器"""
    print("测试异步Excel导出器...")

    try:
        from adapters.data_exporter_adapter import DataExporterAdapter

        # 创建测试导出器
        exporter = DataExporterAdapter(filename="test_async_export.xlsx")

        # 初始化导出器
        exporter.initialize()
        print("[OK] DataExporterAdapter 初始化成功")

        # 测试异步导出数据
        test_data = [
            (25.5, "温度二十五点五度"),
            (75.0, "湿度百分之七十五"),
            (42.0, "数值42"),
            (1.0, "长度为一米二"),
            (90.0, "角度九十度")
        ]

        # 异步导出数据
        written_records = await exporter.append_with_text_async(test_data)

        if written_records:
            print(f"[OK] 异步导出成功: {len(written_records)} 条记录")
            for i, (record_id, value, text) in enumerate(written_records):
                print(f"  记录 {i+1}: ID={record_id}, 值={value}, 文本='{text}'")
        else:
            print("[FAIL] 异步导出失败，没有记录")
            return False

        # 测试获取会话数据
        session_data = exporter.get_session_data()
        if session_data:
            print(f"[OK] 会话数据: {len(session_data)} 条记录")
        else:
            print("[INFO] 会话数据为空")

        # 测试文件信息
        if exporter.file_exists():
            print(f"[OK] Excel文件存在: {exporter.get_file_info()}")
        else:
            print("[FAIL] Excel文件不存在")

        print("[OK] 异步Excel导出器测试完成")
        return True

    except Exception as e:
        print(f"[FAIL] 异步Excel导出器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_batch_export():
    """测试批量导出"""
    print("\n测试批量导出功能...")

    try:
        from adapters.data_exporter_adapter import DataExporterAdapter

        # 创建批量测试数据
        batch_data = [
            [
                ("批量测试1", [10.5, 20.5]),
                ("批量测试2", [30.0]),
                ("批量测试3", [15.5, 25.5, 35.5])
            ]
        ]

        exporter = DataExporterAdapter(filename="test_batch_export.xlsx")
        exporter.initialize()

        # 异步批量导出
        results = await exporter.batch_export_async(batch_data)

        print(f"[OK] 批量导出结果: {len(results)} 个批次")
        for i, result in enumerate(results):
            if result.success:
                print(f"  批次 {i+1}: 成功导出 {result.exported_count} 条记录")
            else:
                print(f"  批次 {i+1}: 导出失败 - {result.error_message}")

        print("[OK] 批量导出测试完成")
        return True

    except Exception as e:
        print(f"[FAIL] 批量导出测试失败: {e}")
        return False

async def test_concurrent_export():
    """测试并发导出"""
    print("\n测试并发导出功能...")

    try:
        from adapters.data_exporter_adapter import DataExporterAdapter

        exporter = DataExporterAdapter(filename="test_concurrent_export.xlsx")
        exporter.initialize()

        # 创建多个并发任务
        async def export_task(task_id: int, data: List[Tuple[float, str]]):
            result = await exporter.append_with_text_async(data)
            return task_id, result

        tasks = []
        for i in range(5):
            data = [(float(i * 10 + j), f"并发测试{i}-{j}") for j in range(3)]
            task = export_task(i, data)
            tasks.append(task)

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  任务 {i}: 失败 - {result}")
            else:
                task_id, records = result
                if records:
                    print(f"  任务 {task_id}: 成功导出 {len(records)} 条记录")
                    success_count += 1

        print(f"[OK] 并发导出完成: {success_count}/{len(tasks)} 个任务成功")
        return success_count == len(tasks)

    except Exception as e:
        print(f"[FAIL] 并发导出测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("[开始] 异步Excel导出器测试")
    print("=" * 50)

    # 测试基本功能
    basic_ok = await test_async_excel_exporter()

    # 测试批量导出
    batch_ok = await test_batch_export()

    # 测试并发导出
    concurrent_ok = await test_concurrent_export()

    print("\n" + "=" * 50)
    if basic_ok and batch_ok and concurrent_ok:
        print("[成功] 所有异步Excel导出器测试通过！")
    else:
        print("[部分失败] 一些测试未通过，需要进一步检查。")

    return basic_ok and batch_ok and concurrent_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)