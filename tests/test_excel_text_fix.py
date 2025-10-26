#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel写入修复 - 验证特殊文本在Excel中显示为OK/Not OK而不是数值
"""

import sys
import os
import pandas as pd

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print('=== 测试Excel写入修复 - 特殊文本显示OK/Not OK ===')

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
            ('一 二 三', [123.0]),        # 纯数字
            ('合格', []),              # 特殊文本 - OK
            ('不合格', []),            # 特殊文本 - Not OK
            ('三 点 五', [3.5]),         # 小数
        ]

        print('\n=== 开始测试 ===')

        # 获取Excel文件路径
        excel_file = system.excel_exporter.filename
        print(f'📄 Excel文件: {excel_file}')

        for i, (original_text, expected_numbers) in enumerate(test_cases, 1):
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
                    # 记录处理前的number_results数量
                    before_count = len(system.number_results) if hasattr(system, 'number_results') else 0

                    system.process_recognition_result(original_text, processed_text, numbers)

                    # 记录处理后的number_results数量
                    after_count = len(system.number_results) if hasattr(system, 'number_results') else 0

                    # 检查是否有新记录
                    if after_count > before_count:
                        latest_record = system.number_results[-1]
                        record_id, record_number, record_text = latest_record
                        print(f'✅ 系统记录: ID {record_id}, 数值: {record_number}, 文本: {record_text}')

                        # 检查Excel中的实际内容
                        try:
                            df = pd.read_excel(excel_file)
                            if not df.empty:
                                last_row = df.iloc[-1]
                                # 尝试中文和英文列名
                                excel_measurement = last_row.get('测量值', last_row.get('Measurement', ''))
                                excel_text = last_row.get('原始语音', last_row.get('Original Text', ''))

                                print(f'✅ Excel中的测量值: {excel_measurement}')
                                print(f'✅ Excel中的原文: {excel_text}')

                                # 验证特殊文本是否正确写入Excel
                                if original_text in ['合格', '不合格']:
                                    expected_excel_value = 'OK' if original_text == '合格' else 'NOT OK'
                                    if excel_measurement == expected_excel_value:
                                        print(f'✅ Excel写入正确：特殊文本显示为 {excel_measurement}')
                                    else:
                                        print(f'❌ Excel写入错误：期望 {expected_excel_value}，实际 {excel_measurement}')
                                elif numbers:
                                    if excel_measurement == numbers[0]:
                                        print(f'✅ Excel写入正确：数字显示为 {excel_measurement}')
                                    else:
                                        print(f'❌ Excel写入错误：期望 {numbers[0]}，实际 {excel_measurement}')
                        except Exception as e:
                            print(f'❌ 读取Excel失败: {e}')

                    else:
                        print('❌ 没有新Excel记录')

                except Exception as e:
                    print(f'❌ 结果处理失败: {e}')
            else:
                print('❌ Excel导出器未初始化')

        print('\n=== 测试完成 ===')

        # 最终检查Excel内容
        try:
            print(f'\n📊 最终Excel内容:')
            df = pd.read_excel(excel_file)
            if not df.empty:
                for idx, row in df.iterrows():
                    measurement = row.get('测量值', row.get('Measurement', ''))
                    original_text = row.get('原始语音', row.get('Original Text', ''))
                    print(f'  行 {idx+1}: 测量值={measurement}, 原文="{original_text}"')
            else:
                print('❌ Excel文件为空')
        except Exception as e:
            print(f'❌ 读取最终Excel内容失败: {e}')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()