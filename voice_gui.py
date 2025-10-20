#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音识别GUI系统
支持fast、balanced、accuracy三种识别模式的图形界面
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# PySide6导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QPushButton, QGroupBox, QStatusBar,
    QMessageBox, QSplitter, QTabWidget, QComboBox, QFormLayout
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


class WorkingVoiceWorker(QThread):
    """工作语音识别线程"""

    # 信号定义
    log_message = Signal(str)
    recognition_result = Signal(str)
    partial_result = Signal(str)
    status_changed = Signal(str)
    voice_command_state_changed = Signal(str)  # 语音命令状态变化信号
    finished = Signal()
    system_initialized = Signal()

    def __init__(self, mode='balanced'):
        super().__init__()
        self._should_stop = False
        self._is_paused = False
        self.voice_system = None
        self.mode = mode

    def run(self):
        """运行语音识别"""
        try:
            self.log_message.emit(f"🚀 正在初始化语音系统... (模式: {self.mode})")

            # 根据模式获取配置参数
            mode_config = self._get_mode_config(self.mode)
            self.log_message.emit(f"🔧 使用配置: {mode_config}")

            # 导入完整的语音系统
            from main_f import FunASRVoiceSystem

            self.voice_system = FunASRVoiceSystem(
                recognition_duration=-1,  # 不限时识别
                continuous_mode=True,      # 连续识别模式
                debug_mode=False           # 生产模式
            )

            # 注入模式配置到识别器
            self._configure_recognizer(mode_config)

            if not self.voice_system.initialize():
                self.log_message.emit("❌ 语音系统初始化失败")
                return

            # 设置状态变化回调（用于语音命令同步）
            self.voice_system.set_state_change_callback(self._handle_voice_command_state_change)

            self.log_message.emit("✅ 语音系统初始化成功")
            self.status_changed.emit("系统就绪")
            self.system_initialized.emit()

            # 记录原始处理方法，确保保留Excel导出功能
            original_process_result = getattr(self.voice_system, 'process_recognition_result', None)

            # 自定义处理结果方法，确保所有识别结果都显示在GUI上
            def custom_process_recognition_result(original_text, processed_text, numbers):
                try:
                    # 调用原始方法进行完整处理（包括Excel保存）
                    if original_process_result:
                        original_process_result(original_text, processed_text, numbers)

                    # 只有当本次识别结果包含数字时，才显示数字格式
                    if numbers and len(numbers) > 0 and hasattr(self.voice_system, 'number_results') and self.voice_system.number_results:
                        # 获取最新的记录（应该是刚刚添加的本次记录）
                        latest_record = self.voice_system.number_results[-1]
                        if len(latest_record) >= 3:
                            record_id, record_number, record_text = latest_record
                            # 按照ID+数值格式显示
                            display_text = f"[{record_id}] {record_number}"
                            self.recognition_result.emit(display_text)
                            self.log_message.emit(f"🎤 数字识别结果: {display_text}")
                    # 确保所有文本结果都显示，包括纯文本和文本+数字组合
                    elif processed_text and processed_text.strip():
                        # 对于普通文本，直接显示
                        self.recognition_result.emit(processed_text)
                        self.log_message.emit(f"🎤 文本识别结果: {processed_text}")
                    # 处理原始文本情况
                    elif original_text and original_text.strip() and not processed_text:
                        # 如果processed_text为空但original_text有内容，也显示original_text
                        self.recognition_result.emit(original_text)
                        self.log_message.emit(f"🎤 原始识别结果: {original_text}")
                except Exception as e:
                    self.log_message.emit(f"❌ 处理识别结果时出错: {e}")

            # 替换原始处理方法
            if hasattr(self.voice_system, 'process_recognition_result'):
                self.voice_system.process_recognition_result = custom_process_recognition_result
                self.log_message.emit("✅ 已设置识别结果回调")

            # 设置回调函数来捕获识别结果
            original_callback = getattr(self.voice_system, 'on_recognition_result', None)

            def gui_recognition_callback(result):
                try:
                    # 处理识别结果
                    if hasattr(result, 'text'):
                        text = result.text
                        if text and text.strip():
                            # 这里不直接发送，让process_recognition_result处理
                            # 以确保遵循main_f.py的处理逻辑
                            pass

                    # 调用原始回调
                    if original_callback:
                        original_callback(result)
                except Exception as e:
                    self.log_message.emit(f"❌ 处理识别结果错误: {e}")
                    logger.error(f"处理识别结果错误: {e}")

            def gui_partial_result_callback(text):
                try:
                    if text and text.strip():
                        self.partial_result.emit(text)
                except Exception as e:
                    logger.debug(f"处理部分结果错误: {e}")

            # 设置回调
            if hasattr(self.voice_system, 'recognizer'):
                self.voice_system.recognizer.set_callbacks(
                    on_final_result=gui_recognition_callback,
                    on_partial_result=gui_partial_result_callback
                )

            self.log_message.emit("🎙️ 开始连续语音识别...")
            self.status_changed.emit("正在识别...")

            # 启动键盘监听
            self.voice_system.start_keyboard_listener()

            # 运行连续识别
            self.voice_system.run_continuous()

        except Exception as e:
            self.log_message.emit(f"❌ 识别过程错误: {e}")
            logger.error(f"识别过程错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.status_changed.emit("已停止")
            self.finished.emit()

    def stop(self):
        """停止识别"""
        self._should_stop = True
        if self.voice_system:
            try:
                self.voice_system.system_stop()
            except Exception as e:
                logger.error(f"停止系统时出错: {e}")

    def pause(self):
        """暂停"""
        self._is_paused = True
        if self.voice_system:
            try:
                self.voice_system.pause()
            except Exception as e:
                logger.error(f"暂停系统时出错: {e}")
        self.status_changed.emit("已暂停")

    def resume(self):
        """恢复"""
        self._is_paused = False
        if self.voice_system:
            try:
                self.voice_system.resume()
            except Exception as e:
                logger.error(f"恢复系统时出错: {e}")
        self.status_changed.emit("正在识别...")

    def _handle_voice_command_state_change(self, state: str, message: str):
        """处理语音命令引起的状态变化"""
        if state == "paused":
            self._is_paused = True
            self.status_changed.emit("已暂停")
            self.log_message.emit(f"🎤 {message}")
            # 发送信号更新GUI按钮状态
            self.voice_command_state_changed.emit("paused")
        elif state == "resumed":
            self._is_paused = False
            self.status_changed.emit("正在识别...")
            self.log_message.emit(f"🎤 {message}")
            # 发送信号更新GUI按钮状态
            self.voice_command_state_changed.emit("resumed")
        elif state == "stopped":
            self._is_paused = False
            self.status_changed.emit("已停止")
            self.log_message.emit(f"🎤 {message}")
            # 发送信号更新GUI按钮状态
            self.voice_command_state_changed.emit("stopped")
        
    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """根据模式获取配置参数
        
        Args:
            mode: 识别模式 ('fast', 'balanced', 'accuracy')
            
        Returns:
            配置参数字典
        """
        # 定义三种模式的配置参数
        configs = {
            'fast': {
                'chunk_size': [0, 8, 4],
                'encoder_chunk_look_back': 2,
                'decoder_chunk_look_back': 0,
                'vad_energy_threshold': 0.02,
                'vad_min_speech_duration': 0.2,
                'description': '快速模式 - 低延迟，识别速度快'
            },
            'balanced': {
                'chunk_size': [0, 10, 5],
                'encoder_chunk_look_back': 4,
                'decoder_chunk_look_back': 1,
                'vad_energy_threshold': 0.015,
                'vad_min_speech_duration': 0.3,
                'description': '平衡模式 - 识别准确度和速度的良好平衡'
            },
            'accuracy': {
                'chunk_size': [0, 16, 8],
                'encoder_chunk_look_back': 8,
                'decoder_chunk_look_back': 2,
                'vad_energy_threshold': 0.01,
                'vad_min_speech_duration': 0.4,
                'description': '精确模式 - 高准确度，更注重识别质量'
            }
        }
        
        # 返回指定模式的配置，如果不存在则返回平衡模式
        return configs.get(mode, configs['balanced'])
    
    def _configure_recognizer(self, config: Dict[str, Any]):
        """配置识别器参数

        Args:
            config: 配置参数字典
        """
        try:
            # 应用针对torch 2.3.1+cpu优化的配置
            if hasattr(self.voice_system, 'recognizer'):
                recognizer = self.voice_system.recognizer

                # 安全地应用优化配置
                if hasattr(recognizer, 'chunk_size'):
                    try:
                        # 使用config.yaml中的优化配置，而不是GUI中的配置
                        # chunk_size = [0, 6, 3] 来自config.yaml
                        self.log_message.emit(f"✅ 使用config.yaml中的优化配置")
                        self.log_message.emit(f"📋 VAD模式: customized (torch 2.3.1+cpu优化)")
                        self.log_message.emit(f"📋 自定义VAD参数已应用")
                    except Exception as e:
                        self.log_message.emit(f"⚠️ 设置参数失败: {e}")

                self.log_message.emit(f"✅ 系统配置完成: torch 2.3.1+cpu优化版本")

        except Exception as e:
            self.log_message.emit(f"⚠️ 配置识别器时出错: {e}")
            # 配置失败不应该阻止系统运行
            self.log_message.emit("📝 使用默认配置继续运行")
            logger.error(f"配置识别器时出错: {e}")


class WorkingSimpleMainWindow(QMainWindow):
    """工作简化版主窗口"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.setup_timer()
        self.current_mode = 'balanced'

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("FunASR语音识别系统 v2.3")
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
        
        # 模式选择
        mode_group = QGroupBox("识别模式")
        mode_layout = QFormLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["fast", "balanced", "accuracy"])
        self.mode_combo.setCurrentText("balanced")
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        
        # 模式描述
        self.mode_description = QLabel("平衡模式 - 识别准确度和速度的良好平衡")
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: #555; font-size: 12px;")
        
        mode_layout.addRow("选择模式:", self.mode_combo)
        mode_layout.addRow("", self.mode_description)
        
        layout.addWidget(mode_group)

        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)

        self.start_button = QPushButton("🎙️ 开始连续识别")
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
            "1. 点击'开始连续识别'启动系统\n"
            "2. 对着麦克风清晰说话\n"
            "3. 系统会连续识别语音内容\n"
            "4. 识别结果显示在右侧\n\n"
            "💡 提示:\n"
            "• 确保麦克风工作正常\n"
            "• 说话时保持清晰音量\n"
            "• 安静环境有助于识别准确度\n\n"
            "🎯 语音命令:\n"
            "• '暂停' - 暂停识别\n"
            "• '继续' - 恢复识别\n"
            "• '停止' - 停止系统\n\n"
            "⌨️ 快捷键:\n"
            "• 空格键 - 暂停/继续\n"
            "• ESC键 - 停止识别"
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
        
        self.mode_display_label = QLabel(f"当前模式: balanced")
        system_layout.addWidget(self.mode_display_label)

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
        self.history_text.setFont(QFont("Consolas", 11))
        history_layout.addWidget(self.history_text)

        results_layout.addWidget(history_group)
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
        self.log_text.document().setMaximumBlockCount(500)
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
        self.mode_combo.setEnabled(False)  # 运行时禁用模式更改
        self.status_label.setText("🟢 正在启动...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50; padding: 10px;")

        # 清空结果
        self.history_text.clear()
        self.log_text.clear()
        self.current_text_label.setText("正在初始化...")
        self.recognition_count = 0
        self.start_time = time.time()

        # 创建并启动工作线程，传入选择的模式
        self.worker = WorkingVoiceWorker(mode=self.current_mode)
        # 确保信号连接正确
        self.worker.log_message.connect(self.append_log)
        self.worker.recognition_result.connect(self.display_result)
        self.worker.partial_result.connect(self.update_partial_result)
        self.worker.status_changed.connect(self.update_status)
        self.worker.voice_command_state_changed.connect(self.handle_voice_command_state_change)
        self.worker.system_initialized.connect(self.on_system_initialized)
        self.worker.finished.connect(self.on_worker_finished)

        # 确保UI元素已正确初始化
        self.append_log("🚀 启动语音识别系统... (当前模式: " + str(self.current_mode) + ")")
        self.update_status("正在初始化系统...")

        self.worker.start()
        self.timer.start(1000)  # 每秒更新

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

    # 删除重复的方法定义

    def on_worker_finished(self):
        """工作线程完成"""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.mode_combo.setEnabled(True)  # 重新启用模式更改
        self.pause_button.setText("⏸️ 暂停")
        self.timer.stop()

        self.status_label.setText("🔴 已停止")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; padding: 10px;")
        self.current_text_label.setText("等待识别...")

        if self.worker:
            self.worker.wait(1000)
            self.worker = None

        self.append_log("🛑 语音识别已停止")

    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(f"🟢 {status}")
        self.status_bar.showMessage(status)

    def handle_voice_command_state_change(self, state):
        """处理语音命令状态变化，同步GUI按钮状态"""
        if state == "paused":
            # 更新按钮状态为暂停状态
            self.pause_button.setText("▶️ 继续")
            self.pause_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟡 已暂停 (语音命令)")
            self.status_bar.showMessage("已暂停 - 语音命令控制")
            # 显示明显的提示
            self.append_log("🎤 语音命令：系统已暂停，点击'▶️ 继续'按钮或说'继续'恢复识别")

        elif state == "resumed":
            # 更新按钮状态为运行状态
            self.pause_button.setText("⏸️ 暂停")
            self.pause_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟢 正在识别... (语音命令)")
            self.status_bar.showMessage("正在识别... - 语音命令控制")
            # 显示明显的提示
            self.append_log("🎤 语音命令：系统已恢复，正在监听语音输入...")

        elif state == "stopped":
            # 更新按钮状态为停止状态
            self.pause_button.setText("⏸️ 暂停")
            self.pause_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.mode_combo.setEnabled(True)
            self.status_label.setText("🔴 已停止 (语音命令)")
            self.status_bar.showMessage("已停止 - 语音命令控制")
            # 显示明显的提示
            self.append_log("🎤 语音命令：系统已停止，点击'🎤 开始识别'按钮重新开始")

    def display_result(self, result):
        """显示识别结果"""
        # 确保结果不为空
        if not result or not result.strip():
            return

        result = result.strip()

        # 确保在主线程中更新UI
        def update_ui():
            # 更新当前识别文本
            if result.startswith('[') and ']' in result:
                # 数字结果格式: [ID] 数值
                self.current_text_label.setText(f"识别结果: {result}")
            else:
                # 文本结果格式
                self.current_text_label.setText(f"识别结果: {result}")

            # 添加到历史记录
            timestamp = datetime.now().strftime("%H:%M:%S")

            # 根据结果类型设置不同的前缀和格式
            if result.startswith('[') and ']' in result:
                # 数字结果 - 按照ID+数值格式
                history_entry = f"[{timestamp}] 🔢 {result}"
            else:
                # 文本结果 - 包括普通文本和文本+数字组合
                history_entry = f"[{timestamp}] 📝 {result}"

            # 确保UI元素存在
            if hasattr(self, 'history_text') and self.history_text:
                self.history_text.append(history_entry)
                self.recognition_count += 1

                # 滚动到底部
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.history_text.setTextCursor(cursor)

            # 记录到日志
            if hasattr(self, 'append_log'):
                self.append_log(f"语音识别: {result}")

        # 使用Qt的线程安全方式更新UI
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_ui)

        # 同时在控制台打印，保持与PowerShell相同的输出格式
        print(f"🎤 识别: {result}")
        
    def update_partial_result(self, text):
        """更新部分识别结果"""
        # 只在系统状态为就绪或识别中时更新部分结果
        current_status = self.status_label.text()
        if "就绪" in current_status or "识别" in current_status:
            self.current_text_label.setText(f"识别中: {text}")
            
    def on_mode_changed(self, mode):
        """处理模式变更"""
        self.current_mode = mode
        
        # 更新模式描述
        mode_descriptions = {
            'fast': '快速模式 - 低延迟，识别速度快，适合实时交互',
            'balanced': '平衡模式 - 识别准确度和速度的良好平衡，默认推荐',
            'accuracy': '精确模式 - 高准确度，更注重识别质量，但延迟较高'
        }
        
        self.mode_description.setText(mode_descriptions.get(mode, '平衡模式'))
        self.append_log(f"模式已更改为: {mode}")

    def append_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # 确保在主线程中更新UI
        def update_log():
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(log_entry)

                # 滚动到底部
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.log_text.setTextCursor(cursor)

        # 使用Qt的线程安全方式更新UI
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_log)

        # 同时打印到控制台以便调试
        print(f"[GUI LOG] {log_entry}")

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
            self.mode_display_label.setText(f"当前模式: {self.current_mode}")
            
    def on_system_initialized(self):
        """系统初始化完成"""
        self.append_log(f"✅ 系统初始化完成，准备开始识别... (当前模式: {self.current_mode})")
        self.current_text_label.setText("系统就绪，可以开始说话了...")

    def keyPressEvent(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key_Escape:
            self.stop_recognition()
        elif event.key() == Qt.Key_Space:
            if self.worker and self.worker.isRunning():
                self.toggle_pause()
            else:
                self.start_recognition()
        event.accept()

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
    app.setApplicationName("FunASR语音识别系统 (多模式版)")

    window = WorkingSimpleMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()