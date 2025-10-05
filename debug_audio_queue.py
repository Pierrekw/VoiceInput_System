#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试音频队列问题
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def debug_audio_queue():
    """调试音频队列"""
    print("调试音频队列问题...")
    print("=" * 50)

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture

        # 创建音频捕获器
        capture = AsyncAudioCapture(test_mode=False)

        print("1. 初始化音频捕获器...")
        success = await capture.initialize()
        print(f"   初始化结果: {success}")

        # 检查初始状态
        print("2. 检查初始状态...")
        print(f"   stop_event: {capture._stop_event.is_set()}")
        print(f"   pause_event: {capture._pause_event.is_set()}")
        print(f"   音频队列大小: {capture._audio_queue.qsize()}")
        print(f"   音频流活跃: {capture.audio_stream._is_active}")

        # 开始识别
        print("3. 开始识别...")
        start_result = await capture.start_recognition()
        print(f"   开始结果: {start_result.final_text}")

        # 再次检查状态
        print("4. 检查识别后状态...")
        print(f"   stop_event: {capture._stop_event.is_set()}")
        print(f"   pause_event: {capture._pause_event.is_set()}")
        print(f"   音频队列大小: {capture._audio_queue.qsize()}")
        print(f"   音频流活跃: {capture.audio_stream._is_active}")

        # 启动一个监控任务
        async def monitor_queue():
            print("5. 启动队列监控...")
            while not capture._stop_event.is_set():
                queue_size = capture._audio_queue.qsize()
                pause_event = capture._pause_event.is_set()
                print(f"   队列大小: {queue_size}, 暂停: {pause_event}")

                # 检查工作协程状态
                if capture._capture_task and not capture._capture_task.done():
                    task_alive = True
                else:
                    task_alive = False

                if capture._recognition_task and not capture._recognition_task.done():
                    recognition_alive = True
                else:
                    recognition_alive = False

                print(f"   工作协程状态: 捕获={task_alive}, 识别={recognition_alive}")

                await asyncio.sleep(0.5)

        # 启动监控
        monitor_task = asyncio.create_task(monitor_queue())

        # 等待一段时间
        print("6. 等待5秒...")
        await asyncio.sleep(5)

        # 手动停止
        print("7. 停止识别...")
        await capture.stop_recognition()

        # 等待监控任务完成
        await monitor_task

        # 最终状态
        print("8. 最终状态检查...")
        print(f"   stop_event: {capture._stop_event.is_set()}")
        print(f"   pause_event: {capture._pause_event.is_set()}")
        print(f"   音频队列大小: {capture._audio_queue.qsize()}")
        print(f"   音频流活跃: {capture.audio_stream._is_active}")

        # 统计信息
        stats = capture._stats
        print(f"   统计信息: {stats}")

        # 清理
        await capture.cleanup()

        return True

    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    try:
        success = await debug_audio_queue()
        print("\n" + "=" * 50)
        if success:
            print("调试完成")
        else:
            print("调试失败")

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())