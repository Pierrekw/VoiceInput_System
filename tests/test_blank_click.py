#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试空白区域点击行为
分析为什么点击Excel下方空白会触发打开
"""

def test_line_selection():
    """测试行选择行为"""
    print("🔍 测试QTextCursor.LineUnderCursor行为")
    print("=" * 50)

    # 模拟各种点击场景
    scenarios = [
        ("Excel文件行", "Report_12345_6789.xlsx"),
        ("Excel按钮行", "📂 点击打开Excel文件: Report_12345_6789.xlsx"),
        ("空白行", ""),
        ("普通文本", "正在处理数据"),
        ("Excel信息行", "📄 文件名: Report_12345_6789.xlsx"),
        ("Excel混合行", "数据已保存 Report_12345_6789.xlsx")
    ]

    for name, content in scenarios:
        print(f"\n场景: {name}")
        print(f"内容: '{content}'")

        # 模拟检测逻辑
        line_text = content.strip()

        # 当前行检测
        current_line_has_excel = ('.xlsx' in line_text.lower() or '.xls' in line_text.lower())
        current_line_has_fileinfo = '文件名' in line_text

        # 如果是空行，可能获取到前一行（这个是问题的关键）
        if not line_text:
            print("  → 这是空行，可能获取到前一行内容")
            print("  ⚠️ 这就是误触发的原因！")

        print(f"  当前行检测: Excel={current_line_has_excel}, 有文件名={current_line_has_fileinfo}")

        # 简化逻辑判断
        will_trigger_old = ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and not current_line_has_fileinfo
        will_trigger_new = ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and '文件名' not in line_text

        print(f"  简化逻辑: 会触发={will_trigger_old}")
        print(f"  精确逻辑: 会触发={will_trigger_new}")

def analyze_click_behavior():
    """分析点击行为"""
    print("\n💡 点击行为分析:")
    print("=" * 40)
    print("❌ 问题原因:")
    print("  1. QTextCursor.LineUnderCursor 在空白区域可能会选中前一行")
    print("  2. 简化逻辑只检查是否包含.xlsx，没有验证是否为当前行")
    print("  3. 空行被误认为包含Excel内容")
    print()
    print("🔧 解决方案:")
    print("  1. 添加空行检查: len(line_text.strip()) > 0")
    print("  2. 或者检查分词数量: len(line_text.split()) == 1")
    print("  3. 确保点击的是有内容的行")
    print()
    print("✅ 修正后的逻辑:")
    print("  if ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and")
    print("     '文件名' not in line_text and")
    print("     len(line_text.strip()) > 0 and")
    print("     self._excel_file_paths:")

def main():
    """主函数"""
    print("🚀 空白区域点击问题分析")
    print("=" * 60)

    test_line_selection()
    analyze_click_behavior()

    print("\n🎯 结论:")
    print("需要添加空行检测来避免误触发！")

if __name__ == "__main__":
    main()