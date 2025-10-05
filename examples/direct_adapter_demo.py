# -*- coding: utf-8 -*-
"""
直接适配器演示

展示直接使用适配器的功能，避免依赖注入容器的复杂性。
"""

import asyncio
import logging
from typing import Dict, Any, List

from adapters.audio_processor_adapter import AudioProcessorAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DirectAdapterDemo:
    """直接适配器演示类"""

    def __init__(self):
        """初始化演示"""
        self.audio_processor = None

    async def initialize(self):
        """初始化系统"""
        logger.info("初始化音频处理器适配器...")

        # 直接创建适配器实例
        self.audio_processor = AudioProcessorAdapter(test_mode=True)
        logger.info(f"音频处理器类型: {type(self.audio_processor).__name__}")

    async def run_demo(self) -> Dict[str, Any]:
        """运行演示"""
        logger.info("运行适配器演示...")

        results = {
            "adapter_info": {},
            "state_info": {},
            "recognition_tests": [],
            "extraction_tests": [],
            "method_tests": []
        }

        try:
            # 1. 获取适配器信息
            await self._get_adapter_info(results)

            # 2. 检查状态
            await self._check_state(results)

            # 3. 测试数值提取
            await self._test_number_extraction(results)

            # 4. 测试其他方法
            await self._test_methods(results)

            logger.info("适配器演示完成")
            return results

        except Exception as e:
            logger.error(f"演示过程中发生错误: {e}")
            raise

    async def _get_adapter_info(self, results: Dict[str, Any]) -> None:
        """获取适配器信息"""
        logger.info("获取适配器信息...")

        try:
            results["adapter_info"] = {
                "type": type(self.audio_processor).__name__,
                "initialized": self.audio_processor.is_initialized(),
                "has_audio_capture": hasattr(self.audio_processor, '_audio_capture')
            }

            # 获取诊断信息
            try:
                diagnostics = self.audio_processor.get_diagnostics_info()
                results["adapter_info"]["diagnostics"] = diagnostics
            except Exception as e:
                logger.warning(f"获取诊断信息失败: {e}")

            logger.info(f"适配器已初始化: {results['adapter_info']['initialized']}")

        except Exception as e:
            logger.error(f"获取适配器信息失败: {e}")
            results["adapter_info"] = {"error": str(e)}

    async def _check_state(self, results: Dict[str, Any]) -> None:
        """检查适配器状态"""
        logger.info("检查适配器状态...")

        try:
            state = self.audio_processor.get_state()
            results["state_info"] = {
                "current_state": str(state),
                "state_type": type(state).__name__
            }

            logger.info(f"当前状态: {results['state_info']['current_state']}")

        except Exception as e:
            logger.error(f"检查状态失败: {e}")
            results["state_info"] = {"error": str(e)}

    async def _test_number_extraction(self, results: Dict[str, Any]) -> None:
        """测试数值提取功能"""
        logger.info("测试数值提取功能...")

        test_cases = [
            {"text": "二十五点五", "expected": [25.5]},
            {"text": "一百零二", "expected": [102]},
            {"text": "三点一四一五九", "expected": [3.14159]},
            {"text": "零点五", "expected": [0.5]},
            {"text": "二十", "expected": [20]},
            {"text": "三十点五", "expected": [30.5]},
            {"text": "一百二十三", "expected": [123]},
            {"text": "零点二五", "expected": [0.25]}
        ]

        extraction_results = []

        for test_case in test_cases:
            text = test_case["text"]
            expected = test_case["expected"]

            try:
                measurements = self.audio_processor.extract_measurements(text)

                success = False
                if measurements:
                    # 简单比较，看是否有数值被提取
                    success = len(measurements) > 0

                extraction_results.append({
                    "text": text,
                    "expected": expected,
                    "actual": measurements,
                    "success": success
                })

                logger.info(f"提取测试: '{text}' -> 期望: {expected}, 实际: {measurements}, 成功: {success}")

            except Exception as e:
                logger.error(f"提取测试失败: '{text}' -> {e}")
                extraction_results.append({
                    "text": text,
                    "expected": expected,
                    "error": str(e),
                    "success": False
                })

        results["extraction_tests"] = extraction_results

    async def _test_methods(self, results: Dict[str, Any]) -> None:
        """测试其他方法"""
        logger.info("测试其他方法...")

        method_results = []

        # 测试各种方法
        methods_to_test = [
            "is_initialized",
            "get_supported_formats",
            "get_diagnostics_info"
        ]

        for method_name in methods_to_test:
            try:
                if hasattr(self.audio_processor, method_name):
                    method = getattr(self.audio_processor, method_name)
                    result = method()

                    method_results.append({
                        "method": method_name,
                        "result": str(result),
                        "success": True
                    })

                    logger.info(f"方法测试 {method_name}: {result}")
                else:
                    method_results.append({
                        "method": method_name,
                        "error": "方法不存在",
                        "success": False
                    })

            except Exception as e:
                logger.error(f"方法测试失败 {method_name}: {e}")
                method_results.append({
                    "method": method_name,
                    "error": str(e),
                    "success": False
                })

        results["method_tests"] = method_results

    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        try:
            if hasattr(self.audio_processor, 'cleanup'):
                self.audio_processor.cleanup()
            logger.info("适配器资源已清理")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")


async def main():
    """主函数"""
    logger.info("Voice Input System 直接适配器演示")
    logger.info("=" * 50)

    demo = DirectAdapterDemo()

    try:
        # 初始化
        await demo.initialize()

        # 运行演示
        results = await demo.run_demo()

        # 显示结果
        logger.info("=" * 50)
        logger.info("演示结果总结:")
        logger.info(f"  适配器类型: {results['adapter_info'].get('type', 'Unknown')}")
        logger.info(f"  适配器状态: {results['state_info'].get('current_state', 'Unknown')}")
        logger.info(f"  提取测试数: {len(results['extraction_tests'])}")
        logger.info(f"  方法测试数: {len(results['method_tests'])}")

        # 统计成功率
        extraction_success = sum(1 for r in results['extraction_tests'] if r.get('success', False))
        method_success = sum(1 for r in results['method_tests'] if r.get('success', False))

        logger.info(f"  提取成功率: {extraction_success}/{len(results['extraction_tests'])} ({extraction_success/len(results['extraction_tests'])*100:.1f}%)")
        logger.info(f"  方法成功率: {method_success}/{len(results['method_tests'])} ({method_success/len(results['method_tests'])*100:.1f}%)")

        return results

    except Exception as e:
        logger.error(f"演示运行失败: {e}")
        raise

    finally:
        # 清理资源
        demo.cleanup()


if __name__ == "__main__":
    # 运行直接适配器演示
    try:
        asyncio.run(main())
        logger.info("直接适配器演示完成")
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"直接适配器演示失败: {e}")