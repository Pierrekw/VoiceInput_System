# -*- coding: utf-8 -*-
"""
基础集成演示

展示Voice Input System的核心功能集成，简化版本避免复杂的依赖问题。
"""

import asyncio
import logging
from typing import Dict, Any

from container import DIContainer
from interfaces import IAudioProcessor
from adapters.audio_processor_adapter import AudioProcessorAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BasicVoiceInputDemo:
    """基础语音输入演示类"""

    def __init__(self):
        """初始化演示"""
        self.container = DIContainer()
        self.audio_processor = None

    def setup_container(self):
        """设置依赖注入容器"""
        logger.info("设置依赖注入容器...")

        # 注册音频处理器（使用工厂函数）
        def create_audio_processor():
            return AudioProcessorAdapter(test_mode=True)

        self.container.register_transient(IAudioProcessor, create_audio_processor)

        logger.info(f"容器注册了 {self.container.get_service_count()} 个服务")

    async def initialize(self):
        """初始化系统"""
        logger.info("初始化系统...")

        # 解析音频处理器
        self.audio_processor = self.container.resolve(IAudioProcessor)
        logger.info(f"音频处理器类型: {type(self.audio_processor).__name__}")

    async def run_basic_demo(self) -> Dict[str, Any]:
        """运行基础演示"""
        logger.info("运行基础演示...")

        results = {
            "processor_info": {},
            "state_info": {},
            "recognition_results": [],
            "extraction_results": []
        }

        try:
            # 1. 获取处理器信息
            await self._get_processor_info(results)

            # 2. 检查状态
            await self._check_processor_state(results)

            # 3. 模拟语音识别
            await self._simulate_recognition(results)

            # 4. 数值提取测试
            await self._test_number_extraction(results)

            logger.info("基础演示完成")
            return results

        except Exception as e:
            logger.error(f"演示过程中发生错误: {e}")
            raise

    async def _get_processor_info(self, results: Dict[str, Any]) -> None:
        """获取处理器信息"""
        logger.info("获取音频处理器信息...")

        try:
            # 获取诊断信息
            diagnostics = self.audio_processor.get_diagnostics_info()
            results["processor_info"] = {
                "type": type(self.audio_processor).__name__,
                "initialized": self.audio_processor.is_initialized(),
                "diagnostics": diagnostics
            }

            logger.info(f"处理器已初始化: {results['processor_info']['initialized']}")

        except Exception as e:
            logger.error(f"获取处理器信息失败: {e}")
            results["processor_info"] = {"error": str(e)}

    async def _check_processor_state(self, results: Dict[str, Any]) -> None:
        """检查处理器状态"""
        logger.info("检查处理器状态...")

        try:
            state = self.audio_processor.get_state()
            results["state_info"] = {
                "current_state": str(state),
                "is_ready": state.name if hasattr(state, 'name') else str(state)
            }

            logger.info(f"当前状态: {results['state_info']['current_state']}")

        except Exception as e:
            logger.error(f"检查状态失败: {e}")
            results["state_info"] = {"error": str(e)}

    async def _simulate_recognition(self, results: Dict[str, Any]) -> None:
        """模拟语音识别"""
        logger.info("模拟语音识别...")

        test_texts = [
            "二十五点五",
            "一百零二",
            "三点一四一五九",
            "零点五"
        ]

        for text in test_texts:
            try:
                # 提取数值
                measurements = self.audio_processor.extract_measurements(text)

                if measurements:
                    logger.info(f"文本: '{text}' -> 数值: {measurements}")
                    results["recognition_results"].append({
                        "text": text,
                        "measurements": measurements,
                        "success": True
                    })
                else:
                    logger.warning(f"文本: '{text}' -> 未提取到数值")
                    results["recognition_results"].append({
                        "text": text,
                        "measurements": [],
                        "success": False
                    })

            except Exception as e:
                logger.error(f"处理文本 '{text}' 失败: {e}")
                results["recognition_results"].append({
                    "text": text,
                    "error": str(e),
                    "success": False
                })

    async def _test_number_extraction(self, results: Dict[str, Any]) -> None:
        """测试数值提取功能"""
        logger.info("测试数值提取功能...")

        test_cases = [
            ("二十", 20),
            ("三十点五", 30.5),
            ("一百二十三", 123),
            ("零点二五", 0.25)
        ]

        extraction_results = []

        for text, expected in test_cases:
            try:
                measurements = self.audio_processor.extract_measurements(text)

                if measurements:
                    actual = measurements[0]
                    success = abs(actual - expected) < 0.01  # 允许小误差
                else:
                    actual = None
                    success = False

                extraction_results.append({
                    "text": text,
                    "expected": expected,
                    "actual": actual,
                    "success": success
                })

                logger.info(f"提取测试: '{text}' -> 期望: {expected}, 实际: {actual}, 成功: {success}")

            except Exception as e:
                logger.error(f"提取测试失败: '{text}' -> {e}")
                extraction_results.append({
                    "text": text,
                    "expected": expected,
                    "error": str(e),
                    "success": False
                })

        results["extraction_results"] = extraction_results

    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        try:
            self.container.dispose()
            logger.info("容器资源已释放")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")


async def main():
    """主函数"""
    logger.info("Voice Input System 基础集成演示")
    logger.info("=" * 50)

    demo = BasicVoiceInputDemo()

    try:
        # 设置容器
        demo.setup_container()

        # 初始化
        await demo.initialize()

        # 运行演示
        results = await demo.run_basic_demo()

        # 显示结果
        logger.info("=" * 50)
        logger.info("演示结果总结:")
        logger.info(f"  处理器类型: {results['processor_info'].get('type', 'Unknown')}")
        logger.info(f"  处理器状态: {results['state_info'].get('current_state', 'Unknown')}")
        logger.info(f"  识别测试数: {len(results['recognition_results'])}")
        logger.info(f"  提取测试数: {len(results['extraction_results'])}")

        # 统计成功率
        recognition_success = sum(1 for r in results['recognition_results'] if r.get('success', False))
        extraction_success = sum(1 for r in results['extraction_results'] if r.get('success', False))

        logger.info(f"  识别成功率: {recognition_success}/{len(results['recognition_results'])} ({recognition_success/len(results['recognition_results'])*100:.1f}%)")
        logger.info(f"  提取成功率: {extraction_success}/{len(results['extraction_results'])} ({extraction_success/len(results['extraction_results'])*100:.1f}%)")

        return results

    except Exception as e:
        logger.error(f"演示运行失败: {e}")
        raise

    finally:
        # 清理资源
        demo.cleanup()


if __name__ == "__main__":
    # 运行基础集成演示
    try:
        asyncio.run(main())
        logger.info("基础集成演示完成")
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"基础集成演示失败: {e}")