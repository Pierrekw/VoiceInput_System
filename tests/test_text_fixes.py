#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试torch 2.3.1+cpu版本的文本修复效果
"""

from text_processor_clean import TextProcessor

def test_torch_cpu_fixes():
    """测试torch 2.3.1+cpu版本的具体修复效果"""

    print("🔧 测试torch 2.3.1+cpu版本文本修复效果")
    print("=" * 60)

    processor = TextProcessor()

    # 测试用例：针对之前报告的问题
    test_cases = [
        # 问题1: "幺"不能识别成"1"
        {
            "input": "幺",
            "expected": "1",
            "description": "修复'幺'不能识别成'1'的问题"
        },
        {
            "input": "幺三五",
            "expected": "135",
            "description": "修复多位数中'幺'的识别"
        },

        # 问题2: "一百十三点二三"被误识别成103.23
        {
            "input": "一百十三点二三",
            "expected": "113.23",
            "description": "修复'一百十三点二三'被误识别成103.23"
        },
        {
            "input": "一百一十三",
            "expected": "113",
            "description": "验证'一百一十三'正确转换"
        },

        # 问题3: 无意义文本过滤
        {
            "input": "嗯",
            "expected": "",
            "description": "过滤无意义文本'嗯'"
        },
        {
            "input": "哦",
            "expected": "",
            "description": "过滤无意义文本'哦'"
        },
        {
            "input": "啊",
            "expected": "",
            "description": "过滤无意义文本'啊'"
        },
        {
            "input": "那个",
            "expected": "",
            "description": "过滤无意义文本'那个'"
        },

        # 问题4: 重复显示修复
        {
            "input": "25 103.23",
            "expected": "103.23",
            "description": "修复重复显示'25 103.23'"
        },
        {
            "input": "30 37.84 30 37.84",
            "expected": "37.84",
            "description": "修复复杂重复显示"
        },

        # 其他数字识别测试
        {
            "input": "十点五",
            "expected": "10.5",
            "description": "修复'十点五'变成1.5的问题"
        },
        {
            "input": "二十点三",
            "expected": "20.3",
            "description": "修复'二十点三'变成2.3的问题"
        },
        {
            "input": "三十点七",
            "expected": "30.7",
            "description": "修复'三十点七'变成3.7的问题"
        }
    ]

    print(f"📝 共测试 {len(test_cases)} 个案例\n")

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        input_text = test_case["input"]
        expected = test_case["expected"]
        description = test_case["description"]

        # 处理文本
        result = processor.process_text(input_text)

        # 检查结果
        success = result == expected

        print(f"测试 {i:2d}: {description}")
        print(f"  输入: '{input_text}'")
        print(f"  预期: '{expected}'")
        print(f"  实际: '{result}'")

        if success:
            print(f"  ✅ 通过")
            passed += 1
        else:
            print(f"  ❌ 失败")
            failed += 1

        print()

    # 统计结果
    print("=" * 60)
    print(f"📊 测试结果统计:")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  📈 成功率: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 所有测试通过！torch 2.3.1+cpu版本的文本修复工作正常。")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要进一步修复。")

    return failed == 0

if __name__ == "__main__":
    test_torch_cpu_fixes()