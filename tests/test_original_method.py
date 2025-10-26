#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试原有文本处理方法的效果
"""

from text_processor_clean import TextProcessor

def test_original_methods():
    """测试原有的文本处理方法"""

    print("🔍 测试原有文本处理方法")
    print("=" * 60)

    processor = TextProcessor()

    test_cases = [
        "一百一十三点二三",
        "一百十三点二三",
        "十点五",
        "三十点七",
        "一二三",
        "三十五点六",
        "一千二百三十四"
    ]

    for test_input in test_cases:
        print(f"\n📝 测试输入: '{test_input}'")
        print("-" * 30)

        # 测试原有的 chinese_to_arabic_number 方法
        result1 = processor.chinese_to_arabic_number(test_input)
        print(f"chinese_to_arabic_number: '{result1}'")

        # 测试新增的 convert_chinese_numbers_in_text 方法
        result2 = processor.convert_chinese_numbers_in_text(test_input)
        print(f"convert_chinese_numbers_in_text: '{result2}'")

        # 测试完整的 process_text 流程
        result3 = processor.process_text(test_input)
        print(f"process_text: '{result3}'")

if __name__ == "__main__":
    test_original_methods()