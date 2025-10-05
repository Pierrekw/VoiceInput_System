#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试音频捕获问题
"""

import asyncio
import sys
import os
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 设置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_audio_stream():
    """测试音频流"""
    print("测试音频流...")

    try:
        from async_audio.async_audio_capture import AsyncAudioStream

        async with AsyncAudioStream(sample_rate=16000, chunk_size=8000) as stream:
            print(f"音频流状态: {stream._is_active}")
            print("音频流已打开，正在读取音频数据...")

            for i in range(10):
                audio_chunk = await stream.read_chunk()
                if audio_chunk:
                    print(f"读取到音频块 {i+1}: 大小={len(audio_chunk)}")
                else:
                    print(f"音频块 {i+1}: 无数据")

                await asyncio.sleep(0.1)

            print("音频流测试完成")
            return True

    except Exception as e:
        print(f"音频流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pyaudio_directly():
    """直接测试PyAudio"""
    print("\n直接测试PyAudio...")

    try:
        import pyaudio

        def run_pyaudio():
            p = pyaudio.PyAudio()
            try:
                default_device = p.get_default_input_device_info()
                print(f"默认音频设备: {default_device['name']}")

                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8000,
                    start=True
                )

                print("音频流已启动，读取数据...")

                for i in range(5):
                    data = stream.read(8000, exception_on_overflow=False)
                    print(f"读取音频数据 {i+1}: 大小={len(data)}")

                stream.stop_stream()
                stream.close()

            finally:
                p.terminate()

        # 在线程池中运行PyAudio
        await asyncio.to_thread(run_pyaudio)
        print("PyAudio直接测试完成")
        return True

    except Exception as e:
        print(f"PyAudio直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_audio_capture():
    """测试完整的异步音频捕获"""
    print("\n测试异步音频捕获...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture

        # 创建音频捕获器（生产模式）
        capture = AsyncAudioCapture(test_mode=False)

        print("初始化异步音频捕获器...")
        success = await capture.initialize()
        print(f"初始化结果: {success}")

        if success:
            # 设置回调
            callback_results = []

            def test_callback(result):
                callback_results.append(result)
                print(f"收到识别回调: {result.final_text}")

            capture.add_recognition_callback(test_callback)
            print("识别回调已设置")

            # 开始识别
            print("开始语音识别...")
            start_result = await capture.start_recognition()
            print(f"开始识别结果: {start_result.final_text}")

            # 运行10秒
            print("监听10秒...")
            await asyncio.sleep(10)

            # 停止识别
            print("停止语音识别...")
            stop_result = await capture.stop_recognition()
            print(f"停止识别结果: {stop_result.final_text}")

            print(f"总共收到 {len(callback_results)} 个识别结果")

            # 清理
            await capture.cleanup()

        return True

    except Exception as e:
        print(f"异步音频捕获测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("开始音频系统调试...")
    print("=" * 50)

    # 测试PyAudio直接使用
    pyaudio_ok = await test_pyaudio_directly()

    # 测试音频流
    stream_ok = await test_audio_stream()

    # 测试完整异步音频捕获
    capture_ok = await test_async_audio_capture()

    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"  PyAudio直接测试: {'✅ 通过' if pyaudio_ok else '❌ 失败'}")
    print(f"  异步音频流测试: {'✅ 通过' if stream_ok else '❌ 失败'}")
    print(f"  异步音频捕获测试: {'✅ 通过' if capture_ok else '❌ 失败'}")

    if all([pyaudio_ok, stream_ok, capture_ok]):
        print("\n🎉 所有测试通过！音频系统工作正常。")
    else:
        print("\n❌ 一些测试失败，需要进一步调试。")

if __name__ == "__main__":
    asyncio.run(main())