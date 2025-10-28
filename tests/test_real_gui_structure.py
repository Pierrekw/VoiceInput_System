#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实GUI结构的点击行为
模拟voice_gui.py中实际的文本格式
"""

import sys
from PySide6.QtWidgets import QApplication, QTextBrowser, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont

def test_real_gui_structure():
    """测试真实GUI结构的点击行为"""
    print("🔍 测试真实GUI结构的点击行为")
    print("=" * 50)

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    layout = QVBoxLayout(window)

    text_browser = QTextBrowser()
    text_browser.setFont(QFont("Microsoft YaHei", 10))

    # 模拟真实的Excel信息添加过程
    def add_excel_info(file_name="Report_4564_54564_20251028_221719.xlsx"):
        """添加Excel信息（模拟真实过程）"""
        excel_info = f"""📊 Excel文件已生成
   📄 文件名: {file_name}
   📊 记录数量: 15 条
   📏 文件大小: 2.5 KB
   🕐 最后修改: 2025-10-28 22:17:19"""

        text_browser.append(excel_info)

        # 添加按钮行（模拟真实过程）
        cursor = text_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 添加换行
        cursor.insertText('\n')

        # 添加带下划线的链接文本
        cursor.insertText('📂 点击打开Excel文件: ')

        # 为文件名设置样式
        format = QTextCharFormat()
        format.setForeground(Qt.blue)
        format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        format.setFontWeight(QFont.Weight.Bold)

        cursor.insertText(file_name, format)

        # 添加一个空行（这可能就是问题所在）
        cursor.insertText('\n')

    # 添加多个Excel记录
    add_excel_info("Report_4564_54564_20251028_221719.xlsx")
    add_excel_info("Report_1234_5678_20251028_220000.xlsx")

    def custom_mouse_press_event(event):
        """自定义鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            try:
                position = event.position()
                cursor = text_browser.cursorForPosition(position.toPoint())
            except AttributeError:
                cursor = text_browser.cursorForPosition(event.pos())

            # 测试不同的选择方式
            cursor.select(QTextCursor.LineUnderCursor)
            line_under = cursor.selectedText()

            cursor.select(QTextCursor.BlockUnderCursor)
            block_under = cursor.selectedText()

            # 获取当前位置的文本块
            block = cursor.block()
            block_text = block.text()

            print(f"\n🖱️ 点击位置: ({position.x():.1f}, {position.y():.1f})")
            print(f"📄 LineUnderCursor: '{line_under}'")
            print(f"📋 BlockUnderCursor: '{block_under}'")
            print(f"🎯 Block.text(): '{block_text}'")

            # 检查各种条件
            print(f"🔍 检测结果:")
            print(f"  - 包含.xlsx: {'.xlsx' in line_under.lower()}")
            print(f"  - 不包含'文件名': {'文件名' not in line_under}")
            print(f"  - LineUnderCursor长度>0: {len(line_under.strip()) > 0}")
            print(f"  - Block.text()长度>0: {len(block_text.strip()) > 0}")

            # 当前的检测逻辑
            will_trigger_current = ('.xlsx' in line_under.lower() and
                                   '文件名' not in line_under and
                                   len(line_under.strip()) > 0)

            # 改进的检测逻辑（使用Block）
            will_trigger_block = ('.xlsx' in block_text.lower() and
                                 '文件名' not in block_text and
                                 len(block_text.strip()) > 0)

            print(f"  - 当前逻辑触发: {will_trigger_current}")
            print(f"  - Block逻辑触发: {will_trigger_block}")

            if will_trigger_current != will_trigger_block:
                print(f"  ⚠️ 两种方法结果不同！")

            # 特别检查空行情况
            if len(line_under.strip()) == 0:
                print(f"  🎯 检测到空行，但LineUnderCursor可能选中了上一行")
                if will_trigger_current:
                    print(f"  ❌ 这就是误触发的原因！")

    text_browser.mousePressEvent = custom_mouse_press_event
    layout.addWidget(text_browser)

    window.setWindowTitle("真实GUI结构测试")
    window.resize(600, 500)
    window.show()

    print("\n📋 测试说明:")
    print("  - 点击Excel按钮行")
    print("  - 点击Excel信息块和按钮之间的空白区域")
    print("  - 点击两个Excel记录之间的空白区域")
    print("  - 观察LineUnderCursor在空白区域的行为")
    print("  - 按Ctrl+C关闭窗口")

    sys.exit(app.exec())

def analyze_real_structure():
    """分析真实结构的问题"""
    print("\n💡 真实结构分析:")
    print("=" * 40)
    print("❌ 实际问题:")
    print("  1. Excel信息通过append()添加，自动换行")
    print("  2. 信息块和按钮行之间有换行符")
    print("  3. 多个Excel记录之间也有空行")
    print("  4. QTextCursor.LineUnderCursor在换行处可能选中上一行")
    print()
    print("🔧 解决方案:")
    print("  1. 使用cursor.block()获取当前文本块")
    print("  2. 检查block.text()而不是selectedText()")
    print("  3. 验证点击位置确实在有内容的区域")
    print()
    print("✅ 改进的检测逻辑:")
    print("  block = cursor.block()")
    print("  block_text = block.text()")
    print("  if ('.xlsx' in block_text.lower() and")
    print("      '文件名' not in block_text and")
    print("      len(block_text.strip()) > 0):")

if __name__ == "__main__":
    print("🚀 真实GUI结构诊断")
    print("=" * 60)

    # 分析真实结构
    analyze_real_structure()

    # 运行测试
    test_real_gui_structure()