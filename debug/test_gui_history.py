#!/usr/bin/env python3
"""
简化的GUI测试 - 模拟语音识别并测试历史记录显示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QPushButton, QTextEdit, QLabel, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QTextCursor, QFont
import time
from datetime import datetime


class MockVoiceWorker(QThread):
    """模拟语音识别工作线程"""
    command_result = Signal(str)  # 命令结果信号
    log_message = Signal(str)     # 日志消息信号

    def __init__(self):
        super().__init__()
        self.test_commands = [
            "设置200",
            "切换300",
            "设置400",
            "切换500"
        ]
        self.current_index = 0

    def run(self):
        """模拟语音识别过程"""
        self.log_message.emit("🎤 开始模拟语音识别...")

        # 模拟识别延迟
        for i, command in enumerate(self.test_commands):
            time.sleep(2)  # 模拟识别间隔

            # 生成格式化命令
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_command = f"🎤 [CMD] {timestamp} 🎤 语音命令: [命令] 切换到标准序号 {command[-3:]}"

            self.log_message.emit(f"🔍 识别到命令: {command}")

            # 发送命令结果信号
            self.command_result.emit(formatted_command)

        self.log_message.emit("✅ 模拟识别完成")


class TestHistoryWindow(QMainWindow):
    """测试历史记录显示的主窗口"""

    def __init__(self):
        super().__init__()
        self.recognition_count = 0
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🧪 GUI历史记录测试")
        self.setGeometry(100, 100, 800, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("🧪 语音命令历史记录测试")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #1976d2;")
        main_layout.addWidget(title_label)

        # 说明文字
        info_label = QLabel("点击'开始测试'按钮模拟语音识别，观察历史记录显示")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("padding: 5px; color: #666;")
        main_layout.addWidget(info_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("🚀 开始测试")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.start_button.clicked.connect(self.start_test)

        self.clear_button = QPushButton("🗑️ 清空历史")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.clear_button.clicked.connect(self.clear_history)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 识别历史区域
        history_label = QLabel("📋 识别历史记录:")
        history_label.setStyleSheet("font-weight: bold; padding: 5px;")
        main_layout.addWidget(history_label)

        self.history_text = QTextEdit()
        self.history_text.setMinimumHeight(300)
        self.history_text.setFont(QFont("Consolas", 10))
        self.history_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: #f9f9f9;
            }
        """)
        self.history_text.setPlaceholderText("识别结果将显示在这里...")
        main_layout.addWidget(self.history_text)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 5px; color: #666; border-top: 1px solid #ddd;")
        main_layout.addWidget(self.status_label)

        # 初始化日志
        self.append_log("🚀 GUI测试窗口已启动")
        self.append_log("📋 准备进行历史记录显示测试")

    def start_test(self):
        """开始测试"""
        if self.worker and self.worker.isRunning():
            return

        self.start_button.setEnabled(False)
        self.append_log("🎤 开始模拟语音识别测试...")

        # 创建并启动工作线程
        self.worker = MockVoiceWorker()
        self.worker.command_result.connect(self.handle_command_result)
        self.worker.log_message.connect(self.append_log)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.start()

    def handle_command_result(self, command_text: str):
        """处理命令结果，添加到历史记录"""
        try:
            # 直接添加到历史文本框
            if hasattr(self, 'history_text'):
                self.history_text.append(command_text)
                self.recognition_count += 1

                # 更新状态
                self.status_label.setText(f"已识别 {self.recognition_count} 条命令")

                # 滚动到底部
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.history_text.setTextCursor(cursor)

                self.append_log(f"✅ 命令已添加到历史记录: {command_text}")

        except Exception as e:
            self.append_log(f"❌ 处理命令结果失败: {e}")

    def clear_history(self):
        """清空历史记录"""
        self.history_text.clear()
        self.recognition_count = 0
        self.status_label.setText("历史记录已清空")
        self.append_log("🗑️ 历史记录已清空")

    def append_log(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)  # 同时输出到控制台

    def on_test_finished(self):
        """测试完成"""
        self.start_button.setEnabled(True)
        self.append_log("✅ 模拟识别测试完成")
        self.append_log(f"📊 总共识别了 {self.recognition_count} 条命令")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("GUI历史记录测试")

    window = TestHistoryWindow()
    window.show()

    print("🚀 GUI历史记录测试窗口已启动")
    print("📋 请在GUI中点击'开始测试'按钮进行测试")
    print("🎯 观察识别历史是否正确显示语音命令")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()