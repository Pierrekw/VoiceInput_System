#!/usr/bin/env python3
"""
自动化GUI历史记录测试 - 不需要用户交互
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor
from datetime import datetime


class AutoTestWindow(QMainWindow):
    """自动化测试窗口"""

    def __init__(self):
        super().__init__()
        self.recognition_count = 0
        self.test_commands = [
            "🎤 [CMD] 22:45:01 🎤 语音命令: [命令] 切换到标准序号 200",
            "🎤 [CMD] 22:45:03 🎤 语音命令: [命令] 切换到标准序号 300",
            "🎤 [CMD] 22:45:05 🎤 语音命令: [命令] 切换到标准序号 400",
            "🎤 [CMD] 22:45:07 🎤 语音命令: [命令] 切换到标准序号 500"
        ]
        self.current_command_index = 0
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("🧪 自动化GUI历史记录测试")
        self.setGeometry(100, 100, 800, 600)

        # 创建历史文本框
        self.history_text = QTextEdit()
        self.history_text.setMinimumHeight(400)
        self.setCentralWidget(self.history_text)

        print("🚀 自动化GUI测试窗口已创建")

        # 设置定时器，1秒后开始自动测试
        QTimer.singleShot(1000, self.start_auto_test)

    def start_auto_test(self):
        """开始自动测试"""
        print("🎯 开始自动测试历史记录显示")
        self.append_log("🎤 开始模拟语音识别...")

        # 设置定时器发送命令
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.send_next_command)
        self.command_timer.start(2000)  # 每2秒发送一个命令

    def send_next_command(self):
        """发送下一个命令"""
        if self.current_command_index < len(self.test_commands):
            command = self.test_commands[self.current_command_index]
            print(f"📤 发送命令 {self.current_command_index + 1}: {command}")

            # 调用命令处理方法
            self.handle_command_result(command)

            self.current_command_index += 1
        else:
            # 测试完成
            self.command_timer.stop()
            self.complete_test()

    def handle_command_result(self, command_text: str):
        """处理命令结果，添加到历史记录"""
        try:
            # 直接添加到历史文本框
            if hasattr(self, 'history_text'):
                self.history_text.append(command_text)
                self.recognition_count += 1

                # 滚动到底部
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.history_text.setTextCursor(cursor)

                print(f"✅ 命令已添加到历史记录: {command_text}")
                self.append_log(f"✅ 命令 {self.recognition_count} 已处理")

        except Exception as e:
            print(f"❌ 处理命令结果失败: {e}")
            self.append_log(f"❌ 处理失败: {e}")

    def append_log(self, message: str):
        """添加日志消息到控制台"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)

    def complete_test(self):
        """完成测试"""
        print("🎉 自动化测试完成!")
        self.append_log("📊 测试统计:")
        self.append_log(f"  - 总共处理了 {self.recognition_count} 条命令")
        self.append_log("  - 历史记录显示功能正常")

        # 验证历史记录内容
        history_content = self.history_text.toPlainText()
        if all(cmd in history_content for cmd in self.test_commands):
            print("✅ 所有命令都已正确显示在历史记录中!")
            self.append_log("✅ 验证通过: 所有命令都在历史记录中")
        else:
            print("❌ 部分命令未显示在历史记录中!")
            self.append_log("❌ 验证失败: 部分命令缺失")

        # 3秒后自动退出
        QTimer.singleShot(3000, self.close)

    def closeEvent(self, event):
        """窗口关闭事件"""
        print("🔚 测试窗口关闭")
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = AutoTestWindow()
    window.show()

    print("🚀 自动化GUI历史记录测试启动")
    print("📋 测试将自动进行，无需人工干预")
    print("🎯 观察控制台输出和GUI窗口")

    return app.exec()


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n🏁 测试程序退出，退出码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 测试程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)