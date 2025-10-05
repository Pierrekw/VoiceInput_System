# -*- coding: utf-8 -*-
"""
同步系统引用共享组件示例

此文件展示了重构后的同步系统如何引用共享组件和专用组件，
以及如何使用独立的配置、日志和依赖管理机制。
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径，确保可以正确导入共享组件
# 实际项目中可以通过环境变量或包安装方式解决导入问题
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入共享配置模块
from example_shared_config import sync_config, ConfigError

# 导入共享文本处理模块
# 注意：重构后，这些模块会位于共享目录中
try:
    from shared.text_processor import extract_measurements, process_voice_text
    from shared.audio_utils import AudioFormatConverter, AudioDeviceInfo
    from shared.data_exporter import DataExporter, ExcelFormatter
    from shared.error_handler import handle_exception, log_error, setup_error_handlers
    from shared.model_manager import ModelManager
except ImportError as e:
    # 在示例环境中可能不存在这些模块，提供模拟实现
    print(f"⚠️ 无法导入共享模块: {e}")
    print("⚠️ 提供模拟实现用于演示...")
    
    # 模拟共享模块
    class MockTextProcessor:
        @staticmethod
        def extract_measurements(text):
            return f"[模拟]从文本'{text}'中提取的数值"
        
        @staticmethod
        def process_voice_text(text):
            return f"[模拟]处理后的文本: {text}"
    
    class MockAudioUtils:
        pass
    
    class MockDataExporter:
        def append_with_text(self, text):
            print(f"[模拟]导出数据到Excel: {text}")
    
    class MockErrorHandler:
        @staticmethod
        def handle_exception(e, context=""):
            print(f"[模拟]处理异常: {e} (上下文: {context})")
        
        @staticmethod
        def log_error(message, error=None):
            print(f"[模拟]记录错误: {message}" + (f" - {error}" if error else ""))
        
        @staticmethod
        def setup_error_handlers():
            print("[模拟]设置全局错误处理器")
    
    class MockModelManager:
        def load_model(self):
            print("[模拟]加载识别模型")
            return True
        
        def unload_model(self):
            print("[模拟]卸载识别模型")
    
    # 模拟模块实例化
    extract_measurements = MockTextProcessor.extract_measurements
    process_voice_text = MockTextProcessor.process_voice_text
    AudioFormatConverter = MockAudioUtils
    AudioDeviceInfo = MockAudioUtils
    DataExporter = MockDataExporter
    ExcelFormatter = MockAudioUtils
    handle_exception = MockErrorHandler.handle_exception
    log_error = MockErrorHandler.log_error
    setup_error_handlers = MockErrorHandler.setup_error_handlers
    ModelManager = MockModelManager

# 导入同步系统专用组件
# 注意：重构后，这些模块会位于同步系统专用目录中
try:
    from sync_system.audio_capture import AudioCapture
    from sync_system.voice_recognizer import VoiceRecognizer
    from sync_system.keyboard_controller import KeyboardController
except ImportError as e:
    # 在示例环境中可能不存在这些模块，提供模拟实现
    print(f"⚠️ 无法导入同步系统专用模块: {e}")
    print("⚠️ 提供模拟实现用于演示...")
    
    # 模拟同步系统专用模块
    class MockAudioCapture:
        def __init__(self):
            self.running = False
            
        def start(self):
            self.running = True
            print("[模拟]启动音频捕获")
            
        def stop(self):
            self.running = False
            print("[模拟]停止音频捕获")
            
        def get_audio_data(self):
            return b"[Simulated Audio Data]"
    
    class MockVoiceRecognizer:
        def __init__(self):
            self.model_loaded = False
            
        def load_model(self, model_path):
            self.model_loaded = True
            print(f"[模拟]加载语音识别模型: {model_path}")
            
        def recognize(self, audio_data):
            return "[模拟识别结果] 体重七十五公斤"
    
    class MockKeyboardController:
        def __init__(self):
            self.hotkey = "space"
            self.callbacks = {}
            
        def register_hotkey(self, key, callback):
            self.hotkey = key
            self.callbacks[key] = callback
            print(f"[模拟]注册热键: {key}")
            
        def start_monitoring(self):
            print("[模拟]开始监听键盘事件")
            
        def stop_monitoring(self):
            print("[模拟]停止监听键盘事件")
    
    # 模拟模块实例化
    AudioCapture = MockAudioCapture
    VoiceRecognizer = MockVoiceRecognizer
    KeyboardController = MockKeyboardController


class VoiceInputSystem:
    """同步语音输入系统主类"""
    
    def __init__(self):
        # 初始化日志
        self.logger = self._setup_logger()
        self.logger.info("🚀 初始化同步语音输入系统...")
        
        # 设置错误处理器
        setup_error_handlers()
        
        # 加载配置
        self.config = sync_config
        self.logger.info(f"📋 配置加载完成: {self.config._config_path}")
        
        # 初始化模型管理器
        self.model_manager = ModelManager()
        
        # 初始化核心组件
        self.audio_capture = None
        self.voice_recognizer = None
        self.keyboard_controller = None
        self.data_exporter = DataExporter()
        
        # 系统状态
        self.running = False
        
        # 初始化系统
        self._initialize_system()
    
    def _setup_logger(self):
        """设置系统日志"""
        # 获取日志级别
        log_level = self.config.get_log_level()
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
        
        # 创建logger
        logger = logging.getLogger('SyncVoiceInputSystem')
        logger.setLevel(numeric_level)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 创建控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(numeric_level)
            
            # 创建文件handler
            log_dir = PROJECT_ROOT / 'logs' / 'sync'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f'sync_system_{Path(__file__).stem}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            
            # 设置日志格式
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            # 添加handler到logger
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger
    
    def _initialize_system(self):
        """初始化系统组件"""
        try:
            # 加载模型
            self.logger.info(f"🧠 加载语音识别模型: {self.config.get('recognition.model_path')}")
            if not self.model_manager.load_model():
                raise Exception("模型加载失败")
            
            # 初始化音频捕获
            self.logger.info(f"🎤 初始化音频捕获: 采样率={self.config.get('audio.sample_rate')}, 通道={self.config.get('audio.channels')}")
            self.audio_capture = AudioCapture()
            
            # 初始化语音识别器
            self.logger.info(f"👂 初始化语音识别器: 语言={self.config.get('recognition.language')}")
            self.voice_recognizer = VoiceRecognizer()
            self.voice_recognizer.load_model(self.config.get('recognition.model_path'))
            
            # 初始化键盘控制器（如果启用）
            if self.config.is_keyboard_control_enabled():
                self.logger.info(f"⌨️ 初始化键盘控制器: 热键={self.config.get_hotkey()}")
                self.keyboard_controller = KeyboardController()
                self.keyboard_controller.register_hotkey(
                    self.config.get_hotkey(), 
                    self._handle_hotkey_press
                )
            
            # 初始化数据导出器
            if self.config.get('excel.auto_export'):
                self.logger.info(f"📊 初始化数据导出器: {self.config.get('excel.file_path')}")
            
            self.logger.info("✅ 同步语音输入系统初始化完成")
        except Exception as e:
            self.logger.error(f"❌ 系统初始化失败: {e}")
            handle_exception(e, "系统初始化阶段")
    
    def start(self):
        """启动系统"""
        try:
            if self.running:
                self.logger.warning("⚠️ 系统已经在运行中")
                return False
            
            self.logger.info("▶️ 启动同步语音输入系统")
            
            # 启动音频捕获
            self.audio_capture.start()
            
            # 启动键盘监听（如果启用）
            if self.keyboard_controller:
                self.keyboard_controller.start_monitoring()
            
            self.running = True
            self.logger.info("✅ 系统启动成功")
            
            # 主循环
            self._main_loop()
            
            return True
        except Exception as e:
            self.logger.error(f"❌ 系统启动失败: {e}")
            handle_exception(e, "系统启动阶段")
            self.stop()
            return False
    
    def stop(self):
        """停止系统"""
        try:
            if not self.running:
                self.logger.warning("⚠️ 系统已经停止")
                return False
            
            self.logger.info("⏹️ 停止同步语音输入系统")
            
            # 停止音频捕获
            self.audio_capture.stop()
            
            # 停止键盘监听
            if self.keyboard_controller:
                self.keyboard_controller.stop_monitoring()
            
            # 卸载模型
            self.model_manager.unload_model()
            
            self.running = False
            self.logger.info("✅ 系统停止成功")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ 系统停止失败: {e}")
            handle_exception(e, "系统停止阶段")
            return False
    
    def _main_loop(self):
        """系统主循环"""
        try:
            self.logger.info(f"🔄 进入主循环，按{self.config.get_hotkey().upper()}键或Ctrl+C退出")
            
            # 模拟主循环，实际系统会有不同的实现
            import time
            iteration_count = 0
            
            while self.running:
                # 获取音频数据
                audio_data = self.audio_capture.get_audio_data()
                
                # 模拟处理逻辑
                if iteration_count % 10 == 0:  # 每10次迭代模拟一次识别
                    # 识别语音
                    text = self.voice_recognizer.recognize(audio_data)
                    self.logger.debug(f"🎯 识别结果: {text}")
                    
                    # 处理文本
                    processed_text = process_voice_text(text)
                    self.logger.debug(f"📝 处理后文本: {processed_text}")
                    
                    # 提取数值
                    measurements = extract_measurements(processed_text)
                    self.logger.info(f"📊 提取数值: {measurements}")
                    
                    # 导出数据
                    if self.config.get('excel.auto_export'):
                        self.data_exporter.append_with_text(processed_text)
                
                iteration_count += 1
                time.sleep(0.1)  # 模拟处理延迟
                
                # 实际系统中可以添加退出条件检查
                # 这里为了演示，循环100次后自动退出
                if iteration_count >= 100:
                    self.logger.info("🔄 主循环测试完成，自动退出")
                    break
        except KeyboardInterrupt:
            self.logger.info("🛑 用户中断")
        except Exception as e:
            self.logger.error(f"❌ 主循环异常: {e}")
            handle_exception(e, "系统主循环阶段")
    
    def _handle_hotkey_press(self):
        """处理热键按下事件"""
        self.logger.info(f"🔥 检测到热键 '{self.config.get_hotkey().upper()}' 按下")
        # 实际系统中可以在这里触发特定操作
        # 例如开始/停止录音、紧急保存数据等


# 主函数
def main():
    """主函数"""
    system = None
    try:
        # 创建系统实例
        system = VoiceInputSystem()
        
        # 启动系统
        if not system.start():
            print("❌ 系统启动失败")
            return 1
        
        # 模拟运行一段时间后停止
        import time
        time.sleep(2)  # 实际系统中会等待用户操作
        
        # 停止系统
        if not system.stop():
            print("❌ 系统停止失败")
            return 1
        
        print("✅ 系统测试完成")
        return 0
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        if system:
            system.stop()
        return 1
    finally:
        # 清理资源
        pass


# 程序入口
if __name__ == "__main__":
    sys.exit(main())