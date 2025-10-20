#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音识别系统 GUI界面
基于PySide6的现代图形用户界面
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from io import StringIO

# PySide6导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QTextEdit, QLabel, QPushButton, QProgressBar,
    QGroupBox, QSplitter, QFrame, QScrollArea, QStatusBar,
    QMessageBox, QFileDialog, QCheckBox, QSpinBox, QComboBox,
    QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon

# 导入核心模块
try:
    from main_f import FunASRVoiceSystem, VoiceCommandType
except ImportError:
    logger.warning("无法导入main_f模块，使用简化版本")
    FunASRVoiceSystem = None
    VoiceCommandType = None

try:
    from funasr_voice_module import FunASRVoiceRecognizer, RecognitionResult
except ImportError:
    logger.warning("无法导入funasr_voice_module模块")
    FunASRVoiceRecognizer = None
    RecognitionResult = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemState(Enum):
    """系统状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class VoiceRecognitionThread(QThread):
    """语音识别工作线程"""

    # 信号定义
    status_changed = Signal(str)  # 状态变化
    recognition_result = Signal(str, str, float)  # 识别结果 (文本, 类型, 置信度)
    partial_result = Signal(str)  # 部分识别结果
    error_occurred = Signal(str)  # 错误信息
    log_message = Signal(str)  # 日志信息
    performance_data = Signal(str)  # 性能数据
    recognition_stopped = Signal()  # 识别停止

    def __init__(self):
        super().__init__()
        self.voice_system = None
        self._should_stop = False

    def run(self):
        """运行语音识别"""
        try:
            # 初始化语音系统
            if FunASRVoiceSystem is None:
                self.error_occurred.emit("语音系统模块不可用")
                return

            self.voice_system = FunASRVoiceSystem()
            if not self.voice_system.initialize():
                self.error_occurred.emit("语音系统初始化失败")
                return

            self.status_changed.emit("系统初始化完成")
            self.log_message.emit("🎤 FunASR语音系统初始化完成")

            # 设置回调（通过recognizer）
            if hasattr(self.voice_system, 'recognizer'):
                self.voice_system.recognizer.set_callbacks(
                    on_final_result=self._on_recognition_result
                )

            # 开始识别
            self.voice_system.start_recognition()
            self.status_changed.emit("正在识别...")

            # 运行识别循环
            self.voice_system.run_recognition_cycle()

        except Exception as e:
            self.error_occurred.emit(f"语音识别异常: {str(e)}")
            logger.error(f"语音识别异常: {e}")
        finally:
            self.recognition_stopped.emit()

    def stop_recognition(self):
        """停止识别"""
        self._should_stop = True
        if self.voice_system:
            self.voice_system.system_stop()

    def pause_recognition(self):
        """暂停识别"""
        if self.voice_system:
            self.voice_system.pause()
            self.status_changed.emit("已暂停")

    def resume_recognition(self):
        """恢复识别"""
        if self.voice_system:
            self.voice_system.resume()
            self.status_changed.emit("正在识别...")

    def _on_recognition_result(self, result):
        """识别结果回调"""
        if hasattr(result, 'text'):
            text = result.text
            # 判断是否包含数字
            if any(char.isdigit() for char in text):
                result_type = "数字"
            else:
                result_type = "文本"
            confidence = getattr(result, 'confidence', 0.0)
            self.recognition_result.emit(text, result_type, confidence)

    def _on_voice_command(self, command_type):
        """语音命令回调"""
        if VoiceCommandType is None:
            return

        if command_type == VoiceCommandType.PAUSE:
            self.status_changed.emit("语音命令：暂停")
            self.log_message.emit("🎤 语音命令：暂停")
        elif command_type == VoiceCommandType.RESUME:
            self.status_changed.emit("语音命令：恢复")
            self.log_message.emit("🎤 语音命令：恢复")
        elif command_type == VoiceCommandType.STOP:
            self.status_changed.emit("语音命令：停止")
            self.log_message.emit("🎤 语音命令：停止")
            self.stop_recognition()


class LogStreamHandler(StringIO):
    """自定义日志流处理器，将日志重定向到GUI"""

    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback

    def write(self, text):
        if text.strip():  # 只处理非空文本
            self.log_callback.emit(text.strip())
        return len(text)

    def flush(self):
        pass


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.voice_thread = None
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("FunASR语音识别系统 v2.3")
        self.setMinimumSize(1200, 800)

        # 设置应用图标（如果有的话）
        # self.setWindowIcon(QIcon("icon.png"))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：控制面板和状态显示
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # 右侧：日志和识别结果
        right_panel = self.create_display_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([400, 800])

        # 创建状态栏
        self.create_status_bar()

        # 应用样式
        self.apply_styles()

    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 系统状态组
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("🔴 系统未启动")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

        # 控制按钮组
        control_group = QGroupBox("控制面板")
        control_layout = QGridLayout(control_group)

        self.start_button = QPushButton("🎙️ 开始识别")
        self.start_button.setMinimumHeight(50)
        self.start_button.clicked.connect(self.start_recognition)
        control_layout.addWidget(self.start_button, 0, 0, 1, 2)

        self.pause_button = QPushButton("⏸️ 暂停")
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_recognition)
        control_layout.addWidget(self.pause_button, 1, 0)

        self.stop_button = QPushButton("🛑 停止")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recognition)
        control_layout.addWidget(self.stop_button, 1, 1)

        layout.addWidget(control_group)

        # 识别设置组
        settings_group = QGroupBox("识别设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("识别模式:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["连续识别", "单次识别"])
        settings_layout.addWidget(self.mode_combo, 0, 1)

        settings_layout.addWidget(QLabel("识别时长(秒):"), 1, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 300)
        self.duration_spin.setValue(30)
        self.duration_spin.setEnabled(False)  # 单次识别时启用
        settings_layout.addWidget(self.duration_spin, 1, 1)

        self.vad_checkbox = QCheckBox("启用VAD语音活动检测")
        self.vad_checkbox.setChecked(True)
        settings_layout.addWidget(self.vad_checkbox, 2, 0, 1, 2)

        layout.addWidget(settings_group)

        # 语音命令组
        command_group = QGroupBox("语音命令")
        command_layout = QVBoxLayout(command_group)

        command_info = QLabel(
            "🎯 语音命令:\n"
            "• 暂停: 暂停, 停一下, 等一下\n"
            "• 继续: 继续, 开始, 重新开始\n"
            "• 停止: 停止, 结束, 关闭"
        )
        command_info.setWordWrap(True)
        command_layout.addWidget(command_info)

        layout.addWidget(command_group)

        # 统计信息组
        stats_group = QGroupBox("识别统计")
        stats_layout = QGridLayout(stats_group)

        self.total_count_label = QLabel("总识别次数: 0")
        stats_layout.addWidget(self.total_count_label, 0, 0)

        self.number_count_label = QLabel("数字识别: 0")
        stats_layout.addWidget(self.number_count_label, 0, 1)

        self.text_count_label = QLabel("文本识别: 0")
        stats_layout.addWidget(self.text_count_label, 1, 0)

        self.elapsed_time_label = QLabel("运行时间: 0s")
        stats_layout.addWidget(self.elapsed_time_label, 1, 1)

        layout.addWidget(stats_group)

        # 添加弹性空间
        layout.addStretch()

        return panel

    def create_display_panel(self):
        """创建显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 创建标签页容器
        tab_widget = QTabWidget()

        # 识别结果标签页
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)

        # 当前识别文本
        current_group = QGroupBox("当前识别")
        current_layout = QVBoxLayout(current_group)

        self.current_text_label = QLabel("等待识别...")
        self.current_text_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1976d2; "
            "background-color: #e3f2fd; padding: 10px; border-radius: 5px;"
        )
        self.current_text_label.setWordWrap(True)
        self.current_text_label.setMinimumHeight(60)
        current_layout.addWidget(self.current_text_label)

        results_layout.addWidget(current_group)

        # 识别历史
        history_group = QGroupBox("识别历史")
        history_layout = QVBoxLayout(history_group)

        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setFont(QFont("Consolas", 10))
        history_layout.addWidget(self.history_text)

        results_layout.addWidget(history_group)
        tab_widget.addTab(results_tab, "识别结果")

        # 系统日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)

        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self.clear_log)
        log_control_layout.addWidget(self.clear_log_button)
        log_control_layout.addStretch()

        log_layout.addLayout(log_control_layout)

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        tab_widget.addTab(log_tab, "系统日志")

        layout.addWidget(tab_widget)

        return panel

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_bar.showMessage("就绪")

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
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
                font-size: 14px;
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
                background-color: #cccccc;
                color: #666666;
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
            }

            QLabel {
                color: #333333;
            }

            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 2px;
            }
        """)

        # 设置按钮对象名称
        self.stop_button.setObjectName("stop_button")
        self.pause_button.setObjectName("pause_button")

    def setup_logging(self):
        """设置日志重定向"""
        # 创建日志流处理器
        self.log_stream = LogStreamHandler(self.append_log)

        # 重定向stdout和stderr
        sys.stdout = self.log_stream
        sys.stderr = self.log_stream

    def start_recognition(self):
        """开始语音识别"""
        if self.voice_thread and self.voice_thread.isRunning():
            return

        # 更新UI状态
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_label.setText("🟢 正在启动...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50;")

        # 清空历史记录
        self.history_text.clear()
        self.current_text_label.setText("正在初始化系统...")

        # 创建并启动语音识别线程
        self.voice_thread = VoiceRecognitionThread()
        self.voice_thread.status_changed.connect(self.update_status)
        self.voice_thread.recognition_result.connect(self.display_recognition_result)
        self.voice_thread.partial_result.connect(self.display_partial_result)
        self.voice_thread.error_occurred.connect(self.display_error)
        self.voice_thread.log_message.connect(self.append_log)
        self.voice_thread.performance_data.connect(self.display_performance_data)
        self.voice_thread.recognition_stopped.connect(self.on_recognition_stopped)

        self.voice_thread.start()

        self.append_log("🚀 启动语音识别系统...")

    def pause_recognition(self):
        """暂停/恢复识别"""
        if not self.voice_thread:
            return

        if self.pause_button.text() == "⏸️ 暂停":
            self.voice_thread.pause_recognition()
            self.pause_button.setText("▶️ 恢复")
        else:
            self.voice_thread.resume_recognition()
            self.pause_button.setText("⏸️ 暂停")

    def stop_recognition(self):
        """停止识别"""
        if self.voice_thread:
            self.voice_thread.stop_recognition()

    def on_recognition_stopped(self):
        """识别停止回调"""
        # 更新UI状态
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("⏸️ 暂停")
        self.status_label.setText("🔴 系统已停止")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        self.current_text_label.setText("等待识别...")

        self.append_log("🛑 语音识别已停止")

        # 清理线程
        if self.voice_thread:
            self.voice_thread.wait(2000)  # 等待2秒
            self.voice_thread = None

    def update_status(self, status):
        """更新状态显示"""
        self.status_label.setText(f"🟢 {status}")
        self.status_bar.showMessage(status)

    def display_recognition_result(self, text, result_type, confidence):
        """显示识别结果"""
        # 更新当前识别文本
        self.current_text_label.setText(f"{text}")

        # 添加到历史记录
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "🔢" if result_type == "数字" else "📝"
        history_entry = f"[{timestamp}] {icon} {text}"

        self.history_text.append(history_entry)

        # 滚动到底部
        cursor = self.history_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.history_text.setTextCursor(cursor)

        # 更新统计信息
        self.update_statistics(result_type)

    def display_partial_result(self, text):
        """显示部分识别结果"""
        if text.strip():
            self.current_text_label.setText(f"🗣️ {text}...")

    def display_error(self, error_message):
        """显示错误信息"""
        self.append_log(f"❌ 错误: {error_message}")
        QMessageBox.critical(self, "错误", error_message)

    def display_performance_data(self, data):
        """显示性能数据"""
        self.append_log(f"📊 {data}")

    def append_log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)

        # 限制日志行数，避免内存占用过多
        if self.log_text.document().blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 删除换行符

        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.append_log("📋 日志已清空")

    def update_statistics(self, result_type):
        """更新统计信息"""
        # 这里可以实现统计逻辑
        pass

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.voice_thread and self.voice_thread.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '语音识别正在运行，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.voice_thread.stop_recognition()
                self.voice_thread.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("FunASR语音识别系统")
    app.setApplicationVersion("2.3")
    app.setOrganizationName("Voice Input System")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()