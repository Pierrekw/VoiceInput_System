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

# 配置logger
logger = logging.getLogger(__name__)

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

    def _handle_vad_event(self, event_type: str, event_data: Dict):
        """处理VAD事件，更新语音能量显示"""
        # 🔍 调试输出 - 在voice_gui.py中接收VAD事件
        energy = event_data.get('energy', 0)
        logger.info(f"[🖥️ GUI接收] ← 收到VAD事件: {event_type} | 原始能量值: {energy:.8f}")
        print(f"[🖥️ GUI接收] ← 收到VAD事件: {event_type} | 原始能量值: {energy:.8f}")

        try:
            # 🔧 修复：只有检测到真正语音（is_speech=True）才更新能量条
            is_speech = False
            energy_level = 0

            # 检查是否为语音相关事件
            if event_type in ["speech_start", "speech_end", "energy_update"]:
                # 🔧 与VAD语音检测阈值统一，使用相同的阈值
                # 从config.yaml获取VAD能量阈值，保持一致性
                try:
                    from config_loader import config
                    vad_threshold = config.get_vad_energy_threshold()
                except:
                    vad_threshold = 0.010  # 默认阈值，与config.yaml一致

                is_speech = energy > vad_threshold  # 使用与VAD相同的阈值

                logger.info(f"[🖥️ GUI判断] 能量: {energy:.8f} vs VAD阈值: {vad_threshold:.8f} = {is_speech}")
                print(f"[🖥️ GUI判断] 能量: {energy:.8f} vs VAD阈值: {vad_threshold:.8f} = {is_speech}")

                if is_speech:
                    # 🔧 优化能量转换逻辑 - 更保守的映射，避免容易满值
                    # 基于VAD阈值0.010进行合理映射
                    if energy < vad_threshold * 0.5:  # 小于VAD阈值一半，显示为低值
                        energy_level = int((energy / vad_threshold) * 30)  # 0-30%
                    elif energy < vad_threshold * 0.8:  # VAD阈值的50%-80%
                        energy_level = int(30 + (energy - vad_threshold * 0.5) * 100)  # 30-60%
                    elif energy < vad_threshold:  # VAD阈值的80%-100%
                        energy_level = int(60 + (energy - vad_threshold * 0.8) * 100)  # 60-100%
                    else:  # 超过VAD阈值，显示为中高值
                        # 使用平方根映射，让大声音的变化更平缓
                        excess = energy - vad_threshold
                        if excess < vad_threshold * 2:  # 1-2倍阈值
                            energy_level = int(75 + excess * 10)  # 75-95%
                        elif excess < vad_threshold * 5:  # 2-5倍阈值
                            energy_level = int(85 + excess * 2)  # 85-95%
                        else:  # 超过5倍阈值
                            energy_level = min(98, int(90 + (excess - vad_threshold * 5) * 2))  # 90-98%

                    # 确保在有效范围内
                    energy_level = max(0, min(100, energy_level))
                else:
                    # 没有检测到语音，不更新能量条（保持当前状态或渐降为0）
                    energy_level = 0

            logger.info(f"[🖥️ GUI处理] 🔄 能量转换: {energy:.8f} → {energy_level}% | 语音检测: {is_speech}")
            print(f"[🖥️ GUI处理] 🔄 能量转换: {energy:.8f} → {energy_level}% | 语音检测: {is_speech}")

            # 只在检测到语音时才发送能量更新信号
            if is_speech and hasattr(self, 'voice_activity'):
                logger.info(f"[🖥️ GUI发送] → 发送voice_activity信号: {energy_level}% (语音)")
                print(f"[🖥️ GUI发送] → 发送voice_activity信号: {energy_level}% (语音)")
                self.voice_activity.emit(energy_level)
                logger.info(f"[🖥️ GUI成功] ✅ voice_activity信号发送成功")
            elif not is_speech and hasattr(self, 'voice_activity'):
                # 🔧 优化：只在之前有显示值时才发送0信号降为0
                # 这样避免静音时频繁的0%更新，减少不必要的界面刷新
                try:
                    current_value = self.voice_energy_bar.value() if hasattr(self, 'voice_energy_bar') else 0
                    if current_value > 0:
                        logger.info(f"[🖥️ GUI发送] → 发送voice_activity信号: 0% (静音，从{current_value}%降为0)")
                        print(f"[🖥️ GUI发送] → 发送voice_activity信号: 0% (静音，从{current_value}%降为0)")
                        self.voice_activity.emit(0)
                        logger.info(f"[🖥️ GUI成功] ✅ voice_activity信号发送成功")
                    else:
                        # 当前已经是0，不发送重复的0信号
                        logger.info(f"[🖥️ GUI跳过] 当前已是0%，跳过发送静音信号")
                        print(f"[🖥️ GUI跳过] 当前已是0%，跳过发送静音信号")
                except Exception as e:
                    logger.error(f"[🖥️ GUI错误] 获取当前能量值失败: {e}")
                    # 发生错误时，仍然发送0信号
                    self.voice_activity.emit(0)
            else:
                logger.error(f"[🖥️ GUI错误] ❌ voice_activity信号未定义！")
                print(f"[🖥️ GUI错误] ❌ voice_activity信号未定义！")

            # 记录关键事件到GUI日志
            if hasattr(self, 'log_message'):
                self.log_message.emit(f"🔊 GUI处理: {event_type}, 能量: {energy:.6f} → {energy_level}% (语音:{is_speech})")

            # 特别关注语音开始/结束事件
            if event_type == "speech_start":
                logger.info(f"[🖥️ GUI语音] 🎤 检测到语音开始")
                if hasattr(self, 'log_message'):
                    self.log_message.emit(f"🎤 GUI检测到语音开始")
            elif event_type == "speech_end":
                logger.info(f"[🖥️ GUI语音] 🎤 检测到语音结束")
                if hasattr(self, 'log_message'):
                    self.log_message.emit("🎤 GUI检测到语音结束")
            elif event_type == "energy_update" and is_speech:
                logger.info(f"[🖥️ GUI能量] ⚡ 语音能量更新: {energy:.8f} → {energy_level}%")
                print(f"[🖥️ GUI能量] ⚡ 语音能量更新: {energy:.8f} → {energy_level}%")

        except Exception as e:
            logger.error(f"[🖥️ GUI错误] ❌ 处理VAD事件异常: {e}")
            print(f"[🖥️ GUI错误] ❌ 处理VAD事件异常: {e}")
            import traceback
            logger.error(f"[🖥️ GUI详细] {traceback.format_exc()}")

    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """根据模式获取配置参数

        Args:
            mode: 识别模式 ('fast', 'balanced', 'accuracy', 'customized')

        Returns:
            配置参数字典
        """
        # 导入配置加载器
        from config_loader import config

        # 定义四种模式的配置参数（包含模型相关参数）
        configs = {
            'fast': {
                'chunk_size': [0, 8, 4],
                'encoder_chunk_look_back': 2,
                'decoder_chunk_look_back': 0,
                'description': '快速模式 - 低延迟，识别速度快'
            },
            'balanced': {
                'chunk_size': [0, 10, 5],
                'encoder_chunk_look_back': 4,
                'decoder_chunk_look_back': 1,
                'description': '平衡模式 - 识别准确度和速度的良好平衡'
            },
            'accuracy': {
                'chunk_size': [0, 16, 8],
                'encoder_chunk_look_back': 8,
                'decoder_chunk_look_back': 2,
                'description': '精确模式 - 高准确度，更注重识别质量'
            },
            'customized': {
                'chunk_size': [0, 10, 5],
                'encoder_chunk_look_back': 4,
                'decoder_chunk_look_back': 1,
                'description': '自定义模式 - 使用config.yaml中的VAD设置，支持小数识别优化'
            }
        }
        
        # 返回指定模式的配置，如果不存在则返回平衡模式
        mode_config = configs.get(mode, configs['balanced'])
        
        # 从config_loader获取VAD配置
        try:
            if mode == 'customized':
                # 自定义模式：直接使用config.yaml中的customized VAD设置
                vad_config = config.get_vad_config()
                if vad_config:
                    mode_config['vad_energy_threshold'] = vad_config.get('energy_threshold', 0.012)
                    mode_config['vad_min_speech_duration'] = vad_config.get('min_speech_duration', 0.2)
                    mode_config['vad_min_silence_duration'] = vad_config.get('min_silence_duration', 0.6)
                    mode_config['vad_speech_padding'] = vad_config.get('speech_padding', 0.4)
                    logger.info(f"✅ 加载自定义VAD配置: {vad_config}")
                else:
                    logger.warning("⚠️ 未找到customized VAD配置，使用默认值")
            else:
                # 预设模式：使用预设VAD参数
                vad_preset = config.get_vad_preset(mode)
                if vad_preset:
                    mode_config['vad_energy_threshold'] = vad_preset.get('energy_threshold', config.get_vad_energy_threshold())
                    mode_config['vad_min_speech_duration'] = vad_preset.get('min_speech_duration', config.get_vad_min_speech_duration())
                    mode_config['vad_min_silence_duration'] = vad_preset.get('min_silence_duration', config.get_vad_min_silence_duration())
                    mode_config['vad_speech_padding'] = vad_preset.get('speech_padding', config.get_vad_speech_padding())
        except Exception as e:
            # 如果加载失败，使用默认值
            logger.warning(f"⚠️ 从config.yaml加载VAD配置失败: {e}")
            mode_config['vad_energy_threshold'] = 0.015
            mode_config['vad_min_speech_duration'] = 0.3
            mode_config['vad_min_silence_duration'] = 0.6
            mode_config['vad_speech_padding'] = 0.3
            
        return mode_config
    
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
                try:
                    # 应用模型相关配置
                    if 'chunk_size' in config and hasattr(recognizer, 'configure_funasr'):
                        recognizer.configure_funasr(chunk_size=config['chunk_size'])
                        
                    # 应用VAD配置
                    if hasattr(recognizer, 'configure_vad'):
                        vad_params = {}
                        if 'vad_energy_threshold' in config:
                            vad_params['energy_threshold'] = config['vad_energy_threshold']
                        if 'vad_min_speech_duration' in config:
                            vad_params['min_speech_duration'] = config['vad_min_speech_duration']
                        if 'vad_min_silence_duration' in config:
                            vad_params['min_silence_duration'] = config['vad_min_silence_duration']
                        if 'vad_speech_padding' in config:
                            vad_params['speech_padding'] = config['vad_speech_padding']
                            
                        # 如果有VAD参数需要配置，则应用
                        if vad_params:
                            recognizer.configure_vad(**vad_params)
                            
                    self.log_message.emit(f"✅ 使用config.yaml中的优化配置")
                    self.log_message.emit(f"📋 VAD模式: {config.get('description', 'customized')}")
                    self.log_message.emit(f"📋 自定义VAD参数已应用")
                except Exception as e:
                    self.log_message.emit(f"⚠️ 设置参数失败: {e}")

                self.log_message.emit(f"✅ 系统配置完成: torch 2.3.1+cpu优化版本")

        except Exception as e:
            self.log_message.emit(f"⚠️ 配置识别器时出错: {e}")
            # 配置失败不应该阻止系统运行
            self.log_message.emit("📝 使用默认配置继续运行")
            logger.error(f"配置识别器时出错: {e}")


class VoiceEnergyBar(QProgressBar):
    """语音能量显示条"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setFixedHeight(20)  # 增加高度使其更可见
        self.setTextVisible(False)  # 不显示百分比文本

        # 设置样式 - 纯蓝色渐变，更美观
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #f0f0f0;
                font-weight: bold;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1E88E5, stop:0.5 #2196F3, stop:1 #42A5F5);
                width: 8px;
                margin: 2px;
            }
        """)

        # 动画效果
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(100)  # 100ms动画
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # 定时器用于自动衰减
        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self.decay_energy)
        self.last_activity_time = 0

    def update_energy(self, level):
        """更新能量级别 (0-100)"""
        # 打印调试日志
        print(f"[DEBUG] VoiceEnergyBar更新能量: {level}")
        
        # 确保值在有效范围内
        if level < 0:
            level = 0
        elif level > 100:
            level = 100

        # 强制更新值
        self.setValue(int(level))
        # 立即刷新显示
        self.update()
        
        # 更新时间戳
        self.last_activity_time = time.time()
        
        # 启动定时器用于衰减
        if not self.decay_timer.isActive():
            self.decay_timer.start(50)

    def decay_energy(self):
        """自动衰减能量级别"""
        current_value = self.value()

        # 简化衰减逻辑，根据时间间隔决定衰减速度
        time_diff = time.time() - self.last_activity_time
        if time_diff > 0.5:  # 降低阈值，更快地响应无活动状态
            # 指数衰减，更快地降为0
            if time_diff > 1.0:
                new_value = 0
            else:
                new_value = max(0, int(current_value * (1 - time_diff * 0.5)))
        else:
            # 缓慢衰减
            new_value = max(0, current_value - 1)

        self.setValue(new_value)

        # 如果能量降到0，停止定时器
        if new_value == 0:
            self.decay_timer.stop()

    def indicate_speech_activity(self):
        """指示语音活动（快速闪烁）"""
        self.update_energy(80)

    def indicate_listening(self):
        """指示监听状态（低能量显示）"""
        self.update_energy(15)


class WorkingSimpleMainWindow(QMainWindow):
    """工作简化版主窗口"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_mode = 'customized'  # 设置默认模式，必须在init_ui之前
        self.voice_energy_bar = None  # 语音能量条
        self.init_ui()
        self.setup_timer()

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
        
        # 添加手动测试按钮
        self.add_test_controls()
        
        # 注释掉随机能量条测试定时器，改用真实VAD能量数据
        # self.random_test_timer = QTimer()
        # self.random_test_timer.timeout.connect(self.update_energy_bar_randomly)
        # self.random_test_timer.start(500)  # 每500毫秒更新一次
        # self.append_log("🎯 启动能量条随机测试模式")

        # 启用真实VAD能量显示模式
        self.append_log("🎯 启用真实VAD能量显示模式")

        # 注释掉直接测试，等待真实VAD事件
        # self.direct_energy_test()

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

        # 语音能量显示
        energy_label = QLabel("🎤 语音能量检测:")
        energy_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 5px;")
        status_layout.addWidget(energy_label)

        self.voice_energy_bar = VoiceEnergyBar()
        status_layout.addWidget(self.voice_energy_bar)

        layout.addWidget(status_group)
        
        # 模式选择
        mode_group = QGroupBox("识别模式")
        mode_layout = QFormLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["fast", "balanced", "accuracy", "customized"])
        self.mode_combo.setCurrentText("customized")  # 默认使用自定义模式以支持小数识别优化
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        
        # 模式描述
        self.mode_description = QLabel("自定义模式 - 使用config.yaml中的VAD设置，支持小数识别优化（推荐）")
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
        
        self.mode_display_label = QLabel(f"当前模式: {self.current_mode}")
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
        print(f"[CRITICAL] start_recognition被调用")
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
        print(f"[CRITICAL] 创建WorkingVoiceWorker实例")
        self.worker = WorkingVoiceWorker(mode=self.current_mode)
        # 确保信号连接正确
        print(f"[CRITICAL] 连接voice_activity信号到update_voice_energy")
        self.worker.voice_activity.connect(self.update_voice_energy)
        print(f"[CRITICAL] 信号连接完成")
        
        self.worker.log_message.connect(self.append_log)
        self.worker.recognition_result.connect(self.display_result)
        self.worker.partial_result.connect(self.update_partial_result)
        self.worker.status_changed.connect(self.update_status)
        self.worker.voice_command_state_changed.connect(self.handle_voice_command_state_change)
        self.worker.system_initialized.connect(self.on_system_initialized)
        self.worker.finished.connect(self.on_worker_finished)
        
        # 添加一个直接测试 - 绕过VAD系统，直接调用update_voice_energy
        print(f"[CRITICAL] 直接测试update_voice_energy")
        self.update_voice_energy(50)  # 直接设置50%的能量值

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

        # 重置能量条
        if self.voice_energy_bar:
            self.voice_energy_bar.setValue(0)

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