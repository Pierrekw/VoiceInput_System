#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户日志中的实际案例
"""

from text_processor_clean import TextProcessor

def test_user_log_cases():
    """测试用户日志中的实际识别案例"""

    print("🔍 测试用户日志中的实际案例")
    print("=" * 60)

    processor = TextProcessor()

    # 用户日志中的实际案例
    test_cases = [
        {
            "input": "十三点三三",
            "expected_number": 13.33,
            "description": "用户日志: 十三点三三 -> 数字: 13.33"
        },
        {
            "input": "三十五点八四",
            "expected_number": 35.84,
            "description": "用户日志: 三十五点八四 -> 数字: 35.84"
        },
        {
            "input": "幺零三",
            "expected_number": 103,
            "description": "用户日志: 幺零三 -> 103"
        },
        {
            "input": "幺幺",
            "expected_number": 11,
            "description": "用户日志: 幺幺 -> 但显示58，需要修复"
        },
        {
            "input": "五十八点八五",
            "expected_number": 58.85,
            "description": "用户日志: 五十八点八五 -> 数字: 58.85"
        },
        {
            "input": "十四点七三",
            "expected_number": 14.73,
            "description": "用户日志: 十四点七三 -> 数字: 14.73"
        },
        {
            "input": "七十五点八八",
            "expected_number": 75.88,
            "description": "用户日志: 七十五点八八 -> 数字: 75.88"
        },
        {
            "input": "八四点九五",
            "expected_number": 84.95,
            "description": "用户日志: 八四点九五 -> 数字: 84.95"
        },
        {
            "input": "一零三点一一四八",
            "expected_number": 103.1148,
            "description": "用户日志: 一零三点一一四八 -> 数字: 103.1148"
        },
        {
            "input": "幺幺三",
            "expected_number": 113,
            "description": "用户日志: 幺幺三 -> 但显示101.13，需要修复"
        },
        {
            "input": "幺幺三点幺幺三",
            "expected_number": None,
            "description": "用户日志: 幺幺三点幺幺三 -> 复杂案例"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"输入: '{test_case['input']}'")

        # 测试process_text
        processed = processor.process_text(test_case['input'])
        print(f"process_text结果: '{processed}'")

        # 测试extract_numbers
        numbers = processor.extract_numbers(test_case['input'], processed)
        print(f"extract_numbers结果: {numbers}")

        # 检查是否正确
        expected = test_case['expected_number']
        if expected is not None:
            if numbers and len(numbers) > 0 and abs(numbers[0] - expected) < 0.001:
                print("✅ 数字提取正确")
            else:
                print(f"❌ 数字提取错误，期望: {expected}")
        else:
            if numbers:
                print(f"📊 提取到数字: {numbers[0]}")
            else:
                print("📝 非数字文本")

if __name__ == "__main__":
    test_user_log_cases()