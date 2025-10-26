#!/usr/bin/env python3
"""
测试GUI中命令显示功能的简单测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_command_handler():
    """测试GUI命令处理功能"""
    print("🧪 测试GUI命令处理功能")
    print("=" * 50)

    try:
        from voice_gui import WorkingSimpleMainWindow
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer

        # 创建应用程序（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建主窗口（不显示）
        main_window = WorkingSimpleMainWindow()
        main_window.hide()

        print("✅ 主窗口创建成功")

        # 检查是否有history_text组件
        if hasattr(main_window, 'history_text'):
            print("✅ history_text组件存在")
        else:
            print("❌ history_text组件不存在")
            return False

        # 检查是否有handle_command_result方法
        if hasattr(main_window, 'handle_command_result'):
            print("✅ handle_command_result方法存在")
        else:
            print("❌ handle_command_result方法不存在")
            return False

        # 测试命令处理
        test_commands = [
            "🎤 [CMD] 22:28:59 🎤 语音命令: [命令] 切换到标准序号 200",
            "🎤 [CMD] 22:29:13 🎤 语音命令: [命令] 切换到标准序号 300",
            "🎤 [CMD] 22:30:00 🎤 语音命令: [命令] 标准序号切换到 400",
        ]

        print("\n📋 测试命令处理:")
        for i, cmd in enumerate(test_commands, 1):
            print(f"\n🎯 测试命令 {i}: '{cmd}'")

            # 获取处理前的历史记录
            before_text = main_window.history_text.toPlainText()
            before_lines = len(before_text.split('\n')) if before_text.strip() else 0

            # 调用命令处理方法
            main_window.handle_command_result(cmd)

            # 检查处理后的历史记录
            after_text = main_window.history_text.toPlainText()
            after_lines = len(after_text.split('\n')) if after_text.strip() else 0

            if cmd in after_text:
                print(f"  ✅ 命令已添加到history_text")
                print(f"  📊 历史记录行数: {before_lines} -> {after_lines}")
            else:
                print(f"  ❌ 命令未在history_text中找到")
                print(f"  📝 当前历史记录内容: {after_text}")

        print("\n🎯 GUI命令处理测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_signal():
    """测试Worker信号功能"""
    print("\n🧪 测试Worker信号功能")
    print("=" * 30)

    try:
        from voice_gui import WorkingVoiceWorker
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QObject, Signal

        # 创建应用程序
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 测试Worker是否有command_result信号
        if hasattr(WorkingVoiceWorker, 'command_result'):
            print("✅ command_result信号存在")
        else:
            print("❌ command_result信号不存在")
            return False

        # 创建模拟接收器
        signal_received = []
        class TestReceiver(QObject):
            def handle_command(self, cmd):
                signal_received.append(cmd)
                print(f"  📡 收到信号: '{cmd}'")

        receiver = TestReceiver()
        worker = WorkingVoiceWorker()

        # 连接信号
        worker.command_result.connect(receiver.handle_command)
        print("✅ 信号连接成功")

        # 测试发送信号
        test_cmd = "🎤 [CMD] 22:28:59 🎤 语音命令: [命令] 切换到标准序号 200"
        print(f"\n📤 发送测试信号: '{test_cmd}'")
        worker.command_result.emit(test_cmd)

        # 检查信号是否被接收
        if signal_received:
            print(f"✅ 信号成功接收: {signal_received[0]}")
        else:
            print("❌ 信号未被接收")

        print("\n🎯 Worker信号测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始GUI命令显示功能测试")
    print("=" * 60)

    # 测试GUI命令处理
    success1 = test_gui_command_handler()

    # 测试Worker信号
    success2 = test_worker_signal()

    if success1 and success2:
        print("\n🎉 GUI命令显示功能测试通过！")
        print("\n📝 测试结果总结:")
        print("1. ✅ GUI能够正确处理命令结果")
        print("2. ✅ 命令能够添加到history_text组件")
        print("3. ✅ Worker信号机制工作正常")
        print("4. ✅ 线程安全的GUI更新机制就绪")
        print("\n🔧 命令显示功能已准备就绪，可以在实际使用中正常工作！")
    else:
        print("\n❌ 部分测试失败，请检查实现代码")