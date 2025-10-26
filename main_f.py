#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音输入系统主程序
集成语音识别、文本处理和循环控制功能
"""

# 在导入任何其他模块之前，首先设置全局日志级别为INFO，确保所有DEBUG日志都被过滤
import logging
logging.basicConfig(
    level=logging.INFO,  # 设置全局默认级别为INFO，完全禁止DEBUG日志显示
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

import sys
import os
import io
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any, Tuple, Union, Type, Sequence

# 类型别名
ExcelExporterType = Union[Type['ExcelExporter'], None]
from enum import Enum

# 配置基础设置
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

# 彻底禁用进度条和调试输出
import os
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['HIDE_PROGRESS'] = '1'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

# 配置日志级别，只显示错误
import logging
logging.getLogger("funasr").setLevel(logging.ERROR)
logging.getLogger("modelscope").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# 进一步抑制输出
import warnings
warnings.filterwarnings('ignore')

# 导入FunASR相关模块
from funasr_voice_tenvad import FunASRVoiceRecognizer
#from funasr_voice_module import FunASRVoiceRecognizer
from text_processor_clean import TextProcessor, VoiceCommandProcessor

# 导入性能监控模块
from utils.performance_monitor import performance_monitor, PerformanceStep

# 导入Debug性能追踪模块
from utils.debug_performance_tracker import debug_tracker

# 导入生产环境延迟记录器
try:
    from utils.production_latency_logger import (
        start_latency_session, end_latency_session,
        log_voice_input_end, log_asr_complete, log_terminal_display
    )
except ImportError:
    # 如果导入失败，提供空函数
    def start_latency_session(): pass
    def end_latency_session(): pass
    def log_voice_input_end(audio_duration: float): pass
    def log_asr_complete(text: str, asr_latency: float): pass
    def log_terminal_display(text: str, display_latency: float = 0.0): pass

# 导入Excel导出模块
try:
    from excel_exporter import ExcelExporter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    ExcelExporter = None  # type: ignore

# 使用统一的日志工具类
import logging
from utils.logging_utils import LoggingManager

# 获取配置好的日志记录器
logger = LoggingManager.get_logger(
    name='main_f',
    level=logging.DEBUG,  # 文件记录详细日志
    console_level=logging.INFO,  # 控制台只显示INFO及以上
    log_to_console=True,
    log_to_file=True
)

# 导入配置加载模块
config_loader: Any = None
CONFIG_AVAILABLE = False

try:
    from utils.config_loader import config
    config_loader = config
    CONFIG_AVAILABLE = True
except ImportError:
    logger.error("配置加载模块不可用，使用默认配置")
    CONFIG_AVAILABLE = False

    # 创建简单的配置替代
    class ConfigPlaceholder:
        def get_voice_commands_config(self):
            return {
                'pause': ['暂停', '停一下', '等一下'],
                'resume': ['继续', '开始', '接着来'],
                'stop': ['停止', '结束', '退出']
            }

        def get_pause_commands(self):
            return ['暂停', '停一下', '等一下']

        def get_resume_commands(self):
            return ['继续', '开始', '接着来']

        def get_stop_commands(self):
            return ['停止', '结束', '退出']

        def get_voice_command_config(self):
            return {
                'match_mode': 'fuzzy',
                'min_match_length': 2,
                'confidence_threshold': 0.8
            }

        def get_special_texts_config(self):
            return {"enabled": True, "exportable_texts": []}

        def is_special_text_export_enabled(self):
            return True

        def get_exportable_texts(self):
            return []

    # 使用替代配置
    config_loader = ConfigPlaceholder()

class SystemState(Enum):
    """系统状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"

class VoiceCommandType(Enum):
    """语音命令类型"""
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    UNKNOWN = "unknown"

class FunASRVoiceSystem:
    """
    FunASR语音输入系统主类
    集成语音识别、文本处理和控制功能
    """

    def __init__(self, recognition_duration: int = 60, continuous_mode: bool = True, debug_mode: bool = False):
        """
        初始化语音系统

        Args:
            recognition_duration: 识别持续时间（秒）
            continuous_mode: 是否启用连续模式
            debug_mode: 是否启用debug模式
        """
        self.recognition_duration = recognition_duration
        self.continuous_mode = continuous_mode
        self.debug_mode = debug_mode

        # 状态变化回调函数（用于GUI同步）
        self.state_change_callback = None

        # VAD事件回调函数（用于语音能量显示）
        self.vad_callback = None

        # 启用性能监控
        performance_monitor.enable()
        logger.info("🔍 性能监控已启用")

        # 系统状态
        self.state = SystemState.STOPPED
        self.results_buffer: List[Dict[str, Any]] = []
        self.number_results: List[Tuple[int, Union[float, str], str]] = []  # (ID, number/str, original_text)

        # 创建核心组件
        self.recognizer = FunASRVoiceRecognizer(silent_mode=True)
        self.processor = TextProcessor()
        self.command_processor = VoiceCommandProcessor()

        # Excel导出器
        self.excel_exporter: Optional[ExcelExporter] = None
        self._setup_excel_exporter()

        # 日志设置
        self._setup_logging()

        # 从配置加载语音命令
        voice_commands_config = config_loader.get_voice_commands_config()
        self.voice_commands = {
            VoiceCommandType.PAUSE: config_loader.get_pause_commands(),
            VoiceCommandType.RESUME: config_loader.get_resume_commands(),
            VoiceCommandType.STOP: config_loader.get_stop_commands()
        }

        # 加载语音命令识别配置
        self.voice_command_config = config_loader.get_voice_command_config()
        match_mode = self.voice_command_config.get('match_mode', 'fuzzy')
        min_match_length = self.voice_command_config.get('min_match_length', 2)
        confidence_threshold = self.voice_command_config.get('confidence_threshold', 0.8)

        # 配置语音命令处理器
        self.command_processor.configure(
            match_mode=match_mode,
            min_match_length=min_match_length,
            confidence_threshold=confidence_threshold
        )
        
        # 加载特定文本配置
        self.special_text_config = config_loader.get_special_texts_config()
        self.export_special_texts = config_loader.is_special_text_export_enabled()
        self.exportable_texts = config_loader.get_exportable_texts()

        # 键盘监听线程和停止标志
        self.keyboard_thread = None
        self.keyboard_active = False
        self.system_should_stop = False  # 系统停止标志

        logger.info("🎤 FunASR语音系统初始化完成")

        # 显示语音命令配置信息
        self._log_voice_commands_config()

    def _setup_excel_exporter(self):
        """设置Excel导出器"""
        if not EXCEL_AVAILABLE:
            logger.warning("Excel导出模块不可用")
            return

        try:
            # 创建reports目录
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)

            # 生成文件名: report_yyyymmdd_hhmmss.xlsx
            now = datetime.now()
            filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(reports_dir, filename)

            self.excel_exporter = ExcelExporter(filename=filepath)
            # 预先创建Excel文件，避免在首次识别后才创建
            self.excel_exporter.create_new_file()
            logger.info(f"Excel导出器已设置: {filepath}")
        except Exception as e:
            logger.error(f"设置Excel导出器失败: {e}")

    def _log_voice_commands_config(self):
        """记录语音命令配置信息"""
        # 从新的命令处理器获取配置
        logger.info("🎯 语音命令配置:")
        logger.info(f"  模式: {self.command_processor.match_mode}")
        logger.info(f"  最小匹配长度: {self.command_processor.min_match_length}")
        logger.info(f"  置信度阈值: {self.command_processor.confidence_threshold}")

        for command_type, keywords in self.voice_commands.items():
            if command_type == VoiceCommandType.PAUSE:
                logger.info(f"  暂停命令: {', '.join(keywords)}")
            elif command_type == VoiceCommandType.RESUME:
                logger.info(f"  继续命令: {', '.join(keywords)}")
            elif command_type == VoiceCommandType.STOP:
                logger.info(f"  停止命令: {', '.join(keywords)}")

    def _setup_logging(self):
        """设置日志记录"""
        from utils.logging_utils import get_logger
        
        # 使用统一的日志工具获取专门的识别日志记录器
        self.recognition_logger = get_logger("voice_recognition", level=logging.INFO)
        logger.info("识别日志已配置完成")

    def set_state_change_callback(self, callback):
        """设置状态变化回调函数（用于GUI同步）"""
        self.state_change_callback = callback

    def set_vad_callback(self, callback):
        """设置VAD事件回调函数（用于语音能量显示）"""
        self.vad_callback = callback

    def _notify_state_change(self, state: str, message: str = ""):
        """通知状态变化"""
        if self.state_change_callback:
            self.state_change_callback(state, message)

    def _handle_vad_event(self, event_type: str, event_data: dict):
        """处理VAD事件并转发给回调函数"""
        # 🔍 调试输出 - 已注释，避免控制台输出过多
        energy = event_data.get('energy', 0)
        logger.debug(f"[🔗 MAIN接收] ← 收到VAD事件: {event_type} | 能量: {energy:.8f} | 数据: {event_data}")
        logger.debug(f"[🔗 MAIN检查] VAD回调已设置: {self.vad_callback is not None}")

        # 🔥 关键修复：添加防护检查，防止语音命令处理期间的VAD回调错误
        if self.vad_callback and event_type in ['speech_start', 'speech_end', 'energy_update']:
            logger.debug(f"[🔗 MAIN转发] → 转发VAD事件给GUI | 事件: {event_type} | 能量: {energy:.8f}")
            try:
                self.vad_callback(event_type, event_data)
                logger.debug(f"[🔗 MAIN成功] ✅ VAD事件转发成功")
            except Exception as e:
                logger.error(f"[🔗 MAIN错误] ❌ VAD事件转发失败: {e}")
        elif not self.vad_callback:
            # 🔥 修复：控制台模式下VAD回调未设置是正常情况，改为DEBUG级别
            if event_type in ['speech_start', 'speech_end']:
                logger.info(f"🎤 {event_type.replace('_', ' ').title()} (能量: {energy:.3f})")
            else:
                logger.debug(f"[🔗 MAIN信息] ℹ️ 控制台模式：VAD回调未设置，跳过GUI事件转发")
        # 🔥 防止其他VAD事件类型的错误日志干扰
        # logger.debug(f"[🔗 MAIN跳过] VAD事件类型: {event_type} (已通过其他渠道处理)")

    def initialize(self) -> bool:
        """初始化系统"""
        try:
            # 设置环境变量禁用进度条
            import os
            os.environ['TQDM_DISABLE'] = '1'

            success = self.recognizer.initialize()
            if success:
                logger.info("✅ FunASR识别器初始化成功")

                # 设置VAD事件回调
                if hasattr(self.recognizer, 'set_callbacks'):
                    self.recognizer.set_callbacks(on_vad_event=self._handle_vad_event)
                    logger.info("✅ VAD事件回调已设置")

                return True
            else:
                logger.error("❌ FunASR识别器初始化失败")
                return False
        except Exception as e:
            logger.error(f"❌ 系统初始化异常: {e}")
            return False

    def recognize_voice_command(self, text: str) -> VoiceCommandType:
        """
        识别语音命令，支持配置化的匹配模式

        Args:
            text: 识别的文本

        Returns:
            语音命令类型
        """
        # 转换命令字典格式以适配新的处理器
        command_dict = {
            command_type.value: keywords
            for command_type, keywords in self.voice_commands.items()
        }

        # 使用新的语音命令处理器
        result = self.command_processor.match_command(text, command_dict)

        if result:
            # 将字符串结果转换回枚举类型
            for command_type in VoiceCommandType:
                if command_type.value == result:
                    return command_type

        return VoiceCommandType.UNKNOWN

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本之间的相似度 (已弃用，使用TextProcessor.calculate_similarity)
        为了向后兼容保留此方法

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1之间的浮点数)
        """
        # 使用新的文本处理器，保持向后兼容
        return self.processor.calculate_similarity(text1, text2)

    def _check_special_text(self, text: str) -> Optional[str]:
        """
        检查文本是否匹配特定文本配置 (已弃用，使用TextProcessor.check_special_text)
        为了向后兼容保留此方法

        Args:
            text: 要检查的文本

        Returns:
            如果匹配，返回对应的基础文本；否则返回None
        """
        # 使用新的文本处理器，保持向后兼容
        return self.processor.check_special_text(
            text,
            self.exportable_texts,
            self.export_special_texts
        )
        
    def process_recognition_result(self, original_text: str, processed_text: str, numbers: List[float]):
        """
        处理识别结果

        Args:
            original_text: 原始识别文本
            processed_text: 处理后文本
            numbers: 提取的数字
        """
        # 添加性能监控
        with PerformanceStep("结果处理", {
            'original_length': len(original_text),
            'processed_length': len(processed_text),
            'numbers_count': len(numbers)
        }):
            # 添加到结果缓冲区
            self.results_buffer.append({
            'original': original_text,
            'processed': processed_text,
            'numbers': numbers,
            'timestamp': time.time()
        })

        # 终端显示（记录时间戳）- 改为DEBUG级别，避免控制台输出过多
        terminal_start = time.time()
        logger.debug(f"\n🎤 识别: {processed_text}")
        if numbers and len(numbers) > 0:
            logger.debug(f"🔢 数字: {numbers[0]}")
        terminal_time = time.time() - terminal_start

        # 记录终端显示时间
        debug_tracker.record_terminal_display(processed_text)

        # 记录生产环境终端显示
        log_terminal_display(processed_text, float(terminal_time))

        # 记录详细日志（包含原始音频输入、处理后的文本和数字）
        if hasattr(self, 'recognition_logger'):
            # 改为info级别以便用户查看，包含完整的处理流程信息
            log_message = f"原始输入: '{original_text}' -> 处理后: '{processed_text}' | 终端显示: {terminal_time*1000:.2f}ms"
            if numbers and len(numbers) > 0:
                log_message += f" -> 提取数字: {numbers[0]}"
            self.recognition_logger.info(log_message)

        # 检查是否为特定文本
        special_text_match = self._check_special_text(processed_text)
        
        # 处理纯数字结果或特定文本结果
        if (numbers and self.excel_exporter) or (special_text_match and self.excel_exporter):
            # 添加到结果列表
            try:
                # 准备要写入Excel的数据
                excel_data: List[Tuple[Union[float, str], str, str]] = []
                
                if numbers:
                    # 数字结果
                    excel_data.append((numbers[0], original_text, processed_text))
                    result_type = "数字"
                    result_value: Union[float, str] = numbers[0]
                else:
                    # 特定文本结果
                    # 将特定文本直接写入Excel，而不是数值
                    text_value = special_text_match  # 直接使用OK/Not OK文本
                    excel_data.append((text_value, original_text, special_text_match))
                    result_type = "特定文本"
                    result_value = special_text_match  # type: ignore
                
                # Excel写入开始
                excel_start = time.time()

                # 使用Excel导出器生成ID并保存
                with PerformanceStep("Excel写入", {
                    'data_type': result_type,
                    'data_count': len(excel_data),
                    'result_value': result_value
                }):
                    excel_result = self.excel_exporter.append_with_text(excel_data)

                # Excel写入结束
                excel_time = time.time() - excel_start
                debug_tracker.record_excel_write(processed_text, excel_time)

                if excel_result:
                    record_id, record_number, record_text = excel_result[0]

                    # 根据结果类型处理record_number
                    if result_type == "特定文本":
                        # 特定文本结果：直接存储特殊文本，便于GUI区分
                        number_value = record_number  # 存储OK/Not OK文本
                    else:
                        # 数字结果：record_number是数值
                        number_value = float(record_number) if isinstance(record_number, (int, float)) else 0.0

                    self.number_results.append((record_id, number_value, record_text))

                    # 统一使用logger.info记录识别结果
                    if hasattr(self, 'recognition_logger'):
                        log_message = f"识别文本: '{processed_text}' -> {result_type}: {record_id}: {result_value}"
                        self.recognition_logger.info(log_message)
                else:
                    # Excel写入失败，使用logger.info记录
                    if hasattr(self, 'recognition_logger'):
                        log_message = f"识别文本: '{processed_text}' -> {result_type}: -: {result_value}"
                        self.recognition_logger.info(log_message)
            except Exception as e:
                logger.error(f"Excel导出失败: {e}")
                # 回退记录
                if hasattr(self, 'recognition_logger'):
                    if numbers:
                        log_message = f"识别文本: '{processed_text}' -> 数字: -: {numbers[0]}"
                    else:
                        log_message = f"识别文本: '{processed_text}' -> 特定文本: -: {special_text_match}"
                    self.recognition_logger.info(log_message)
        else:
            # 非数字结果，也非特定文本结果，记录到日志
            if hasattr(self, 'recognition_logger'):
                self.recognition_logger.info(f"识别文本: '{processed_text}'")

    def on_recognition_result(self, result):
        """识别结果回调函数"""
        # 如果系统已经停止，不再处理任何识别结果
        if self.system_should_stop:
            return

        if result.text.strip():
            # 记录ASR结果完成
            debug_tracker.record_asr_result(result.text, getattr(result, 'confidence', 0.0))

            # 记录生产环境ASR完成
            log_asr_complete(result.text, 0.0)  # 这里可以传入实际的ASR处理时间

            # 文本处理开始
            debug_tracker.record_text_processing_start(result.text)
            text_processing_start = time.time()

            processed = self.processor.process_text(result.text)
            numbers = self.processor.extract_numbers(result.text, processed)

            # 文本处理结束
            text_processing_time = time.time() - text_processing_start
            debug_tracker.record_text_processing_end(processed, len(numbers) > 0)

            # 记录详细处理时间到日志
            logger.debug(f"[LATENCY] ASR结果: '{result.text}' | 文本处理: {text_processing_time*1000:.2f}ms")

            # 检查是否为语音命令
            command_type = self.recognize_voice_command(processed)

            if command_type != VoiceCommandType.UNKNOWN:
                self.handle_voice_command(command_type)
            else:
                # 处理普通识别结果
                if self.state == SystemState.RUNNING:
                    self.process_recognition_result(result.text, processed, numbers)

    def handle_voice_command(self, command_type: VoiceCommandType):
        """处理语音命令"""
        # 防止在系统停止后重复处理命令
        if self.system_should_stop:
            return

        if command_type == VoiceCommandType.PAUSE:
            self.pause()
            logger.debug(f"\n🎤 语音命令：暂停")
            self._notify_state_change("paused", "语音命令：暂停")
        elif command_type == VoiceCommandType.RESUME:
            self.resume()
            logger.debug(f"\n🎤 语音命令：恢复")
            self._notify_state_change("resumed", "语音命令：恢复")
        elif command_type == VoiceCommandType.STOP:
            self.system_stop()
            logger.debug(f"\n🎤 语音命令：停止")
            self._notify_state_change("stopped", "语音命令：停止")

    def start_keyboard_listener(self):
        """启动键盘监听线程"""
        self.keyboard_active = True

        def keyboard_monitor():
            """键盘监听函数"""
            import msvcrt  # Windows专用
            import sys

            while self.keyboard_active and not self.system_should_stop:
                try:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()

                        if key == b' ':  # 空格键
                            if self.state == SystemState.RUNNING:
                                self.pause()
                                logger.debug(f"\n⌨️ 键盘命令：暂停")
                            elif self.state == SystemState.PAUSED:
                                self.resume()
                                logger.debug(f"\n⌨️ 键盘命令：恢复")
                            elif self.state == SystemState.STOPPED:
                                # 在停止状态下，空格键开始新的识别
                                logger.debug(f"\n⌨️ 键盘命令：开始识别")
                                self.run_recognition_cycle()

                        elif key == b'\x1b':  # ESC键
                            self.system_stop()
                            logger.debug(f"\n⌨️ 键盘命令：停止")
                            break

                except KeyboardInterrupt:
                    self.system_stop()
                    break
                except Exception:
                    # 忽略键盘异常，继续监听
                    pass

                time.sleep(0.05)  # 减少延迟，提高响应性

        self.keyboard_thread = threading.Thread(target=keyboard_monitor, daemon=True)
        self.keyboard_thread.start()
        logger.debug("⌨️ 键盘监听器已启动")

    def stop_keyboard_listener(self):
        """停止键盘监听"""
        self.keyboard_active = False
        if self.keyboard_thread and self.keyboard_thread.is_alive():
            self.keyboard_thread.join(timeout=1)
        logger.debug("⌨️ 键盘监听器已停止")

    def start_recognition(self):
        """开始语音识别"""
        if self.state != SystemState.STOPPED:
            return

        self.state = SystemState.RUNNING
        logger.info(f"\n🎯 开始语音识别")
        logger.debug("请说话...")
        logger.debug("控制：空格键-暂停/恢复 | ESC键-停止 | 语音命令-暂停/继续/停止")
        logger.debug(f"语音命令 (模式: {self.command_processor.match_mode}):")
        logger.debug(f"  暂停: {', '.join(self.voice_commands[VoiceCommandType.PAUSE][:3])}{'...' if len(self.voice_commands[VoiceCommandType.PAUSE]) > 3 else ''}")
        logger.debug(f"  继续: {', '.join(self.voice_commands[VoiceCommandType.RESUME][:3])}{'...' if len(self.voice_commands[VoiceCommandType.RESUME]) > 3 else ''}")
        logger.debug(f"  停止: {', '.join(self.voice_commands[VoiceCommandType.STOP][:3])}{'...' if len(self.voice_commands[VoiceCommandType.STOP]) > 3 else ''}")
        logger.debug("-" * 50)

    def pause(self):
        """暂停识别"""
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            logger.debug(f"\n⏸️ 已暂停")

    def resume(self):
        """恢复识别"""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            logger.debug(f"\n▶️ 已恢复")

    def stop(self):
        """停止当前识别（不停止系统）"""
        if self.state != SystemState.STOPPED:
            self.state = SystemState.STOPPED
            logger.debug(f"\n🛑 识别已停止")

    def system_stop(self):
        """完全停止系统"""
        self.state = SystemState.STOPPED
        self.system_should_stop = True
        logger.info(f"\n🛑 系统停止")

        # 立即停止识别器
        try:
            self.recognizer.stop_recognition()
        except:
            pass

        # 输出性能分析报告
        try:
            performance_report = performance_monitor.export_performance_report()
            if performance_report:
                logger.debug("\n" + "="*80)
                logger.debug("📊 系统性能分析报告")
                logger.debug("="*80)
                logger.debug(performance_report)
                logger.debug("="*80)

                # 将性能报告写入日志文件
                performance_logger = logging.getLogger("performance")
                performance_logger.info(performance_report)
        except Exception as e:
            logger.error(f"性能报告生成失败: {e}")

        # 清理性能监控数据
        performance_monitor.clear_records()

    def run_recognition_cycle(self):
        """运行识别循环"""
        # 设置回调（保留VAD回调）
        self.recognizer.set_callbacks(
            on_final_result=self.on_recognition_result,
            on_vad_event=self._handle_vad_event  # 🔧 修复：保留VAD回调
        )

        # 开始识别
        self.start_recognition()

        try:
            # 执行识别
            self.recognizer.recognize_speech(
                duration=self.recognition_duration,
                real_time_display=False
            )

        except KeyboardInterrupt:
            logger.info(f"\n⚠️ 用户中断")
            logger.info("🛑 用户手动中断识别流程")
        except Exception as e:
            logger.error(f"❌ 识别异常: {e}")
            logger.debug(f"❌ 识别异常，请检查日志")

        # 识别结束，记录原因
        if self.system_should_stop:
            logger.info("🛑 系统接收到停止信号")
            logger.debug("🛑 系统停止")
        else:
            logger.info("🛑 识别流程正常结束")
            logger.debug("🛑 识别结束")

        self.stop()

    def run_continuous(self):
        """运行单次识别模式"""
        logger.info("🎤 FunASR语音输入系统")
        logger.debug("=" * 50)
        logger.debug(f"模式：单次识别")
        logger.debug(f"识别时长：{self.recognition_duration}秒")
        logger.debug("控制：空格键暂停/恢复 | ESC键停止 | 语音命令控制")
        logger.debug(f"语音命令配置 (模式: {self.command_processor.match_mode}):")
        logger.debug(f"  暂停: {', '.join(self.voice_commands[VoiceCommandType.PAUSE][:3])}{'...' if len(self.voice_commands[VoiceCommandType.PAUSE]) > 3 else ''}")
        logger.debug(f"  继续: {', '.join(self.voice_commands[VoiceCommandType.RESUME][:3])}{'...' if len(self.voice_commands[VoiceCommandType.RESUME]) > 3 else ''}")
        logger.debug(f"  停止: {', '.join(self.voice_commands[VoiceCommandType.STOP][:3])}{'...' if len(self.voice_commands[VoiceCommandType.STOP]) > 3 else ''}")
        logger.debug("=" * 50)

        # 启动键盘监听
        self.start_keyboard_listener()

        # 启动debug性能追踪
        debug_tracker.start_debug_session(f"funasr_session_{int(time.time())}")

        # 启动生产环境延迟记录
        start_latency_session()

        try:
            # 🔥 修复：检查系统是否已经被停止
            if self.system_should_stop:
                logger.info("🛑 系统已收到停止信号，退出识别循环")
                return

            # 直接开始识别
            logger.info(f"\n🎯 开始语音识别")
            logger.debug("请说话...")
            logger.debug("-" * 50)

            self.run_recognition_cycle()

            # 🔥 修复：在识别循环后再次检查停止信号
            if self.system_should_stop:
                logger.info("🛑 识别循环结束后收到停止信号，不显示汇总")
                return

            # 显示汇总（只显示一次）
            if not self.system_should_stop:  # 只有当系统没有被命令停止时才显示汇总
                logger.debug("\n" + "=" * 50)
                logger.debug("识别汇总")
                logger.debug("=" * 50)

                self.show_results_summary()

        except KeyboardInterrupt:
            logger.info(f"\n⚠️ 用户中断")
            self.system_stop()

        finally:
            # 停止键盘监听
            self.stop_keyboard_listener()

            # 停止debug追踪并生成报告
            debug_tracker.stop_debug_session()

            # 停止生产环境延迟记录
            end_latency_session()

            # 清理资源
            try:
                self.recognizer.stop_recognition()
                self.recognizer.unload_model()
            except:
                pass

    def show_results_summary(self):
        """显示识别结果汇总"""
        if not self.results_buffer:
            logger.debug("\n📊 本次运行无识别结果")
            return

        logger.debug(f"\n📊 识别结果汇总")
        logger.debug("=" * 50)

        # 统计信息
        total_results = len(self.results_buffer)
        number_results = [r for r in self.results_buffer if r['numbers']]
        text_results = [r for r in self.results_buffer if not r['numbers']]

        logger.debug(f"📈 总识别次数：{total_results}")
        logger.debug(f"🔢 纯数字识别：{len(number_results)}")
        logger.debug(f"📝 文本识别：{len(text_results)}")

        if number_results:
            all_numbers = []
            for result in number_results:
                all_numbers.extend(result['numbers'])
            logger.debug(f"📊 提取的数字：{all_numbers}")

        # 显示详细结果
        logger.debug(f"\n📋 详细识别结果：")
        for i, result in enumerate(self.results_buffer, 1):
            status = "🔢" if result['numbers'] else "📝"
            logger.debug(f"{i:2d}. {status} {result['original']}")
            if result['numbers']:
                logger.debug(f"     → {result['numbers'][0]}")
            elif result['processed'] != result['original']:
                if self.processor.is_pure_number_or_with_unit(result['original']):
                    logger.debug(f"     → {result['processed']}")
                else:
                    clean_text = self.processor.remove_spaces(result['original'])
                    logger.debug(f"     → {clean_text}")

def main():
    """主函数"""
    # 检查是否启用debug模式
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    # 动态调整日志级别 - 现在只需要设置logger本身的级别
    # 控制台级别已经在logging_utils.py中统一设置为INFO
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    if debug_mode:
        logger.info("🐛 Debug模式已启用")
    else:
        logger.info("🏭 生产模式")

    # 创建系统实例
    system = FunASRVoiceSystem(
        recognition_duration=60,  # 每次识别60秒
        continuous_mode=False,     # 单次模式
        debug_mode=debug_mode      # debug模式设置
    )

    # 初始化系统
    if not system.initialize():
        logger.error("❌ 系统初始化失败")
        return

    try:
        # 运行系统
        system.run_continuous()

    except Exception as e:
        logger.error(f"❌ 系统运行异常: {e}")

    finally:
        # 显示Excel文件路径（如果有数字数据）
        if system.number_results and system.excel_exporter:
            logger.info(f"\n📊 数据已保存到: {system.excel_exporter.filename}")

        logger.info("\n👋 感谢使用FunASR语音输入系统！")

if __name__ == "__main__":
    main()