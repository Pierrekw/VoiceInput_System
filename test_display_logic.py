#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实时显示逻辑
"""

from text_processor_clean import TextProcessor

def test_display_logic():
    """测试显示逻辑"""
    processor = TextProcessor()

    test_cases = [
        "三十七点五",  # 有数字
        "今天天气很好",  # 没有数字
        "一百二十三",  # 有数字
        "你好世界",  # 没有数字
    ]

    print("测试实时显示逻辑")
    print("=" * 30)

    for text in test_cases:
        processed = processor.process_text(text)
        numbers = processor.extract_numbers(processed)

        print(f"\n{text}")
        if numbers:
            print(f"{numbers[0]}")
        else:
            print(f"{processed}")

if __name__ == "__main__":
    test_display_logic()