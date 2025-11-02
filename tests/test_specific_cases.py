#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户指定的具体案例
"""

from text_processor import TextProcessor

def test_specific_cases():
    """测试用户指定的具体案例"""

    print("🔍 测试用户指定的具体案例")
    print("=" * 60)

    processor = TextProcessor()

    # 用户指定的具体案例
    test_cases = [
        {
            "input": "一百二十三点二三",
            "question": "测试: 一百二十三点二三"
        },
        {
            "input": "二百一十三点七四",
            "question": "测试: 二百一十三点七四"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['question']}")
        print(f"输入: '{test_case['input']}'")

        # 测试process_text
        processed = processor.process_text(test_case['input'])
        print(f"process_text结果: '{processed}'")

        # 测试extract_numbers
        numbers = processor.extract_numbers(test_case['input'], processed)
        print(f"extract_numbers结果: {numbers}")

        # 模拟显示逻辑
        if numbers and len(numbers) > 0:
            display_result = f"{processed} -> {numbers[0]}"
        else:
            display_result = processed
        print(f"显示结果: '{display_result}'")

if __name__ == "__main__":
    test_specific_cases()