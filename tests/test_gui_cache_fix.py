#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI缓存问题修复
"""

from text_processor_clean import TextProcessor

def test_gui_cache_fix():
    """测试GUI缓存问题修复"""

    print("🔍 测试GUI缓存问题修复")
    print("=" * 50)

    processor = TextProcessor()

    # 模拟用户报告的问题场景
    test_cases = [
        {
            "input": "其实小米",  # 非数字文本
            "description": "非数字文本：其实小米"
        },
        {
            "input": "十三点一醒三点二十",  # 非数字文本
            "description": "非数字文本：十三点一醒三点二十"
        },
        {
            "input": "三十四点一寸",  # 非数字文本
            "description": "非数字文本：三十四点一寸"
        },
        {
            "input": "十三点一四",  # 数字文本
            "description": "数字文本：十三点一四"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"输入: '{test_case['input']}'")

        # 测试文本处理
        processed = processor.process_text(test_case['input'])
        print(f"处理后: '{processed}'")

        # 测试数字提取
        numbers = processor.extract_numbers(test_case['input'], processed)
        print(f"提取数字: {numbers}")

        # 模拟GUI显示逻辑
        if numbers and len(numbers) > 0:
            display_result = f"应该显示数字格式: [{i}] {numbers[0]}"
            print(f"✅ {display_result}")
        else:
            display_result = f"应该显示文本: {processed}"
            print(f"✅ {display_result}")

if __name__ == "__main__":
    test_gui_cache_fix()