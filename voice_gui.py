#!/usr/bin/env python3
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
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from utils.logging_utils import LoggingManager

logger = LoggingManager.get_logger(
    name='voice_gui',
    level=logging.DEBUG,  # 文件记录详细日志
    console_level=logging.INFO,  # 控制台只显示INFO及以上信息
    log_to_console=True,
    log_to_file=True
)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QLabel, QPushButton, QGroupBox, QStatusBar,
    QMessageBox, QSplitter, QTabWidget, QComboBox, QFormLayout, QProgressBar,
    QLineEdit, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QTextCharFormat

os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'


class WorkingVoiceWorker(QThread):
    """工作语音识别线程"""

    log_message = Signal(str)
    recognition_result = Signal(str)
    partial_result = Signal(str)
    status_changed = Signal(str)
    voice_command_state_changed = Signal(str)  # 语音命令状态变化信号
    voice_activity = Signal(int)  # 语音活动级别信号 (0-100)
    command_result = Signal(str)  # 命令结果信号(关键修复，命令在历史显示窗口显示）
    finished = Signal()
    
    system_initialized = Signal()

    def __init__(self, mode='customized'):
        super().__init__()
        self._should_stop = False
        self._is_paused = False
        self.voice_system = None
        self.mode = mode
        self.input_values = {}  # 存储GUI输入的值

    def set_input_values(self, values: Dict[str, str]):
        """设置GUI输入的值"""
        self.input_values = values.copy()

    def run(self):
        """运行语音识别"""
        try:
            logger.info(f"[🧵 WORKER启动] 🚀 Worker线程开始运行")            
            self.log_message.emit(f"🧵 Worker线程启动，模式: {self.mode}")

            self.log_message.emit(f"🚀 正在初始化语音系统... (模式: {self.mode})")

            mode_config = self._get_mode_config(self.mode)
            self.log_message.emit(f"🔧 使用配置: {mode_config}")

            logger.info(f"[🧵 WORKER导入] 📦 开始导入FunASRVoiceSystem")            

            from main_f import FunASRVoiceSystem

            #logger.info(f"[🧵 WORKER创建] 🏗️ 创建FunASRVoiceSystem实例")            

            self.voice_system = FunASRVoiceSystem(
                recognition_duration=-1,  # 不限时识别
                continuous_mode=True,      # 连续识别模式
                debug_mode=False           # 调式模式
            )

            logger.info(f"[🧵 WORKER创建] ✅ FunASRVoiceSystem创建完成")            

            # 🔥 关键修复：传递mode参数到语音系统
            mode_config_with_mode = mode_config.copy()
            mode_config_with_mode['mode'] = self.mode
            self._configure_recognizer(mode_config_with_mode)

            if not self.voice_system.initialize():
                self.log_message.emit("❌ 语音系统初始化失败")
                return

            #logger.debug(f"[🔗 WORKER设置] 🔧 开始设置状态变化回调")
            
            self.voice_system.set_state_change_callback(self._handle_voice_command_state_change)
            #logger.debug(f"[🔗 WORKER设置] ✅ 状态变化回调设置成功")

            # 🔥 关键修复：设置VAD回调以解决GUI无响应问题
            if hasattr(self.voice_system, 'set_vad_callback'):
                #logger.info(f"[🔗 WORKER设置] ✅ voice_system有set_vad_callback方法，开始设置")
                try:
                    self.voice_system.set_vad_callback(self._handle_vad_event)
                    #logger.info(f"[🔗 WORKER设置] ✅ VAD回调设置成功")
                    self.log_message.emit("✅ 已设置VAD能量监听")


                except Exception as e:
                    logger.error(f"[🔗 WORKER错误] ❌ VAD回调设置失败: {e}")                    
                    import traceback
                    logger.error(f"[🔗 WORKER详细] {traceback.format_exc()}")
            else:
                logger.error(f"[🔗 WORKER错误] ❌ voice_system没有set_vad_callback方法！")                

            self.log_message.emit("✅ 语音系统初始化成功")

            # 设置Excel模板
            if self.input_values:
                part_no = self.input_values.get('part_no', '')
                batch_no = self.input_values.get('batch_no', '')
                inspector = self.input_values.get('inspector', '')

                # 🎯 修复：严格要求所有必填字段都填写才使用模板
                if part_no and batch_no and inspector:
                    # 所有必填字段都完整，使用模板
                    success = self.voice_system.setup_excel_from_gui(part_no, batch_no, inspector)
                    if success:
                        self.log_message.emit(f"✅ Excel模板已创建: {part_no}_{batch_no}")
                    else:
                        self.log_message.emit("⚠️ Excel模板创建失败，使用默认方式")
                else:
                    # 有字段缺失，不使用模板，明确提醒用户
                    missing_fields = []
                    if not part_no:
                        missing_fields.append("零件号")
                    if not batch_no:
                        missing_fields.append("批次号")
                    if not inspector:
                        missing_fields.append("检验员")

                    if missing_fields:
                        self.log_message.emit(f"⚠️ 未填写: {', '.join(missing_fields)}")
                        self.log_message.emit("ℹ️ 请完整填写所有字段以使用Excel模板功能")
                        self.log_message.emit("📝 当前使用默认方式创建Excel文件")
                    else:
                        self.log_message.emit("ℹ️ 使用默认方式创建Excel文件")

            self.status_changed.emit("系统就绪")
            self.system_initialized.emit()

            original_process_result = getattr(self.voice_system, 'process_recognition_result', None)

            def custom_process_recognition_result(original_text, processed_text, numbers):
                try:
                    if original_process_result:
                        original_process_result(original_text, processed_text, numbers)

                    has_new_record = False
                    if hasattr(self.voice_system, 'number_results') and self.voice_system.number_results:
                        # 注意：这里假设调用original_process_result后会立即产生新记录
                        latest_record = self.voice_system.number_results[-1]
                        if len(latest_record) >= 3:
                            record_id, record_number, record_text = latest_record

                            is_matching_record = False
                            if record_text:
                                # 🎯 修复：检查命令结果格式 [CMD]
                                if record_text.startswith("[CMD]"):
                                    # 命令结果直接匹配
                                    if numbers and len(numbers) > 0:
                                        if isinstance(record_number, (int, float)):
                                            try:
                                                if float(record_number) == numbers[0]:
                                                    is_matching_record = True
                                            except:
                                                pass
                                elif record_text == processed_text or record_text == original_text:
                                    is_matching_record = True
                                elif numbers and len(numbers) > 0:
                                    if isinstance(record_number, (int, float)):
                                        try:
                                            if float(record_number) == numbers[0]:
                                                is_matching_record = True
                                        except:
                                            pass
                                    elif str(numbers[0]) in str(record_number):
                                        is_matching_record = True

                            if is_matching_record:
                                has_new_record = True

                                # 🎯 修复：优化显示逻辑，特别是命令结果
                                if record_text and record_text.startswith("[CMD]"):
                                    # 命令结果：直接显示命令文本
                                    display_text = record_text
                                elif isinstance(record_number, str) and record_text and record_text.strip():
                                    display_text = f"[{record_id}] {record_number}"
                                else:
                                    display_text = f"[{record_id}] {record_number}"

                                self.recognition_result.emit(display_text)
                                self.log_message.emit(f"🎤 识别结果: {display_text}")

                    if not has_new_record:
                        if processed_text and processed_text.strip():
                            self.recognition_result.emit(processed_text)
                            self.log_message.emit(f"🎤 文本识别结果: {processed_text}")
                        elif original_text and original_text.strip() and not processed_text:
                            self.recognition_result.emit(original_text)
                            self.log_message.emit(f"🎤 原始识别结果: {original_text}")

                except Exception as e:
                    self.log_message.emit(f"❌ 处理识别结果时出错: {e}")

            if hasattr(self.voice_system, 'process_recognition_result'):
                self.voice_system.process_recognition_result = custom_process_recognition_result
                self.log_message.emit("✅ 已设置识别结果回调")

            original_callback = getattr(self.voice_system, 'on_recognition_result', None)

            def gui_recognition_callback(result):
                try:
                    if hasattr(result, 'text'):
                        text = result.text
                        if text and text.strip():
                            pass

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
                    logger.error(f"处理部分结果错误: {e}")

            if hasattr(self.voice_system, 'recognizer'):
                self.voice_system.recognizer.set_callbacks(
                    on_final_result=gui_recognition_callback,
                    on_partial_result=gui_partial_result_callback
                )

            self.log_message.emit("🎙️ 开始连续语音识别...")
            self.status_changed.emit("正在识别...")

            self.voice_system.start_keyboard_listener()

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
            self.voice_command_state_changed.emit("paused")
        elif state == "resumed":
            self._is_paused = False
            self.status_changed.emit("正在识别...")
            self.log_message.emit(f"🎤 {message}")
            self.voice_command_state_changed.emit("resumed")
        elif state == "stopped":
            self._is_paused = False
            self.status_changed.emit("已停止")
            self.log_message.emit(f"🎤 {message}")
            self.voice_command_state_changed.emit("stopped")
        elif state == "command":
            # 🎯 通过信号确保在主线程中添加到history_text
            try:
                # 直接使用接收到的格式化命令，不再添加时间戳
                formatted_command = message

                # 通过命令结果信号发送到主线程
                self.command_result.emit(formatted_command)

                # 记录到日志
                self.log_message.emit(f"🎤 命令识别: {message}")
                #self.append_log(f"🎤 命令识别: {message}") 在worker中会报错，是在GUI的命令

            except Exception as e:
                logger.error(f"发送命令到历史记录失败: {e}")

    
    def _handle_vad_event(self, event_type: str, event_data: Dict):
        """处理VAD事件，更新语音能量显示"""
        energy = event_data.get('energy', 0)
        #logger.debug(f"[🖥️ GUI接收] ← 收到VAD事件: {event_type} | 原始能量值: {energy:.8f}")

        try:
            is_speech = False
            energy_level = 0

            if event_type in ["speech_start", "speech_end", "energy_update"]:
                try:
                    from utils.config_loader import config
                    vad_threshold = config.get_vad_energy_threshold()
                except:
                    vad_threshold = 0.010  # 默认阈值，与config.yaml一致

                is_speech = energy > vad_threshold  # 使用与VAD相同的阈值

                #.debug(f"[🖥️ GUI判断] 能量: {energy:.8f} vs VAD阈值: {vad_threshold:.8f} = {is_speech}")

                if is_speech:
                    if energy < vad_threshold * 0.5:  # 小于VAD阈值一半，显示为低值
                        energy_level = int((energy / vad_threshold) * 30)  # 0-30%
                    elif energy < vad_threshold * 0.8:  # VAD阈值的50%-80%
                        energy_level = int(30 + (energy - vad_threshold * 0.5) * 100)  # 30-60%
                    elif energy < vad_threshold:  # VAD阈值的80%-100%
                        energy_level = int(60 + (energy - vad_threshold * 0.8) * 100)  # 60-100%
                    else:  # 超过VAD阈值，精细音量映射
                        excess = energy - vad_threshold

                        if excess < vad_threshold * 0.5:      # 刚超过阈值 (0.010-0.015)
                            energy_level = int(60 + excess * 400)  # 60-80%
                        elif excess < vad_threshold * 1:      # 轻度声音 (0.015-0.020)
                            energy_level = int(70 + excess * 300)  # 70-85%
                        elif excess < vad_threshold * 2:      # 中度声音 (0.020-0.030)
                            energy_level = int(80 + excess * 150)  # 80-85%
                        elif excess < vad_threshold * 5:      # 响亮声音 (0.030-0.060)
                            energy_level = int(83 + excess * 40)   # 83-89%
                        elif excess < vad_threshold * 10:     # 很响亮 (0.060-0.110)
                            energy_level = int(86 + excess * 18)   # 86-89%
                        else:  # 极响亮 (>0.110)
                            energy_level = min(92, int(89 + (excess - vad_threshold * 10) * 1))  # 89-92%

                    energy_level = max(0, min(100, energy_level))
                else:
                    energy_level = 0

            volume_level = self._get_volume_description(energy)
            
            #logger.debug(f"[🖥️ GUI处理] 🔄 能量转换: {energy:.8f} → {energy_level}% | 音量级别: {volume_level} | 语音检测: {is_speech}")
            ## 注释掉调试日志，避免控制台输出过多
            #if energy_level > vad_threshold:  # 只在能量超过VAD阈值时记录INFO级别日志
            #   logger.debug(f"[🖥️ 音量变化] 能量: {energy:.8f} → {energy_level}% ({volume_level})")

            if is_speech and hasattr(self, 'voice_activity'):
                #logger.debug(f"[🖥️ GUI发送] → 发送voice_activity信号: {energy_level}% (语音)")                
                self.voice_activity.emit(energy_level)
                #logger.debug(f"[🖥️ GUI成功] ✅ voice_activity信号发送成功")
            elif not is_speech and hasattr(self, 'voice_activity'):
                try:
                    current_value = self.voice_energy_bar.value() if hasattr(self, 'voice_energy_bar') else 0
                    if current_value > 0:
                        #logger.debug(f"[🖥️ GUI发送] → 发送voice_activity信号: 0% (静音，从{current_value}%降为0)")                        
                        self.voice_activity.emit(0)
                        #logger.debug(f"[🖥️ GUI成功] ✅ voice_activity信号发送成功")
                    #else:
                        #logger.debug(f"[🖥️ GUI跳过] 当前已是0%，跳过发送静音信号")                        
                except Exception as e:
                    logger.error(f"[🖥️ GUI错误] 获取当前能量值失败: {e}")
                    self.voice_activity.emit(0)
            else:
                logger.error(f"[🖥️ GUI错误] ❌ voice_activity信号未定义！")
                print(f"[🖥️ GUI错误] ❌ voice_activity信号未定义！")

        except Exception as e:
            logger.error(f"[🖥️ GUI错误] ❌ 处理VAD事件异常: {e}")
            # 使用sys.stderr输出错误信息
            import sys
            print(f"[🖥️ GUI错误] ❌ 处理VAD事件异常: {e}", file=sys.stderr)

    def _get_volume_description(self, energy):
        """根据能量值返回音量级别描述"""
        vad_threshold = 0.010  # VAD阈值

        if energy < vad_threshold * 0.5:
            return "🔇 极轻声"
        elif energy < vad_threshold * 0.8:
            return "🔈 轻声"
        elif energy < vad_threshold:
            return "🔉 正常音量"
        elif energy < vad_threshold * 1.5:
            return "🔊 刚听到"
        elif energy < vad_threshold * 2:
            return "🔊 轻度声音"
        elif energy < vad_threshold * 5:
            return "📢 中度声音"
        elif energy < vad_threshold * 10:
            return "📢 响亮声音"
        else:
            return "📣 很响亮"

    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """根据模式获取配置参数

        Args:
            mode: 识别模式 ('fast', 'balanced', 'accuracy', 'customized')

        Returns:
            配置参数字典
        """
        from utils.config_loader import config

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
                'description': '自定义模式 - 自定义VAD设置和优化小数'
            }
        }
        
        mode_config = configs.get(mode, configs['balanced'])
        
        try:
            if mode == 'customized':
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
                vad_preset = config.get_vad_preset(mode)
                if vad_preset:
                    mode_config['vad_energy_threshold'] = vad_preset.get('energy_threshold', config.get_vad_energy_threshold())
                    mode_config['vad_min_speech_duration'] = vad_preset.get('min_speech_duration', config.get_vad_min_speech_duration())
                    mode_config['vad_min_silence_duration'] = vad_preset.get('min_silence_duration', config.get_vad_min_silence_duration())
                    mode_config['vad_speech_padding'] = vad_preset.get('speech_padding', config.get_vad_speech_padding())
        except Exception as e:
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
            if hasattr(self.voice_system, 'recognizer'):
                recognizer = self.voice_system.recognizer

                try:
                    if 'chunk_size' in config and hasattr(recognizer, 'configure_funasr'):
                        recognizer.configure_funasr(chunk_size=config['chunk_size'])
                        
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
            self.log_message.emit("📝 使用默认配置继续运行")
            logger.error(f"配置识别器时出错: {e}")


class VoiceEnergyBar(QProgressBar):
    """语音能量显示条"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setFixedHeight(16)  # 增加高度使其更可见
        self.setTextVisible(False)  # 不显示百分比文本

        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: #2196F3;
                margin: 2px;
            }
        """)

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(100)  # 100ms动画
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self.decay_energy)
        self.last_activity_time = 0

    def update_energy(self, level):
        """更新能量级别 (0-100)"""
        
        if level < 0:
            level = 0
        elif level > 100:
            level = 100

        self.setValue(int(level))
        self.update()
        
        self.last_activity_time = time.time()
        
        if not self.decay_timer.isActive():
            self.decay_timer.start(50)

    def decay_energy(self):
        """自动衰减能量级别"""
        current_value = self.value()

        time_diff = time.time() - self.last_activity_time
        if time_diff > 0.5:  # 降低阈值，更快地响应无活动状态
            if time_diff > 1.0:
                new_value = 0
            else:
                new_value = max(0, int(current_value * (1 - time_diff * 0.5)))
        else:
            new_value = max(0, current_value - 1)

        self.setValue(new_value)

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
        self._excel_info_shown = False  # 防止重复显示Excel信息

        # 输入验证相关属性
        self.part_no_input = None
        self.batch_no_input = None
        self.inspector_input = None
        self.validation_errors = {}

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("FunASR语音识别系统 v2.4")
        self.setMinimumSize(700, 890)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel)

        right_panel = self.create_display_panel()
        main_layout.addWidget(right_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        self.apply_styles()
        
                

        self.append_log("🎯 启用真实VAD能量显示模式")


    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("🔴 未启动")
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #d32f2f; padding: 10px;"
        )
        status_layout.addWidget(self.status_label)

        energy_label = QLabel("🎤 语音能量检测:")
        energy_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 5px;")
        status_layout.addWidget(energy_label)

        self.voice_energy_bar = VoiceEnergyBar()
        status_layout.addWidget(self.voice_energy_bar)

        layout.addWidget(status_group)
        
        mode_group = QGroupBox("识别模式")
        mode_layout = QFormLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["fast", "balanced", "accuracy", "customized"])
        self.mode_combo.setCurrentText("customized")  # 默认使用自定义模式以支持小数识别优化
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        
        self.mode_description = QLabel("自定义模式 - config自定义VAD，小数优化")
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: #555; font-size: 12px;")
        
        mode_layout.addRow("选择模式:", self.mode_combo)
        mode_layout.addRow("", self.mode_description)
        
        layout.addWidget(mode_group)

        # 添加输入信息组
        input_group = QGroupBox("报告信息")
        input_layout = QFormLayout(input_group)

        # 零件号输入
        self.part_no_input = QLineEdit()
        self.part_no_input.setMinimumHeight(30)
        self.part_no_input.setPlaceholderText("请输入零件号，如: PART-A001")
        self.part_no_input.textChanged.connect(self.validate_part_no)
        input_layout.addRow("零件号 *:", self.part_no_input)

        # 批次号输入
        self.batch_no_input = QLineEdit()
        self.batch_no_input.setMinimumHeight(30)
        self.batch_no_input.setPlaceholderText("请输入批次号，如: B20250105")
        self.batch_no_input.textChanged.connect(self.validate_batch_no)
        input_layout.addRow("批次号 *:", self.batch_no_input)

        # 检验员输入
        self.inspector_input = QLineEdit()
        self.inspector_input.setMinimumHeight(30)
        self.inspector_input.setPlaceholderText("请输入检验员姓名，如: 张三")
        self.inspector_input.textChanged.connect(self.validate_inspector)
        input_layout.addRow("检验员 *:", self.inspector_input)

        # 添加分隔线
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        input_layout.addRow(separator_line)

        # 添加说明文字
        info_label = QLabel("⚠️ 带星号(*)的字段为必填项，\n请在开始识别前填写完整")
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        info_label.setWordWrap(True)
        input_layout.addRow(info_label)

        layout.addWidget(input_group)

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

        info_group = QGroupBox("使用说明")
        info_layout = QVBoxLayout(info_group)

        info_text = QLabel(
            "📖 使用说明:\n"
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
        info_text.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 可选中文本（可选）
        info_text.setStyleSheet("color: #555; padding: 5px;")
        #info_layout.addWidget(info_text)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 关键：让 QLabel 自适应宽度
        scroll_area.setWidget(info_text)

        # 将滚动区域加入布局
        info_layout.addWidget(scroll_area)
        layout.addWidget(info_group)

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

        tab_widget = QTabWidget()

        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)

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

        history_group = QGroupBox("识别历史")
        history_layout = QVBoxLayout(history_group)

        self.history_text = QTextBrowser()
        self.history_text.setFont(QFont("Microsoft YaHei", 10))  # 使用支持中文的字体

        self.history_text.setAcceptRichText(True)

        self.history_text.setOpenExternalLinks(False)  # 我们自己处理链接点击
        self.history_text.mousePressEvent = self._history_mouse_press_event  # 自定义鼠标点击事件

        self.history_text.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            }
            QTextBrowser a {
                color: #2196F3;
                text-decoration: underline;
                font-weight: bold;
            }
            QTextBrowser a:hover {
                color: #1976D2;
                text-decoration: underline;
            }
        """)

        self.history_text.anchorClicked.connect(self._handle_link_clicked)

        history_layout.addWidget(self.history_text)

        results_layout.addWidget(history_group)
        tab_widget.addTab(results_tab, "识别结果")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)

        log_control = QHBoxLayout()
        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self.clear_log)
        log_control.addWidget(self.clear_log_button)
        log_control.addStretch()

        log_layout.addLayout(log_control)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.document().setMaximumBlockCount(500)

        self.log_text.setAcceptRichText(True)

        current_flags = self.log_text.textInteractionFlags()
        self.log_text.setTextInteractionFlags(
            current_flags |
            Qt.TextInteractionFlag.LinksAccessibleByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )

        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QTextEdit a {
                color: #2196F3;
                text-decoration: underline;
                font-weight: bold;
            }
            QTextEdit a:hover {
                color: #1976D2;
                text-decoration: underline;
            }
        """)

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

        # 🎯 修复：强制验证所有必填字段
        self.validate_part_no(self.part_no_input.text() if self.part_no_input else "")
        self.validate_batch_no(self.batch_no_input.text() if self.batch_no_input else "")
        self.validate_inspector(self.inspector_input.text() if self.inspector_input else "")

        # 验证输入信息
        if not self.are_inputs_valid():
            error_messages = list(self.validation_errors.values())
            QMessageBox.warning(
                self, '输入验证失败',
                f"请修正以下错误后再开始识别:\n\n" + "\n".join(f"• {msg}" for msg in error_messages),
                QMessageBox.Ok
            )
            self.append_log("❌ 启动失败：请填写所有必填字段")
            return  # 阻止启动
        else:
            self.append_log("✅ 输入验证通过")

        # 获取输入值
        input_values = self.get_input_values()
        part_no = input_values['part_no']
        batch_no = input_values['batch_no']
        inspector = input_values['inspector']

        self.append_log(f"📋 报告信息: 零件号={part_no}, 批次号={batch_no}, 检验员={inspector}")

        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.mode_combo.setEnabled(False)  # 运行时禁用模式更改

        # 禁用输入框，防止运行时修改
        self.part_no_input.setEnabled(False)
        self.batch_no_input.setEnabled(False)
        self.inspector_input.setEnabled(False)

        self.status_label.setText("🟢 正在启动...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50; padding: 10px;")

        # 清空识别历史记录并重置文本格式
        if hasattr(self, 'history_text') and self.history_text:
            self.history_text.clear()
            # 显式重置文本格式为默认格式，防止之前的格式影响新文本
            cursor = self.history_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.setCharFormat(QTextCharFormat())  # 应用默认格式
            self.history_text.setTextCursor(cursor)

        self.log_text.clear()
        self.current_text_label.setText("正在初始化...")
        self.recognition_count = 0
        self.start_time = time.time()

        self._excel_info_shown = False

        # 初始化状态优化：添加预加载机制，改善第一次启动体验
        # 提前导入必要模块，避免在worker线程中动态导入导致的延迟
        try:
            import importlib.util
            if importlib.util.find_spec('main_f'):
                from main_f import FunASRVoiceSystem
                self.append_log("📦 预加载语音系统模块...")
        except Exception as e:
            logger.debug(f"预加载模块时出错: {e}")
            
        self.worker = WorkingVoiceWorker(mode=self.current_mode)
        self.worker.voice_activity.connect(self.update_voice_energy)

        # 传递输入信息到worker
        self.worker.set_input_values(input_values)

        self.worker.log_message.connect(self.append_log)
        self.worker.recognition_result.connect(self.display_result)
        self.worker.command_result.connect(self.handle_command_result)
        self.worker.partial_result.connect(self.update_partial_result)
        self.worker.status_changed.connect(self.update_status)
        self.worker.voice_command_state_changed.connect(self.handle_voice_command_state_change)
        self.worker.system_initialized.connect(self.on_system_initialized)
        self.worker.finished.connect(self.on_worker_finished)
        
        # 优化启动流程：增加详细的状态反馈，减少用户等待焦虑
        self.append_log("🚀 启动语音识别系统... (当前模式: " + str(self.current_mode) + ")")
        self.update_status("正在初始化系统...")

        # 启动工作线程
        self.worker.start()
        # 启动定时器更新UI
        self.timer.start(500)  # 优化：增加更新频率，使UI响应更及时

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

            self.append_log("🛑 正在停止语音识别...")
            self.status_label.setText("🟡 正在停止...")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff9800; padding: 10px;")

            if hasattr(self, 'history_text') and self.history_text:
                history_count = self.history_text.document().blockCount()
                if history_count > 0:
                    self.append_log(f"📝 识别历史: 共 {history_count} 条记录")
                else:
                    self.append_log("📝 识别历史: 暂无记录")

            self.append_log("⏹️ 等待系统完全停止...")

        # 显示Excel文件保存信息（在停止时显示，而不是在worker完成时）
        self._show_excel_save_info()


    def on_worker_finished(self):
        """工作线程完成"""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.mode_combo.setEnabled(True)  # 重新启用模式更改
        self.pause_button.setText("⏸️ 暂停")

        # 重新启用输入框
        self.part_no_input.setEnabled(True)
        self.batch_no_input.setEnabled(True)
        self.inspector_input.setEnabled(True)

        self.timer.stop()

        self.status_label.setText("🔴 已停止")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; padding: 10px;")
        self.current_text_label.setText("等待识别...")

        # 不要在停止时清空识别历史，保留给用户查看
        # 只有在新启动时才清空历史（在start_recognition方法中）
        # if hasattr(self, 'history_text') and self.history_text:
        #     self.history_text.clear()
        #     self.append_log("📋 识别历史已清空")

        # 不再清空Excel文件路径列表，以便用户仍然可以访问之前保存的Excel文件
        # 这样用户在识别停止后仍然可以点击历史记录中的链接打开文件

        # 重置Excel信息显示标志，为下次启动做准备
        self._excel_info_shown = False

    def _show_excel_save_info(self):
        """显示Excel文件保存信息"""
        if self._excel_info_shown:
            return

        try:
            if hasattr(self.worker, 'voice_system') and self.worker.voice_system:
                system = self.worker.voice_system

                if hasattr(system, 'excel_exporter') and system.excel_exporter:
                    excel_exporter = system.excel_exporter

                    file_path = excel_exporter.filename
                    file_name = os.path.basename(file_path)

                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        mtime_str = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")

                        record_count = len(excel_exporter.get_session_data())

                        if record_count == 0:
                            try:
                                import pandas as pd
                                df = pd.read_excel(file_path)
                                record_count = len(df)
                            except:
                                record_count = 0

                        self._append_excel_info_to_history(file_name, file_path, record_count, file_size, mtime_str)

                        self.append_log(f"📁 Excel文件已生成: {file_name} ({record_count}条记录)")
                        logger.info(f"Excel文件已生成: {file_path}")
                        logger.info(f"记录数量: {record_count} 条, 文件大小: {self._format_file_size(file_size)}")

                        self.status_bar.showMessage(f"✅ Excel已保存: {file_name} ({record_count}条记录)", 8000)

                        self._excel_info_shown = True

                    else:
                        self.append_log("⚠️ Excel文件不存在")
                        self.status_bar.showMessage("⚠️ Excel文件未生成", 3000)
                else:
                    self.append_log("ℹ️ Excel导出功能未启用")
                    self.status_bar.showMessage("ℹ️ Excel导出功能未启用", 3000)
        except Exception as e:
            self.append_log(f"❌ 获取Excel保存信息失败: {e}")
            self.status_bar.showMessage("❌ 获取Excel信息失败", 3000)

    def _format_file_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

        if self.voice_energy_bar:
            self.voice_energy_bar.setValue(0)

    def _get_recognition_statistics(self):
        """获取识别统计信息"""
        stats = {
            'total_records': 0,
            'number_records': 0,
            'text_records': 0,
            'first_record_time': None,
            'last_record_time': None
        }

        if hasattr(self, 'history_text') and self.history_text:
            document = self.history_text.document()
            stats['total_records'] = document.blockCount()

            for i in range(stats['total_records']):
                block = document.findBlockByNumber(i)
                if block.isValid():
                    text = block.text()
                    if '[' in text and ']' in text:
                        try:
                            if '🔢' in text:  # 数字记录
                                stats['number_records'] += 1
                            elif '📝' in text:  # 文本记录
                                stats['text_records'] += 1

                            timestamp_start = text.find('[')
                            timestamp_end = text.find(']')
                            if timestamp_start != -1 and timestamp_end != -1:
                                timestamp_str = text[timestamp_start+1:timestamp_end]
                                if ':' in timestamp_str:
                                    stats['last_record_time'] = timestamp_str
                                    if stats['first_record_time'] is None:
                                        stats['first_record_time'] = timestamp_str
                        except:
                            pass

        return stats

    def _show_recognition_summary(self):
        """显示识别统计摘要"""
        try:
            stats = self._get_recognition_statistics()

            self.append_log("📈 " + "="*50)
            self.append_log("📊 识别会话统计摘要")
            self.append_log("📈 " + "="*50)

            if stats['total_records'] > 0:
                self.append_log(f"📝 总记录数: {stats['total_records']} 条")
                self.append_log(f"🔢 数字记录: {stats['number_records']} 条")
                self.append_log(f"📝 文本记录: {stats['text_records']} 条")

                if stats['first_record_time']:
                    self.append_log(f"🕐 开始时间: {stats['first_record_time']}")
                if stats['last_record_time']:
                    self.append_log(f"🕐 结束时间: {stats['last_record_time']}")

                if stats['first_record_time'] and stats['last_record_time'] and ':' in stats['first_record_time']:
                    try:
                        from datetime import datetime
                        time_format = "%H:%M:%S"
                        start_time = datetime.strptime(stats['first_record_time'], time_format)
                        end_time = datetime.strptime(stats['last_record_time'], time_format)
                        duration = end_time - start_time

                        if stats['total_records'] > 1:
                            avg_interval = duration.total_seconds() / (stats['total_records'] - 1)
                            self.append_log(f"⏱️ 平均间隔: {avg_interval:.1f} 秒/条")
                    except:
                        pass
            else:
                self.append_log("📝 本次会话暂无识别记录")

            self.append_log("📈 " + "="*50)

        except Exception as e:
            self.append_log(f"❌ 统计信息获取失败: {e}")

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
            self.pause_button.setText("▶️ 继续")
            self.pause_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟡 已暂停 (语音命令)")
            self.status_bar.showMessage("已暂停 - 语音命令控制")
            self.append_log("🎤 语音命令：系统已暂停，点击'▶️ 继续'按钮或说'继续'恢复识别")

        elif state == "resumed":
            self.pause_button.setText("⏸️ 暂停")
            self.pause_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟢 正在识别... (语音命令)")
            self.status_bar.showMessage("正在识别... - 语音命令控制")
            self.append_log("🎤 语音命令：系统已恢复，正在监听语音输入...")

        elif state == "stopped":
            self.pause_button.setText("⏸️ 暂停")
            self.pause_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.mode_combo.setEnabled(True)
            self.stop_recognition()
            #self.status_label.setText("🔴 已停止 (语音命令)")
            #self.status_bar.showMessage("已停止 - 语音命令控制")
            self.append_log("🎤 语音命令：系统已停止，点击'🎤 开始识别'按钮重新开始")

    def add_command_to_history(self, command_message: str):
        """将命令添加到历史记录"""
        try:
            def update_ui():
                # 获取当前时间戳
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")

                # 创建命令记录格式，类似于数字记录但标记为命令
                formatted_command = f"[CMD] {timestamp} {command_message}"

                # 添加到历史文本框
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(f"{formatted_command}\n")

                # 滚动到底部
                self.history_text.ensureCursorVisible()

                # 同时添加到历史记录列表（如果存在）
                if hasattr(self, 'history_data'):
                    self.history_data.append({
                        'type': 'command',
                        'content': command_message,
                        'timestamp': timestamp,
                        'formatted': formatted_command
                    })

            # 在主线程中更新UI
            if hasattr(self, 'history_text'):
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, update_ui)

        except Exception as e:
            self.append_log(f"❌ 添加命令到历史记录失败: {e}")

    def _add_to_history_text(self, text: str):
        """直接添加文本到历史文本框"""
        try:
            if hasattr(self, 'history_text'):
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(f"{text}\n")
                self.history_text.ensureCursorVisible()
        except Exception as e:
            logger.error(f"添加文本到历史记录失败: {e}")

    def display_result(self, result):
        """显示识别结果 - 显示所有[xxx]格式的信息"""
        if not result or not result.strip():
            return

        result = result.strip()

        # 简化逻辑：所有以[开头且包含]的内容都认为是record
        # 包括：[id] 数字, [id] 特殊文本, [CMD] 命令
        is_record = result.startswith('[') and ']' in result
        logger.debug(f"识别结果: '{result}', is_record: {is_record}")

        if not is_record:
            if hasattr(self, 'append_log'):
                self.append_log(f"过滤非record信息: {result}")
            return

        def update_ui():
            # 获取当前标准序号（如果可用）
            standard_id = ""
            try:
                if hasattr(self, 'worker') and self.worker and hasattr(self.worker, 'voice_system') and self.worker.voice_system:
                    if hasattr(self.worker.voice_system, 'excel_exporter') and self.worker.voice_system.excel_exporter:
                        standard_id = self.worker.voice_system.excel_exporter.current_standard_id
            except Exception as e:
                logger.debug(f"获取标准序号失败: {e}")

            # 构建显示文本
            if standard_id:
                display_text = f"标准序号{standard_id}: {result}"
            else:
                display_text = f"识别结果: {result}"

            self.current_text_label.setText(display_text)

            # 构建历史记录条目
            if result.startswith("[CMD]"):
                # 命令记录格式
                history_entry = f"🎤 {result}"
            elif standard_id:
                history_entry = f"🔢 [标准序号{standard_id}] {result}"
            else:
                history_entry = f"🔢 {result}"

            if hasattr(self, 'history_text') and self.history_text:
                self.history_text.append(history_entry)
                self.recognition_count += 1

                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.history_text.setTextCursor(cursor)

            if hasattr(self, 'append_log'):
                if standard_id:
                    self.append_log(f"语音识别(record) [标准序号{standard_id}]: {result}")
                else:
                    self.append_log(f"语音识别(record): {result}")

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_ui)

        # 记录日志
        logger.info(f"🎤 识别(record): {result}")
        
    def update_partial_result(self, text):
        """更新部分识别结果"""
        current_status = self.status_label.text()
        if "就绪" in current_status or "识别" in current_status:
            self.current_text_label.setText(f"识别中: {text}")

    def update_voice_energy(self, energy_level):
        """更新语音能量显示"""
        # 注释掉调试日志，减少控制台输出
        #logger.debug(f"[🖥️ GUI主线程] ← 收到voice_activity信号: {energy_level}%")
        
        # 只在能量有显著变化或非零时记录日志，减少频率
        #if energy_level > 10 or energy_level == 0 and hasattr(self, '_last_energy_level') and self._last_energy_level > 0:
              # 注释掉能量条日志记录，避免系统日志过多
              # self.append_log(f"📊 GUI能量条更新: {energy_level}%")
        # 记录最后能量值用于比较（保持在if语句外，确保每次都更新）
        self._last_energy_level = energy_level

        if hasattr(self, 'voice_energy_bar') and self.voice_energy_bar:
            # 注释掉调试日志
            #logger.debug(f"[🖥️ GUI能量条] ✅ 能量条对象存在，开始更新")

            try:
                # 注释掉调试日志
                #logger.debug(f"[🖥️ GUI更新] 🔄 设置能量条值: {energy_level}%")
                self.voice_energy_bar.setValue(energy_level)
                self.voice_energy_bar.update_energy(energy_level)
                # 注释掉调试日志
                #logger.debug(f"[🖥️ GUI成功] ✅ 能量条更新完成: {energy_level}%")
            except Exception as e:
                logger.error(f"[🖥️ GUI错误] ❌ 能量条更新失败: {e}")
        else:
            logger.error(f"[🖥️ GUI错误] ❌ 能量条未初始化或不存在！")
            self.append_log("❌ GUI错误: 能量条未初始化")

            # 注释掉调试日志
            #energy_attrs = [attr for attr in dir(self) if 'energy' in attr.lower()]
            #logger.debug(f"[🖥️ GUI调试] 🔍 找到energy相关属性: {energy_attrs}")
            
    def on_mode_changed(self, mode):
        """处理模式变更"""
        self.current_mode = mode
        
        mode_descriptions = {
            'fast': '快速模式 - 低延迟，识别速度快，实时交互',
            'balanced': '平衡模式 - 识别准确度和速度平衡，默认',
            'accuracy': '精确模式 - 高准确度，注重识别质量，但延迟较高',
            'customized': '自定义模式 - 自定义VAD和优化小数识别'
        }
        
        self.mode_description.setText(mode_descriptions.get(mode, '平衡模式'))
        self.mode_display_label.setText(f"当前模式: {mode}")
        self.append_log(f"模式已更改为: {mode}")

    def append_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        def update_log():
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(log_entry)

                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_text.setTextCursor(cursor)

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_log)
        
        # 使用logger.info代替直接print，这样可以受日志级别控制
        # 只记录重要信息，避免过多输出
        if any(keyword in message for keyword in ['错误', '警告', '系统初始化', '系统已']):
            logger.info(f"[GUI LOG] {log_entry}")

    def _history_mouse_press_event(self, event):
        """处理历史文本区域的鼠标点击事件"""
        # 初始化_excel_file_paths属性（如果不存在）
        if not hasattr(self, '_excel_file_paths'):
            self._excel_file_paths = []
            
        if event.button() == Qt.LeftButton:
            # 获取点击位置 (兼容PySide6 6.6+)
            # pos() 在新版本中已弃用，使用 position() 替代
            try:
                # 优先使用新方法
                position = event.position()
                cursor = self.history_text.cursorForPosition(position.toPoint())
            except AttributeError:
                # 回退到旧方法 (向后兼容)
                cursor = self.history_text.cursorForPosition(event.pos())
            # 使用更可靠的block.text()方法获取当前行内容
            # 避免LineUnderCursor在边界情况下的意外行为
            block = cursor.block()
            line_text = block.text().strip()

            # 调试信息：输出点击详情
            print(f"[DEBUG] 点击位置: ({position.x():.1f}, {position.y():.1f})")
            print(f"[DEBUG] 块文本: '{block.text()}'")
            print(f"[DEBUG] 清理后文本: '{line_text}'")
            print(f"[DEBUG] 文本长度: {len(line_text)}")
            print(f"[DEBUG] 包含.xlsx: {'.xlsx' in line_text.lower()}")
            print(f"[DEBUG] 不包含'文件名': {'文件名' not in line_text}")
            print(f"[DEBUG] 有Excel文件路径: {len(self._excel_file_paths) > 0}")

            # 检查是否点击了Excel文件相关内容
            # 精确逻辑：包含.xlsx但不包含"文件名"，且不是空行
            will_trigger = ('.xlsx' in line_text.lower() or '.xls' in line_text.lower()) and '文件名' not in line_text and len(line_text.strip()) > 0 and self._excel_file_paths
            print(f"[DEBUG] 会触发Excel打开: {will_trigger}")

            if will_trigger:
                try:
                    # 直接使用最新的Excel文件路径
                    file_path_to_open = self._excel_file_paths[-1]

                    if os.path.exists(file_path_to_open):
                        # 直接打开文件，不改变UI
                        if sys.platform == 'win32':
                            os.startfile(file_path_to_open)
                        elif sys.platform == 'darwin':
                            subprocess.run(['open', file_path_to_open], check=True)
                        else:
                            subprocess.run(['xdg-open', file_path_to_open], check=True)

                        logger.info(f"用户点击打开Excel文件: {file_path_to_open}")

                    else:
                        logger.warning(f"Excel文件不存在: {file_path_to_open}")
                        # 向用户显示更友好的消息
                        self.status_bar.showMessage("⚠️ Excel文件不存在或已被移动", 3000)
                except Exception as e:
                    logger.error(f"打开Excel文件失败: {e}")
                    self.status_bar.showMessage("❌ 打开Excel文件失败", 3000)

                # 不调用原始事件处理，避免任何UI变化
                return
            else:
                print(f"[DEBUG] 不会触发Excel打开")

        # 对于其他点击，调用原始处理
        super(QTextBrowser, self.history_text).mousePressEvent(event)

    def _handle_link_clicked(self, url):
        """处理链接点击事件 - 简单打开文件，不改变显示"""
        # 这个方法现在基本不会被调用，但保留作为备用
        return False

  
    def _append_excel_info_to_history(self, file_name, file_path, record_count, file_size, mtime_str):
        """在识别历史标签页中添加Excel文件信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        excel_info = f"""
📊 Excel文件已生成
   📄 文件名: {file_name}
   📊 记录数量: {record_count} 条
   📏 文件大小: {self._format_file_size(file_size)}
   🕐 最后修改: {mtime_str}
        """

        def update_history():
            if hasattr(self, 'history_text') and self.history_text:
                scrollbar = self.history_text.verticalScrollBar()
                was_at_bottom = scrollbar.value() == scrollbar.maximum()

                # 添加Excel信息（不要时间戳前缀）
                self.history_text.append(excel_info)

                # 首先存储文件路径供后续使用（确保即使格式设置失败也能存储）
                # 只保留当前识别循环的Excel文件路径，不累积历史路径
                if not hasattr(self, '_excel_file_paths'):
                    self._excel_file_paths = []
                self._excel_file_paths = [file_path]  # 覆盖旧路径，只保留当前路径

                # 添加可点击的文件链接 - 使用富文本添加下划线但避免HTML链接
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)

                # 添加换行
                cursor.insertText('\n')

                # 添加带下划线的链接文本（普通格式）
                cursor.insertText('📂 点击打开Excel文件: ')

                # 只显示文件名，但存储完整路径用于点击打开
                file_name = os.path.basename(file_path)

                # 为文件名设置下划线和蓝色样式
                try:
                    # 保存当前格式
                    current_format = cursor.charFormat()

                    # 创建一个新的文本块来设置文件名样式，避免影响其他文本
                    char_format = QTextCharFormat()
                    char_format.setForeground(QColor("#2196F3"))  # 蓝色
                    char_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)  # 下划线
                    char_format.setFontItalic(True)  # 斜体

                    # 设置格式并插入文件名
                    cursor.setCharFormat(char_format)
                    cursor.insertText(file_name)

                    # 立即重置为默认格式，确保不影响后续任何文本
                    cursor.setCharFormat(current_format)  # 恢复之前的格式
                except Exception as e:
                    # 如果格式设置失败，使用普通文本
                    logger.warning(f"设置Excel链接样式失败，使用普通文本: {e}")
                    cursor.insertText(file_name)

                if was_at_bottom:
                    scrollbar.setValue(scrollbar.maximum())

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_history)

        print(f"[HISTORY] [{timestamp}] 📊 Excel文件已生成: {file_name} ({record_count}条记录)")
    def _append_clickable_file_link(self, file_name, file_path):
        """添加可点击的文件链接"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted_path = file_path.replace("\\", "/")
        html_message = f'[{timestamp}]   🔗 文件链接: <a href="file:///{formatted_path}" style="color: #2196F3; text-decoration: underline; font-weight: bold;">{file_name}</a>'

        def update_log_with_link():
            if hasattr(self, 'log_text') and self.log_text:
                scrollbar = self.log_text.verticalScrollBar()
                was_at_bottom = scrollbar.value() == scrollbar.maximum()

                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertHtml(f"<br>{html_message}")

                if was_at_bottom:
                    scrollbar.setValue(scrollbar.maximum())

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, update_log_with_link)

        print(f"[GUI LOG] [{timestamp}]   🔗 文件链接: {file_name} -> {file_path}")

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

    def validate_part_no(self, text):
        """验证零件号输入"""
        text = text.strip()
        if not text:
            self.validation_errors['part_no'] = "零件号不能为空"
            self.part_no_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        elif len(text) < 3:
            self.validation_errors['part_no'] = "零件号至少需要3个字符"
            self.part_no_input.setStyleSheet("border: 2px solid #ff9800; background-color: #fff3e0;")
        elif len(text) > 20:
            self.validation_errors['part_no'] = "零件号不能超过20个字符"
            self.part_no_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        else:
            self.validation_errors.pop('part_no', None)
            self.part_no_input.setStyleSheet("border: 2px solid #4caf50; background-color: #e8f5e8;")

        self.update_start_button_state()

    def validate_batch_no(self, text):
        """验证批次号输入"""
        text = text.strip()
        if not text:
            self.validation_errors['batch_no'] = "批次号不能为空"
            self.batch_no_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        elif len(text) < 3:
            self.validation_errors['batch_no'] = "批次号至少需要3个字符"
            self.batch_no_input.setStyleSheet("border: 2px solid #ff9800; background-color: #fff3e0;")
        elif len(text) > 15:
            self.validation_errors['batch_no'] = "批次号不能超过15个字符"
            self.batch_no_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        else:
            self.validation_errors.pop('batch_no', None)
            self.batch_no_input.setStyleSheet("border: 2px solid #4caf50; background-color: #e8f5e8;")

        self.update_start_button_state()

    def validate_inspector(self, text):
        """验证检验员输入"""
        text = text.strip()
        if not text:
            self.validation_errors['inspector'] = "检验员姓名不能为空"
            self.inspector_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        elif len(text) < 2:
            self.validation_errors['inspector'] = "检验员姓名至少需要2个字符"
            self.inspector_input.setStyleSheet("border: 2px solid #ff9800; background-color: #fff3e0;")
        elif len(text) > 10:
            self.validation_errors['inspector'] = "检验员姓名不能超过10个字符"
            self.inspector_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        elif not all(char.isalpha() or char in '·' for char in text):
            self.validation_errors['inspector'] = "检验员姓名只能包含中文字符"
            self.inspector_input.setStyleSheet("border: 2px solid #f44336; background-color: #ffebee;")
        else:
            self.validation_errors.pop('inspector', None)
            self.inspector_input.setStyleSheet("border: 2px solid #4caf50; background-color: #e8f5e8;")

        self.update_start_button_state()

    def update_start_button_state(self):
        """根据验证状态更新开始按钮"""
        has_errors = len(self.validation_errors) > 0

        if hasattr(self, 'start_button') and self.start_button:
            if has_errors:
                self.start_button.setEnabled(False)
                error_messages = list(self.validation_errors.values())
                self.start_button.setToolTip(f"请修正以下错误后再开始:\n" + "\n".join(f"• {msg}" for msg in error_messages))
                self.start_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ccc;
                        color: #666;
                        font-size: 12px;
                        font-weight: bold;
                        border: none;
                        border-radius: 6px;
                        padding: 8px;
                    }
                """)
            else:
                self.start_button.setEnabled(True)
                self.start_button.setToolTip("所有必填项已填写完整，可以开始识别")
                self.start_button.setStyleSheet("""
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
                """)

    def get_input_values(self):
        """获取输入框的值"""
        return {
            'part_no': self.part_no_input.text().strip() if self.part_no_input else "",
            'batch_no': self.batch_no_input.text().strip() if self.batch_no_input else "",
            'inspector': self.inspector_input.text().strip() if self.inspector_input else ""
        }

    def clear_input_fields(self):
        """清空输入框"""
        if self.part_no_input:
            self.part_no_input.clear()
            self.part_no_input.setStyleSheet("")
        if self.batch_no_input:
            self.batch_no_input.clear()
            self.batch_no_input.setStyleSheet("")
        if self.inspector_input:
            self.inspector_input.clear()
            self.inspector_input.setStyleSheet("")

        self.validation_errors.clear()
        self.update_start_button_state()

    def are_inputs_valid(self):
        """检查所有输入是否有效"""
        return len(self.validation_errors) == 0

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

    def handle_command_result(self, command_text: str):
        """处理命令结果，添加到历史记录"""
        try:
            # 直接添加到历史文本框
            if hasattr(self, 'history_text'):
                self.history_text.append(command_text)
                self.recognition_count += 1

                # 滚动到底部
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.history_text.setTextCursor(cursor)

        except Exception as e:
            logger.error(f"处理命令结果失败: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")    
    app.setApplicationName("FunASR语音识别系统 (多模式版)")

    window = WorkingSimpleMainWindow()
    window.show()
    
    window.update()
    window.repaint()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()