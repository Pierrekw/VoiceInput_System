#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文本处理的具体问题
"""

from text_processor_clean import TextProcessor

def test_text_processing_issues():
    """测试用户报告的具体文本处理问题"""

    print("🔍 测试用户报告的文本处理问题")
    print("=" * 60)

    processor = TextProcessor()

    # 用户报告的具体问题
    test_cases = [
        {
            "input": "幺幺三",
            "expected": "113",
            "issue": "无法识别幺幺三=113"
        },
        {
            "input": "一百二十三",
            "expected": "123",
            "issue": "一百二十三识别有错误"
        },
        {
            "input": "七十三点八四",
            "expected": "73.84",
            "issue": "末尾数字的识别存在遗漏"
        },
        {
            "input": "你好",
            "expected": "你好",
            "issue": "非数字文本应该正确显示，不显示上次的数字"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['issue']}")
        print(f"输入: '{test_case['input']}'")
        print(f"预期: '{test_case['expected']}'")

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

        # 检查是否正确
        if test_case['expected'] in display_result:
            print("✅ 通过")
        else:
            print("❌ 失败")

if __name__ == "__main__":
    test_text_processing_issues()