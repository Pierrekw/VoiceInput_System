#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI显示修复 - 验证特殊文本显示原文而不是数值
"""

import sys
import os

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print('=== 测试GUI显示修复 - 特殊文本显示原文 ===')

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
            ('五 点 六 七', [5.67]),    # 小数
        ]

        print('\n=== 开始测试 ===')

        for i, (original_text, expected_numbers) in enumerate(test_cases, 1):
            print(f'\n--- 测试 {i}: {original_text} ---')

            # 调用文本处理
            processed_text = system.processor.process_text(original_text)
            numbers = system.processor.extract_numbers(original_text, processed_text)

            print(f'原始文本: {original_text}')
            print(f'处理后文本: {processed_text}')
            print(f'提取数字: {numbers}')
            print(f'预期数字: {expected_numbers}')
            print(f'数字匹配: {"✅" if numbers == expected_numbers else "❌"}')

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
                        print(f'✅ Excel记录: ID {record_id}, 数值: {record_number}, 文本: {record_text}')

                        # 模拟新的GUI显示逻辑
                        if record_number in [1.0, 0.0] and record_text and record_text.strip():
                            # 特殊文本显示原文而不是数值
                            display_text = f"[{record_id}] {record_text}"
                            print(f'✅ GUI应该显示（特殊文本）: {display_text}')
                        else:
                            # 普通数字显示数值
                            display_text = f"[{record_id}] {record_number}"
                            print(f'✅ GUI应该显示（普通数字）: {display_text}')

                        # 验证显示格式是否符合预期
                        if original_text in ['合格', '不合格']:
                            expected_display = f"[{record_id}] {original_text}"
                            if display_text == expected_display:
                                print(f'✅ 特殊文本显示格式正确')
                            else:
                                print(f'❌ 特殊文本显示格式错误，期望: {expected_display}, 实际: {display_text}')
                        elif numbers:
                            expected_display = f"[{record_id}] {numbers[0]}"
                            if display_text == expected_display:
                                print(f'✅ 数字显示格式正确')
                            else:
                                print(f'❌ 数字显示格式错误，期望: {expected_display}, 实际: {display_text}')

                    else:
                        print('❌ 没有新Excel记录')

                except Exception as e:
                    print(f'❌ 结果处理失败: {e}')
            else:
                print('❌ Excel导出器未初始化')

        print('\n=== 测试完成 ===')

        # 检查最终的number_results
        if hasattr(system, 'number_results') and system.number_results:
            print(f'\n📊 最终记录结果:')
            for record_id, number_value, text in system.number_results:
                # 模拟GUI显示逻辑
                if number_value in [1.0, 0.0] and text and text.strip():
                    display_text = f"[{record_id}] {text}"
                else:
                    display_text = f"[{record_id}] {number_value}"

                print(f'  {display_text} <- GUI显示格式')

                # 检查特殊文本
                if number_value == 1.0 and ('合格' in text or '可以' in text or 'ok' in text.lower()):
                    print(f'    ✅ 正确识别为OK，显示原文')
                elif number_value == 0.0 and ('不合格' in text or '不行' in text or 'error' in text.lower() or 'ng' in text.lower()):
                    print(f'    ✅ 正确识别为NOT OK，显示原文')
                elif number_value > 0:
                    print(f'    ✅ 正确识别为数字')
        else:
            print('\n❌ 没有记录结果')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()