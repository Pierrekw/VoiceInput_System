# -*- coding: utf-8 -*-
"""
Voice Input System - 生产环境异步主程序

解决TTS回声检测和键盘控制问题的现代化异步版本。
"""

import asyncio
import logging
import sys
import os
import signal
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入异步组件
from events.event_bus import AsyncEventBus, EventPriority
from events.event_types import (
    AudioStreamStartedEvent, AudioDataReceivedEvent, RecognitionCompletedEvent,
    TTSPlaybackStartedEvent, TTSPlaybackCompletedEvent,
    KeyboardPressEvent, VoiceCommandEvent, SystemShutdownEvent,
    AudioStreamStoppedEvent
)
from interfaces.audio_processor import RecognitionResult
from events.system_coordinator import SystemCoordinator
from optimization.async_optimizer import get_global_optimizer, start_global_optimizer, stop_global_optimizer
from error_handling.async_error_handler import get_global_error_handler, ErrorSeverity, ErrorCategory

# 导入新的异步音频控制器
from async_audio.async_audio_stream_controller import (
    AsyncAudioStreamController, StreamConfig, StreamState
)
from async_audio.async_audio_stream_controller import TTSController

# 导入共享组件
from text_processor import extract_measurements, extract_primary_measurement
from adapters.data_exporter_adapter import DataExporterAdapter
from async_audio.async_audio_capture import AsyncAudioCapture

# 导入异步配置加载器
from async_config import AsyncConfigLoader, create_audio_config_validator, create_system_config_validator


@dataclass
class AudioDetectionState:
    """音频检测状态"""
    is_processing: bool = False
    tts_active: bool = False
    tts_start_time: float = 0.0
    last_tts_end_time: float = 0.0
    voice_threshold: float = 0.01

    # 精确控制参数
    audio_stream_control: bool = True  # 启用音频流精确控制
    immediate_mute: bool = True     # TTS开始时立即静音
    unmute_threshold: float = 0.05  # 解除静音的最小间隔（50ms）


class AsyncAudioProcessor:
    """异步音频处理器 - 解决TTS回声问题"""

    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
        # 创建专用日志记录器
        self.logger = logging.getLogger('audio.processor')
        self.tts_logger = logging.getLogger('tts')

        # 创建异步音频流控制器
        self.audio_stream_controller = AsyncAudioStreamController()
        # 创建TTS控制器，与音频流控制器集成
        self.tts_controller = TTSController(self.audio_stream_controller)

        # 识别结果ID计数器
        self.recognition_counter = 0
        self.recognition_results = {}  # 存储识别结果历史

        self.voice_commands = {
            'pause': ["暂停录音", "暂停", "pause"],
            'resume': ["继续录音", "继续", "恢复", "resume"],
            'stop': ["停止录音", "停止", "结束", "stop", "exit"]
        }

    async def initialize(self):
        """初始化音频处理器"""
        try:
            # 启动音频流控制器和TTS控制器
            await self.audio_stream_controller.start()
            await self.tts_controller.start()

            # 订阅TTS播放事件
            await self.event_bus.subscribe(TTSPlaybackStartedEvent, self._on_tts_started)
            await self.event_bus.subscribe(TTSPlaybackCompletedEvent, self._on_tts_completed)

            # 订阅音频数据事件
            await self.event_bus.subscribe(AudioDataReceivedEvent, self._on_audio_data_received)

            self.logger.info("异步音频处理器已初始化（集成TTS静音控制）")
        except Exception as e:
            self.logger.error(f"音频处理器初始化失败: {e}")
            raise

    async def _on_tts_started(self, event: TTSPlaybackStartedEvent):
        """TTS播放开始时的处理"""
        # 音频流控制器会通过TTSController自动静音
        self.tts_logger.info(f"TTS播放开始，音频流已自动静音: {event.text}")
        self.logger.debug(f"TTS静音激活 - 文本: '{event.text}', 播放器: {event.player_id}")

    async def _on_tts_completed(self, event: TTSPlaybackCompletedEvent):
        """TTS播放完成时的处理"""
        # 音频流控制器会通过TTSController自动恢复
        self.tts_logger.info(f"TTS播放完成，音频流将自动恢复: {event.text}")
        self.logger.debug(f"TTS静音解除 - 文本: '{event.text}', 播放器: {event.player_id}")

    async def _on_audio_data_received(self, event: AudioDataReceivedEvent):
        """处理接收到的音频数据"""
        try:
            # 将音频数据传递给音频流控制器（会根据状态自动处理）
            await self.audio_stream_controller.process_audio_chunk(event.audio_data)

            # 处理音频数据（这里可以集成原始的音频处理逻辑）
            if event.sequence_number % 100 == 0:  # 每100个数据包记录一次
                current_state = await self.audio_stream_controller.get_state()
                self.logger.debug(f"处理音频数据: 序列号={event.sequence_number}, 大小={event.size}字节, 状态={current_state.value}")
        except Exception as e:
            self.logger.error(f"音频数据处理错误: {e}")

    async def process_recognition_result(self, text: str) -> List[float]:
        """异步处理语音识别结果"""
        try:
            # 检查音频流状态（TTSController会自动管理静音状态）
            current_state = await self.audio_stream_controller.get_state()
            if current_state == StreamState.MUTED:
                self.logger.info(f"TTS播放期间，忽略识别结果: '{text}'")
                return []

            # 处理语音命令
            if self._process_voice_commands(text):
                return []

            # 生成唯一识别ID
            recognition_id = self._generate_recognition_id()

            # 提取数值
            try:
                primary_value = extract_primary_measurement(text)
                values = [primary_value] if primary_value is not None else []

                # 存储识别结果历史
                self.recognition_results[recognition_id] = {
                    'original_text': text,
                    'extracted_values': values,
                    'primary_value': primary_value,
                    'timestamp': time.time(),
                    'text_length': len(text),
                    'has_numbers': len(values) > 0
                }

                if values:
                    # 改进的日志格式：ID + 单个数值 + 原始文本 (模拟老系统)
                    value = values[0]
                    self.logger.info(f"识别文字：{text} -> ID {recognition_id}, 数值 {value}，已写入Excel")

                    # 检查是否为中文数字（后续用于字典优化）
                    chinese_numbers = self._extract_chinese_numbers(text)
                    if chinese_numbers:
                        self.logger.debug(f"ID{recognition_id} 中文数字检测: {chinese_numbers}")

                else:
                    self.logger.debug(f"ID{recognition_id} 无数值提取 (来源文本: '{text}')")

                return values

            except Exception as e:
                self.logger.error(f"ID{recognition_id} 数值提取错误: {e} (文本: '{text}')")
                return []

        except Exception as e:
            self.logger.error(f"识别结果处理异常: {e}")
            return []

    def _generate_recognition_id(self) -> str:
        """生成唯一识别ID"""
        self.recognition_counter += 1
        return f"{self.recognition_counter:04d}"

    def _extract_chinese_numbers(self, text: str) -> List[str]:
        """提取文本中的中文数字（用于后续字典优化）"""
        chinese_digits = {
            '零', '一', '二', '三', '四', '五', '六', '七', '八', '九',
            '十', '百', '千', '万', '亿', '点', '负', '正'
        }

        found_numbers = []
        for char in text:
            if char in chinese_digits:
                found_numbers.append(char)

        return found_numbers if found_numbers else []

    def get_recognition_history(self, limit: int = 100) -> Dict[str, Any]:
        """获取识别历史记录"""
        # 返回最近的识别记录
        recent_ids = sorted(self.recognition_results.keys(), reverse=True)[:limit]
        return {rid: self.recognition_results[rid] for rid in recent_ids}

    def get_recognition_statistics(self) -> Dict[str, Any]:
        """获取识别统计信息"""
        total = len(self.recognition_results)
        if total == 0:
            return {'total_recognitions': 0}

        successful = sum(1 for r in self.recognition_results.values() if r['has_numbers'])
        success_rate = (successful / total) * 100

        return {
            'total_recognitions': total,
            'successful_extractions': successful,
            'success_rate': success_rate,
            'average_text_length': sum(r['text_length'] for r in self.recognition_results.values()) / total
        }

    def _process_voice_commands(self, text: str) -> bool:
        """处理语音命令"""
        text_lower = text.lower()

        # 检查暂停命令
        if any(cmd in text_lower for cmd in self.voice_commands['pause']):
            self.logger.info(f"检测到语音命令：暂停 (文本: '{text}')")
            asyncio.create_task(self._publish_voice_command("pause"))
            return True

        # 检查恢复命令
        if any(cmd in text_lower for cmd in self.voice_commands['resume']):
            self.logger.info(f"检测到语音命令：恢复 (文本: '{text}')")
            asyncio.create_task(self._publish_voice_command("resume"))
            return True

        # 检查停止命令
        if any(cmd in text_lower for cmd in self.voice_commands['stop']):
            self.logger.info(f"检测到语音命令：停止 (文本: '{text}')")
            asyncio.create_task(self._publish_voice_command("stop"))
            return True

        return False

    async def _publish_voice_command(self, command: str):
        """发布语音命令事件"""
        from events.event_types import VoiceCommandEvent
        event = VoiceCommandEvent(
            source="AsyncAudioProcessor",
            command=command,
            timestamp=time.time()
        )
        await self.event_bus.publish(event)

    async def speak(self, text: str):
        """使用TTS控制器播放语音"""
        await self.tts_controller.speak(text)


class AsyncTTSManager:
    """异步TTS管理器 - 避免自激问题"""

    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger('tts.manager')
        self.tts_logger = logging.getLogger('tts')

        self.is_enabled = True
        self.is_playing = False
        self.audio_queue = asyncio.Queue()

    async def initialize(self):
        """初始化TTS管理器"""
        try:
            # 启动音频播放任务
            asyncio.create_task(self._audio_player_loop())
            self.logger.info("异步TTS管理器已初始化")
        except Exception as e:
            self.logger.error(f"TTS管理器初始化失败: {e}")
            raise

    async def speak(self, text: str, force: bool = False):
        """播放TTS语音"""
        try:
            if not self.is_enabled and not force:
                self.logger.debug(f"TTS已禁用，忽略播放请求: '{text}'")
                return

            # 将音频加入队列，避免重叠播放
            await self.audio_queue.put(text)
            self.tts_logger.info(f"TTS播放请求已入队: '{text}' (强制: {force})")
        except Exception as e:
            self.logger.error(f"TTS播放请求失败: {e} (文本: '{text}')")

    async def _audio_player_loop(self):
        """音频播放循环"""
        self.logger.info("TTS播放循环已启动")

        while True:
            try:
                # 等待音频数据
                text = await self.audio_queue.get()

                if text == "__STOP__":
                    self.logger.info("收到停止信号，TTS播放循环退出")
                    break

                # 发布TTS开始事件
                await self.event_bus.publish(TTSPlaybackStartedEvent(
                    source="AsyncTTSManager",
                    text=text,
                    player_id="main_tts",
                    duration=0,
                    success=True
                ))

                self.is_playing = True
                start_time = time.time()

                try:
                    # 这里集成实际的TTS播放逻辑
                    # 模拟TTS播放时间
                    estimated_duration = len(text) * 0.1
                    actual_duration = min(estimated_duration, 3.0)

                    self.tts_logger.info(f"开始TTS播放: '{text}' (预计时长: {actual_duration:.2f}秒)")
                    await asyncio.sleep(actual_duration)

                    actual_duration = time.time() - start_time
                    self.tts_logger.info(f"TTS播放完成: '{text}' (实际时长: {actual_duration:.2f}秒)")

                except Exception as e:
                    self.logger.error(f"TTS播放错误: {e} (文本: '{text}')")
                    self.tts_logger.error(f"TTS播放失败: '{text}'")

                finally:
                    self.is_playing = False

                    # 发布TTS完成事件
                    await self.event_bus.publish(TTSPlaybackCompletedEvent(
                        source="AsyncTTSManager",
                        text=text,
                        player_id="main_tts",
                        duration=actual_duration,
                        success=True
                    ))

            except asyncio.CancelledError:
                self.logger.info("TTS播放循环被取消")
                break
            except Exception as e:
                self.logger.error(f"TTS管理器错误: {e}")

    async def stop(self):
        """停止TTS管理器"""
        try:
            await self.audio_queue.put("__STOP__")
            self.logger.info("TTS管理器停止信号已发送")
        except Exception as e:
            self.logger.error(f"停止TTS管理器失败: {e}")

    def enable(self):
        """启用TTS"""
        self.is_enabled = True
        self.logger.info("TTS已启用")

    def disable(self):
        """禁用TTS"""
        self.is_enabled = False
        self.logger.info("TTS已禁用")


class AsyncKeyboardController:
    """异步键盘控制器 - 解决键盘控制问题"""

    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger('keyboard.controller')

        self.is_running = False
        self.key_states = {}
        self.key_handlers = {
            'space': self._handle_space_key,
            'esc': self._handle_esc_key,
            't': self._handle_t_key
        }

    async def start(self):
        """启动键盘监听"""
        try:
            self.is_running = True
            # 启动键盘监听任务
            asyncio.create_task(self._keyboard_monitor_loop())
            self.logger.info("异步键盘控制器已启动")
        except Exception as e:
            self.logger.error(f"键盘控制器启动失败: {e}")
            raise

    async def stop(self):
        """停止键盘监听"""
        self.is_running = False
        self.logger.info("键盘控制器已停止")

    async def _keyboard_monitor_loop(self):
        """键盘监控循环"""
        self.logger.debug("键盘监控循环已启动")
        try:
            # 使用异步方式监听键盘
            # 这里可以集成pynput的异步版本或使用select监听
            while self.is_running:
                # 模拟键盘检查（实际实现需要具体的异步键盘库）
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            self.logger.debug("键盘监控循环被取消")
        except Exception as e:
            self.logger.error(f"键盘监控错误: {e}")

    def simulate_key_press(self, key: str):
        """模拟按键（用于测试或程序化控制）"""
        asyncio.create_task(self._handle_key_press(key))

    async def _handle_key_press(self, key: str):
        """处理按键事件"""
        try:
            key_lower = key.lower()

            if key_lower in self.key_handlers:
                await self.key_handlers[key_lower]()

            # 发布键盘事件
            from events.event_types import KeyboardPressEvent
            event = KeyboardPressEvent(
                source="AsyncKeyboardController",
                key=key,
                timestamp=time.time()
            )
            await self.event_bus.publish(event)
            self.logger.debug(f"键盘事件已发布: '{key}'")
        except Exception as e:
            self.logger.error(f"按键处理错误: {e} (按键: '{key}')")

    async def _handle_space_key(self):
        """处理空格键"""
        self.logger.info("空格键按下 - 暂停/恢复切换")
        try:
            from events.event_types import VoiceCommandEvent
            event = VoiceCommandEvent(
                source="KeyboardController",
                command="toggle_pause",
                timestamp=time.time()
            )
            await self.event_bus.publish(event)
        except Exception as e:
            self.logger.error(f"空格键命令发布失败: {e}")

    async def _handle_esc_key(self):
        """处理ESC键"""
        self.logger.info("ESC键按下 - 系统关闭")
        try:
            from events.event_types import SystemShutdownEvent
            event = SystemShutdownEvent(
                source="KeyboardController",
                reason="用户按下ESC键",
                timestamp=time.time()
            )
            await self.event_bus.publish(event)
        except Exception as e:
            self.logger.error(f"ESC键命令发布失败: {e}")

    async def _handle_t_key(self):
        """处理T键"""
        self.logger.info("T键按下 - TTS切换")
        # T键切换功能将在系统控制器中处理


class ProductionVoiceSystem:
    """生产环境语音系统"""

    def __init__(self, config_path: Optional[str] = None):
        # 配置文件路径
        self.config_path = config_path or "config.yaml"

        # 核心系统组件
        self.event_bus = AsyncEventBus()
        self.coordinator = SystemCoordinator(self.event_bus)
        self.audio_processor = AsyncAudioProcessor(self.event_bus)
        self.tts_manager = AsyncTTSManager(self.event_bus)
        self.keyboard_controller = AsyncKeyboardController(self.event_bus)
        self.data_exporter = None

        # 异步配置加载器
        self.config_loader = AsyncConfigLoader(self.config_path, enable_hot_reload=True)

        # 异步音频捕获器
        self.audio_capture = None

        # 异步数据导出器
        self.data_exporter = None

        # 系统状态
        self.system_state = "idle"
        self.recognition_active = False

        # 日志记录器
        self.logger = logging.getLogger('system.production')
        self.main_logger = logging.getLogger()

    async def initialize(self):
        """初始化系统"""
        self.logger.info("开始初始化生产环境语音系统...")

        try:
            # 1. 初始化异步配置加载器
            await self._initialize_config_loader()

            # 2. 启动优化器和错误处理器
            await start_global_optimizer()
            self.logger.info("全局优化器已启动")

            # 3. 启动事件总线
            await self.event_bus.start()
            self.logger.info("事件总线已启动")

            # 4. 启动系统协调器
            await self.coordinator.start()
            self.logger.info("系统协调器已启动")

            # 5. 初始化组件（使用配置参数）
            await self._initialize_components()

            # 6. 注册系统组件
            await self._register_system_components()

            # 7. 初始化数据导出器
            await self._initialize_data_exporter()

            # 8. 订阅系统事件
            await self._setup_event_subscriptions()

            self.main_logger.info("✅ 生产环境语音系统初始化完成（使用异步配置）")

        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise

    async def _initialize_config_loader(self):
        """初始化配置加载器"""
        try:
            # 添加配置验证器
            self.config_loader.add_validator(create_audio_config_validator())
            self.config_loader.add_validator(create_system_config_validator())

            # 添加配置变更回调
            self.config_loader.add_change_callback(self._on_config_changed)

            # 初始化并加载配置
            success = await self.config_loader.initialize()
            if not success:
                raise Exception("配置加载器初始化失败")

            config_info = self.config_loader.get_config_info()
            self.logger.info(f"异步配置加载器已初始化: {config_info}")

        except Exception as e:
            self.logger.error(f"配置加载器初始化失败: {e}")
            raise

    async def _initialize_components(self):
        """初始化组件"""
        try:
            # 从配置中获取参数
            audio_config = self.config_loader.get('audio', {})

            # 初始化音频处理器
            await self.audio_processor.initialize()
            self.logger.info("异步音频处理器已初始化")

            # 初始化TTS管理器
            await self.tts_manager.initialize()
            self.logger.info("异步TTS管理器已初始化")

            # 初始化键盘控制器
            await self.keyboard_controller.start()
            self.logger.info("异步键盘控制器已启动")

            # 初始化异步音频捕获器
            timeout = audio_config.get('timeout_seconds', 30)
            model_path = self.config_loader.get('model.default_path', 'model/cn')

            self.audio_capture = AsyncAudioCapture(
                timeout_seconds=timeout,
                model_path=model_path,
                test_mode=False  # 生产模式
            )
            self.logger.info("异步音频捕获器已初始化")

            self.logger.info("所有核心组件已初始化")

        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise

    async def _register_system_components(self):
        """注册系统组件"""
        try:
            await self.coordinator.register_component(
                "AudioProcessor", "AsyncAudioProcessor",
                dependencies=[]
            )
            await self.coordinator.register_component(
                "TTSManager", "AsyncTTSManager",
                dependencies=[]
            )
            await self.coordinator.register_component(
                "KeyboardController", "AsyncKeyboardController",
                dependencies=[]
            )
            await self.coordinator.register_component(
                "ConfigLoader", "AsyncConfigLoader",
                dependencies=[]
            )
            self.logger.info("系统组件已注册到协调器")

        except Exception as e:
            self.logger.error(f"系统组件注册失败: {e}")
            raise

    async def _initialize_data_exporter(self):
        """初始化异步数据导出器"""
        try:
            # 从配置中获取Excel设置
            excel_config = self.config_loader.get('excel', {})
            output_file = excel_config.get('output_file', 'measurement_data.xlsx')

            # 使用异步数据导出器适配器
            self.data_exporter = DataExporterAdapter(filename=output_file)
            self.data_exporter.initialize()

            self.logger.info(f"异步数据导出器已初始化，输出文件: {output_file}")

        except Exception as e:
            self.logger.error(f"数据导出器初始化失败: {e}")
            self.data_exporter = None

    async def _setup_event_subscriptions(self):
        """设置事件订阅"""
        try:
            await self.event_bus.subscribe(VoiceCommandEvent, self._on_voice_command)
            await self.event_bus.subscribe(SystemShutdownEvent, self._on_shutdown)
            self.logger.info("系统事件订阅已配置")

        except Exception as e:
            self.logger.error(f"事件订阅设置失败: {e}")
            raise

    async def _on_config_changed(self, event):
        """配置变更处理"""
        try:
            self.logger.info(f"检测到配置变更: {event.changed_keys}")

            # 处理关键配置变更
            for key in event.changed_keys:
                if key == 'audio.sample_rate':
                    self.logger.warning("音频采样率已变更，建议重启系统以生效")
                elif key == 'system.log_level':
                    # 动态更新日志级别
                    new_level = self.config_loader.get('system.log_level', 'INFO')
                    logging.getLogger().setLevel(new_level)
                    self.logger.info(f"日志级别已更新为: {new_level}")
                elif key.startswith('tts.'):
                    self.logger.info("TTS配置已变更，将影响后续语音反馈")

        except Exception as e:
            self.logger.error(f"配置变更处理失败: {e}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值的便捷方法"""
        return self.config_loader.get(key, default)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'system_state': self.system_state,
            'recognition_active': self.recognition_active,
            'config_loaded': self.config_loader.is_loaded(),
            'config_info': self.config_loader.get_config_info(),
            'audio_processor_stats': self.audio_processor.get_recognition_statistics(),
            'components_initialized': True
        }

    async def start_recognition(self):
        """开始语音识别"""
        if self.recognition_active:
            return

        print("[开始语音识别]...")
        self.recognition_active = True
        self.system_state = "recording"

        # 初始化异步音频捕获
        if self.audio_capture:
            try:
                # 初始化异步音频捕获
                success = await self.audio_capture.initialize()
                if not success:
                    self.logger.error("异步音频捕获初始化失败")
                    return

                # 添加识别回调
                self.audio_capture.add_recognition_callback(self._on_recognition_result)
                self.logger.info("异步音频捕获回调已设置")
            except Exception as e:
                self.logger.error(f"初始化异步音频捕获失败: {e}")
                return

        # 发布音频流开始事件
        await self.event_bus.publish(AudioStreamStartedEvent(
            source="ProductionVoiceSystem",
            stream_id="main_stream",
            sample_rate=16000
        ))

        # 启动异步语音识别
        if self.audio_capture:
            try:
                result = await self.audio_capture.start_recognition()
                if result.final_text != "Recognition started successfully":
                    self.logger.error(f"启动异步语音识别失败: {result.final_text}")
                    return
                self.logger.info("异步语音识别已启动")
            except Exception as e:
                self.logger.error(f"启动异步语音识别失败: {e}")
                return

        # 启动TTS确认
        await self.tts_manager.speak("语音识别已开始", force=True)

    async def stop_recognition(self):
        """停止语音识别"""
        if not self.recognition_active:
            return

        print("[停止语音识别]...")
        self.recognition_active = False
        self.system_state = "stopped"

        # 停止异步音频捕获
        if self.audio_capture:
            try:
                result = await self.audio_capture.stop_recognition()
                if result.final_text != "Recognition stopped successfully":
                    self.logger.error(f"停止异步语音识别失败: {result.final_text}")
                else:
                    self.logger.info("异步音频捕获已停止")
            except Exception as e:
                self.logger.error(f"停止异步音频捕获失败: {e}")

        # 发布音频流停止事件
        await self.event_bus.publish(AudioStreamStoppedEvent(
            source="ProductionVoiceSystem",
            stream_id="main_stream",
            reason="user_stop"
        ))

        # 启动TTS确认
        await self.tts_manager.speak("语音识别已停止", force=True)

    def _on_recognition_result(self, result):
        """识别结果回调"""
        try:
            # 使用共享文本处理器提取数值
            if result and hasattr(result, 'final_text') and result.final_text:
                primary_value = extract_primary_measurement(result.final_text)
                values = [primary_value] if primary_value is not None else []

                if values:
                    # 使用音频处理器的集成TTS控制器播报数值
                    value = values[0]
                    value_text = f"{value:.1f}"
                    # 在新线程中执行TTS播放以避免阻塞
                    asyncio.create_task(self.audio_processor.speak(f"识别到数值: {value_text}"))

                    # 异步写入Excel
                    if self.data_exporter:
                        try:
                            # 将结果转换为列表格式
                            data_to_write = [(float(value), str(result.final_text))]
                            # 创建异步任务写入Excel
                            asyncio.create_task(self._write_to_excel_async(data_to_write, values, result.final_text))
                        except Exception as e:
                            self.logger.error(f"Excel写入错误: {e}")
        except Exception as e:
            self.logger.error(f"处理识别结果失败: {e}")

    async def _write_to_excel_async(self, data_to_write, values, original_text):
        """异步写入Excel的辅助方法"""
        try:
            written_records = await self.data_exporter.append_with_text_async(data_to_write)

            if written_records:
                latest_id = written_records[-1][0] if written_records else "0000"
                value = values[0] if values else 0.0
                self.logger.info(f"识别文字：{original_text} -> ID {latest_id}, 数值 {value}，已写入Excel")
        except Exception as e:
            self.logger.error(f"异步Excel写入错误: {e}")

    async def _on_voice_command(self, event):
        """处理语音命令事件"""
        command = event.command
        print(f"[收到语音命令]: {command}")

        if command == "pause" and self.system_state == "recording":
            print("⏸️ 暂停语音识别")
            self.system_state = "paused"
            await self.tts_manager.speak("语音识别已暂停")

        elif command == "resume" and self.system_state == "paused":
            print("▶️ 恢复语音识别")
            self.system_state = "recording"
            await self.tts_manager.speak("语音识别已恢复")

        elif command == "toggle_pause":
            if self.system_state == "recording":
                self.system_state = "paused"
                await self.tts_manager.speak("语音识别已暂停")
            elif self.system_state == "paused":
                self.system_state = "recording"
                await self.tts_manager.speak("语音识别已恢复")

        elif command == "stop":
            await self.stop_recognition()

    async def _on_shutdown(self, event):
        """处理系统关闭事件"""
        print(f"🔴 系统关闭: {event.reason}")
        await self.stop_recognition()

    async def run(self):
        """运行系统主循环"""
        await self.initialize()

        print("\n" + "=" * 60)
        print("[语音识别系统] - 生产环境")
        print("=" * 60)
        print("控制方式:")
        print("  空格键: 暂停/恢复识别")
        print("  ESC键: 停止系统")
        print("  T键: 切换TTS开关")
        print("  语音命令: 暂停/继续/停止")
        print("=" * 60)

        try:
            # 启动识别
            await self.start_recognition()

            # 主循环
            while self.system_state != "stopped":
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n👋 用户中断")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """关闭系统"""
        self.logger.info("正在关闭系统...")

        try:
            # 停止语音识别
            await self.stop_recognition()

            # 给任务一些时间来完成
            await asyncio.sleep(0.1)

            # 停止其他组件
            try:
                await self.keyboard_controller.stop()
            except Exception as e:
                self.logger.warning(f"键盘控制器停止时出错: {e}")

            try:
                await self.tts_manager.stop()
            except Exception as e:
                self.logger.warning(f"TTS管理器停止时出错: {e}")

            # 停止配置加载器
            if self.config_loader:
                try:
                    await self.config_loader.stop()
                except Exception as e:
                    self.logger.warning(f"配置加载器停止时出错: {e}")

            # 停止核心组件
            try:
                await self.coordinator.stop()
            except Exception as e:
                self.logger.warning(f"协调器停止时出错: {e}")

            try:
                await self.event_bus.stop()
            except Exception as e:
                self.logger.warning(f"事件总线停止时出错: {e}")

            # 停止优化器
            try:
                await stop_global_optimizer()
            except Exception as e:
                self.logger.warning(f"优化器停止时出错: {e}")

            # 等待所有待完成的任务
            await asyncio.sleep(0.5)

            self.logger.info("系统已安全关闭")

        except Exception as e:
            self.logger.error(f"系统关闭过程中发生错误: {e}")


def setup_logging():
    """设置日志系统"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 保持详细日志到文件

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器 - 开发模式显示所有调试信息
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # 开发模式：显示所有调试信息
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 用户友好消息处理器 - 显示简化的系统状态
    user_handler = logging.StreamHandler(sys.stdout)
    user_handler.setLevel(logging.INFO)
    user_handler.addFilter(lambda record: record.name == 'system.production' and record.levelno == logging.INFO)
    user_handler.setFormatter(logging.Formatter('%(message)s'))  # 简化格式
    root_logger.addHandler(user_handler)

    # 文件处理器 - 主日志（保留所有详细信息）
    file_handler = logging.FileHandler(
        log_dir / "voice_system.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # 记录所有调试信息
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 错误日志处理器
    error_handler = logging.FileHandler(
        log_dir / "voice_system_errors.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)  # 包含警告和错误
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # TTS专用日志处理器
    tts_handler = logging.FileHandler(
        log_dir / "tts_interactions.log",
        encoding='utf-8'
    )
    tts_handler.setLevel(logging.DEBUG)  # 详细TTS调试信息
    tts_handler.setFormatter(formatter)
    tts_logger = logging.getLogger('tts')
    tts_logger.addHandler(tts_handler)
    tts_logger.setLevel(logging.DEBUG)
    tts_logger.propagate = False  # 避免重复记录

    # 音频处理专用日志处理器
    audio_handler = logging.FileHandler(
        log_dir / "audio_processing.log",
        encoding='utf-8'
    )
    audio_handler.setLevel(logging.DEBUG)
    audio_handler.setFormatter(formatter)
    audio_logger = logging.getLogger('audio')
    audio_logger.addHandler(audio_handler)
    audio_logger.setLevel(logging.DEBUG)
    audio_logger.propagate = False

    return root_logger


async def main():
    """主函数"""
    # 设置日志系统
    logger = setup_logging()

    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建并运行系统
    system = ProductionVoiceSystem()
    await system.run()


if __name__ == "__main__":
    # 检查是否在虚拟环境中运行
    if "VIRTUAL_ENV" not in os.environ and ".venv" not in sys.executable:
        print("⚠️ 警告: 建议在虚拟环境中运行此程序")
        print("激活虚拟环境: .venv\\Scripts\\activate")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"[程序运行错误]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)