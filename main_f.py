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

# 导入Excel导出模块
try:
    from excel_exporter import ExcelExporter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    ExcelExporter: ExcelExporterType = None

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
    
    config_loader: Union[ConfigPlaceholder, Any] = ConfigPlaceholder()

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

        # 语音命令配置
        self.voice_commands = {
            VoiceCommandType.PAUSE: ["暂停", "暂停录音", "暂停识别", "pause"],
            VoiceCommandType.RESUME: ["继续", "继续录音", "恢复", "恢复识别", "resume"],
            VoiceCommandType.STOP: ["停止", "停止录音", "结束", "exit", "stop"]
        }
        
        # 加载特定文本配置
        self.special_text_config = config_loader.get_special_texts_config()
        self.export_special_texts = config_loader.is_special_text_export_enabled()
        self.exportable_texts = config_loader.get_exportable_texts()

        # 键盘监听线程和停止标志
        self.keyboard_thread = None
        self.keyboard_active = False
        self.system_should_stop = False  # 系统停止标志

        logger.info("🎤 FunASR语音系统初始化完成")

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
        识别语音命令

        Args:
            text: 识别的文本

        Returns:
            语音命令类型
        """
        text_lower = text.lower().strip()

        # 精确匹配语音命令，避免误识别
        # 对stop命令要求更严格，需要精确匹配或完全包含命令词
        for command_type, keywords in self.voice_commands.items():
            # 对于停止命令，要求更精确的匹配
            if command_type == VoiceCommandType.STOP:
                # 只有当文本完全等于命令词或者文本就是命令词加上感叹号等标点时才匹配
                if text_lower in keywords or any(text_lower == keyword for keyword in keywords) or \
                   any(text_lower == keyword + '!' or text_lower == keyword + '.' for keyword in keywords):
                    return command_type
            # 对于其他命令，可以稍微宽松一些
            else:
                # 只有当文本主要内容是命令词时才匹配
                if any(keyword == text_lower or text_lower == keyword + '!' or text_lower == keyword + '.' 
                       for keyword in keywords):
                    return command_type

        return VoiceCommandType.UNKNOWN

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
        # 添加到结果缓冲区
        self.results_buffer.append({
            'original': original_text,
            'processed': processed_text,
            'numbers': numbers,
            'timestamp': time.time()
        })

        # 记录调试日志
        if hasattr(self, 'recognition_logger'):
            # 改为debug级别
            debug_message = f"识别文本: '{processed_text}'"
            if numbers and len(numbers) > 0:
                debug_message += f" -> 提取数字: {numbers[0]}"
            self.recognition_logger.debug(debug_message)

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
                    result_value = numbers[0]
                else:
                    # 特定文本结果
                    # 将特定文本作为数值的替代写入Excel
                    # 使用1代表OK，0代表Not OK或其他特殊文本
                    text_value = 1.0 if special_text_match == "OK" else 0.0
                    excel_data.append((text_value, original_text, special_text_match))
                    result_type = "特定文本"
                    result_value = special_text_match
                
                # 使用Excel导出器生成ID并保存
                excel_result = self.excel_exporter.append_with_text(excel_data)
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
            processed = self.processor.process_text(result.text)
            numbers = self.processor.extract_numbers(result.text, processed)

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
        elif command_type == VoiceCommandType.RESUME:
            self.resume()
            print(f"\n🎤 语音命令：恢复")
        elif command_type == VoiceCommandType.STOP:
            self.system_stop()
            print(f"\n🎤 语音命令：停止")

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
        except Exception as e:
            logger.error(f"❌ 识别异常: {e}")

        # 识别结束
        self.stop()

    def run_continuous(self):
        """运行单次识别模式"""
        print("🎤 FunASR语音输入系统")
        print("=" * 50)
        print(f"模式：单次识别")
        print(f"识别时长：{self.recognition_duration}秒")
        print("控制：空格键暂停/恢复 | ESC键停止 | 语音命令控制")
        print("=" * 50)

        # 启动键盘监听
        self.start_keyboard_listener()

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