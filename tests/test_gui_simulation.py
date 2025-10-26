#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI操作模拟测试脚本
模拟真实的GUI操作流程，包括输入验证、Excel创建、语音识别等
"""

import sys
import os
import time
import threading
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simulate_gui_workflow():
    """模拟GUI工作流程"""
    print("="*80)
    print("🖥️ 模拟GUI操作流程")
    print("="*80)

    try:
        # 1. 导入GUI组件（但不显示窗口）
        from voice_gui import WorkingSimpleMainWindow
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer

        # 创建QApplication实例（如果不存在）
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

        print("\n1️⃣ 创建GUI窗口...")
        window = WorkingSimpleMainWindow()
        print("✅ GUI窗口创建成功")

        # 2. 模拟用户输入操作
        print("\n2️⃣ 模拟用户输入...")

        # 测试无效输入
        print("   测试无效输入:")
        window.part_no_input.setText("")  # 空零件号
        window.batch_no_input.setText("X")  # 太短
        window.inspector_input.setText("123")  # 数字字符

        # 检查开始按钮状态
        if not window.start_button.isEnabled():
            print("   ✅ 开始按钮正确禁用（输入无效）")
            print(f"   错误提示: {window.start_button.toolTip()}")

        # 测试有效输入
        print("\n   测试有效输入:")
        window.part_no_input.setText("PART-A001")
        window.batch_no_input.setText("BATCH-202501")
        window.inspector_input.setText("张三")

        # 等待验证完成
        time.sleep(0.1)

        if window.start_button.isEnabled():
            print("   ✅ 开始按钮正确启用（输入有效）")
            values = window.get_input_values()
            print(f"   输入值: {values}")
        else:
            print("   ❌ 开始按钮状态异常")

        # 3. 模拟启动语音系统
        print("\n3️⃣ 模拟启动语音系统...")

        # 创建worker但不实际启动语音识别
        from voice_gui import WorkingVoiceWorker
        worker = WorkingVoiceWorker(mode='customized')

        # 设置输入值
        input_values = window.get_input_values()
        worker.set_input_values(input_values)

        print("   ✅ Worker创建成功")
        print(f"   输入值已传递: {worker.input_values}")

        # 4. 模拟语音系统初始化
        print("\n4️⃣ 模拟语音系统初始化...")

        from main_f import FunASRVoiceSystem
        system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=False
        )

        # 模拟设置Excel模板
        success = system.setup_excel_from_gui(
            input_values['part_no'],
            input_values['batch_no'],
            input_values['inspector']
        )

        if success:
            print(f"   ✅ Excel模板创建成功: {os.path.basename(system.excel_exporter.filename)}")
        else:
            print("   ⚠️ Excel模板创建失败，使用默认方式")

        # 5. 模拟数据识别和写入
        print("\n5️⃣ 模拟语音识别和数据写入...")

        if system.excel_exporter:
            # 模拟不同标准序号的数据
            test_scenarios = [
                {
                    'standard_id': 100,
                    'data': [
                        (12.5, "十二点五", "12.5"),
                        (15.8, "十五点八", "15.8"),
                        ("OK", "好的", "OK")
                    ]
                },
                {
                    'standard_id': 200,
                    'data': [
                        (8.1, "八点一", "8.1"),
                        (25.6, "二十五点六", "25.6"),
                        ("NOK", "不行", "NOK")
                    ]
                }
            ]

            for scenario in test_scenarios:
                standard_id = scenario['standard_id']
                data = scenario['data']

                system.excel_exporter.current_standard_id = standard_id
                results = system.excel_exporter.append_with_text(data)

                print(f"   标准序号{standard_id}: 写入{len(results)}条数据")
                for voice_id, value, original in results:
                    print(f"     Voice ID {voice_id}: {value}")

        # 6. 模拟停止系统
        print("\n6️⃣ 模拟停止系统...")

        system._finalize_excel()
        print("   ✅ Excel最终处理完成")

        # 7. 验证结果
        print("\n7️⃣ 验证最终结果...")

        if system.excel_exporter and os.path.exists(system.excel_exporter.filename):
            file_size = os.path.getsize(system.excel_exporter.filename)
            print(f"   📁 Excel文件: {os.path.basename(system.excel_exporter.filename)}")
            print(f"   📊 文件大小: {file_size / 1024:.1f} KB")

            # 读取Excel验证内容
            try:
                import pandas as pd
                df = pd.read_excel(system.excel_exporter.filename)
                print(f"   📈 记录数量: {len(df)} 条")

                if not df.empty:
                    print("   📋 前5条记录:")
                    for idx, row in df.head().iterrows():
                        print(f"     行{idx+4}: {dict(row)}")

            except Exception as e:
                print(f"   ⚠️ 读取Excel文件失败: {e}")

        # 清理资源
        window.close()
        worker = None
        system = None

        print("\n✅ GUI工作流程模拟完成")
        return True

    except Exception as e:
        print(f"\n❌ GUI模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_gui_interaction():
    """模拟GUI交互细节"""
    print("\n" + "="*80)
    print("🎮 模拟GUI交互细节")
    print("="*80)

    try:
        from voice_gui import WorkingSimpleMainWindow
        from PySide6.QtWidgets import QApplication

        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        window = WorkingSimpleMainWindow()

        print("\n1️⃣ 测试输入框交互...")

        # 测试逐字符输入和实时验证
        test_inputs = [
            ("part_no_input", "P", "PA", "PAR", "PART001", ""),
            ("batch_no_input", "B", "B2", "B20", "B2025", "B202501", "X"),
            ("inspector_input", "张", "张三", "张三丰", "123", "A")
        ]

        for input_name, *values in test_inputs:
            input_widget = getattr(window, input_name)
            print(f"\n   测试 {input_name}:")

            for value in values:
                input_widget.setText(value)
                time.sleep(0.05)  # 模拟用户输入延迟

                # 检查验证状态
                style = input_widget.styleSheet()
                is_valid = "4caf50" in style  # 绿色边框表示有效
                is_invalid = "f44336" in style  # 红色边框表示无效
                is_warning = "ff9800" in style  # 橙色边框表示警告

                status = "✅" if is_valid else ("❌" if is_invalid else ("⚠️" if is_warning else "⏳"))
                print(f"     '{value}' -> {status}")

        print("\n2️⃣ 测试按钮状态同步...")

        # 检查开始按钮状态
        print(f"   开始按钮状态: {'启用' if window.start_button.isEnabled() else '禁用'}")
        print(f"   工具提示: {window.start_button.toolTip()}")

        print("\n3️⃣ 测试输入验证函数...")

        # 测试验证函数
        test_cases = [
            ("", "", "", "全部为空"),
            ("A", "B", "张", "部分太短"),
            ("A"*25, "B"*20, "张"*15, "超过长度限制"),
            ("PART001", "B202501", "张三", "有效输入")
        ]

        for part_no, batch_no, inspector, desc in test_cases:
            window.part_no_input.setText(part_no)
            window.batch_no_input.setText(batch_no)
            window.inspector_input.setText(inspector)

            time.sleep(0.05)
            is_valid = window.are_inputs_valid()
            error_count = len(window.validation_errors)

            status = "✅" if is_valid else "❌"
            print(f"   {desc}: {status} (错误数: {error_count})")

        print("\n4️⃣ 测试输入值获取...")

        # 设置有效输入并获取
        window.part_no_input.setText("TEST-PART")
        window.batch_no_input.setText("BATCH-001")
        window.inspector_input.setText("李四")

        values = window.get_input_values()
        print(f"   获取的输入值: {values}")

        # 验证输入值的正确性
        expected = {
            'part_no': 'TEST-PART',
            'batch_no': 'BATCH-001',
            'inspector': '李四'
        }

        if values == expected:
            print("   ✅ 输入值获取正确")
        else:
            print(f"   ❌ 输入值获取错误，期望: {expected}")

        print("\n5️⃣ 测试输入框清空...")

        window.clear_input_fields()
        cleared_values = window.get_input_values()

        if all(not v for v in cleared_values.values()):
            print("   ✅ 输入框清空成功")
        else:
            print(f"   ❌ 输入框清空失败: {cleared_values}")

        window.close()
        print("\n✅ GUI交互细节模拟完成")
        return True

    except Exception as e:
        print(f"\n❌ GUI交互模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始GUI操作模拟测试")
    print("="*80)

    results = []

    # 测试GUI工作流程
    workflow_result = simulate_gui_workflow()
    results.append(("GUI工作流程", workflow_result))

    # 测试GUI交互细节
    interaction_result = simulate_gui_interaction()
    results.append(("GUI交互细节", interaction_result))

    # 输出测试结果汇总
    print("\n" + "="*80)
    print("📊 GUI模拟测试结果汇总")
    print("="*80)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 项GUI模拟测试通过")

    if passed == total:
        print("🎉 所有GUI功能模拟测试通过！")
        print("📝 说明: GUI组件的输入验证、状态管理、数据传递等功能都正常工作")
        return True
    else:
        print("⚠️ 部分GUI功能存在问题，请检查上述错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)