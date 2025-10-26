#!/usr/bin/env python3
"""
GUI组件模块
从voice_gui.py拆分出的GUI组件，用于模块化开发
"""

import sys
import os
import time
import logging
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

from logging_utils import LoggingManager

logger = LoggingManager.get_logger(
    name='gui_components',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
    QLabel, QPushButton, QGroupBox, QStatusBar, QMessageBox,
    QSplitter, QTabWidget, QComboBox, QFormLayout, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QTextCharFormat


class VoiceEnergyBar(QProgressBar):
    """语音能量显示条"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setFormat("能量: %v%")
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #8BC34A, stop:1 #CDDC39);
            }
        """)


class ModeSelector(QWidget):
    """模式选择组件"""

    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        label = QLabel("识别模式:")
        label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["fast", "balanced", "accuracy"])
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)
        layout.addWidget(self.mode_combo)

        # 添加说明
        info_label = QLabel("快速/平衡/精确")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)

        layout.addStretch()


class ControlPanel(QWidget):
    """控制面板组件"""

    start_clicked = Signal()
    stop_clicked = Signal()
    pause_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        self.start_button = QPushButton("🎤 开始")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_button.clicked.connect(self.start_clicked.emit)
        layout.addWidget(self.start_button)

        self.pause_button = QPushButton("⏸️ 暂停")
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        self.pause_button.setEnabled(False)
        layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("🛑 停止")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        layout.addStretch()

    def set_running_state(self, is_running):
        """设置运行状态"""
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.pause_button.setEnabled(is_running)


class LogDisplay(QWidget):
    """日志显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("系统日志")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(title)

        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: #f9f9f9;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)

        # 清除按钮
        clear_button = QPushButton("清除日志")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        clear_button.clicked.connect(self.clear_log)
        layout.addWidget(clear_button)

    def append_log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        self.log_text.append(formatted_message)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # 限制日志行数，避免内存占用过多
        document = self.log_text.document()
        if document.blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()


class ResultDisplay(QWidget):
    """结果显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("识别结果")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(title)

        # 结果文本区域
        self.result_text = QTextBrowser()
        self.result_text.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 12px;
                background-color: white;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.result_text)

        # 统计信息
        self.stats_label = QLabel("统计: 识别 0 次，有效 0 次")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        layout.addWidget(self.stats_label)

        # 清除按钮
        clear_button = QPushButton("清除结果")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        clear_button.clicked.connect(self.clear_results)
        layout.addWidget(clear_button)

        # 初始化统计
        self.total_count = 0
        self.valid_count = 0

    def add_result(self, text, is_valid=True):
        """添加识别结果"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "#2196F3" if is_valid else "#757575"

        html = f'<div style="margin: 8px 0; padding: 8px; background-color: #f5f5f5; border-left: 4px solid {color}; border-radius: 4px;">'
        html += f'<div style="font-size: 12px; color: #666; margin-bottom: 4px;">{timestamp}</div>'
        html += f'<div style="font-size: 14px;">{text}</div>'
        html += '</div>'

        self.result_text.append(html)

        # 更新统计
        self.total_count += 1
        if is_valid:
            self.valid_count += 1
        self.update_stats()

        # 自动滚动到底部
        scrollbar = self.result_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_stats(self):
        """更新统计信息"""
        self.stats_label.setText(f"统计: 识别 {self.total_count} 次，有效 {self.valid_count} 次")

    def clear_results(self):
        """清除结果"""
        self.result_text.clear()
        self.total_count = 0
        self.valid_count = 0
        self.update_stats()


class StatusBar(QWidget):
    """状态栏组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 状态指示器
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 5px 10px;
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                min-width: 80px;
                text-align: center;
            }
        """)
        layout.addWidget(self.status_label)

        # 分隔符
        layout.addWidget(QLabel("|"))

        # 能量条
        layout.addWidget(QLabel("能量:"))
        self.energy_bar = VoiceEnergyBar()
        self.energy_bar.setMaximumWidth(200)
        layout.addWidget(self.energy_bar)

        # 时间显示
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("color: #666; font-family: monospace;")
        layout.addWidget(self.time_label)

        layout.addStretch()

        # 启动计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.start_time = None

    def set_status(self, status, color=None):
        """设置状态"""
        self.status_label.setText(status)

        if color:
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: {color};
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    text-align: center;
                }}
            """)
        elif status == "正在识别...":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    text-align: center;
                }
            """)
        elif status == "已暂停":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: #FF9800;
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    text-align: center;
                }
            """)
        elif status == "已停止":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: #f44336;
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    text-align: center;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    text-align: center;
                }
            """)

    def update_energy(self, level):
        """更新能量级别"""
        self.energy_bar.setValue(level)

    def start_timer(self):
        """启动计时器"""
        self.start_time = time.time()
        self.timer.start(1000)  # 每秒更新一次

    def stop_timer(self):
        """停止计时器"""
        self.timer.stop()
        self.time_label.setText("00:00:00")

    def update_time(self):
        """更新时间显示"""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


# 导出所有组件
__all__ = [
    'VoiceEnergyBar',
    'ModeSelector',
    'ControlPanel',
    'LogDisplay',
    'ResultDisplay',
    'StatusBar'
]