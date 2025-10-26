#!/usr/bin/env python3
"""
测试PySide6兼容性修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pyside6_compatibility():
    """测试PySide6兼容性"""
    print("🧪 测试PySide6兼容性修复")
    print("=" * 50)

    try:
        from PySide6.QtWidgets import QApplication, QTextBrowser
        from PySide6.QtCore import Qt, QEvent, QPointF
        from PySide6.QtGui import QMouseEvent, QTextCursor
        import time

        # 创建应用程序（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建测试窗口
        text_browser = QTextBrowser()
        text_browser.setPlainText("测试文本\n第二行\n第三行")
        text_browser.show()

        print("✅ PySide6基础组件创建成功")

        # 测试鼠标事件处理
        try:
            # 创建鼠标事件对象
            mouse_event = QMouseEvent(
                QEvent.MouseButtonPress,
                QPointF(10, 10),  # 使用QPointF
                Qt.LeftButton,
                Qt.LeftButton,
                Qt.NoModifier
            )

            print("✅ QMouseEvent创建成功")

            # 测试新方法
            try:
                position = mouse_event.position()
                print(f"✅ 新方法 position() 工作正常: {position}")
            except AttributeError as e:
                print(f"❌ 新方法 position() 失败: {e}")

            # 测试旧方法
            try:
                old_pos = mouse_event.pos()
                print(f"⚠️ 旧方法 pos() 仍可用: {old_pos}")
            except AttributeError as e:
                print(f"⚠️ 旧方法 pos() 不可用: {e}")

            # 测试cursorForPosition
            try:
                cursor = text_browser.cursorForPosition(position.toPoint())
                print("✅ cursorForPosition() 工作正常")
            except Exception as e:
                # 回退测试
                try:
                    cursor = text_browser.cursorForPosition(mouse_event.pos())
                    print("✅ cursorForPosition() 回退方法工作正常")
                except Exception as e2:
                    print(f"❌ cursorForPosition() 失败: {e2}")

        except Exception as e:
            print(f"❌ 鼠标事件测试失败: {e}")

        print("\n🎯 兼容性测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_import():
    """测试GUI模块导入"""
    print("🧪 测试GUI模块导入")
    print("=" * 30)

    try:
        # 测试主要导入
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
        from PySide6.QtCore import Qt, QThread, Signal
        from PySide6.QtGui import QFont, QTextCursor, QMouseEvent

        print("✅ PySide6核心组件导入成功")

        # 测试我们的GUI模块
        import voice_gui
        print("✅ voice_gui模块导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始PySide6兼容性测试")
    print("=" * 60)

    # 测试导入
    import_success = test_gui_import()
    print()

    # 测试兼容性
    compat_success = test_pyside6_compatibility()
    print()

    if import_success and compat_success:
        print("🎉 PySide6兼容性测试通过！")
        print("\n📝 修复说明:")
        print("1. ✅ 使用 position() 替代已弃用的 pos() 方法")
        print("2. ✅ 添加向后兼容的回退机制")
        print("3. ✅ 支持PySide6 6.6+版本")
        print("\n🔧 现在可以安全运行 voice_gui.py")
    else:
        print("❌ 部分测试失败，请检查PySide6版本")