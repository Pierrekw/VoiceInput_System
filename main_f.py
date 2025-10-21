#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音输入系统主程序
集成语音识别、文本处理和循环控制功能
"""

import sys
import os
import io
import threading
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any, Tuple, Union, Type

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
from funasr_voice_module import FunASRVoiceRecognizer
from text_processor_clean import TextProcessor

# 导入性能监控模块
from performance_monitor import performance_monitor, PerformanceStep

# 导入Debug性能追踪模块
from debug_performance_tracker import debug_tracker

# 导入生产环境延迟记录器
try:
    from production_latency_logger import (
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_input_funasr.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 导入配置加载模块
try:
    from config_loader import config as config_loader
except ImportError:
    logger.error("配置加载模块不可用，使用默认配置")
    
    # 创建简单的配置替代
    class ConfigPlaceholder:
        def get_special_texts_config(self):
            return {"enabled": True, "exportable_texts": []}
        
        def is_special_text_export_enabled(self):
            return True
            
        def get_exportable_texts(self):
            return []
    
    # config_loader 模块的占位符，实际运行时动态加载
config_loader = None  # type: ignore

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

        # 启用性能监控
        performance_monitor.enable()
        logger.info("🔍 性能监控已启用")

        # 系统状态
        self.state = SystemState.STOPPED
        self.results_buffer: List[Dict[str, Any]] = []
        self.number_results: List[Tuple[int, Union[int, float], str]] = []  # (ID, number, original_text)

        # 创建核心组件
        self.recognizer = FunASRVoiceRecognizer(silent_mode=True)
        self.processor = TextProcessor()

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
        self.match_mode = self.voice_command_config.get('match_mode', 'fuzzy')
        self.min_match_length = self.voice_command_config.get('min_match_length', 2)
        self.confidence_threshold = self.voice_command_config.get('confidence_threshold', 0.8)
        
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
        logger.info("🎯 语音命令配置:")
        logger.info(f"  模式: {self.match_mode}")
        logger.info(f"  最小匹配长度: {self.min_match_length}")
        logger.info(f"  置信度阈值: {self.confidence_threshold}")

        for command_type, keywords in self.voice_commands.items():
            if command_type == VoiceCommandType.PAUSE:
                logger.info(f"  暂停命令: {', '.join(keywords)}")
            elif command_type == VoiceCommandType.RESUME:
                logger.info(f"  继续命令: {', '.join(keywords)}")
            elif command_type == VoiceCommandType.STOP:
                logger.info(f"  停止命令: {', '.join(keywords)}")

    def _setup_logging(self):
        """设置日志记录"""
        try:
            # 创建logs目录
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)

            # 生成日志文件名: voice_recognition_yyyymmdd_hhmmss.log
            now = datetime.now()
            log_filename = f"voice_recognition_{now.strftime('%Y%m%d_%H%M%S')}.log"
            log_filepath = os.path.join(logs_dir, log_filename)

            # 配置专门的识别日志记录器
            self.recognition_logger = logging.getLogger("voice_recognition")
            self.recognition_logger.setLevel(logging.INFO)

            # 文件处理器
            file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
            file_handler.setLevel(logging.INFO)

            # 格式化器
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)

            # 添加处理器
            self.recognition_logger.addHandler(file_handler)

            logger.info(f"识别日志已设置: {log_filepath}")
        except Exception as e:
            logger.error(f"设置识别日志失败: {e}")

    def set_state_change_callback(self, callback):
        """设置状态变化回调函数（用于GUI同步）"""
        self.state_change_callback = callback

    def _notify_state_change(self, state: str, message: str = ""):
        """通知状态变化"""
        if self.state_change_callback:
            self.state_change_callback(state, message)

    def initialize(self) -> bool:
        """初始化系统"""
        try:
            # 设置环境变量禁用进度条
            import os
            os.environ['TQDM_DISABLE'] = '1'

            success = self.recognizer.initialize()
            if success:
                logger.info("✅ FunASR识别器初始化成功")
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
        if not text or len(text.strip()) < self.min_match_length:
            return VoiceCommandType.UNKNOWN

        text_clean = text.lower().strip()

        # 移除常见的标点符号
        import re
        text_clean = re.sub(r'[。！？\.,!?\s]', '', text_clean)

        for command_type, keywords in self.voice_commands.items():
            for keyword in keywords:
                keyword_clean = keyword.lower().strip()
                keyword_clean = re.sub(r'[。！？\.,!?\s]', '', keyword_clean)

                if self.match_mode == "exact":
                    # 精确匹配模式
                    if text_clean == keyword_clean:
                        logger.debug(f"精确匹配命令: '{text}' -> '{keyword}' ({command_type.value})")
                        return command_type

                elif self.match_mode == "fuzzy":
                    # 模糊匹配模式 - 支持包含匹配和相似度匹配
                    if keyword_clean in text_clean or text_clean in keyword_clean:
                        # 对于停止命令，要求更高的匹配度
                        if command_type == VoiceCommandType.STOP:
                            # 停止命令需要至少70%的相似度或者是完全包含
                            similarity = self._calculate_similarity(text_clean, keyword_clean)
                            if similarity >= 0.7 or keyword_clean in text_clean:
                                logger.debug(f"模糊匹配停止命令: '{text}' -> '{keyword}' (相似度: {similarity:.2f})")
                                return command_type
                        else:
                            # 其他命令使用标准的相似度阈值
                            similarity = self._calculate_similarity(text_clean, keyword_clean)
                            if similarity >= self.confidence_threshold:
                                logger.debug(f"模糊匹配命令: '{text}' -> '{keyword}' (相似度: {similarity:.2f})")
                                return command_type

        return VoiceCommandType.UNKNOWN

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本之间的相似度
        使用简单的编辑距离算法

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1之间的浮点数)
        """
        if not text1 or not text2:
            return 0.0

        # 如果完全相等，返回1.0
        if text1 == text2:
            return 1.0

        # 计算编辑距离
        len1, len2 = len(text1), len(text2)
        if len1 == 0:
            return 0.0
        if len2 == 0:
            return 0.0

        # 创建动态规划表
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        # 初始化边界条件
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        # 填充动态规划表
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,      # 删除
                        dp[i][j-1] + 1,      # 插入
                        dp[i-1][j-1] + 1     # 替换
                    )

        # 计算相似度
        max_len = max(len1, len2)
        edit_distance = dp[len1][len2]
        similarity = 1.0 - (edit_distance / max_len)

        return max(0.0, similarity)

    def _check_special_text(self, text: str) -> Optional[str]:
        """
        检查文本是否匹配特定文本配置
        
        Args:
            text: 要检查的文本
            
        Returns:
            如果匹配，返回对应的基础文本；否则返回None
        """
        if not self.export_special_texts or not self.exportable_texts:
            return None
        
        text_lower = text.lower().strip()
        
        for text_config in self.exportable_texts:
            base_text = text_config.get('base_text')
            variants = text_config.get('variants', [])
            
            # 检查文本是否匹配任何变体
            for variant in variants:
                if variant.lower() == text_lower or text_lower in variant.lower():
                    return base_text
        
        return None
        
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

        # 终端显示（记录时间戳）
        terminal_start = time.time()
        print(f"\n🎤 识别: {processed_text}")
        if numbers and len(numbers) > 0:
            print(f"🔢 数字: {numbers[0]}")
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
                excel_data = []
                
                if numbers:
                    # 数字结果
                    excel_data.append((numbers[0], original_text, processed_text))
                    result_type = "数字"
                    result_value: Union[float, str] = numbers[0]
                else:
                    # 特定文本结果
                    # 将特定文本作为数值的替代写入Excel
                    # 使用1代表OK，0代表Not OK或其他特殊文本
                    text_value = 1.0 if special_text_match == "OK" else 0.0
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
                    # 确保record_number是数值类型
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
            print(f"\n🎤 语音命令：暂停")
            self._notify_state_change("paused", "语音命令：暂停")
        elif command_type == VoiceCommandType.RESUME:
            self.resume()
            print(f"\n🎤 语音命令：恢复")
            self._notify_state_change("resumed", "语音命令：恢复")
        elif command_type == VoiceCommandType.STOP:
            self.system_stop()
            print(f"\n🎤 语音命令：停止")
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
                                print(f"\n⌨️ 键盘命令：暂停")
                            elif self.state == SystemState.PAUSED:
                                self.resume()
                                print(f"\n⌨️ 键盘命令：恢复")
                            elif self.state == SystemState.STOPPED:
                                # 在停止状态下，空格键开始新的识别
                                print(f"\n⌨️ 键盘命令：开始识别")
                                self.run_recognition_cycle()

                        elif key == b'\x1b':  # ESC键
                            self.system_stop()
                            print(f"\n⌨️ 键盘命令：停止")
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
        logger.info("⌨️ 键盘监听器已启动")

    def stop_keyboard_listener(self):
        """停止键盘监听"""
        self.keyboard_active = False
        if self.keyboard_thread and self.keyboard_thread.is_alive():
            self.keyboard_thread.join(timeout=1)
        logger.info("⌨️ 键盘监听器已停止")

    def start_recognition(self):
        """开始语音识别"""
        if self.state != SystemState.STOPPED:
            return

        self.state = SystemState.RUNNING
        print(f"\n🎯 开始语音识别")
        print("请说话...")
        print("控制：空格键-暂停/恢复 | ESC键-停止 | 语音命令-暂停/继续/停止")
        print(f"语音命令 (模式: {self.match_mode}):")
        print(f"  暂停: {', '.join(self.voice_commands[VoiceCommandType.PAUSE][:3])}{'...' if len(self.voice_commands[VoiceCommandType.PAUSE]) > 3 else ''}")
        print(f"  继续: {', '.join(self.voice_commands[VoiceCommandType.RESUME][:3])}{'...' if len(self.voice_commands[VoiceCommandType.RESUME]) > 3 else ''}")
        print(f"  停止: {', '.join(self.voice_commands[VoiceCommandType.STOP][:3])}{'...' if len(self.voice_commands[VoiceCommandType.STOP]) > 3 else ''}")
        print("-" * 50)

    def pause(self):
        """暂停识别"""
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            print(f"\n⏸️ 已暂停")

    def resume(self):
        """恢复识别"""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            print(f"\n▶️ 已恢复")

    def stop(self):
        """停止当前识别（不停止系统）"""
        if self.state != SystemState.STOPPED:
            self.state = SystemState.STOPPED
            print(f"\n🛑 识别已停止")

    def system_stop(self):
        """完全停止系统"""
        self.state = SystemState.STOPPED
        self.system_should_stop = True
        print(f"\n🛑 系统停止")

        # 立即停止识别器
        try:
            self.recognizer.stop_recognition()
        except:
            pass

        # 输出性能分析报告
        try:
            performance_report = performance_monitor.export_performance_report()
            if performance_report:
                print("\n" + "="*80)
                print("📊 系统性能分析报告")
                print("="*80)
                print(performance_report)
                print("="*80)

                # 将性能报告写入日志文件
                performance_logger = logging.getLogger("performance")
                performance_logger.info(performance_report)
        except Exception as e:
            logger.error(f"性能报告生成失败: {e}")

        # 清理性能监控数据
        performance_monitor.clear_records()

    def run_recognition_cycle(self):
        """运行识别循环"""
        # 设置回调
        self.recognizer.set_callbacks(on_final_result=self.on_recognition_result)

        # 开始识别
        self.start_recognition()

        try:
            # 执行识别
            self.recognizer.recognize_speech(
                duration=self.recognition_duration,
                real_time_display=False
            )

        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断")
            logger.info("🛑 用户手动中断识别流程")
        except Exception as e:
            logger.error(f"❌ 识别异常: {e}")
            print(f"❌ 识别异常，请检查日志")

        # 识别结束，记录原因
        if self.system_should_stop:
            logger.info("🛑 系统接收到停止信号")
            print("🛑 系统停止")
        else:
            logger.info("🛑 识别流程正常结束")
            print("🛑 识别结束")

        self.stop()

    def run_continuous(self):
        """运行单次识别模式"""
        print("🎤 FunASR语音输入系统")
        print("=" * 50)
        print(f"模式：单次识别")
        print(f"识别时长：{self.recognition_duration}秒")
        print("控制：空格键暂停/恢复 | ESC键停止 | 语音命令控制")
        print(f"语音命令配置 (模式: {self.match_mode}):")
        print(f"  暂停: {', '.join(self.voice_commands[VoiceCommandType.PAUSE][:3])}{'...' if len(self.voice_commands[VoiceCommandType.PAUSE]) > 3 else ''}")
        print(f"  继续: {', '.join(self.voice_commands[VoiceCommandType.RESUME][:3])}{'...' if len(self.voice_commands[VoiceCommandType.RESUME]) > 3 else ''}")
        print(f"  停止: {', '.join(self.voice_commands[VoiceCommandType.STOP][:3])}{'...' if len(self.voice_commands[VoiceCommandType.STOP]) > 3 else ''}")
        print("=" * 50)

        # 启动键盘监听
        self.start_keyboard_listener()

        # 启动debug性能追踪
        debug_tracker.start_debug_session(f"funasr_session_{int(time.time())}")

        # 启动生产环境延迟记录
        start_latency_session()

        try:
            # 直接开始识别
            print(f"\n🎯 开始语音识别")
            print("请说话...")
            print("-" * 50)

            self.run_recognition_cycle()

            # 显示汇总（只显示一次）
            if not self.system_should_stop:  # 只有当系统没有被命令停止时才显示汇总
                print("\n" + "=" * 50)
                print("识别汇总")
                print("=" * 50)
                
                self.show_results_summary()

        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断")
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
            print("\n📊 本次运行无识别结果")
            return

        print(f"\n📊 识别结果汇总")
        print("=" * 50)

        # 统计信息
        total_results = len(self.results_buffer)
        number_results = [r for r in self.results_buffer if r['numbers']]
        text_results = [r for r in self.results_buffer if not r['numbers']]

        print(f"📈 总识别次数：{total_results}")
        print(f"🔢 纯数字识别：{len(number_results)}")
        print(f"📝 文本识别：{len(text_results)}")

        if number_results:
            all_numbers = []
            for result in number_results:
                all_numbers.extend(result['numbers'])
            print(f"📊 提取的数字：{all_numbers}")

        # 显示详细结果
        print(f"\n📋 详细识别结果：")
        for i, result in enumerate(self.results_buffer, 1):
            status = "🔢" if result['numbers'] else "📝"
            print(f"{i:2d}. {status} {result['original']}")
            if result['numbers']:
                print(f"     → {result['numbers'][0]}")
            elif result['processed'] != result['original']:
                if self.processor.is_pure_number_or_with_unit(result['original']):
                    print(f"     → {result['processed']}")
                else:
                    clean_text = self.processor.remove_spaces(result['original'])
                    print(f"     → {clean_text}")

def main():
    """主函数"""
    print("🎤 启动FunASR语音输入系统...")

    # 检查是否启用debug模式
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    if debug_mode:
        print("🐛 Debug模式已启用")
    else:
        print("🏭 生产模式")

    # 创建系统实例
    system = FunASRVoiceSystem(
        recognition_duration=60,  # 每次识别60秒
        continuous_mode=False,     # 单次模式
        debug_mode=debug_mode      # debug模式设置
    )

    # 初始化系统
    if not system.initialize():
        print("❌ 系统初始化失败")
        return

    try:
        # 运行系统
        system.run_continuous()

    except Exception as e:
        logger.error(f"❌ 系统运行异常: {e}")
        print(f"❌ 系统运行异常: {e}")

    finally:
        # 显示Excel文件路径（如果有数字数据）
        if system.number_results and system.excel_exporter:
            print(f"\n📊 数据已保存到: {system.excel_exporter.filename}")

        print("\n👋 感谢使用FunASR语音输入系统！")

if __name__ == "__main__":
    main()