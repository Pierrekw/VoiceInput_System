# -*- coding: utf-8 -*-
"""
集成验证示例

展示Voice Input System的完整集成使用，包括：
- 依赖注入容器的配置和使用
- 适配器的集成
- 异步操作的处理
- 系统生命周期管理
"""

import asyncio
import logging
from typing import List, Dict, Any

from container import DIContainer
from interfaces import (
    IAudioProcessor, IDataExporter, ITTSProvider,
    IConfigProvider, AudioProcessorState
)
from adapters import (
    AudioProcessorAdapter, DataExporterAdapter,
    TTSProviderAdapter, ConfigProviderAdapter
)
from adapters.adapter_factory import global_adapter_factory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceInputSystem:
    """
    Voice Input System主类

    演示如何使用依赖注入和适配器模式构建完整的系统。
    """

    def __init__(self, container: DIContainer):
        """
        初始化系统

        Args:
            container: 配置好的依赖注入容器
        """
        self.container = container
        self.audio_processor = None
        self.data_exporter = None
        self.tts_provider = None
        self.config_provider = None

    async def initialize(self) -> None:
        """初始化系统组件"""
        logger.info("初始化Voice Input System...")

        # 从容器解析服务
        self.audio_processor = self.container.resolve(IAudioProcessor)
        self.data_exporter = self.container.resolve(IDataExporter)
        self.tts_provider = self.container.resolve(ITTSProvider)
        self.config_provider = self.container.resolve(IConfigProvider)

        logger.info("所有服务已成功解析")

    async def run_demo(self) -> Dict[str, Any]:
        """运行演示"""
        logger.info("开始运行演示...")

        results = {
            "recognition_results": [],
            "export_results": [],
            "tts_results": [],
            "config_info": {}
        }

        try:
            # 1. 配置系统
            await self._configure_system(results)

            # 2. 运行音频识别
            await self._run_audio_recognition(results)

            # 3. 导出数据
            await self._export_data(results)

            # 4. 语音反馈
            await self._provide_voice_feedback(results)

            logger.info("演示完成")
            return results

        except Exception as e:
            logger.error(f"演示过程中发生错误: {e}")
            raise

    async def _configure_system(self, results: Dict[str, Any]) -> None:
        """配置系统"""
        logger.info("配置系统参数...")

        # 设置配置
        await self.config_provider.set_async("recognition.timeout_seconds", 30)
        await self.config_provider.set_async("tts.volume", 0.8)
        await self.config_provider.set_async("export.auto_save", True)

        # 获取配置信息
        timeout = await self.config_provider.get_async("recognition.timeout_seconds")
        volume = await self.config_provider.get_async("tts.volume")

        results["config_info"] = {
            "timeout": timeout,
            "volume": volume
        }

        logger.info(f"系统配置完成 - 超时: {timeout}秒, 音量: {volume}")

    async def _run_audio_recognition(self, results: Dict[str, Any]) -> None:
        """运行音频识别"""
        logger.info("开始音频识别...")

        try:
            # 检查音频处理器状态
            state = self.audio_processor.get_state()
            logger.info(f"音频处理器状态: {state}")

            # 启动识别
            recognition_result = await self.audio_processor.start_recognition_async()

            if recognition_result.success:
                logger.info(f"识别成功: {recognition_result.text}")
                results["recognition_results"].append({
                    "text": recognition_result.text,
                    "confidence": recognition_result.confidence,
                    "timestamp": recognition_result.timestamp
                })

                # 提取数值
                measurements = self.audio_processor.extract_measurements(recognition_result.text)
                if measurements:
                    logger.info(f"提取的数值: {measurements}")
                    results["recognition_results"][-1]["measurements"] = measurements
            else:
                logger.warning(f"识别失败: {recognition_result.error_message}")

        except Exception as e:
            logger.error(f"音频识别错误: {e}")

    async def _export_data(self, results: Dict[str, Any]) -> None:
        """导出数据"""
        logger.info("导出数据...")

        try:
            # 准备导出数据
            export_data = []
            for result in results["recognition_results"]:
                if "measurements" in result:
                    for measurement in result["measurements"]:
                        export_data.append((measurement, f"数值{measurement}"))

            if export_data:
                # 批量导出
                export_results = await self.data_exporter.batch_export_async(export_data)

                for i, export_result in enumerate(export_results):
                    if export_result.success:
                        logger.info(f"导出成功: {export_result.records_count}条记录")
                        results["export_results"].append({
                            "file_path": export_result.file_path,
                            "records_count": export_result.records_count
                        })
                    else:
                        logger.error(f"导出失败: {export_result.error_message}")
            else:
                logger.info("没有数据需要导出")

        except Exception as e:
            logger.error(f"数据导出错误: {e}")

    async def _provide_voice_feedback(self, results: Dict[str, Any]) -> None:
        """提供语音反馈"""
        logger.info("提供语音反馈...")

        try:
            feedback_messages = []

            # 根据识别结果生成反馈
            for result in results["recognition_results"]:
                if result.get("text"):
                    feedback_messages.append(f"识别到: {result['text']}")

            # 根据导出结果生成反馈
            if results["export_results"]:
                feedback_messages.append(f"成功导出{len(results['export_results'])}个文件")

            # 播放反馈
            for message in feedback_messages[:3]:  # 限制最多3条反馈
                tts_result = await self.tts_provider.speak_async(message)

                if tts_result.success:
                    logger.info(f"语音反馈成功: {message}")
                    results["tts_results"].append({
                        "text": message,
                        "success": True,
                        "duration": tts_result.duration
                    })
                else:
                    logger.error(f"语音反馈失败: {tts_result.error_message}")
                    results["tts_results"].append({
                        "text": message,
                        "success": False,
                        "error": tts_result.error_message
                    })

        except Exception as e:
            logger.error(f"语音反馈错误: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                "container_services": len(self.container.get_registered_services()),
                "audio_processor_state": self.audio_processor.get_state() if self.audio_processor else None,
                "tts_provider_initialized": self.tts_provider.is_initialized() if self.tts_provider else False,
                "config_provider_cache_size": self.config_provider.get_cache_size() if self.config_provider else 0
            }
        except Exception as e:
            logger.error(f"获取系统信息错误: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """清理系统资源"""
        logger.info("清理系统资源...")

        try:
            # 停止音频处理
            if self.audio_processor:
                stop_result = await self.audio_processor.stop_recognition_async()
                if stop_result.success:
                    logger.info("音频处理器已停止")
                else:
                    logger.warning(f"停止音频处理器失败: {stop_result.error_message}")

            # 释放容器资源
            self.container.dispose()
            logger.info("容器资源已释放")

        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")


def configure_container() -> DIContainer:
    """
    配置依赖注入容器

    Returns:
        DIContainer: 配置好的容器
    """
    logger.info("配置依赖注入容器...")

    container = DIContainer()

    # 注册配置提供者（单例）
    container.register_singleton(
        IConfigProvider,
        lambda: ConfigProviderAdapter()
    )

    # 注册数据导出器（作用域）
    container.register_scoped(
        IDataExporter,
        lambda: DataExporterAdapter()
    )

    # 注册TTS服务（瞬态）
    container.register_transient(
        ITTSProvider,
        lambda: TTSProviderAdapter()
    )

    # 注册音频处理器（瞬态，有依赖）
    container.register_transient(
        IAudioProcessor,
        lambda c: AudioProcessorAdapter(
            config_provider=c.resolve(IConfigProvider),
            data_exporter=c.resolve(IDataExporter),
            tts_provider=c.resolve(ITTSProvider)
        )
    )

    logger.info(f"容器配置完成，注册了{container.get_service_count()}个服务")
    return container


async def main():
    """主函数"""
    logger.info("Voice Input System 集成验证示例")
    logger.info("=" * 50)

    # 配置容器
    container = configure_container()

    # 创建系统
    system = VoiceInputSystem(container)

    try:
        # 初始化系统
        await system.initialize()

        # 显示系统信息
        system_info = system.get_system_info()
        logger.info(f"系统信息: {system_info}")

        # 运行演示
        results = await system.run_demo()

        # 显示结果
        logger.info("=" * 50)
        logger.info("演示结果:")
        logger.info(f"  识别结果: {len(results['recognition_results'])}个")
        logger.info(f"  导出结果: {len(results['export_results'])}个")
        logger.info(f"  TTS结果: {len(results['tts_results'])}个")
        logger.info(f"  配置信息: {results['config_info']}")

        return results

    except Exception as e:
        logger.error(f"系统运行失败: {e}")
        raise

    finally:
        # 清理资源
        await system.cleanup()


if __name__ == "__main__":
    # 运行集成验证示例
    try:
        asyncio.run(main())
        logger.info("集成验证示例完成")
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"集成验证示例失败: {e}")