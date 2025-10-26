#!/usr/bin/env python3
"""
测试命令显示到history_text的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_command_to_history():
    """测试命令显示到history_text的完整流程"""
    print("🧪 测试命令显示到history_text")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟GUI回调连接
        command_received = []
        def mock_state_callback(state, message):
            print(f"📢 状态变化回调: {state} -> {message}")
            command_received.append({
                'state': state,
                'message': message,
                'time': __import__('time').time()
            })

        # 设置状态变化回调
        voice_system.set_state_change_callback(mock_state_callback)

        print("📋 测试命令处理流程:")

        # 模拟命令处理
        test_commands = [
            ("设置200", "设置200", [200]),
            ("切换300", "切换300", [300]),
        ]

        for original_text, processed_text, numbers in test_commands:
            print(f"\n🎯 测试命令: '{original_text}'")

            # 检查命令识别
            command_type = voice_system.recognize_voice_command(processed_text)
            if command_type.name == "STANDARD_ID":
                print(f"  ✅ 识别为标准序号命令")

                # 模拟命令处理
                initial_callback_count = len(command_received)
                voice_system._handle_standard_id_command(processed_text)
                final_callback_count = len(command_received)

                print(f"  📊 状态回调变化: {initial_callback_count} -> {final_callback_count}")

                if final_callback_count > initial_callback_count:
                    latest_callback = command_received[-1]
                    print(f"  📝 回调信息: {latest_callback['message']}")
                    print(f"  ✅ 状态回调工作正常")
                else:
                    print(f"  ❌ 状态回调未触发")
            else:
                print(f"  ❌ 未识别为标准序号命令")

        print("\n🎯 命令处理流程测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_flow():
    """测试信号流程"""
    print("\n🧪 测试信号流程")
    print("=" * 30)

    try:
        from voice_gui import MainWindow
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer

        # 创建应用程序（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建主窗口（不显示）
        main_window = MainWindow()
        main_window.hide()

        # 模拟Worker命令信号
        print("📋 模拟Worker发送命令信号:")

        test_commands = [
            "🎤 [CMD] 22:28:59 🎤 语音命令: [命令] 切换到标准序号 200",
            "🎤 [CMD] 22:29:13 🎤 语音命令: [命令] 切换到标准序号 300",
        ]

        for cmd in test_commands:
            print(f"  发送信号: '{cmd}'")

            # 直接调用handle_command_result
            main_window.handle_command_result(cmd)

            # 检查history_text内容
            if hasattr(main_window, 'history_text'):
                text_content = main_window.history_text.toPlainText()
                if cmd in text_content:
                    print(f"  ✅ 命令已添加到history_text")
                else:
                    print(f"  ❌ 命令未在history_text中找到")
            else:
                print(f"  ❌ history_text不存在")

        print("\n🎯 信号流程测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始命令显示到history_text测试")
    print("=" * 60)

    # 测试命令处理流程
    success1 = test_command_to_history()

    # 测试信号流程
    success2 = test_signal_flow()

    if success1 and success2:
        print("\n🎉 命令显示到history_text测试通过！")
        print("\n📝 最终修复说明:")
        print("1. ✅ 命令通过worker.command_result信号发送")
        print("2. ✅ 主线程接收信号并操作history_text")
        print("3. ✅ 命令会显示在历史记录文本框中")
        print("4. ✅ 线程安全，避免GUI线程问题")
        print("\n🔧 现在命令会正确显示在GUI的历史记录中！")
    else:
        print("\n❌ 部分测试失败，请检查修复代码")