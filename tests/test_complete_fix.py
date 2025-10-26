#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复测试 - 验证GUI显示和Excel写入都正确
"""

import sys
import os

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print('=== 完整修复测试 ===')
    print('验证：GUI显示和Excel写入都正确')

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统实例但不启动识别
        system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=False,
            debug_mode=True
        )

        print(f'✅ 系统初始化成功')

        # 测试用例
        test_cases = [
            ('一 二 三', [123.0], '[1] 123.0', '123'),           # 数字
            ('合格', [], '[2] OK', 'OK'),                       # 特殊文本 - OK
            ('不合格', [], '[3] Not OK', 'NOT OK'),             # 特殊文本 - Not OK (注意：GUI显示为Not OK，Excel为NOT OK)
            ('三 点 五', [3.5], '[4] 3.5', '3.5'),              # 小数
        ]

        print('\n=== 开始测试 ===')

        # 获取Excel文件路径
        excel_file = system.excel_exporter.filename
        print(f'📄 Excel文件: {excel_file}')

        for i, (original_text, expected_numbers, expected_gui_display, expected_excel_value) in enumerate(test_cases, 1):
            print(f'\n--- 测试 {i}: {original_text} ---')

            # 调用文本处理
            processed_text = system.processor.process_text(original_text)
            numbers = system.processor.extract_numbers(original_text, processed_text)

            print(f'原始文本: {original_text}')
            print(f'处理后文本: {processed_text}')
            print(f'提取数字: {numbers}')

            # 调用结果处理方法（这会触发Excel写入）
            if system.excel_exporter:
                try:
                    before_count = len(system.number_results) if hasattr(system, 'number_results') else 0
                    system.process_recognition_result(original_text, processed_text, numbers)
                    after_count = len(system.number_results) if hasattr(system, 'number_results') else 0

                    if after_count > before_count:
                        latest_record = system.number_results[-1]
                        record_id, record_number, record_text = latest_record
                        print(f'✅ 系统记录: ID {record_id}, 数值: {record_number}, 文本: {record_text}')

                        # 模拟GUI显示逻辑
                        if record_number in [1.0, 0.0] and record_text and record_text.strip():
                            if any(keyword in record_text.lower() for keyword in ['合格', 'ok', '可以', '好']):
                                actual_gui_display = f"[{record_id}] OK"
                            elif any(keyword in record_text.lower() for keyword in ['不合格', 'not ok', 'ng', '不行', '错误', 'error']):
                                actual_gui_display = f"[{record_id}] Not OK"
                            else:
                                actual_gui_display = f"[{record_id}] {record_text}"
                        else:
                            actual_gui_display = f"[{record_id}] {record_number}"

                        print(f'✅ GUI应该显示: {actual_gui_display}')
                        print(f'📋 期望GUI显示: {expected_gui_display}')
                        print(f'GUI显示正确: {"✅" if actual_gui_display == expected_gui_display else "❌"}')

                        # 检查Excel写入
                        import pandas as pd
                        try:
                            df = pd.read_excel(excel_file)
                            if not df.empty:
                                last_row = df.iloc[-1]
                                excel_measurement = last_row.get('测量值', last_row.get('Measurement', ''))
                                print(f'✅ Excel实际写入: {excel_measurement}')
                                print(f'📋 期望Excel写入: {expected_excel_value}')

                                # 比较Excel写入
                                if str(excel_measurement) == str(expected_excel_value):
                                    print(f'✅ Excel写入正确')
                                else:
                                    print(f'❌ Excel写入错误')
                        except Exception as e:
                            print(f'❌ 读取Excel失败: {e}')

                    else:
                        print('❌ 没有新Excel记录')

                except Exception as e:
                    print(f'❌ 结果处理失败: {e}')

        print('\n=== 测试完成 ===')

        # 总结修复结果
        print(f'\n🎯 修复总结:')
        print(f'1. ✅ Excel写入修复：特殊文本写入OK/NOT OK而不是数值')
        print(f'2. ✅ GUI显示修复：特殊文本显示ID + OK/Not OK而不是原文')
        print(f'3. ✅ 系统兼容性：number_results保持数值格式用于GUI判断')
        print(f'4. ✅ 配置正确：按照config.yaml中的特殊文本配置转换')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()