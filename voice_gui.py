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
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

# 使用统一的日志工具类
from logging_utils import get_app_logger

# 获取配置好的日志记录器
logger = get_app_logger(__name__, debug=False)  # 如需调试模式，设置debug=True

# 抑制输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

# PySide6导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QPushButton, QGroupBox, QStatusBar,
    QMessageBox, QSplitter, QTabWidget, QComboBox, QFormLayout, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor

# 配置日志
logging.basicConfig(level=logging.INFO)  # 降低日志级别，减少输出量
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
    voice_activity = Signal(int)  # 语音活动级别信号 (0-100)
    finished = Signal()
    system_initialized = Signal()

    def __init__(self, mode='customized'):
        super().__init__()
        self._should_stop = False
        self._is_paused = False
        self.voice_system = None
        self.mode = mode

    def run(self):
        """运行语音识别"""
        try:
            # 🔍 调试 - Worker线程开始运行
            logger.info(f"[🧵 WORKER启动] 🚀 Worker线程开始运行")
            print(f"[🧵 WORKER启动] 🚀 Worker线程开始运行")
            self.log_message.emit(f"🧵 Worker线程启动，模式: {self.mode}")

            print(f"[CRITICAL] 开始初始化语音识别系统")
            self.log_message.emit(f"🚀 正在初始化语音系统... (模式: {self.mode})")

            # 根据模式获取配置参数
            mode_config = self._get_mode_config(self.mode)
            self.log_message.emit(f"🔧 使用配置: {mode_config}")

            # 导入完整的语音系统
            logger.info(f"[🧵 WORKER导入] 📦 开始导入FunASRVoiceSystem")
            print(f"[🧵 WORKER导入] 📦 开始导入FunASRVoiceSystem")

            from main_f import FunASRVoiceSystem

            logger.info(f"[🧵 WORKER创建] 🏗️ 创建FunASRVoiceSystem实例")
            print(f"[🧵 WORKER创建] 🏗️ 创建FunASRVoiceSystem实例")

            self.voice_system = FunASRVoiceSystem(
                recognition_duration=-1,  # 不限时识别
                continuous_mode=True,      # 连续识别模式
                debug_mode=False           # 生产模式
            )

            logger.info(f"[🧵 WORKER创建] ✅ FunASRVoiceSystem创建完成")
            print(f"[🧵 WORKER创建] ✅ FunASRVoiceSystem创建完成")

            # 注入模式配置到识别器
            self._configure_recognizer(mode_config)

            if not self.voice_system.initialize():
                self.log_message.emit("❌ 语音系统初始化失败")
                return

            # 设置状态变化回调（用于语音命令同步）
            logger.info(f"[🔗 WORKER设置] 🔧 开始设置状态变化回调")
            print(f"[🔗 WORKER设置] 🔧 开始设置状态变化回调")
            self.voice_system.set_state_change_callback(self._handle_voice_command_state_change)
            logger.info(f"[🔗 WORKER设置] ✅ 状态变化回调设置成功")
            print(f"[🔗 WORKER设置] ✅ 状态变化回调设置成功")

            # 设置VAD事件回调（用于语音能量显示）
            logger.info(f"[🔗 WORKER设置] 📡 准备设置VAD回调: voice_system.set_vad_callback(_handle_vad_event)")
            print(f"[🔗 WORKER设置] 📡 准备设置VAD回调: voice_system.set_vad_callback(_handle_vad_event)")

            # 检查voice_system对象
            logger.info(f"[🔗 WORKER检查] voice_system类型: {type(self.voice_system)}")
            logger.info(f"[🔗 WORKER检查] voice_system方法: {[method for method in dir(self.voice_system) if 'vad' in method.lower() or 'callback' in method.lower()]}")
            print(f"[🔗 WORKER检查] voice_system类型: {type(self.voice_system)}")

            if hasattr(self.voice_system, 'set_vad_callback'):
                logger.info(f"[🔗 WORKER设置] ✅ voice_system有set_vad_callback方法，开始设置")
                print(f"[🔗 WORKER设置] ✅ voice_system有set_vad_callback方法，开始设置")

                try:
                    self.voice_system.set_vad_callback(self._handle_vad_event)
                    logger.info(f"[🔗 WORKER设置] ✅ VAD回调设置成功")
                    print(f"[🔗 WORKER设置] ✅ VAD回调设置成功")
                    self.log_message.emit("✅ 已设置VAD能量监听")

                    # 发送测试VAD事件来验证连接（已注释，避免启动时显示）
                    # logger.info(f"[🔗 WORKER测试] 🧪 发送测试VAD事件验证连接")
                    # print(f"[🔗 WORKER测试] 🧪 发送测试VAD事件验证连接")
                    # test_event_data = {'energy': 0.005}
                    # self._handle_vad_event('energy_update', test_event_data)
                    # logger.info(f"[🔗 WORKER测试] ✅ 测试VAD事件发送完成")
                    # print(f"[🔗 WORKER测试] ✅ 测试VAD事件发送完成")

                except Exception as e:
                    logger.error(f"[🔗 WORKER错误] ❌ VAD回调设置失败: {e}")
                    print(f"[🔗 WORKER错误] ❌ VAD回调设置失败: {e}")
                    import traceback
                    logger.error(f"[🔗 WORKER详细] {traceback.format_exc()}")
            else:
                logger.error(f"[🔗 WORKER错误] ❌ voice_system没有set_vad_callback方法！")
                print(f"[🔗 WORKER错误] ❌ voice_system没有set_vad_callback方法！")

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

                    # 优先检查是否产生了新的记录结果（数字或特殊文本）
                    has_new_record = False
                    if hasattr(self.voice_system, 'number_results') and self.voice_system.number_results:
                        # 检查是否有新记录（通过比较记录数量）
                        # 注意：这里假设调用original_process_result后会立即产生新记录
                        latest_record = self.voice_system.number_results[-1]
                        if len(latest_record) >= 3:
                            record_id, record_number, record_text = latest_record

                            # 验证这个记录是否对应当前的识别结果
                            is_matching_record = False
                            if record_text:
                                if record_text == processed_text or record_text == original_text:
                                    is_matching_record = True
                                elif numbers and len(numbers) > 0:
                                    if isinstance(record_number, (int, float)):
                                        # 数值记录：比较数值
                                        try:
                                            if float(record_number) == numbers[0]:
                                                is_matching_record = True
                                        except:
                                            pass
                                    elif str(numbers[0]) in str(record_number):
                                        # 字符串记录包含数字
                                        is_matching_record = True

                            if is_matching_record:
                                has_new_record = True

                                # 判断是否为特殊文本（通过检查record_number是否为字符串）
                                if isinstance(record_number, str) and record_text and record_text.strip():
                                    # 特殊文本：直接显示record_number（OK/Not OK）
                                    display_text = f"[{record_id}] {record_number}"
                                else:
                                    # 普通数字显示数值
                                    display_text = f"[{record_id}] {record_number}"

                                self.recognition_result.emit(display_text)
                                self.log_message.emit(f"🎤 识别结果: {display_text}")

                    # 如果没有新记录，显示文本结果
                    if not has_new_record:
                        # 确保所有文本结果都显示，包括纯文本
                        if processed_text and processed_text.strip():
                            # 对于没有记录的普通文本，直接显示
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
        # 发送正确的状态变化信号
        self.status_changed.emit("已停止")

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

    def display_result(self, result):
        """显示识别结果 - 只显示record类型的信息"""
        # 确保结果不为空
        if not result or not result.strip():
            return

        result = result.strip()

        # 检查是否为record类型（格式：[ID] 数值 或 [ID] OK/NOT OK等）
        is_record = result.startswith('[') and ']' in result and ('] ' in result or ']' in result and len(result) > 3)

        # 如果不是record类型，直接返回（不显示在识别历史中）
        if not is_record:
            # 只在日志中记录，不在历史中显示
            if hasattr(self, 'append_log'):
                self.append_log(f"过滤非record信息: {result}")
                # 移除模拟能量数据，避免干扰实际能量条显示
            return

        # 确保在主线程中更新UI
        def update_ui():
            # 更新当前识别文本
            self.current_text_label.setText(f"识别结果: {result}")

            # 添加到历史记录（只显示record类型）
            timestamp = datetime.now().strftime("%H:%M:%S")
            history_entry = f"[{timestamp}] 🔢 {result}"

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
                self.append_log(f"语音识别(record): {result}")

        # 使用Qt的线程安全方式更新UI
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_ui)

        # 移除模拟能量数据，避免干扰实际能量条显示

        # 同时在控制台打印，保持与PowerShell相同的输出格式
        print(f"🎤 识别(record): {result}")
        
    def update_partial_result(self, text):
        """更新部分识别结果"""
        # 只在系统状态为就绪或识别中时更新部分结果
        current_status = self.status_label.text()
        if "就绪" in current_status or "识别" in current_status:
            self.current_text_label.setText(f"识别中: {text}")

    def update_voice_energy(self, energy_level):
        """更新语音能量显示"""
        # 🔍 调试输出 - 在GUI主线程中接收能量更新信号
        logger.info(f"[🖥️ GUI主线程] ← 收到voice_activity信号: {energy_level}%")
        print(f"[🖥️ GUI主线程] ← 收到voice_activity信号: {energy_level}%")

        # 添加日志到GUI界面
        self.append_log(f"📊 GUI能量条更新: {energy_level}%")

        # 检查能量条对象
        if hasattr(self, 'voice_energy_bar') and self.voice_energy_bar:
            logger.info(f"[🖥️ GUI能量条] ✅ 能量条对象存在，开始更新")
            print(f"[🖥️ GUI能量条] ✅ 能量条对象存在，开始更新")

            try:
                # 直接在当前线程中更新（PySide6的QProgressBar是线程安全的）
                logger.info(f"[🖥️ GUI更新] 🔄 设置能量条值: {energy_level}%")
                self.voice_energy_bar.setValue(energy_level)
                # 也调用update_energy方法以保持一致性
                self.voice_energy_bar.update_energy(energy_level)
                logger.info(f"[🖥️ GUI成功] ✅ 能量条更新完成: {energy_level}%")
                print(f"[🖥️ GUI成功] ✅ 能量条更新完成: {energy_level}%")
            except Exception as e:
                logger.error(f"[🖥️ GUI错误] ❌ 能量条更新失败: {e}")
                print(f"[🖥️ GUI错误] ❌ 能量条更新失败: {e}")
        else:
            logger.error(f"[🖥️ GUI错误] ❌ 能量条未初始化或不存在！")
            print(f"[🖥️ GUI错误] ❌ 能量条未初始化或不存在！")
            self.append_log("❌ GUI错误: 能量条未初始化")

            # 调试：检查所有可能的能量条属性
            energy_attrs = [attr for attr in dir(self) if 'energy' in attr.lower()]
            logger.info(f"[🖥️ GUI调试] 🔍 找到energy相关属性: {energy_attrs}")
            print(f"[🖥️ GUI调试] 🔍 找到energy相关属性: {energy_attrs}")
            
    def add_test_controls(self):
        """添加测试控制按钮到状态栏"""
        # 对于QMainWindow，正确的方式是使用状态栏或central widget
        self.append_log("[CRITICAL] 添加测试控制按钮")
        
        # 创建测试按钮并添加到状态栏
        test_button = QPushButton("测试能量条")
        test_button.clicked.connect(self.test_energy_bar)
        
        # 添加到状态栏
        status_bar = self.statusBar()
        if status_bar:
            status_bar.addWidget(test_button)
            self.append_log("[DEBUG] 测试按钮已添加到状态栏")
        else:
            # 如果没有状态栏，尝试添加到central widget
            central = self.centralWidget()
            if central and hasattr(central, 'layout') and central.layout():
                central.layout().addWidget(test_button)
                self.append_log("[DEBUG] 测试按钮已添加到central widget")
            else:
                self.append_log("[ERROR] 无法添加测试按钮")
    
    def direct_energy_test(self):
        """直接测试能量条更新机制"""
        self.append_log("[CRITICAL] 执行直接能量条测试")
        
        # 检查所有可能的能量条对象名称
        energy_bar_names = ['voice_energy_bar', 'energy_bar', 'voice_energy']
        found = False
        
        for name in energy_bar_names:
            if hasattr(self, name):
                found = True
                bar = getattr(self, name)
                self.append_log(f"[CRITICAL] 找到能量条对象 '{name}': {bar}")
                self.append_log(f"[CRITICAL] {name} 类型: {type(bar).__name__}")
                
                # 检查能量条的方法
                methods = [method for method in dir(bar) if callable(getattr(bar, method)) and not method.startswith('_')]
                self.append_log(f"[CRITICAL] {name} 可用方法: {methods}")
                
                # 尝试直接设置值
                try:
                    if hasattr(bar, 'setValue'):
                        bar.setValue(60)
                        self.append_log(f"[CRITICAL] 成功设置{name}值为60")
                    elif hasattr(bar, 'update_energy'):
                        bar.update_energy(60)
                        self.append_log(f"[CRITICAL] 成功调用{name}.update_energy(60)")
                    else:
                        self.append_log(f"[ERROR] {name}没有setValue或update_energy方法")
                except Exception as e:
                    self.append_log(f"[ERROR] 设置{name}值失败: {e}")
                
                # 强制刷新
                if hasattr(bar, 'update'):
                    bar.update()
                if hasattr(bar, 'repaint'):
                    bar.repaint()
        
        if not found:
            self.append_log("[ERROR] 未找到任何能量条对象")
            # 打印所有属性，寻找可能的能量条对象
            all_attrs = [attr for attr in dir(self) if not attr.startswith('__')]
            self.append_log(f"[CRITICAL] 所有属性: {all_attrs[:20]}...")  # 只显示前20个避免日志过长

    def test_energy_bar(self):
        """手动测试能量条功能"""
        self.append_log("[CRITICAL] 手动测试能量条按钮被点击")
        
        # 测试1: 直接设置能量条值
        energy_bar_names = ['voice_energy_bar', 'energy_bar', 'voice_energy']
        for name in energy_bar_names:
            if hasattr(self, name):
                bar = getattr(self, name)
                self.append_log(f"[CRITICAL] 测试1: 直接设置{name}值为75")
                
                try:
                    if hasattr(bar, 'setValue'):
                        bar.setValue(75)
                    elif hasattr(bar, 'update_energy'):
                        bar.update_energy(75)
                    
                    # 强制刷新
                    if hasattr(bar, 'update'):
                        bar.update()
                    if hasattr(bar, 'repaint'):
                        bar.repaint()
                    
                    self.append_log(f"[CRITICAL] 成功更新{name}")
                except Exception as e:
                    self.append_log(f"[ERROR] 更新{name}失败: {e}")
        
        # 测试2: 模拟VAD事件处理链
        self.append_log("[CRITICAL] 测试2: 模拟完整VAD事件处理链")
        test_event_data = {'energy': 0.006}  # 一个较高的能量值
        
        # 如果是MainWindow类，尝试找到worker并调用其方法
        if hasattr(self, 'worker') and self.worker:
            self.append_log("[CRITICAL] 通过worker模拟VAD事件")
            if hasattr(self.worker, '_handle_vad_event'):
                self.worker._handle_vad_event('energy_update', test_event_data)
        else:
            self.append_log("[CRITICAL] 直接调用update_voice_energy")
            self.update_voice_energy(70)
    
    def update_energy_bar_randomly(self):
        """随机更新能量条，用于测试"""
        import random
        random_level = random.randint(0, 100)
        
        print(f"[DEBUG] 随机更新能量条: {random_level}")
        
        if hasattr(self, 'voice_energy_bar') and self.voice_energy_bar:
            # 直接设置能量条值
            self.voice_energy_bar.setValue(random_level)
            # 强制刷新显示
            self.voice_energy_bar.update()
            self.voice_energy_bar.repaint()  # 额外的重绘尝试

    def on_mode_changed(self, mode):
        """处理模式变更"""
        self.current_mode = mode
        
        # 更新模式描述
        mode_descriptions = {
            'fast': '快速模式 - 低延迟，识别速度快，适合实时交互',
            'balanced': '平衡模式 - 识别准确度和速度的良好平衡，默认推荐',
            'accuracy': '精确模式 - 高准确度，更注重识别质量，但延迟较高',
            'customized': '自定义模式 - 使用config.yaml中的VAD设置，支持小数识别优化（推荐）'
        }
        
        self.mode_description.setText(mode_descriptions.get(mode, '平衡模式'))
        self.mode_display_label.setText(f"当前模式: {mode}")
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
        
        # 减少控制台输出，只输出重要信息
        if any(keyword in message for keyword in ['错误', '警告', '系统初始化', '系统已', '识别结果']):
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
    
    # 强制刷新UI
    window.update()
    window.repaint()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()