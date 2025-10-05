#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试语音识别问题
"""

import asyncio
import sys
import os
import logging
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 设置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_recognition_pipeline():
    """测试完整的识别流水线"""
    print("测试语音识别流水线...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture
        from async_audio.async_audio_capture import AudioChunk

        # 创建音频捕获器（生产模式）
        capture = AsyncAudioCapture(test_mode=False)

        print("1. 初始化异步音频捕获器...")
        success = await capture.initialize()
        print(f"   初始化结果: {success}")

        if not success:
            print("   ❌ 初始化失败，无法继续")
            return False

        # 手动创建一些音频数据进行测试
        print("2. 创建测试音频数据...")
        test_audio_data = b'\x00' * 16000  # 创建1秒的静音数据
        test_chunk = AudioChunk(data=test_audio_data, timestamp=time.time())
        print(f"   创建测试音频块: {len(test_chunk.data)} 字节")

        # 测试识别器
        print("3. 测试语音识别器...")
        if capture.recognizer and capture.recognizer._is_initialized:
            print("   识别器已初始化")

            # 直接测试识别
            print("   开始识别测试音频...")
            result = await capture.recognizer.process_audio(test_chunk)
            print(f"   识别结果: '{result}'")
        else:
            print("   ❌ 识别器未初始化")
            return False

        # 设置回调
        callback_results = []

        def test_callback(result):
            callback_results.append(result)
            print(f"   📞 收到识别回调: '{result.final_text}'")

        capture.add_recognition_callback(test_callback)
        print("4. 识别回调已设置")

        # 手动调用识别回调（模拟识别结果）
        print("5. 模拟识别结果...")
        from interfaces.audio_processor import RecognitionResult
        mock_result = RecognitionResult(
            final_text="测试识别结果",
            processing_time=time.time()
        )

        test_callback(mock_result)
        print(f"   模拟回调结果数量: {len(callback_results)}")

        # 开始真实的语音识别
        print("6. 开始真实语音识别...")
        start_result = await capture.start_recognition()
        print(f"   开始识别结果: {start_result.final_text}")

        # 监听状态变化
        print("7. 监听5秒...")
        start_time = time.time()
        last_stats = None

        while time.time() - start_time < 5:
            await asyncio.sleep(0.5)
            current_stats = capture._stats.copy()

            if current_stats != last_stats:
                print(f"   统计信息更新: {current_stats}")
                last_stats = current_stats.copy()

        # 停止识别
        print("8. 停止语音识别...")
        stop_result = await capture.stop_recognition()
        print(f"   停止识别结果: {stop_result.final_text}")

        print(f"   最终统计: {capture._stats}")
        print(f"   回调结果数量: {len(callback_results)}")

        # 清理
        await capture.cleanup()

        return len(callback_results) > 0

    except Exception as e:
        print(f"❌ 识别流水线测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_audio_queue_flow():
    """测试音频队列流程"""
    print("\n测试音频队列流程...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture, AudioChunk

        capture = AsyncAudioCapture(test_mode=False)
        await capture.initialize()

        # 手动添加音频数据到队列
        print("1. 手动添加音频数据到队列...")
        test_data = [AudioChunk(data=b'test' * 4000, timestamp=time.time()) for _ in range(3)]

        for i, chunk in enumerate(test_data):
            try:
                capture._audio_queue.put_nowait(chunk)
                print(f"   添加音频块 {i+1}")
            except asyncio.QueueFull:
                print(f"   ❌ 队列已满，无法添加音频块 {i+1}")

        print(f"   队列大小: {capture._audio_queue.qsize()}")

        # 测试队列读取
        print("2. 测试队列读取...")
        for i in range(3):
            try:
                chunk = await asyncio.wait_for(capture._audio_queue.get(), timeout=1.0)
                print(f"   读取音频块 {i+1}: {len(chunk.data)} 字节")
            except asyncio.TimeoutError:
                print(f"   ❌ 读取音频块 {i+1} 超时")

        await capture.cleanup()
        return True

    except Exception as e:
        print(f"❌ 音频队列测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始语音识别调试...")
    print("=" * 50)

    # 测试音频队列流程
    queue_ok = await test_audio_queue_flow()

    # 测试识别流水线
    recognition_ok = await test_recognition_pipeline()

    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"  音频队列流程: {'✅ 通过' if queue_ok else '❌ 失败'}")
    print(f"  识别流水线: {'✅ 通过' if recognition_ok else '❌ 失败'}")

    if queue_ok and recognition_ok:
        print("\n🎉 语音识别系统工作正常！")
    else:
        print("\n❌ 语音识别系统有问题，需要进一步调试。")

if __name__ == "__main__":
    asyncio.run(main())