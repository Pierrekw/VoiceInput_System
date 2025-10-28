#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Excel点击检测
验证使用block.text()替代LineUnderCursor的效果
"""

import sys
from PySide6.QtWidgets import QApplication, QTextBrowser, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont

def test_fixed_click_detection():
    """测试修复后的点击检测"""
    print("🧪 测试修复后的Excel点击检测")
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

        # 添加一个空行
        cursor.insertText('\n')

    # 添加多个Excel记录
    add_excel_info("Report_4564_54564_20251028_221719.xlsx")
    add_excel_info("Report_1234_5678_20251028_220000.xlsx")

    # 旧的检测逻辑（使用LineUnderCursor）
    def old_detection_logic(cursor):
        cursor.select(QTextCursor.LineUnderCursor)
        line_text = cursor.selectedText().strip()
        return ('.xlsx' in line_text.lower() and '文件名' not in line_text and len(line_text.strip()) > 0)

    # 新的检测逻辑（使用block.text()）
    def new_detection_logic(cursor):
        block = cursor.block()
        line_text = block.text().strip()
        return ('.xlsx' in line_text.lower() and '文件名' not in line_text and len(line_text.strip()) > 0)

    def custom_mouse_press_event(event):
        """自定义鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            try:
                position = event.position()
                cursor = text_browser.cursorForPosition(position.toPoint())
            except AttributeError:
                cursor = text_browser.cursorForPosition(event.pos())

            # 获取原始块信息用于调试
            block = cursor.block()
            block_text = block.text()

            # 获取LineUnderCursor用于对比
            cursor.select(QTextCursor.LineUnderCursor)
            line_under = cursor.selectedText()

            print(f"\n🖱️ 点击位置: ({position.x():.1f}, {position.y():.1f})")
            print(f"📄 原始块内容: '{block_text}'")
            print(f"📋 LineUnderCursor: '{line_under}'")

            # 测试两种检测逻辑
            old_result = old_detection_logic(text_browser.textCursor())
            new_result = new_detection_logic(cursor)

            print(f"🔍 检测结果:")
            print(f"  - 旧逻辑(LineUnderCursor): {old_result}")
            print(f"  - 新逻辑(block.text()): {new_result}")

            if old_result != new_result:
                print(f"  ⚠️ 两种逻辑结果不同！")
                if new_result and not old_result:
                    print(f"  ✅ 新逻辑修复了误触发问题")
                elif old_result and not new_result:
                    print(f"  ❌ 新逻辑可能导致漏检")
            else:
                if new_result:
                    print(f"  ✅ 两种逻辑都正确检测")
                else:
                    print(f"  ✅ 两种逻辑都正确拒绝")

            # 特别检查边界情况
            if len(block_text.strip()) == 0:
                print(f"  🎯 边界情况：点击了空行")
                if old_result and not new_result:
                    print(f"  ✅ 修复成功：新逻辑正确拒绝空行点击")
                elif old_result == new_result == False:
                    print(f"  ✅ 两种逻辑都正确拒绝空行点击")

    text_browser.mousePressEvent = custom_mouse_press_event
    layout.addWidget(text_browser)

    window.setWindowTitle("修复后的点击检测测试")
    window.resize(600, 500)
    window.show()

    print("\n📋 测试说明:")
    print("  - 点击Excel按钮行")
    print("  - 点击Excel信息区域")
    print("  - 点击空白区域（特别是行与行之间的边界）")
    print("  - 观察新旧逻辑的差异")
    print("  - 按Ctrl+C关闭窗口")

    print("\n💡 修复说明:")
    print("  - 旧逻辑：使用QTextCursor.LineUnderCursor")
    print("  - 新逻辑：使用cursor.block().text()")
    print("  - 预期：新逻辑更准确地处理边界情况")

    sys.exit(app.exec())

def main():
    """主函数"""
    print("🚀 修复后的Excel点击检测验证")
    print("=" * 60)

    test_fixed_click_detection()

if __name__ == "__main__":
    main()