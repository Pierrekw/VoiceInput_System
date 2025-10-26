#!/usr/bin/env python3
"""
FunASR语音识别GUI系统 - 重构版本
基于组件化架构的语音识别图形界面
使用gui_components.py中的组件构建
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from logging_utils import LoggingManager

logger = LoggingManager.get_logger(
    name='voice_gui_refractor',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont

# 导入自定义组件
from gui_components import (
    VoiceEnergyBar, ModeSelector, ControlPanel,
    LogDisplay, ResultDisplay, StatusBar
)

# 导入工作线程
from voice_gui import WorkingVoiceWorker

os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'


class VoiceRecognitionApp(QMainWindow):
    """语音识别主应用 - 重构版本"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_mode = "balanced"
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("FunASR语音识别系统 - 重构版")
        self.setGeometry(100, 100, 1200, 800)

        # 应用整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333;
            }
        """)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("🎤 FunASR语音识别系统")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196F3;
                padding: 20px;
                background-color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)

        # 创建主要组件
        self.create_main_components(main_layout)

        # 创建状态栏
        self.status_bar = StatusBar()
        self.status_bar.set_status("就绪")
        main_layout.addWidget(self.status_bar)

    def create_main_components(self, parent_layout):
        """创建主要组件"""
        # 顶部控制面板
        top_panel = QGroupBox("控制面板")
        top_layout = QHBoxLayout(top_panel)

        # 模式选择器
        self.mode_selector = ModeSelector()
        self.mode_selector.mode_changed.connect(self.on_mode_changed)
        top_layout.addWidget(self.mode_selector)

        # 控制按钮
        self.control_panel = ControlPanel()
        self.control_panel.start_clicked.connect(self.start_recognition)
        self.control_panel.stop_clicked.connect(self.stop_recognition)
        self.control_panel.pause_clicked.connect(self.pause_recognition)
        top_layout.addWidget(self.control_panel)

        parent_layout.addWidget(top_panel)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        parent_layout.addWidget(splitter)

        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setSizes([600, 600])

    def create_left_panel(self):
        """创建左侧面板"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 实时结果显示
        result_group = QGroupBox("实时识别")
        result_layout = QVBoxLayout(result_group)

        self.result_display = ResultDisplay()
        result_layout.addWidget(self.result_display)

        left_layout.addWidget(result_group)

        # 系统日志
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)

        self.log_display = LogDisplay()
        log_layout.addWidget(self.log_display)

        left_layout.addWidget(log_group)

        return left_panel

    def create_right_panel(self):
        """创建右侧面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 能量显示
        energy_group = QGroupBox("语音能量")
        energy_layout = QVBoxLayout(energy_group)

        self.energy_bar = VoiceEnergyBar()
        self.energy_bar.setFixedHeight(30)
        energy_layout.addWidget(self.energy_bar)

        right_layout.addWidget(energy_group)

        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        self.info_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: #f9f9f9;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.info_text)

        right_layout.addWidget(info_group)

        right_layout.addStretch()

        return right_panel

    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_system_info)
        self.update_timer.start(5000)  # 每5秒更新一次

    def on_mode_changed(self, mode):
        """模式改变处理"""
        self.current_mode = mode
        self.log_display.append_log(f"切换到 {mode} 模式")

    def start_recognition(self):
        """开始识别"""
        if self.worker and self.worker.isRunning():
            self.log_display.append_log("⚠️ 识别已在运行中")
            return

        try:
            self.log_display.append_log(f"🚀 开始语音识别 (模式: {self.current_mode})")

            # 创建工作线程
            self.worker = WorkingVoiceWorker(mode=self.current_mode)

            # 连接信号
            self.worker.log_message.connect(self.on_log_message)
            self.worker.recognition_result.connect(self.on_recognition_result)
            self.worker.partial_result.connect(self.on_partial_result)
            self.worker.status_changed.connect(self.on_status_changed)
            self.worker.voice_activity.connect(self.on_voice_activity)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.system_initialized.connect(self.on_system_initialized)

            # 启动工作线程
            self.worker.start()

            # 更新UI状态
            self.control_panel.set_running_state(True)
            self.status_bar.set_status("正在识别...")
            self.status_bar.start_timer()

        except Exception as e:
            self.log_display.append_log(f"❌ 启动失败: {e}")
            QMessageBox.critical(self, "错误", f"启动识别失败: {e}")

    def stop_recognition(self):
        """停止识别"""
        if not self.worker:
            return

        try:
            self.log_display.append_log("🛑 正在停止语音识别...")

            # 停止工作线程
            self.worker.stop()

            # 更新UI状态
            self.status_bar.set_status("正在停止...")
            self.status_bar.stop_timer()

        except Exception as e:
            self.log_display.append_log(f"❌ 停止失败: {e}")

    def pause_recognition(self):
        """暂停/恢复识别"""
        if not self.worker:
            return

        try:
            if hasattr(self.worker, '_is_paused') and self.worker._is_paused:
                self.worker.resume()
                self.log_display.append_log("▶️ 恢复识别")
                self.status_bar.set_status("正在识别...")
            else:
                self.worker.pause()
                self.log_display.append_log("⏸️ 暂停识别")
                self.status_bar.set_status("已暂停")
        except Exception as e:
            self.log_display.append_log(f"❌ 暂停/恢复失败: {e}")

    def on_log_message(self, message):
        """处理日志消息"""
        self.log_display.append_log(message)

    def on_recognition_result(self, text):
        """处理识别结果"""
        if text and text.strip():
            self.result_display.add_result(text, is_valid=True)
            self.log_display.append_log(f"🎯 识别结果: {text}")

    def on_partial_result(self, text):
        """处理部分识别结果"""
        if text and text.strip():
            self.log_display.append_log(f"🔊 实时识别: {text}")

    def on_status_changed(self, status):
        """处理状态改变"""
        self.log_display.append_log(f"📊 状态: {status}")

    def on_voice_activity(self, level):
        """处理语音活动"""
        self.energy_bar.setValue(level)
        self.status_bar.update_energy(level)

    def on_worker_finished(self):
        """工作线程完成"""
        self.log_display.append_log("✅ 识别线程已结束")

        # 更新UI状态
        self.control_panel.set_running_state(False)
        self.status_bar.set_status("已停止")
        self.energy_bar.setValue(0)

        # 清理工作线程
        if self.worker:
            self.worker = None

    def on_system_initialized(self):
        """系统初始化完成"""
        self.log_display.append_log("✅ 系统初始化完成")

    def update_system_info(self):
        """更新系统信息"""
        try:
            info_lines = []
            info_lines.append(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            info_lines.append(f"当前模式: {self.current_mode}")

            if self.worker:
                info_lines.append(f"工作线程: {'运行中' if self.worker.isRunning() else '已停止'}")

                if hasattr(self.worker, '_is_paused') and self.worker._is_paused:
                    info_lines.append("状态: 已暂停")
                else:
                    info_lines.append("状态: 正在识别")
            else:
                info_lines.append("工作线程: 未启动")

            info_lines.append(f"识别次数: {self.result_display.total_count}")
            info_lines.append(f"有效次数: {self.result_display.valid_count}")

            # 显示Excel文件信息（如果有的话）
            if hasattr(self, 'last_excel_path') and self.last_excel_path:
                info_lines.append(f"Excel文件: {os.path.basename(self.last_excel_path)}")

            self.info_text.setText('\n'.join(info_lines))

        except Exception as e:
            logger.error(f"更新系统信息失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            if self.worker and self.worker.isRunning():
                self.log_display.append_log("🔄 正在停止识别线程...")
                self.worker.stop()
                self.worker.wait(3000)  # 等待3秒

                if self.worker.isRunning():
                    self.log_display.append_log("⚠️ 强制终止识别线程")
                    self.worker.terminate()
                    self.worker.wait(1000)

            event.accept()
            logger.info("应用程序已关闭")

        except Exception as e:
            logger.error(f"关闭应用程序时出错: {e}")
            event.accept()  # 无论如何都允许关闭


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = VoiceRecognitionApp()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()