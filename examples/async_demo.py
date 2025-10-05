# -*- coding: utf-8 -*-
"""
异步音频处理演示

展示Voice Input System的异步功能，包括：
- 异步音频流管理
- 异步语音识别
- 异步数值提取
- 异步TTS播放
- 模式切换和兼容性
"""

import asyncio
import logging
import time
from typing import List, Dict, Any

from adapters.async_audio_processor_adapter import (
    AsyncAudioProcessorAdapter, create_async_audio_processor_adapter,
    create_hybrid_audio_processor_adapter
)
from async_audio import create_async_audio_capture
from async_audio.async_number_extractor import extract_measurements
from interfaces.audio_processor import RecognitionResult, AudioProcessorState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncAudioDemo:
    """异步音频处理演示类"""

    def __init__(self):
        """初始化演示"""
        self.adapter = None
        self.capture = None
        self.recognition_results = []
        self.state_changes = []

    async def initialize(self):
        """初始化系统"""
        logger.info("🚀 初始化异步音频处理系统...")

        # 创建异步适配器
        self.adapter = await create_async_audio_processor_adapter(
            test_mode=True,
            timeout_seconds=10
        )

        # 设置回调
        self.adapter.add_recognition_callback(self._on_recognition_result)
        self.adapter.add_state_change_callback(self._on_state_change)

        logger.info("✅ 异步音频处理系统初始化完成")

    def _on_recognition_result(self, result: RecognitionResult):
        """处理识别结果回调"""
        self.recognition_results.append(result)
        logger.info(f"🎤 识别结果: {result.text} (置信度: {result.confidence:.2f})")

    def _on_state_change(self, state: AudioProcessorState):
        """处理状态变更回调"""
        self.state_changes.append(state)
        logger.info(f"🔄 状态变更: {state.name}")

    async def demo_basic_operations(self) -> Dict[str, Any]:
        """演示基本操作"""
        logger.info("🎯 演示基本异步操作...")

        results = {"basic_operations": {}}

        try:
            # 获取初始状态
            initial_state = self.adapter.get_state()
            results["basic_operations"]["initial_state"] = initial_state.name
            logger.info(f"初始状态: {initial_state.name}")

            # 开始语音识别
            start_result = await self.adapter.start_recognition_async()
            results["basic_operations"]["recognition_started"] = start_result.success

            if start_result.success:
                logger.info("✅ 语音识别已启动")

                # 等待一段时间
                await asyncio.sleep(3.0)

                # 检查状态
                current_state = self.adapter.get_state()
                results["basic_operations"]["recognition_state"] = current_state.name

                # 停止语音识别
                stop_result = await self.adapter.stop_recognition_async()
                results["basic_operations"]["recognition_stopped"] = stop_result.success

                if stop_result.success:
                    logger.info("✅ 语音识别已停止")

            # 获取统计信息
            stats = self.adapter.get_statistics()
            results["basic_operations"]["statistics"] = stats

            return results

        except Exception as e:
            logger.error(f"❌ 基本操作演示失败: {e}")
            results["basic_operations"]["error"] = str(e)
            return results

    async def demo_pause_resume(self) -> Dict[str, Any]:
        """演示暂停和恢复功能"""
        logger.info("⏸️ 演示暂停和恢复功能...")

        results = {"pause_resume": {}}

        try:
            # 开始识别
            start_result = await self.adapter.start_recognition_async()
            results["pause_resume"]["started"] = start_result.success

            if start_result.success:
                logger.info("🎤 识别已启动")

                # 等待一段时间
                await asyncio.sleep(1.0)

                # 暂停识别
                paused = await self.adapter.pause_recognition_async()
                results["pause_resume"]["paused"] = paused

                if paused:
                    logger.info("⏸️ 识别已暂停")
                    results["pause_resume"]["pause_state"] = self.adapter.get_state().name

                    # 等待一段时间
                    await asyncio.sleep(1.0)

                    # 恢复识别
                    resumed = await self.adapter.resume_recognition_async()
                    results["pause_resume"]["resumed"] = resumed

                    if resumed:
                        logger.info("▶️ 识别已恢复")
                        results["pause_resume"]["resume_state"] = self.adapter.get_state().name

                # 停止识别
                await self.adapter.stop_recognition_async()

            return results

        except Exception as e:
            logger.error(f"❌ 暂停恢复演示失败: {e}")
            results["pause_resume"]["error"] = str(e)
            return results

    async def demo_number_extraction(self) -> Dict[str, Any]:
        """演示异步数值提取"""
        logger.info("🔢 演示异步数值提取...")

        results = {"number_extraction": {}}

        test_cases = [
            "二十五点五",
            "一百零二",
            "三点一四一五九",
            "零点五",
            "二十",
            "三十点五"
        ]

        extraction_results = []

        for text in test_cases:
            try:
                # 同步数值提取
                sync_result = self.adapter.extract_measurements(text)

                # 异步数值提取
                async_result = await self.adapter.extract_measurements_async(text)

                extraction_results.append({
                    "text": text,
                    "sync_result": sync_result,
                    "async_result": async_result,
                    "success": len(async_result) > 0
                })

                logger.info(f"数值提取: '{text}' -> {async_result}")

            except Exception as e:
                logger.error(f"❌ 数值提取失败 '{text}': {e}")
                extraction_results.append({
                    "text": text,
                    "error": str(e),
                    "success": False
                })

        results["number_extraction"]["results"] = extraction_results
        results["number_extraction"]["total_cases"] = len(test_cases)
        results["number_extraction"]["successful_cases"] = sum(1 for r in extraction_results if r.get("success", False))

        return results

    async def demo_mode_switching(self) -> Dict[str, Any]:
        """演示模式切换"""
        logger.info("🔄 演示模式切换...")

        results = {"mode_switching": {}}

        try:
            # 创建混合模式适配器
            hybrid_adapter = create_hybrid_audio_processor_adapter(
                use_async=False,
                test_mode=True
            )

            results["mode_switching"]["initial_mode"] = "sync"
            results["mode_switching"]["initial_state"] = hybrid_adapter.get_state().name

            # 测试同步模式
            sync_result = hybrid_adapter.extract_measurements("二十五点五")
            results["mode_switching"]["sync_extraction"] = sync_result

            # 切换到异步模式
            switch_success = await hybrid_adapter.switch_to_async_mode()
            results["mode_switching"]["switch_success"] = switch_success

            if switch_success:
                results["mode_switching"]["new_mode"] = "async"
                results["mode_switching"]["new_state"] = hybrid_adapter.get_state().name

                # 测试异步模式
                async_result = await hybrid_adapter.extract_measurements_async("二十五点五")
                results["mode_switching"]["async_extraction"] = async_result

                # 切换回同步模式
                await hybrid_adapter.switch_to_sync_mode()
                results["mode_switching"]["final_mode"] = "sync"

            # 清理
            await hybrid_adapter.cleanup_async()

            return results

        except Exception as e:
            logger.error(f"❌ 模式切换演示失败: {e}")
            results["mode_switching"]["error"] = str(e)
            return results

    async def demo_performance_comparison(self) -> Dict[str, Any]:
        """演示性能对比"""
        logger.info("⚡ 演示性能对比...")

        results = {"performance": {}}

        test_text = "二十五点五"
        iterations = 50

        try:
            # 同步模式性能测试
            start_time = time.time()
            for _ in range(iterations):
                self.adapter.extract_measurements(test_text)
            sync_time = time.time() - start_time

            # 异步模式性能测试
            start_time = time.time()
            for _ in range(iterations):
                await self.adapter.extract_measurements_async(test_text)
            async_time = time.time() - start_time

            results["performance"] = {
                "iterations": iterations,
                "sync_time": sync_time,
                "async_time": async_time,
                "sync_avg": sync_time / iterations,
                "async_avg": async_time / iterations,
                "performance_ratio": async_time / sync_time
            }

            logger.info(f"📊 性能对比结果 ({iterations}次迭代):")
            logger.info(f"  同步模式: {sync_time:.4f}s (平均: {sync_time/iterations:.6f}s)")
            logger.info(f"  异步模式: {async_time:.4f}s (平均: {async_time/iterations:.6f}s)")
            logger.info(f"  性能比: {async_time/sync_time:.2f}x")

            return results

        except Exception as e:
            logger.error(f"❌ 性能对比演示失败: {e}")
            results["performance"]["error"] = str(e)
            return results

    async def demo_concurrent_operations(self) -> Dict[str, Any]:
        """演示并发操作"""
        logger.info("🚀 演示并发操作...")

        results = {"concurrent": {}}

        try:
            # 创建多个异步任务
            async def concurrent_extraction(text: str, task_id: int):
                start_time = time.time()
                result = await self.adapter.extract_measurements_async(text)
                end_time = time.time()
                return {
                    "task_id": task_id,
                    "text": text,
                    "result": result,
                    "duration": end_time - start_time
                }

            # 创建并发任务
            tasks = [
                concurrent_extraction(f"测试文本{i}", i) for i in range(10)
            ]

            # 执行并发任务
            start_time = time.time()
            concurrent_results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            results["concurrent"] = {
                "tasks_count": len(tasks),
                "total_time": total_time,
                "results": concurrent_results,
                "successful_tasks": sum(1 for r in concurrent_results if r["result"])
            }

            logger.info(f"🚀 并发操作结果:")
            logger.info(f"  任务数量: {len(tasks)}")
            logger.info(f"  总时间: {total_time:.4f}s")
            logger.info(f"  成功任务: {results['concurrent']['successful_tasks']}/{len(tasks)}")

            return results

        except Exception as e:
            logger.error(f"❌ 并发操作演示失败: {e}")
            results["concurrent"]["error"] = str(e)
            return results

    async def run_full_demo(self) -> Dict[str, Any]:
        """运行完整演示"""
        logger.info("🎭 开始完整异步音频处理演示")
        logger.info("=" * 60)

        all_results = {}

        try:
            # 演示基本操作
            logger.info("\n📋 1. 基本操作演示")
            all_results["basic"] = await self.demo_basic_operations()

            # 演示数值提取
            logger.info("\n🔢 2. 数值提取演示")
            all_results["extraction"] = await self.demo_number_extraction()

            # 演示暂停恢复
            logger.info("\n⏸️ 3. 暂停恢复演示")
            all_results["pause_resume"] = await self.demo_pause_resume()

            # 演示模式切换
            logger.info("\n🔄 4. 模式切换演示")
            all_results["mode_switching"] = await self.demo_mode_switching()

            # 演示性能对比
            logger.info("\n⚡ 5. 性能对比演示")
            all_results["performance"] = await self.demo_performance_comparison()

            # 演示并发操作
            logger.info("\n🚀 6. 并发操作演示")
            all_results["concurrent"] = await self.demo_concurrent_operations()

            # 获取诊断信息
            logger.info("\n🔍 7. 诊断信息")
            diagnostics = await self.adapter.get_diagnostics_info()
            all_results["diagnostics"] = diagnostics

            logger.info("\n" + "=" * 60)
            logger.info("🎉 完整演示完成!")

            return all_results

        except Exception as e:
            logger.error(f"❌ 完整演示失败: {e}")
            all_results["error"] = str(e)
            return all_results

    async def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理演示资源...")
        try:
            await self.adapter.cleanup_async()
            logger.info("✅ 演示资源清理完成")
        except Exception as e:
            logger.error(f"❌ 演示资源清理失败: {e}")


async def main():
    """主函数"""
    logger.info("Voice Input System 异步音频处理演示")
    logger.info("=" * 60)

    demo = AsyncAudioDemo()

    try:
        # 初始化演示
        await demo.initialize()

        # 运行完整演示
        results = await demo.run_full_demo()

        # 显示总结
        logger.info("\n" + "=" * 60)
        logger.info("📊 演示结果总结:")

        for demo_name, demo_results in results.items():
            if demo_name != "error":
                logger.info(f"  {demo_name}: ✅ 完成")
            else:
                logger.info(f"  错误: {demo_results}")

        # 显示关键统计
        if "extraction" in results:
            extraction = results["extraction"]["number_extraction"]
            logger.info(f"  数值提取成功率: {extraction['successful_cases']}/{extraction['total_cases']}")

        if "performance" in results:
            perf = results["performance"]["performance"]
            if "performance_ratio" in perf:
                ratio = perf["performance_ratio"]
                logger.info(f"  异步/同步性能比: {ratio:.2f}x")

        return results

    except Exception as e:
        logger.error(f"🚨 演示运行失败: {e}")
        raise

    finally:
        # 清理资源
        await demo.cleanup()


if __name__ == "__main__":
    # 运行异步演示
    try:
        asyncio.run(main())
        logger.info("🎊 异步音频处理演示完成")
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断")
    except Exception as e:
        logger.error(f"🚨 演示执行失败: {e}")