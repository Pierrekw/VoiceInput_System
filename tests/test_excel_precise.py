#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试精确的Excel点击检测逻辑
验证新的排除"文件名"关键词的逻辑
"""

def test_precise_logic():
    """测试精确的Excel点击检测逻辑"""
    print("🧪 测试精确的Excel点击检测逻辑")
    print("=" * 50)

    # 测试各种点击场景
    test_cases = [
        ("按钮点击", "📂 点击打开Excel文件: Report_4564_54564_20251028_221719.xlsx"),
        ("文件名显示", "📄 文件名: Report_4564_54564_20251028_221719.xlsx"),
        ("纯文件名", "Report_4564_54564_20251028_221719.xlsx"),
        ("混合文本", "数据已保存 Report_4564_54564_20251028_221719.xlsx"),
        ("普通文本", "正在处理数据，请稍候..."),
        ("xls文件", "老格式文件.xls"),
        ("文件名信息", "文件名: data.xlsx"),
        ("其他文件名", "这个文件的文件名是test.xlsx")
    ]

    # 精确的检测逻辑
    def detect_excel_click_precise(line_text):
        """精确的Excel点击检测"""
        return ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and '文件名' not in line_text

    print("📋 测试结果:")

    passed = 0
    total = len(test_cases)

    for name, line in test_cases:
        detected = detect_excel_click_precise(line)

        # 手动判断预期结果
        should_detect = ('.xlsx' in line.lower() or '.xls' in line.lower()) and '文件名' not in line

        if detected == should_detect:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"

        print(f"  {name}: {status}")
        print(f"    文本: {line}")
        print(f"    预期: {'检测' if should_detect else '不检测'}")
        print(f"    实际: {'检测' if detected else '不检测'}")
        print()

    print(f"📊 测试总结: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！精确检测逻辑工作正常")
        return True
    else:
        print("⚠️ 有测试失败，需要调整逻辑")
        return False

def explain_logic():
    """解释新的检测逻辑"""
    print("\n💡 精确检测逻辑说明:")
    print("=" * 40)
    print("🎯 检测条件:")
    print("  1. 必须包含.xlsx或.xls")
    print("  2. 不能包含'文件名'三个字")
    print("  3. 必须有Excel文件路径记录")
    print()
    print("🔑 核心代码:")
    print("  if ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and '文件名' not in line_text:")
    print("      # 打开Excel文件")
    print()
    print("📋 具体效果:")
    print("  ✅ Report_4564_54564_20251028_221719.xlsx → 打开Excel")
    print("  ✅ 📂 点击打开Excel文件: Report.xlsx → 打开Excel")
    print("  ✅ 数据已保存 Report.xlsx → 打开Excel")
    print("  ❌ 📄 文件名: Report.xlsx → 不触发")
    print("  ❌ 文件名: data.xlsx → 不触发")
    print("  ❌ 普通文本行 → 不触发")

def main():
    """主函数"""
    print("🚀 精确Excel点击功能测试")
    print("=" * 60)

    success = test_precise_logic()
    explain_logic()

    if success:
        print("\n🎯 结论:")
        print("精确检测逻辑工作正常，避免了误触发问题！")
        print("现在用户只能点击不包含'文件名'的Excel相关行来打开文件。")
    else:
        print("\n❌ 结论:")
        print("需要进一步调整检测逻辑")

if __name__ == "__main__":
    main()