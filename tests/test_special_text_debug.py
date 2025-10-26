#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试特殊文本处理 - 查看special_text_match的值
"""

import sys
import os

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print('=== 调试特殊文本处理 ===')

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
        test_cases = ['合格', '不合格']

        for original_text in test_cases:
            print(f'\n--- 测试: {original_text} ---')

            # 调用文本处理
            processed_text = system.processor.process_text(original_text)
            numbers = system.processor.extract_numbers(original_text, processed_text)

            print(f'原始文本: {original_text}')
            print(f'处理后文本: {processed_text}')
            print(f'提取数字: {numbers}')

            # 检查特殊文本匹配
            special_text_match = system._check_special_text(processed_text)
            print(f'special_text_match: {special_text_match}')
            print(f'special_text_match类型: {type(special_text_match)}')

            # 检查excel_data应该是什么
            if special_text_match:
                text_value = special_text_match  # 直接使用OK/Not OK文本
                excel_data = (text_value, original_text, special_text_match)
                print(f'excel_data: {excel_data}')
            else:
                print('❌ 没有匹配到特殊文本')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()