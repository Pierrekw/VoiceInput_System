#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的Excel写入功能
验证数字提取、特殊文本处理和Excel写入是否正常
"""

import sys
import os
import time

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print('=== 测试重构后的Excel写入功能 ===')

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统实例但不启动识别
        system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=False,
            debug_mode=True
        )

        print(f'✅ 系统初始化成功')
        print(f'✅ Excel导出器状态: {"已初始化" if system.excel_exporter else "未初始化"}')

        # 测试用例
        test_cases = [
            ('一 二 三', '123', [123.0]),      # 纯数字
            ('合格', '合格', []),              # 特殊文本 - OK
            ('不合格', '不合格', []),          # 特殊文本 - Not OK
            ('三 点 五', '3.5', [3.5]),       # 小数
            ('一百二十三', '123', [123.0]),    # 中文数字
        ]

        print('\n=== 开始测试 ===')

        for i, (original_text, expected_processed, expected_numbers) in enumerate(test_cases, 1):
            print(f'\n--- 测试 {i}: {original_text} ---')

            # 调用文本处理
            processed_text = system.processor.process_text(original_text)
            print(f'原始文本: {original_text}')
            print(f'处理后文本: {processed_text}')
            print(f'预期处理: {expected_processed}')
            print(f'匹配程度: {"✅" if processed_text == expected_processed else "❌"}')

            # 调用数字提取
            numbers = system.processor.extract_numbers(original_text, processed_text)
            print(f'提取数字: {numbers}')
            print(f'预期数字: {expected_numbers}')
            print(f'数字匹配: {"✅" if numbers == expected_numbers else "❌"}')

            # 调用结果处理方法（这会触发Excel写入）
            if system.excel_exporter:
                try:
                    system.process_recognition_result(original_text, processed_text, numbers)
                    print('✅ 结果处理方法调用成功')
                except Exception as e:
                    print(f'❌ 结果处理方法调用失败: {e}')
            else:
                print('❌ Excel导出器未初始化')

            time.sleep(0.2)  # 短暂延迟

        print('\n=== 测试完成 ===')

        # 检查number_results
        if hasattr(system, 'number_results') and system.number_results:
            print(f'\n📊 数字结果记录:')
            for record_id, number_value, text in system.number_results:
                print(f'  ID {record_id}: {number_value} -> "{text}"')
        else:
            print('\n❌ 没有数字结果记录')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()