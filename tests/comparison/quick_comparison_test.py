# -*- coding: utf-8 -*-
"""
快速对比测试 - 简化版
用于快速验证两个系统的基本功能差异
"""

import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from audio_capture_v import extract_measurements

def test_number_extraction():
    """测试数字提取功能"""
    print("🔢 测试数字提取功能")
    print("-" * 50)

    test_cases = [
        ("温度二十五点五度", [25.5]),
        ("压力一百二十帕斯卡", [120.0]),
        ("湿度百分之七十五", [75.0]),
        ("负十度", [-10.0]),
        ("零点零零一", [0.001]),
        ("一百二十和三百四十五", [120.0, 345.0]),
        ("温度25.5度湿度36度", [25.5, 36.0]),
        ("无数字文本", []),
        ("", []),
    ]

    passed = 0
    total = len(test_cases)

    for text, expected in test_cases:
        try:
            result = extract_measurements(text)
            is_correct = result == expected
            if is_correct:
                passed += 1

            status = "✅" if is_correct else "❌"
            print(f"{status} '{text}' -> {result} (期望: {expected})")

        except Exception as e:
            print(f"❌ '{text}' -> 错误: {e}")

    accuracy = (passed / total) * 100
    print(f"\n📊 数字提取准确率: {accuracy:.1f}% ({passed}/{total})")
    return accuracy

def test_print_function():
    """测试Print功能识别"""
    print("\n🖨️ 测试Print功能识别")
    print("-" * 50)

    test_cases = [
        ("Print 当前状态正常", True, "当前状态正常"),
        ("Print system status", True, "system status"),
        ("Print 温度二十五点五度", True, "温度二十五点五度"),
        ("当前状态正常", False, None),
        ("system is running", False, None),
        ("print 警告信息", True, "警告信息"),
    ]

    passed = 0
    total = len(test_cases)

    def handle_print_function(text: str):
        """处理Print功能"""
        text_lower = text.lower().strip()
        if text_lower.startswith('print '):
            return True, text[6:].strip()
        elif 'print' in text_lower:
            parts = text.split('print', 1)
            if len(parts) == 2:
                return True, parts[1].strip()
        return False, None

    for text, expected_is_print, expected_content in test_cases:
        try:
            is_print, content = handle_print_function(text)
            is_correct = (is_print == expected_is_print and content == expected_content)
            if is_correct:
                passed += 1

            status = "✅" if is_correct else "❌"
            print(f"{status} '{text}' -> Print: {is_print}, 内容: '{content}'")

        except Exception as e:
            print(f"❌ '{text}' -> 错误: {e}")

    accuracy = (passed / total) * 100
    print(f"\n📊 Print功能识别准确率: {accuracy:.1f}% ({passed}/{total})")
    return accuracy

def test_performance():
    """测试基本性能"""
    print("\n⚡ 测试基本性能")
    print("-" * 50)

    test_texts = [
        "温度二十五点五度",
        "压力一百二十帕斯卡",
        "湿度百分之七十五",
        "测量值为十二点五和三十三点八",
    ]

    # 测试单个处理时间
    times = []
    for text in test_texts:
        start = time.time()
        result = extract_measurements(text)
        end = time.time()
        times.append(end - start)
        print(f"'{text}' -> {result} (耗时: {(end-start)*1000:.1f}ms)")

    avg_time = sum(times) / len(times)
    print(f"\n📊 平均处理时间: {avg_time*1000:.1f}ms")
    return avg_time

def run_quick_comparison():
    """运行快速对比测试"""
    print("🚀 开始快速对比测试")
    print("=" * 60)
    print("测试系统: 基于 extract_measurements 函数的数字提取")
    print("对比目标: 验证基本功能正确性")
    print("=" * 60)

    # 运行各项测试
    number_accuracy = test_number_extraction()
    print_accuracy = test_print_function()
    avg_time = test_performance()

    # 生成简要报告
    print("\n" + "=" * 60)
    print("📋 快速对比测试报告")
    print("=" * 60)
    print(f"数字提取准确率: {number_accuracy:.1f}%")
    print(f"Print功能识别准确率: {print_accuracy:.1f}%")
    print(f"平均处理时间: {avg_time*1000:.1f}ms")
    print(f"整体功能状态: {'✅ 正常' if number_accuracy > 80 else '⚠️ 需要优化'}")

    # 性能评估
    if avg_time < 0.01:  # 小于10ms
        performance_level = "优秀"
    elif avg_time < 0.05:  # 小于50ms
        performance_level = "良好"
    elif avg_time < 0.1:   # 小于100ms
        performance_level = "一般"
    else:
        performance_level = "需要优化"

    print(f"性能评估: {performance_level}")
    print("=" * 60)

    return {
        'number_accuracy': number_accuracy,
        'print_accuracy': print_accuracy,
        'avg_time': avg_time,
        'overall_status': '正常' if number_accuracy > 80 else '需要优化',
        'performance_level': performance_level
    }

if __name__ == "__main__":
    try:
        results = run_quick_comparison()
        print("\n✅ 快速对比测试完成！")

        # 保存结果到文件
        result_file = Path("tests/comparison/quick_test_results.txt")
        result_file.parent.mkdir(parents=True, exist_ok=True)

        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"快速对比测试结果\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数字提取准确率: {results['number_accuracy']:.1f}%\n")
            f.write(f"Print功能识别准确率: {results['print_accuracy']:.1f}%\n")
            f.write(f"平均处理时间: {results['avg_time']*1000:.1f}ms\n")
            f.write(f"整体功能状态: {results['overall_status']}\n")
            f.write(f"性能评估: {results['performance_level']}\n")

        print(f"📁 结果已保存到: {result_file}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()