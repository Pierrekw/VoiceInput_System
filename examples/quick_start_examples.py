#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 快速入门示例集
基于Voice Energy Bar项目的实用示例
"""

import sys
import random
import time
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit, QGroupBox,
    QSlider, QSpinBox, QComboBox, QCheckBox, QRadioButton,
    QButtonGroup, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette

# ==============================================================================
# 示例1: 基础窗口和布局
# ==============================================================================

class BasicWindowExample(QMainWindow):
    """示例1: 基础窗口和布局"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("示例1: 基础窗口和布局")
        self.setGeometry(200, 200, 400, 300)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 垂直布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("🎯 PySide6 基础布局示例")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 按钮水平布局
        button_layout = QHBoxLayout()

        btn1 = QPushButton("按钮1")
        btn2 = QPushButton("按钮2")
        btn3 = QPushButton("按钮3")

        button_layout.addWidget(btn1)
        button_layout.addWidget(btn2)
        button_layout.addWidget(btn3)

        main_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(30)
        main_layout.addWidget(self.progress_bar)

        # 文本显示
        self.status_label = QLabel("状态: 准备就绪")
        main_layout.addWidget(self.status_label)

        # 连接信号
        btn1.clicked.connect(lambda: self.update_progress(25))
        btn2.clicked.connect(lambda: self.update_progress(50))
        btn3.clicked.connect(lambda: self.update_progress(75))

        # 应用样式
        self.apply_basic_styles()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"状态: 进度更新为 {value}%")

    def apply_basic_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

# ==============================================================================
# 示例2: 自定义组件
# ==============================================================================

class CustomProgressBar(QProgressBar):
    """自定义进度条组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setFixedHeight(25)
        self.setTextVisible(True)

        # 自定义样式
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: #ecf0f1;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:0.5 #2ecc71, stop:1 #f39c12);
                margin: 1px;
            }
        """)

    def animate_to_value(self, target_value):
        """动画过渡到目标值"""
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.start()

class CustomComponentExample(QMainWindow):
    """示例2: 自定义组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        self.setWindowTitle("示例2: 自定义组件")
        self.setGeometry(250, 250, 450, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 标题
        title = QLabel("🎨 自定义进度条组件")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 自定义进度条
        self.custom_progress = CustomProgressBar()
        layout.addWidget(self.custom_progress)

        # 控制按钮
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("🚀 开始动画")
        self.stop_btn = QPushButton("⏸️ 暂停")
        self.reset_btn = QPushButton("🔄 重置")

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.reset_btn)

        layout.addLayout(control_layout)

        # 数值控制
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("目标值:"))

        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 100)
        self.value_spin.setValue(80)
        value_layout.addWidget(self.value_spin)

        self.set_btn = QPushButton("设置")
        value_layout.addWidget(self.set_btn)

        layout.addLayout(value_layout)

        # 连接信号
        self.start_btn.clicked.connect(self.start_animation)
        self.stop_btn.clicked.connect(self.stop_animation)
        self.reset_btn.clicked.connect(self.reset_progress)
        self.set_btn.clicked.connect(self.set_target_value)

        self.is_running = False

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.current_value = 0

    def start_animation(self):
        if not self.is_running:
            self.is_running = True
            self.timer.start(50)  # 20 FPS
            self.start_btn.setText("⏸️ 暂停")

    def stop_animation(self):
        self.is_running = False
        self.timer.stop()
        self.start_btn.setText("🚀 开始动画")

    def reset_progress(self):
        self.current_value = 0
        self.custom_progress.setValue(0)
        self.stop_animation()

    def set_target_value(self):
        target = self.value_spin.value()
        self.custom_progress.animate_to_value(target)

    def update_progress(self):
        if self.current_value < 100:
            self.current_value += 1
            self.custom_progress.setValue(self.current_value)
        else:
            self.stop_animation()

# ==============================================================================
# 示例3: 信号槽和事件处理
# ==============================================================================

class WorkerThread(QThread):
    """工作线程示例"""
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, duration=5):
        super().__init__()
        self.duration = duration
        self._should_stop = False

    def run(self):
        try:
            for i in range(101):
                if self._should_stop:
                    break

                self.progress.emit(i)
                time.sleep(self.duration / 100.0)  # duration秒完成

            if not self._should_stop:
                self.finished.emit(f"任务完成！用时 {self.duration} 秒")
        except Exception as e:
            self.error.emit(f"错误: {str(e)}")

    def stop(self):
        self._should_stop = True

class SignalSlotExample(QMainWindow):
    """示例3: 信号槽和事件处理"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        self.setWindowTitle("示例3: 信号槽和事件处理")
        self.setGeometry(300, 300, 500, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 标题
        title = QLabel("⚡ 信号槽和事件处理")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 任务控制
        task_group = QGroupBox("任务控制")
        task_layout = QVBoxLayout(task_group)

        # 进度显示
        self.task_progress = QProgressBar()
        task_layout.addWidget(self.task_progress)

        # 控制按钮
        button_layout = QHBoxLayout()

        self.start_task_btn = QPushButton("▶️ 开始任务")
        self.stop_task_btn = QPushButton("⏹️ 停止任务")
        self.stop_task_btn.setEnabled(False)

        button_layout.addWidget(self.start_task_btn)
        button_layout.addWidget(self.stop_task_btn)
        task_layout.addLayout(button_layout)

        # 时长设置
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("任务时长(秒):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(5)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        task_layout.addLayout(duration_layout)

        layout.addWidget(task_group)

        # 事件日志
        log_group = QGroupBox("事件日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 连接信号
        self.start_task_btn.clicked.connect(self.start_task)
        self.stop_task_btn.clicked.connect(self.stop_task)

    def start_task(self):
        self.worker = WorkerThread(self.duration_spin.value())
        self.worker.progress.connect(self.task_progress.setValue)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.error.connect(self.on_task_error)
        self.worker.finished.connect(self.on_task_completed)

        self.worker.start()

        self.start_task_btn.setEnabled(False)
        self.stop_task_btn.setEnabled(True)
        self.duration_spin.setEnabled(False)

        self.log_message(f"🚀 开始任务，预计用时 {self.duration_spin.value()} 秒")

    def stop_task(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        self.start_task_btn.setEnabled(True)
        self.stop_task_btn.setEnabled(False)
        self.duration_spin.setEnabled(True)

        self.log_message("⏹️ 任务已停止")

    def on_task_finished(self, message):
        self.log_message(f"✅ {message}")

    def on_task_error(self, error_msg):
        self.log_message(f"❌ {error_msg}")

    def on_task_completed(self):
        self.start_task_btn.setEnabled(True)
        self.stop_task_btn.setEnabled(False)
        self.duration_spin.setEnabled(True)

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

# ==============================================================================
# 示例4: 高级UI布局
# ==============================================================================

class AdvancedLayoutExample(QMainWindow):
    """示例4: 高级UI布局"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("示例4: 高级UI布局")
        self.setGeometry(350, 350, 600, 450)

        # 使用分割窗口
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧面板 - 使用标签页
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置初始比例
        splitter.setSizes([200, 400])

    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 控制组
        control_group = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_group)

        # 下拉框
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["快速", "标准", "精确"])
        combo_layout.addWidget(self.mode_combo)
        control_layout.addLayout(combo_layout)

        # 复选框
        self.auto_check = QCheckBox("自动模式")
        self.debug_check = QCheckBox("调试模式")
        control_layout.addWidget(self.auto_check)
        control_layout.addWidget(self.debug_check)

        # 单选按钮组
        radio_group = QGroupBox("显示选项")
        radio_layout = QVBoxLayout(radio_group)

        self.radio_group = QButtonGroup()
        self.radio_simple = QRadioButton("简单显示")
        self.radio_detail = QRadioButton("详细显示")
        self.radio_chart = QRadioButton("图表显示")

        self.radio_group.addButton(self.radio_simple, 0)
        self.radio_group.addButton(self.radio_detail, 1)
        self.radio_group.addButton(self.radio_chart, 2)

        self.radio_simple.setChecked(True)

        radio_layout.addWidget(self.radio_simple)
        radio_layout.addWidget(self.radio_detail)
        radio_layout.addWidget(self.radio_chart)

        control_layout.addWidget(radio_group)

        # 滑块
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(QLabel("速度:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        slider_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("当前值: 5")
        slider_layout.addWidget(self.speed_label)

        control_layout.addLayout(slider_layout)

        layout.addWidget(control_group)

        # 操作按钮
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)

        self.apply_btn = QPushButton("应用设置")
        self.reset_btn = QPushButton("重置默认")
        self.export_btn = QPushButton("导出配置")

        action_layout.addWidget(self.apply_btn)
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.export_btn)

        layout.addWidget(action_group)

        layout.addStretch()

        # 连接信号
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"当前值: {v}")
        )
        self.apply_btn.clicked.connect(self.apply_settings)
        self.reset_btn.clicked.connect(self.reset_settings)
        self.export_btn.clicked.connect(self.export_config)

        return panel

    def create_right_panel(self):
        """创建右侧面板"""
        tab_widget = QTabWidget()

        # 状态标签页
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)

        status_group = QGroupBox("系统状态")
        status_group_layout = QVBoxLayout(status_group)

        self.status_labels = {}
        status_items = [
            ("运行状态", "就绪"),
            ("处理速度", "5"),
            ("当前模式", "快速"),
            ("自动模式", "关闭"),
            ("调试模式", "关闭")
        ]

        for item, value in status_items:
            label = QLabel(f"{item}: {value}")
            self.status_labels[item] = label
            status_group_layout.addWidget(label)

        status_layout.addWidget(status_group)
        status_layout.addStretch()

        tab_widget.addTab(status_tab, "状态")

        # 配置标签页
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMaximumHeight(300)
        config_layout.addWidget(self.config_text)

        config_layout.addStretch()

        tab_widget.addTab(config_tab, "配置")

        # 日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        tab_widget.addTab(log_tab, "日志")

        return tab_widget

    def apply_settings(self):
        """应用设置"""
        mode = self.mode_combo.currentText()
        speed = self.speed_slider.value()
        auto = self.auto_check.isChecked()
        debug = self.debug_check.isChecked()
        display = self.radio_group.checkedId()

        # 更新状态
        self.status_labels["当前模式"].setText(f"当前模式: {mode}")
        self.status_labels["处理速度"].setText(f"处理速度: {speed}")
        self.status_labels["自动模式"].setText(f"自动模式: {'开启' if auto else '关闭'}")
        self.status_labels["调试模式"].setText(f"调试模式: {'开启' if debug else '关闭'}")

        display_names = ["简单显示", "详细显示", "图表显示"]
        self.status_labels["运行状态"].setText(f"运行状态: 已应用 ({display_names[display]})")

        # 更新配置文本
        config = f"""
当前配置:
- 模式: {mode}
- 速度: {speed}
- 自动模式: {auto}
- 调试模式: {debug}
- 显示方式: {display_names[display]}
"""
        self.config_text.setText(config)

        # 添加日志
        self.add_log("✅ 设置已应用")

    def reset_settings(self):
        """重置设置"""
        self.mode_combo.setCurrentIndex(0)
        self.speed_slider.setValue(5)
        self.auto_check.setChecked(False)
        self.debug_check.setChecked(False)
        self.radio_simple.setChecked(True)

        self.status_labels["运行状态"].setText("运行状态: 已重置")
        self.add_log("🔄 设置已重置为默认值")

    def export_config(self):
        """导出配置"""
        config = {
            "mode": self.mode_combo.currentText(),
            "speed": self.speed_slider.value(),
            "auto_mode": self.auto_check.isChecked(),
            "debug_mode": self.debug_check.isChecked(),
            "display_type": self.radio_group.checkedId()
        }

        # 模拟导出
        self.add_log(f"📤 配置已导出: {config}")

    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

# ==============================================================================
# 主示例选择器
# ==============================================================================

class ExampleSelector(QMainWindow):
    """示例选择器"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PySide6 学习示例集")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 标题
        title = QLabel("🎓 PySide6 学习示例集")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2196F3; margin: 20px;")
        layout.addWidget(title)

        # 示例按钮
        examples = [
            ("📐 示例1: 基础窗口和布局", BasicWindowExample),
            ("🎨 示例2: 自定义组件", CustomComponentExample),
            ("⚡ 示例3: 信号槽和事件处理", SignalSlotExample),
            ("🏗️ 示例4: 高级UI布局", AdvancedLayoutExample),
        ]

        for text, example_class in examples:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #2196F3;
                }
            """)
            btn.clicked.connect(lambda checked, cls=example_class: self.open_example(cls))
            layout.addWidget(btn)

        layout.addStretch()

        # 底部信息
        info = QLabel("选择一个示例开始学习 PySide6")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666; font-style: italic; margin: 20px;")
        layout.addWidget(info)

    def open_example(self, example_class):
        """打开示例窗口"""
        example = example_class()
        example.show()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("PySide6 学习示例集")

    # 设置应用样式
    app.setStyle('Fusion')

    # 显示选择器
    selector = ExampleSelector()
    selector.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()