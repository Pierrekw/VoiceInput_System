#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文数字识别错误的具体案例
"""

from text_processor_clean import TextProcessor

def test_chinese_number_errors():
    """测试中文数字识别错误的具体案例"""

    print("🔍 测试中文数字识别错误的具体案例")
    print("=" * 60)

    processor = TextProcessor()

    # 用户报告的错误案例
    test_cases = [
        {
            "input": "一百十三",
            "expected": 113,
            "actual_error": 103,
            "description": "用户: 一百十三 -> 总是被出103"
        },
        {
            "input": "二百十三",
            "expected": 213,
            "actual_error": 203,
            "description": "用户: 二百十三 -> 变成203"
        },
        {
            "input": "三百十三",
            "expected": 313,
            "description": "测试: 三百十三"
        },
        {
            "input": "一百二十三",
            "expected": 123,
            "description": "对比: 一百二十三 (这个正确)"
        },
        {
            "input": "二百二十三",
            "expected": 223,
            "description": "对比: 二百二十三"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"输入: '{test_case['input']}'")

        # 测试process_text
        processed = processor.process_text(test_case['input'])
        print(f"process_text结果: '{processed}'")

        # 测试extract_numbers
        numbers = processor.extract_numbers(test_case['input'], processed)
        print(f"extract_numbers结果: {numbers}")

        # 测试chinese_to_arabic_number
        direct_result = processor.chinese_to_arabic_number(test_case['input'])
        print(f"chinese_to_arabic_number结果: '{direct_result}'")

        # 检查是否正确
        expected = test_case.get('expected')
        if expected:
            if numbers and len(numbers) > 0 and abs(numbers[0] - expected) < 0.001:
                print("✅ 数字提取正确")
            else:
                actual_error = test_case.get('actual_error')
                if actual_error and numbers and len(numbers) > 0 and abs(numbers[0] - actual_error) < 0.001:
                    print(f"❌ 确认出现错误: 期望{expected}，实际{actual_error}")
                else:
                    print(f"❌ 数字提取错误，期望: {expected}，实际: {numbers[0] if numbers else 'None'}")

        # 测试cn2an直接转换
        try:
            import cn2an
            cn2an_result = cn2an.cn2an(test_case['input'], "smart")
            print(f"cn2an直接转换结果: '{cn2an_result}'")
        except:
            print("cn2an转换失败")

if __name__ == "__main__":
    test_chinese_number_errors()