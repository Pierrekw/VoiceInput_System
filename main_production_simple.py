#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版生产环境语音系统 - 使用已验证的异步组件
"""

import asyncio
import logging
import sys
import os
import signal
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

# 导入核心异步组件
from async_audio.async_audio_stream_controller import (
    AsyncAudioStreamController, StreamConfig, StreamState
)
from async_audio.async_audio_stream_controller import TTSController

# 导入共享组件
from text_processor import extract_measurements
from async_audio.async_audio_capture import AsyncAudioCapture

# 导入简化的Excel导出器
from excel_exporter import ExcelExporter

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


class SimpleVoiceSystem:
    """简化版语音系统"""

    def __init__(self, config_path: Optional[str] = None):
        # 配置文件路径
        self.config_path = config_path or "config.yaml"

        # 核心系统组件
        self.event_bus = AsyncEventBus()
        self.coordinator = SystemCoordinator(self.event_bus)
        self.audio_capture = None
        self.excel_exporter = None

        # 异步配置加载器
        self.config_loader = AsyncConfigLoader(self.config_path, enable_hot_reload=True)

        # 系统状态
        self.system_state = "idle"
        self.recognition_active = False

        # 日志记录器
        self.logger = logging.getLogger('simple.voice.system')
        self.main_logger = logging.getLogger()

    async def initialize(self):
        """初始化系统"""
        self.logger.info("开始初始化简化版语音系统...")

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

            # 5. 初始化异步音频捕获器
            await self._initialize_audio_capture()

            # 6. 初始化Excel导出器
            await self._initialize_excel_exporter()

            # 7. 订阅系统事件
            await self._setup_event_subscriptions()

            self.main_logger.info("✅ 简化版语音系统初始化完成")

        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise

    async def _initialize_config_loader(self):
        """初始化配置加载器"""
        try:
            success = await self.config_loader.initialize()
            if not success:
                raise Exception("配置加载器初始化失败")

            config_info = self.config_loader.get_config_info()
            self.logger.info(f"异步配置加载器已初始化: {config_info}")

        except Exception as e:
            self.logger.error(f"配置加载器初始化失败: {e}")
            raise

    async def _initialize_audio_capture(self):
        """初始化异步音频捕获器"""
        try:
            audio_config = self.config_loader.get('audio', {})
            timeout = audio_config.get('timeout_seconds', 30)
            model_path = self.config_loader.get('model.default_path', 'model/cn')

            self.audio_capture = AsyncAudioCapture(
                timeout_seconds=timeout,
                model_path=model_path,
                test_mode=False  # 生产模式
            )
            self.logger.info("异步音频捕获器已初始化")

        except Exception as e:
            self.logger.error(f"异步音频捕获器初始化失败: {e}")
            raise

    async def _initialize_excel_exporter(self):
        """初始化Excel导出器"""
        try:
            excel_config = self.config_loader.get('excel', {})
            output_file = excel_config.get('output_file', 'measurement_data.xlsx')

            # 使用同步Excel导出器（避免adapter问题）
            self.excel_exporter = ExcelExporter(output_file)
            self.logger.info(f"Excel导出器已初始化，输出文件: {output_file}")

        except Exception as e:
            self.logger.error(f"Excel导出器初始化失败: {e}")
            self.excel_exporter = None

    async def _setup_event_subscriptions(self):
        """设置事件订阅"""
        try:
            # 这里可以添加事件订阅逻辑
            self.logger.info("系统事件订阅已配置")

        except Exception as e:
            self.logger.error(f"事件订阅配置失败: {e}")

    def _on_recognition_result(self, result):
        """识别结果回调"""
        try:
            # 使用共享文本处理器提取数值
            if result and hasattr(result, 'final_text') and result.final_text:
                values = extract_measurements(result.final_text)

                if values:
                    print(f"识别到数值: {values} (原始文本: {result.final_text})")

                    # 写入Excel
                    if self.excel_exporter:
                        try:
                            # 将结果转换为列表格式
                            data_to_write = [(float(v), str(result.final_text)) for v in values]
                            written_records = self.excel_exporter.append_with_text(data_to_write)

                            if written_records:
                                latest_id = written_records[-1][0] if written_records else "0000"
                                self.logger.info(f"ID{latest_id} 数据已写入Excel: 数值={values}, 原始文本='{result.final_text}'")
                        except Exception as e:
                            self.logger.error(f"Excel写入错误: {e}")
        except Exception as e:
            self.logger.error(f"处理识别结果失败: {e}")

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
            source="SimpleVoiceSystem",
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
            source="SimpleVoiceSystem",
            stream_id="main_stream",
            reason="user_stop"
        ))

    async def run(self):
        """运行系统主循环"""
        await self.initialize()

        print("\n" + "=" * 60)
        print("[简化版语音识别系统] - 生产环境")
        print("=" * 60)
        print("控制方式:")
        print("  Ctrl+C: 停止系统")
        print("=" * 60)

        try:
            # 启动识别
            await self.start_recognition()

            # 主循环
            while self.system_state != "stopped":
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n[用户中断]")
        except Exception as e:
            self.logger.error(f"系统运行错误: {e}")
        finally:
            await self.stop_recognition()

    async def cleanup(self):
        """清理资源"""
        try:
            if self.audio_capture:
                await self.audio_capture.cleanup()
            await self.event_bus.stop()
            await self.coordinator.stop()
            await stop_global_optimizer()
            self.logger.info("系统资源已清理")
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")


def setup_logging():
    """设置日志系统"""
    import logging
    from pathlib import Path

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
    root_logger.setLevel(logging.DEBUG)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器 - 只显示警告和错误
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器 - 保留所有详细信息
    file_handler = logging.FileHandler(
        log_dir / "simple_voice_system.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

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
    system = SimpleVoiceSystem()
    try:
        await system.run()
    finally:
        await system.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[程序已退出]")
    except Exception as e:
        print(f"[程序运行错误]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)