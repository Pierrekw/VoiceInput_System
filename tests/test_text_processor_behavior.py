#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试text_processor.py如何处理不同类型的输入
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_text_processor():
    """测试文本处理器的行为"""
    print("🧪 测试TextProcessor处理不同输入的行为")
    print("=" * 60)

    try:
        from text_processor import TextProcessor
        processor = TextProcessor()

        # 测试用例
        test_cases = [
            # 基本数字
            "二百",
            "三百",
            "一千一百",

            # 带空格的数字
            "二 百",
            "三 百",
            "一 千 一 百",

            # 命令形式
            "切换二百",
            "设置序号三百",
            "切换到一百",

            # 混合情况
            "二百点五",
            "标准二百",
            "序号三百",

            # 小数字
            "一",
            "二",
            "三",
            "五",
            "八",
            "十"
        ]

        print(f"{'输入文本':<20} {'处理后':<15} {'提取数字':<10} {'说明'}")
        print("-" * 70)

        for text in test_cases:
            # 处理文本
            processed = processor.process_text(text)

            # 提取数字
            numbers = processor.extract_numbers(processed)
            numbers_str = str(numbers[0]) if numbers else "无"

            # 判断行为
            if text in ["切换二百", "设置序号三百", "切换到一百"]:
                behavior = "命令"
            elif any(keyword in text for keyword in ["切换", "设置", "序号"]):
                behavior = "命令(未匹配)"
            elif numbers:
                if any(text == num for num in ["一", "二", "三", "五", "八", "十"]):
                    behavior = "小数字"
                else:
                    behavior = "测量数据"
            else:
                behavior = "其他"

            print(f"{text:<20} {processed:<15} {numbers_str:<10} {behavior}")

        print("\n📊 处理规则分析:")
        print("1. 基本数字(>9): 转换为阿拉伯数字，作为测量数据")
        print("2. 带空格数字: 去除空格后处理")
        print("3. 命令形式: 包含命令词，作为语音命令")
        print("4. 小数字(≤9): 保留中文，但仍可提取")
        print("5. 小数: 总是转换为阿拉伯数字")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_command_matching():
    """测试命令匹配的边界情况"""
    print("\n🧪 测试命令匹配边界情况")
    print("=" * 60)

    try:
        from text_processor import VoiceCommandProcessor
        from config_loader import ConfigLoader

        processor = VoiceCommandProcessor()
        config = ConfigLoader()

        # 获取标准序号命令
        commands = {
            "standard_id": config.get_standard_id_commands()
        }

        # 测试用例
        test_cases = [
            "二百",           # 纯数字
            "切换二百",       # 匹配命令
            "设置二百",       # 部分匹配
            "二百号",         # 部分匹配
            "二零零",         # 不同表达
            "200",           # 阿拉伯数字
            "序号200",        # 混合
        ]

        print(f"{'输入文本':<15} {'匹配结果':<15} {'置信度':<10}")
        print("-" * 45)

        for text in test_cases:
            result = processor.match_command(text, commands)
            result_str = result if result else "unknown"
            print(f"{text:<15} {result_str:<15} {'-':<10}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_processor()
    test_command_matching()