#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版FunASR语音识别GUI界面
专注于基本功能展示和简单控制
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List

# PySide6导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QPushButton, QGroupBox, QStatusBar,
    QMessageBox, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 抑制输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'


class SimpleVoiceWorker(QThread):
    """简化版语音识别工作线程"""

    # 信号定义
    log_message = Signal(str)
    recognition_result = Signal(str)
    status_changed = Signal(str)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self._should_stop = False
        self._is_paused = False
        self.voice_system = None

    def run(self):
        """运行语音识别"""
        try:
            self.log_message.emit("🚀 正在初始化语音系统...")

            # 尝试导入并初始化语音系统
            try:
                from main_f import FunASRVoiceSystem
                self.voice_system = FunASRVoiceSystem()

                if not self.voice_system.initialize():
                    self.log_message.emit("❌ 语音系统初始化失败")
                    return

                self.log_message.emit("✅ 语音系统初始化成功")

            except Exception as e:
                self.log_message.emit(f"❌ 无法加载语音系统: {e}")
                return

            self.status_changed.emit("系统就绪")

            # 模拟语音识别循环
            start_time = time.time()
            recognition_count = 0

            while not self._should_stop:
                if self._is_paused:
                    time.sleep(0.1)
                    continue

                try:
                    # 这里应该调用实际的语音识别
                    # 由于集成复杂性，这里提供模拟界面
                    elapsed = int(time.time() - start_time)
                    self.status_changed.emit(f"正在监听... ({elapsed}s)")

                    # 模拟定期状态更新
                    time.sleep(1)

                    # 每30秒模拟一次识别结果（用于测试界面）
                    if elapsed > 0 and elapsed % 30 == 0 and not self._should_stop:
                        recognition_count += 1
                        test_result = f"模拟识别结果 #{recognition_count}: 测试语音输入 {recognition_count}"
                        self.recognition_result.emit(test_result)
                        self.log_message.emit(f"🎤 {test_result}")

                except Exception as e:
                    self.log_message.emit(f"❌ 识别过程错误: {e}")
                    break

        except Exception as e:
            self.log_message.emit(f"❌ 工作线程异常: {e}")
        finally:
            self.status_changed.emit("已停止")
            self.finished.emit()

    def stop(self):
        """停止识别"""
        self._should_stop = True
        if self.voice_system:
            try:
                self.voice_system.system_stop()
            except:
                pass

    def pause(self):
        """暂停"""
        self._is_paused = True
        self.status_changed.emit("已暂停")

    def resume(self):
        """恢复"""
        self._is_paused = False
        self.status_changed.emit("正在监听...")


class SimpleMainWindow(QMainWindow):
    """简化版主窗口"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("FunASR语音识别系统 - 简化版 v2.3")
        self.setMinimumSize(900, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel)

        # 右侧显示面板
        right_panel = self.create_display_panel()
        main_layout.addWidget(right_panel)

        # 设置比例
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 应用样式
        self.apply_styles()

    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 状态显示
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("🔴 未启动")
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #d32f2f; padding: 10px;"
        )
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_group)

        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)

        self.start_button = QPushButton("🎙️ 开始识别")
        self.start_button.setMinimumHeight(45)
        self.start_button.clicked.connect(self.start_recognition)
        control_layout.addWidget(self.start_button)

        button_row = QHBoxLayout()

        self.pause_button = QPushButton("⏸️ 暂停")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        button_row.addWidget(self.pause_button)

        self.stop_button = QPushButton("🛑 停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recognition)
        button_row.addWidget(self.stop_button)

        control_layout.addLayout(button_row)
        layout.addWidget(control_group)

        # 使用说明
        info_group = QGroupBox("使用说明")
        info_layout = QVBoxLayout(info_group)

        info_text = QLabel(
            "📖 使用说明:\n\n"
            "1. 点击'开始识别'启动系统\n"
            "2. 对着麦克风说话\n"
            "3. 系统会自动识别语音\n"
            "4. 支持语音命令控制:\n"
            "   • '暂停' - 暂停识别\n"
            "   • '继续' - 恢复识别\n"
            "   • '停止' - 停止系统\n\n"
            "⌨️ 快捷键:\n"
            "• 空格键 - 暂停/继续\n"
            "• ESC - 停止识别"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #555; padding: 5px;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        # 系统信息
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout(system_group)

        self.runtime_label = QLabel("运行时间: 0s")
        system_layout.addWidget(self.runtime_label)

        self.recognition_count_label = QLabel("识别次数: 0")
        system_layout.addWidget(self.recognition_count_label)

        layout.addWidget(system_group)

        layout.addStretch()
        return panel

    def create_display_panel(self):
        """创建显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 创建标签页
        tab_widget = QTabWidget()

        # 识别结果标签页
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 11))
        self.results_text.setStyleSheet("background-color: #f9f9f9;")
        results_layout.addWidget(self.results_text)

        tab_widget.addTab(results_tab, "识别结果")

        # 系统日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)

        # 日志控制
        log_control = QHBoxLayout()
        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self.clear_log)
        log_control.addWidget(self.clear_log_button)
        log_control.addStretch()

        log_layout.addLayout(log_control)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        # 注意：QTextEdit没有setMaximumBlockCount方法，改用document().setMaximumBlockCount
        self.log_text.document().setMaximumBlockCount(500)  # 限制行数
        log_layout.addWidget(self.log_text)

        tab_widget.addTab(log_tab, "系统日志")

        layout.addWidget(tab_widget)
        return panel

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }

            QPushButton {
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px;
                background-color: #2196f3;
                color: white;
            }

            QPushButton:hover {
                background-color: #1976d2;
            }

            QPushButton:pressed {
                background-color: #0d47a1;
            }

            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }

            QPushButton#stop_button {
                background-color: #f44336;
            }

            QPushButton#stop_button:hover {
                background-color: #d32f2f;
            }

            QPushButton#pause_button {
                background-color: #ff9800;
            }

            QPushButton#pause_button:hover {
                background-color: #f57c00;
            }

            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-family: 'Consolas', monospace;
            }
        """)

        self.stop_button.setObjectName("stop_button")
        self.pause_button.setObjectName("pause_button")

    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_runtime)
        self.start_time = None
        self.recognition_count = 0

    def start_recognition(self):
        """开始识别"""
        if self.worker and self.worker.isRunning():
            return

        # 更新UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_label.setText("🟢 正在启动...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50; padding: 10px;")

        # 清空结果
        self.results_text.clear()
        self.log_text.clear()
        self.recognition_count = 0
        self.start_time = time.time()

        # 创建并启动工作线程
        self.worker = SimpleVoiceWorker()
        self.worker.log_message.connect(self.append_log)
        self.worker.recognition_result.connect(self.display_result)
        self.worker.status_changed.connect(self.update_status)
        self.worker.finished.connect(self.on_worker_finished)

        self.worker.start()
        self.timer.start(1000)  # 每秒更新

        self.append_log("🚀 启动语音识别系统...")

    def toggle_pause(self):
        """切换暂停状态"""
        if not self.worker:
            return

        if self.pause_button.text() == "⏸️ 暂停":
            self.worker.pause()
            self.pause_button.setText("▶️ 继续")
            self.append_log("⏸️ 已暂停识别")
        else:
            self.worker.resume()
            self.pause_button.setText("⏸️ 暂停")
            self.append_log("▶️ 已恢复识别")

    def stop_recognition(self):
        """停止识别"""
        if self.worker:
            self.worker.stop()
            self.timer.stop()

    def on_worker_finished(self):
        """工作线程完成"""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("⏸️ 暂停")
        self.timer.stop()

        self.status_label.setText("🔴 已停止")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; padding: 10px;")

        if self.worker:
            self.worker.wait(1000)
            self.worker = None

        self.append_log("🛑 语音识别已停止")

    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(f"🟢 {status}")
        self.status_bar.showMessage(status)

    def display_result(self, result):
        """显示识别结果"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_result = f"[{timestamp}] {result}"

        self.results_text.append(formatted_result)
        self.recognition_count += 1

        # 滚动到底部
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.results_text.setTextCursor(cursor)

    def append_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)

        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.append_log("📋 日志已清空")

    def update_runtime(self):
        """更新运行时间"""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.runtime_label.setText(f"运行时间: {elapsed}s")
            self.recognition_count_label.setText(f"识别次数: {self.recognition_count}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '语音识别正在运行，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("FunASR语音识别系统")

    window = SimpleMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()