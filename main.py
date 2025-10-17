# -*- coding: utf-8 -*-
# Voice Input System Main Module / 语音输入系统主模块

import logging
import sys
import os
import io
import threading
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter
from config_loader import config  # 导入配置系统
# ---------- Basic Configuration ----------
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

# 从配置系统获取VOSK日志级别
os.environ["VOSK_LOG_LEVEL"] = str(config.get_vosk_log_level())

logging.basicConfig(
    level=getattr(logging, config.get_log_level()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_input.log', encoding='utf-8'),
        logging.StreamHandler(stream=sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VoiceInputSystem:
    """
    Program entry point: Create ExcelExporter → Inject AudioCapture → Register callback → Start recognition
    """

    def __init__(self, timeout_seconds=None, test_mode=None, engine="vosk"):
        # 从配置系统获取参数，允许命令行覆盖
        self.test_mode = test_mode if test_mode is not None else config.get_test_mode()
        timeout = timeout_seconds if timeout_seconds is not None else config.get_timeout_seconds()
        self.engine = engine.lower()  # 转为小写以支持大小写不敏感
        
        # 根据配置决定是否创建ExcelExporter
        self.excel_exporter = None
        auto_export = config.get("excel.auto_export", True)
        if auto_export:
            self.excel_exporter = ExcelExporter()
            logger.info("📊 Excel导出器已创建")
        else:
            logger.info("📊 Excel自动导出功能已禁用")
        
        self.audio_capture = AudioCapture(
            timeout_seconds=timeout,
            excel_exporter=self.excel_exporter,
            test_mode=self.test_mode
        )
        
        # 根据选择的引擎预加载相应模型
        if self.engine == "funasr":
            logger.info("🚀 准备加载FunASR模型...")
            if not self.audio_capture.load_funasr_model():
                print("⚠️ FunASR模型加载失败，将尝试回退到VOSK引擎")
                self.engine = "vosk"
                # 回退到VOSK时加载VOSK模型
                if not self.audio_capture.load_model():
                    print("❌ 所有模型加载失败，系统可能无法正常工作")
        else:
            # 默认使用VOSK引擎
            if not self.audio_capture.load_model():
                print("❌ VOSK模型加载失败，系统可能无法正常工作")
        
        # 设置测试模式
        if self.test_mode:
            self.audio_capture.test_mode = True
            print("🧪 测试模式已启用")
        
        print(f"🔊 当前语音识别引擎: {self.engine.upper()}")
        


    def on_data_detected(self, values, text=None) -> None:
        """Callback function: print values when detected"""
        pass

    def start_realtime_vosk(self) -> None:
        """Start real-time voice recognition system using VOSK"""
        self.audio_capture.set_callback(self.on_data_detected)

        # 启动键盘监听器，传递测试模式
        keyboard_listener = start_keyboard_listener(self.audio_capture, test_mode=self.test_mode)
        
        # 确保模型已加载
        if not self.audio_capture._model_loaded:
            if not self.audio_capture.load_model():
                print("❌ VOSK模型加载失败，系统可能无法正常工作")
                return

        # 直接调用内部的实时监听（阻塞式）
        result = self.audio_capture.listen_realtime_vosk()
        
        self._process_and_display_results(result)
        
        # 停止键盘监听器
        if keyboard_listener:
            keyboard_listener.stop()
            keyboard_listener.join()
    
    def _process_and_display_results(self, result):
        """处理并显示识别结果（通用方法）"""
        buffered_values = result.get('buffered_values', [])
        session_data = result.get('session_data', [])
        
        if buffered_values:
            print(f"\n🛑 监听结束，共捕获 {len(buffered_values)} 个数值")
            print(f"📊 输入Excel的数字信息：{buffered_values}")
            # 基于session_data判断Excel数据存储状态，更加准确
            if session_data:
                print("✅ Excel数据存储成功")
        else:
            print("\n🛑 监听结束，未捕获到数值")
        
        # 显示会话数据
        if session_data:
            print("\n📋 本次识别会话数据列表:")
            for record in session_data:
                if isinstance(record, tuple) and len(record) >= 3:
                    record_id, value, original_text = record
                    print(f"  ID: {record_id}, {value}, 原始文本: {original_text}")
                else:
                    print(f"  无效记录: {record}")
            
            # 提供数据汇总
            print("\n📈 数据汇总:")
            print(f"  总记录数: {len(session_data)}")
            
            # 提取有效的数值进行统计
            valid_values = []
            for record in session_data:
                if isinstance(record, tuple) and len(record) >= 2 and isinstance(record[1], (int, float)):
                    valid_values.append(record[1])
            
            if valid_values:
                print(f"  数值范围: {min(valid_values):.2f} - {max(valid_values):.2f}")
                print(f"  平均值: {sum(valid_values)/len(valid_values):.2f}")
            else:
                print("  无法计算数值统计: 没有有效的数值数据")
    
    def start_realtime_funasr(self) -> None:
        """Start real-time voice recognition system using FunASR"""
        self.audio_capture.set_callback(self.on_data_detected)

        # 启动键盘监听器，传递测试模式
        keyboard_listener = start_keyboard_listener(self.audio_capture, test_mode=self.test_mode)
        
        # 确保FunASR模型已加载
        if not self.audio_capture._funasr_model_loaded:
            if not self.audio_capture.load_funasr_model():
                print("❌ FunASR模型加载失败，系统可能无法正常工作")
                return

        # 直接调用内部的实时监听（阻塞式）
        result = self.audio_capture.listen_realtime_funasr()

        # 打印结果
        buffered_values = result.get('buffered_values', [])
        session_data = result.get('session_data', [])
        
        if buffered_values:
            print(f"\n🛑 监听结束，共捕获 {len(buffered_values)} 个数值")
            print(f"📊 输入Excel的数字信息：{buffered_values}")
            # 基于session_data判断Excel数据存储状态，更加准确
            if session_data:
                print("✅ Excel数据存储成功")
        else:
            print("\n🛑 监听结束，未捕获到数值")
        
        # 显示会话数据
        if session_data:
            print("\n📋 本次识别会话数据列表:")
            for record in session_data:
                if isinstance(record, tuple) and len(record) >= 3:
                    record_id, value, original_text = record
                    print(f"  ID: {record_id}, {value}, 原始文本: {original_text}")
                else:
                    print(f"  无效记录: {record}")
            
            # 提供数据汇总
            print("\n📈 数据汇总:")
            print(f"  总记录数: {len(session_data)}")
            
            # 提取有效的数值进行统计
            valid_values = []
            for record in session_data:
                if isinstance(record, tuple) and len(record) >= 2 and isinstance(record[1], (int, float)):
                    valid_values.append(record[1])
            
            if valid_values:
                print(f"  数值范围: {min(valid_values):.2f} - {max(valid_values):.2f}")
                print(f"  平均值: {sum(valid_values)/len(valid_values):.2f}")
            else:
                print("  无法计算数值统计: 没有有效的数值数据")
        
        # 停止键盘监听器
        if keyboard_listener:
            keyboard_listener.stop()
            keyboard_listener.join()

    def stop(self) -> None:
        """Stop the system"""
        self.audio_capture.stop()
        # 清理模型资源
        if hasattr(self.audio_capture, '_funasr_model_loaded') and self.audio_capture._funasr_model_loaded:
            self.audio_capture.unload_funasr_model()
        logging.info("=== 系统已停止 ===")
    
    def start(self) -> None:
        """根据选择的引擎启动识别系统"""
        if self.engine == "funasr":
            logger.info("🚀 启动FunASR语音识别引擎")
            self.start_realtime_funasr()
        else:
            logger.info("🚀 启动VOSK语音识别引擎")
            self.start_realtime_vosk()

if __name__ == "__main__":
    # 可以通过命令行参数或环境变量控制测试模式，配置系统的值作为默认值
    test_mode = "--test" in sys.argv or os.getenv("VOICE_INPUT_TEST_MODE", "").lower() == "true" or config.get_test_mode()
    
    # 控制是否在程序退出时全局卸载模型（仅对VOSK引擎有效）
    global_unload = "--global-unload" in sys.argv or os.getenv("VOICE_INPUT_GLOBAL_UNLOAD", "").lower() == "true" or config.get_global_unload()
    
    # 语音识别引擎选择
    engine = "vosk"  # 默认使用VOSK引擎
    if "--engine=funasr" in sys.argv:
        engine = "funasr"
    elif "--engine=vosk" in sys.argv:
        engine = "vosk"
    
    # 也可以通过环境变量设置
    env_engine = os.getenv("VOICE_INPUT_ENGINE", "").lower()
    if env_engine in ["vosk", "funasr"]:
        engine = env_engine
    
    if test_mode:
        print("🧪 运行在测试模式")
    else:
        print("🚀 运行在生产模式")
    
    print(f"🔊 语音识别引擎: {engine.upper()}")
    
    # 使用配置系统的超时时间
    system = VoiceInputSystem(test_mode=test_mode, engine=engine)
    
    try:
        system.start()  # 使用统一的启动方法
    except KeyboardInterrupt:
        print("👋 用户中断程序")
    finally:
        # 在程序结束时的模型管理策略
        if engine == "funasr":
            # FunASR模型清理
            if hasattr(system.audio_capture, 'unload_funasr_model'):
                system.audio_capture.unload_funasr_model()
                print("🧹 FunASR模型已清理")
        else:
            # VOSK模型清理
            print("🔄 正在清理VOSK模型资源...")
            if global_unload:
                # 全局卸载模型，完全释放内存
                system.audio_capture.unload_model_globally()
                print("✅ VOSK模型已全局卸载，完全释放内存")
            else:
                # 仅清除本地模型引用
                system.audio_capture.unload_model()
                print("💡 已清除VOSK本地模型引用，Python垃圾回收器将在适当时机释放内存")
                print("   提示: 如需立即完全释放内存，请使用 '--global-unload' 参数")
        
        print("✅ 系统已安全退出")
        sys.exit(0)