# -*- coding: utf-8 -*-
"""
异步系统引用共享组件示例

此文件展示了重构后的异步系统如何引用共享组件和专用组件，
以及如何使用独立的配置、日志和依赖管理机制。
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径，确保可以正确导入共享组件
# 实际项目中可以通过环境变量或包安装方式解决导入问题
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入共享配置模块
from example_shared_config import async_config, ConfigError

# 导入共享文本处理模块
# 注意：重构后，这些模块会位于共享目录中
try:
    from shared.text_processor import extract_measurements, process_voice_text, detect_tts_feedback
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
        
        @staticmethod
        def detect_tts_feedback(text):
            return "成功提取" in text or "识别到" in text
    
    class MockAudioUtils:
        pass
    
    class MockDataExporter:
        async def append_with_text_async(self, text):
            print(f"[模拟]异步导出数据到Excel: {text}")
    
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
        async def load_model_async(self):
            print("[模拟]异步加载识别模型")
            return True
        
        async def unload_model_async(self):
            print("[模拟]异步卸载识别模型")
    
    # 模拟模块实例化
    extract_measurements = MockTextProcessor.extract_measurements
    process_voice_text = MockTextProcessor.process_voice_text
    detect_tts_feedback = MockTextProcessor.detect_tts_feedback
    AudioFormatConverter = MockAudioUtils
    AudioDeviceInfo = MockAudioUtils
    DataExporter = MockDataExporter
    ExcelFormatter = MockAudioUtils
    handle_exception = MockErrorHandler.handle_exception
    log_error = MockErrorHandler.log_error
    setup_error_handlers = MockErrorHandler.setup_error_handlers
    ModelManager = MockModelManager

# 导入异步系统专用组件
# 注意：重构后，这些模块会位于异步系统专用目录中
try:
    from async_system.async_audio_stream_controller import AsyncAudioStreamController
    from async_system.async_tts_manager import AsyncTTSManager
    from async_system.async_voice_recognizer import AsyncVoiceRecognizer
    from async_system.event_bus import EventBus, EventType
except ImportError as e:
    # 在示例环境中可能不存在这些模块，提供模拟实现
    print(f"⚠️ 无法导入异步系统专用模块: {e}")
    print("⚠️ 提供模拟实现用于演示...")
    
    # 模拟异步系统专用模块
    class MockAsyncAudioStreamController:
        def __init__(self):
            self.running = False
            self.callbacks = {}
            
        async def start(self):
            self.running = True
            print("[模拟]启动异步音频流控制器")
            
        async def stop(self):
            self.running = False
            print("[模拟]停止异步音频流控制器")
            
        def register_callback(self, event_type, callback):
            if event_type not in self.callbacks:
                self.callbacks[event_type] = []
            self.callbacks[event_type].append(callback)
            print(f"[模拟]注册回调: {event_type}")
    
    class MockAsyncTTSManager:
        def __init__(self):
            self.initialized = False
            
        async def initialize(self):
            self.initialized = True
            print("[模拟]初始化异步TTS管理器")
            
        async def speak(self, text):
            print(f"[模拟]TTS语音播报: {text}")
            
        async def cleanup(self):
            print("[模拟]清理TTS资源")
    
    class MockAsyncVoiceRecognizer:
        def __init__(self):
            self.model_loaded = False
            
        async def load_model_async(self, model_path):
            self.model_loaded = True
            print(f"[模拟]异步加载语音识别模型: {model_path}")
            
        async def recognize_async(self, audio_data):
            return "[模拟识别结果] 身高一百八十厘米"
    
    class MockEventBus:
        def __init__(self):
            self.subscribers = {}
            
        def subscribe(self, event_type, subscriber):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(subscriber)
            print(f"[模拟]订阅事件: {event_type}")
            
        async def publish(self, event_type, data):
            print(f"[模拟]发布事件: {event_type}, 数据: {data}")
    
    class MockEventType:
        AUDIO_DATA_AVAILABLE = "AUDIO_DATA_AVAILABLE"
        RECOGNITION_COMPLETE = "RECOGNITION_COMPLETE"
        TEXT_PROCESSED = "TEXT_PROCESSED"
        MEASUREMENT_EXTRACTED = "MEASUREMENT_EXTRACTED"
        DATA_EXPORTED = "DATA_EXPORTED"
        ERROR_OCCURRED = "ERROR_OCCURRED"
    
    # 模拟模块实例化
    AsyncAudioStreamController = MockAsyncAudioStreamController
    AsyncTTSManager = MockAsyncTTSManager
    AsyncVoiceRecognizer = MockAsyncVoiceRecognizer
    EventBus = MockEventBus
    EventType = MockEventType


class AsyncVoiceInputSystem:
    """异步语音输入系统主类"""
    
    def __init__(self):
        # 初始化日志
        self.logger = self._setup_logger()
        self.logger.info("🚀 初始化异步语音输入系统...")
        
        # 设置错误处理器
        setup_error_handlers()
        
        # 加载配置
        self.config = async_config
        self.logger.info(f"📋 配置加载完成: {self.config._config_path}")
        
        # 设置事件循环策略（如果配置了）
        self._setup_event_loop_policy()
        
        # 获取或创建事件循环
        self.loop = asyncio.get_event_loop()
        
        # 初始化模型管理器
        self.model_manager = ModelManager()
        
        # 初始化核心组件
        self.audio_stream_controller = None
        self.tts_manager = None
        self.voice_recognizer = None
        self.event_bus = None
        self.data_exporter = DataExporter()
        
        # 系统状态
        self.running = False
        
        # 任务集合
        self.tasks = set()
        
        # 初始化系统
        self.loop.run_until_complete(self._initialize_system_async())
    
    def _setup_logger(self):
        """设置系统日志"""
        # 获取日志级别
        log_level = self.config.get_log_level()
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
        
        # 创建logger
        logger = logging.getLogger('AsyncVoiceInputSystem')
        logger.setLevel(numeric_level)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 创建控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(numeric_level)
            
            # 创建文件handler
            log_dir = PROJECT_ROOT / 'logs' / 'async'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f'async_system_{Path(__file__).stem}.log'
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
    
    def _setup_event_loop_policy(self):
        """设置事件循环策略"""
        policy = self.config.get_event_loop_policy()
        if policy != 'default':
            try:
                if policy == 'windows_selector' and sys.platform == 'win32':
                    from asyncio import WindowsSelectorEventLoopPolicy
                    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
                    self.logger.info(f"🔄 设置事件循环策略: {policy}")
                elif policy == 'windows_proactor' and sys.platform == 'win32':
                    from asyncio import WindowsProactorEventLoopPolicy
                    asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
                    self.logger.info(f"🔄 设置事件循环策略: {policy}")
                else:
                    self.logger.warning(f"⚠️ 不支持的事件循环策略: {policy}")
            except ImportError:
                self.logger.error(f"❌ 无法设置事件循环策略: {policy}")
    
    async def _initialize_system_async(self):
        """异步初始化系统组件"""
        try:
            # 创建事件总线
            self.logger.info("📡 创建事件总线")
            self.event_bus = EventBus()
            self.event_bus.subscribe(EventType.RECOGNITION_COMPLETE, self._handle_recognition_complete)
            self.event_bus.subscribe(EventType.TEXT_PROCESSED, self._handle_text_processed)
            self.event_bus.subscribe(EventType.MEASUREMENT_EXTRACTED, self._handle_measurement_extracted)
            self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._handle_error)
            
            # 加载模型
            self.logger.info(f"🧠 异步加载语音识别模型: {self.config.get('recognition.model_path')}")
            if not await self.model_manager.load_model_async():
                raise Exception("模型加载失败")
            
            # 初始化音频流控制器
            self.logger.info(f"🎤 初始化异步音频流控制器: 采样率={self.config.get('audio.sample_rate')}, 缓冲区大小={self.config.get('async_specific.stream_buffer_size')}")
            self.audio_stream_controller = AsyncAudioStreamController()
            self.audio_stream_controller.register_callback(
                EventType.AUDIO_DATA_AVAILABLE, 
                self._handle_audio_data_available
            )
            
            # 初始化语音识别器
            self.logger.info(f"👂 初始化异步语音识别器: 语言={self.config.get('recognition.language')}")
            self.voice_recognizer = AsyncVoiceRecognizer()
            await self.voice_recognizer.load_model_async(self.config.get('recognition.model_path'))
            
            # 初始化TTS管理器（如果启用）
            if self.config.get('tts.enabled'):
                self.logger.info(f"🔊 初始化异步TTS管理器: 语音={self.config.get('tts.voice')}")
                self.tts_manager = AsyncTTSManager()
                await self.tts_manager.initialize()
            
            # 初始化数据导出器
            if self.config.get('excel.auto_export'):
                self.logger.info(f"📊 初始化数据导出器: {self.config.get('excel.file_path')}")
            
            self.logger.info("✅ 异步语音输入系统初始化完成")
        except Exception as e:
            self.logger.error(f"❌ 系统初始化失败: {e}")
            handle_exception(e, "系统初始化阶段")
    
    def start(self):
        """启动系统"""
        try:
            if self.running:
                self.logger.warning("⚠️ 系统已经在运行中")
                return False
            
            self.logger.info("▶️ 启动异步语音输入系统")
            
            # 创建主任务
            main_task = self.loop.create_task(self._run_async())
            self.tasks.add(main_task)
            main_task.add_done_callback(self.tasks.discard)
            
            # 运行事件循环
            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                self.logger.info("🛑 用户中断")
            except Exception as e:
                self.logger.error(f"❌ 事件循环异常: {e}")
                handle_exception(e, "事件循环阶段")
            finally:
                self.loop.run_until_complete(self.stop_async())
                self.loop.close()
            
            self.logger.info("✅ 系统启动成功并正常退出")
            return True
        except Exception as e:
            self.logger.error(f"❌ 系统启动失败: {e}")
            handle_exception(e, "系统启动阶段")
            self.loop.run_until_complete(self.stop_async())
            return False
    
    async def stop_async(self):
        """异步停止系统"""
        try:
            if not self.running:
                self.logger.warning("⚠️ 系统已经停止")
                return False
            
            self.logger.info("⏹️ 停止异步语音输入系统")
            
            # 取消所有任务
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            
            if tasks:
                self.logger.info(f"⏳ 等待{len(tasks)}个任务取消...")
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # 停止音频流控制器
            if self.audio_stream_controller:
                await self.audio_stream_controller.stop()
            
            # 清理TTS资源
            if self.tts_manager:
                await self.tts_manager.cleanup()
            
            # 卸载模型
            await self.model_manager.unload_model_async()
            
            self.running = False
            self.logger.info("✅ 系统停止成功")
            
            # 停止事件循环
            if self.loop.is_running():
                self.loop.stop()
            
            return True
        except Exception as e:
            self.logger.error(f"❌ 系统停止失败: {e}")
            handle_exception(e, "系统停止阶段")
            return False
    
    async def _run_async(self):
        """系统主运行函数"""
        try:
            self.running = True
            
            # 启动音频流控制器
            await self.audio_stream_controller.start()
            
            self.logger.info("🔄 异步系统已启动，按Ctrl+C退出")
            
            # 保持主任务运行
            # 实际系统中，这里会等待事件触发或满足退出条件
            while self.running:
                # 模拟系统活动
                await asyncio.sleep(1)
                
                # 为了演示，运行10秒后自动退出
                # 实际系统中会持续运行直到用户中断或发生错误
                if self.running:
                    import time
                    start_time = getattr(self, '_start_time', time.time())
                    if not hasattr(self, '_start_time'):
                        self._start_time = start_time
                    
                    if time.time() - start_time > 10:
                        self.logger.info("🔄 系统测试完成，自动退出")
                        await self.stop_async()
        except Exception as e:
            self.logger.error(f"❌ 系统运行异常: {e}")
            handle_exception(e, "系统运行阶段")
            await self.stop_async()
    
    async def _handle_audio_data_available(self, audio_data):
        """处理音频数据可用事件"""
        try:
            # 创建识别任务
            recognition_task = asyncio.create_task(
                self._process_audio_data_async(audio_data)
            )
            self.tasks.add(recognition_task)
            recognition_task.add_done_callback(self.tasks.discard)
        except Exception as e:
            self.logger.error(f"❌ 处理音频数据失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '音频数据处理阶段'
            })
    
    async def _process_audio_data_async(self, audio_data):
        """异步处理音频数据"""
        try:
            # 异步识别语音
            text = await self.voice_recognizer.recognize_async(audio_data)
            self.logger.debug(f"🎯 识别结果: {text}")
            
            # 发布识别完成事件
            await self.event_bus.publish(EventType.RECOGNITION_COMPLETE, text)
        except Exception as e:
            self.logger.error(f"❌ 语音识别失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '语音识别阶段'
            })
    
    async def _handle_recognition_complete(self, text):
        """处理识别完成事件"""
        try:
            # 检查是否为TTS反馈（避免循环）
            if detect_tts_feedback(text):
                self.logger.debug(f"🔄 检测到TTS反馈文本，跳过处理: {text}")
                return
            
            # 处理文本
            processed_text = process_voice_text(text)
            self.logger.debug(f"📝 处理后文本: {processed_text}")
            
            # 发布文本处理完成事件
            await self.event_bus.publish(EventType.TEXT_PROCESSED, processed_text)
        except Exception as e:
            self.logger.error(f"❌ 处理识别结果失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '识别结果处理阶段'
            })
    
    async def _handle_text_processed(self, processed_text):
        """处理文本处理完成事件"""
        try:
            # 提取数值
            measurements = extract_measurements(processed_text)
            self.logger.info(f"📊 提取数值: {measurements}")
            
            # 发布数值提取完成事件
            await self.event_bus.publish(EventType.MEASUREMENT_EXTRACTED, {
                'measurements': measurements,
                'original_text': processed_text
            })
        except Exception as e:
            self.logger.error(f"❌ 提取数值失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '数值提取阶段'
            })
    
    async def _handle_measurement_extracted(self, data):
        """处理数值提取完成事件"""
        try:
            measurements = data['measurements']
            original_text = data['original_text']
            
            # 导出数据到Excel（如果启用）
            if self.config.get('excel.auto_export'):
                export_task = asyncio.create_task(
                    self._write_to_excel_async(original_text)
                )
                self.tasks.add(export_task)
                export_task.add_done_callback(self.tasks.discard)
            
            # TTS播报结果（如果启用）
            if self.config.get('tts.enabled') and self.tts_manager:
                tts_task = asyncio.create_task(
                    self.tts_manager.speak(f"成功提取数值: {measurements}")
                )
                self.tasks.add(tts_task)
                tts_task.add_done_callback(self.tasks.discard)
        except Exception as e:
            self.logger.error(f"❌ 处理提取结果失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '提取结果处理阶段'
            })
    
    async def _write_to_excel_async(self, text):
        """异步写入数据到Excel"""
        try:
            await self.data_exporter.append_with_text_async(text)
            self.logger.debug(f"💾 异步导出数据成功: {text}")
        except Exception as e:
            self.logger.error(f"❌ 导出数据失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '数据导出阶段'
            })
    
    async def _handle_error(self, error_data):
        """处理错误事件"""
        error = error_data.get('error', 'Unknown error')
        context = error_data.get('context', 'Unknown context')
        self.logger.error(f"❌ 系统错误 ({context}): {error}")
        # 实际系统中可以根据错误类型和严重程度采取不同的处理策略
        # 例如重试操作、降级服务、发送通知等


# 主函数
def main():
    """主函数"""
    system = None
    try:
        # 创建系统实例
        system = AsyncVoiceInputSystem()
        
        # 启动系统
        if not system.start():
            print("❌ 系统启动失败")
            return 1
        
        print("✅ 系统测试完成")
        return 0
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        if system and system.loop.is_running():
            system.loop.run_until_complete(system.stop_async())
        return 1
    finally:
        # 清理资源
        pass


# 程序入口
if __name__ == "__main__":
    sys.exit(main())