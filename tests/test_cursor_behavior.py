#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QTextCursor.LineUnderCursor的行为
分析为什么点击空白区域还是会选中Excel内容
"""

import sys
from PySide6.QtWidgets import QApplication, QTextBrowser, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

def test_cursor_behavior():
    """测试光标选择行为"""
    print("🔍 测试QTextCursor.LineUnderCursor行为")
    print("=" * 50)

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    layout = QVBoxLayout(window)

    text_browser = QTextBrowser()
    text_browser.setHtml("""
        <div>📂 点击打开Excel文件: Report_4564_54564_20251028_221719.xlsx</div>
        <div>📄 文件名: Report_4564_54564_20251028_221719.xlsx</div>
        <div>数据已保存 Report_4564_54564_20251028_221719.xlsx</div>
        <div>Report_4564_54564_20251028_221719.xlsx</div>
        <div>&nbsp;</div>  <!-- 空行 -->
        <div>&nbsp;</div>  <!-- 另一个空行 -->
        <div>普通文本行</div>
    """)

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

            cursor.select(QTextCursor.WordUnderCursor)
            word_under = cursor.selectedText()

            cursor.select(QTextCursor.BlockUnderCursor)
            block_under = cursor.selectedText()

            # 获取当前位置的文本块
            block = cursor.block()
            block_text = block.text()

            print(f"\n🖱️ 点击位置: ({position.x()}, {position.y()})")
            print(f"📄 LineUnderCursor: '{line_under}'")
            print(f"📝 WordUnderCursor: '{word_under}'")
            print(f"📋 BlockUnderCursor: '{block_under}'")
            print(f"🎯 Block.text(): '{block_text}'")

            # 检查各种条件
            print(f"🔍 检测结果:")
            print(f"  - 包含.xlsx: {'.xlsx' in line_under.lower()}")
            print(f"  - 不包含'文件名': {'文件名' not in line_under}")
            print(f"  - 长度>0: {len(line_under.strip()) > 0}")
            print(f"  - 块长度>0: {len(block_text.strip()) > 0}")

            # 测试改进的逻辑
            should_trigger_line = ('.xlsx' in line_under.lower() and
                                  '文件名' not in line_under and
                                  len(line_under.strip()) > 0)

            should_trigger_block = ('.xlsx' in block_text.lower() and
                                   '文件名' not in block_text and
                                   len(block_text.strip()) > 0)

            print(f"  - LineUnderCursor触发: {should_trigger_line}")
            print(f"  - Block.text()触发: {should_trigger_block}")

            if should_trigger_line != should_trigger_block:
                print(f"  ⚠️ 两种方法结果不同！")

    text_browser.mousePressEvent = custom_mouse_press_event
    layout.addWidget(text_browser)

    window.setWindowTitle("QTextCursor行为测试")
    window.resize(600, 400)
    window.show()

    print("\n📋 测试说明:")
    print("  - 点击Excel文件行")
    print("  - 点击Excel文件下方的空白区域")
    print("  - 观察不同选择方式的差异")
    print("  - 按Ctrl+C关闭窗口")

    sys.exit(app.exec())

def analyze_problem():
    """分析问题原因"""
    print("\n💡 问题分析:")
    print("=" * 40)
    print("❌ 可能的问题:")
    print("  1. QTextCursor.LineUnderCursor在空白区域可能选中前一行")
    print("  2. HTML中的&nbsp;可能被当作实际内容")
    print("  3. 光标定位机制存在偏差")
    print()
    print("🔧 解决方案:")
    print("  1. 使用BlockUnderCursor代替LineUnderCursor")
    print("  2. 检查光标所在位置的原始文本块")
    print("  3. 添加额外的位置验证")
    print()
    print("✅ 改进的检测逻辑:")
    print("  block = cursor.block()")
    print("  block_text = block.text()")
    print("  if ('.xlsx' in block_text.lower() and")
    print("      '文件名' not in block_text and")
    print("      len(block_text.strip()) > 0):")

if __name__ == "__main__":
    print("🚀 QTextCursor行为诊断")
    print("=" * 60)

    # 分析问题
    analyze_problem()

    # 运行测试
    test_cursor_behavior()