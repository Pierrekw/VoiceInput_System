#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试音频流读取问题
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def debug_audio_stream():
    """调试音频流读取"""
    print("调试音频流读取问题...")
    print("=" * 50)

    try:
        from async_audio.async_audio_capture import AsyncAudioStream

        # 创建音频流
        audio_stream = AsyncAudioStream(sample_rate=16000, chunk_size=8000)

        print("1. 打开音频流...")
        await audio_stream.open()
        print(f"   音频流活跃: {audio_stream._is_active}")

        # 检查PyAudio和stream对象
        print("2. 检查底层对象...")
        print(f"   PyAudio对象: {audio_stream.pyaudio is not None}")
        print(f"   Stream对象: {audio_stream.stream is not None}")
        print(f"   Stream活跃: {audio_stream.stream.is_active() if audio_stream.stream else 'None'}")

        # 测试直接读取
        print("3. 测试直接音频读取...")
        read_count = 0
        total_bytes = 0

        for i in range(20):  # 尝试读取20次
            chunk = await audio_stream.read_chunk()
            if chunk:
                read_count += 1
                total_bytes += len(chunk.data)
                print(f"   读取 {read_count}: {len(chunk.data)} 字节 (总计: {total_bytes})")

                # 检查数据是否包含实际音频信号
                if len(chunk.data) > 0:
                    import numpy as np
                    audio_array = np.frombuffer(chunk.data, dtype=np.int16)
                    volume = np.max(np.abs(audio_array))
                    print(f"      音量: {volume}")

                    if volume > 100:  # 检测到声音
                        print(f"      [MIC] 检测到音频信号！")
                        break
                else:
                    print(f"      空数据")
            else:
                print(f"   读取 {i+1}: 无数据")

            await asyncio.sleep(0.1)

        print(f"4. 直接读取结果: {read_count} 次读取, {total_bytes} 总字节")

        # 关闭音频流
        print("5. 关闭音频流...")
        await audio_stream.close()
        print(f"   音频流活跃: {audio_stream._is_active}")

        return read_count > 0

    except Exception as e:
        print(f"[ERROR] 音频流调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manual_audio():
    """手动测试音频"""
    print("\n手动测试音频...")
    print("=" * 50)

    try:
        import pyaudio

        def run_audio_test():
            p = pyaudio.PyAudio()
            try:
                # 获取默认设备信息
                device_info = p.get_default_input_device_info()
                print(f"默认设备: {device_info['name']}")

                # 创建音频流
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8000,
                    start=True
                )

                print("音频流已启动，读取数据...")
                read_count = 0

                for i in range(10):
                    try:
                        data = stream.read(8000, exception_on_overflow=False)
                        if data:
                            read_count += 1
                            print(f"  读取 {read_count}: {len(data)} 字节")
                        else:
                            print(f"  读取 {i+1}: 无数据")
                    except Exception as e:
                        print(f"  读取失败: {e}")

                    time.sleep(0.1)

                stream.stop_stream()
                stream.close()

            finally:
                p.terminate()

        # 在线程池中运行
        await asyncio.to_thread(run_audio_test)

        return True

    except Exception as e:
        print(f"[ERROR] 手动音频测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始音频流读取调试...")
    print("=" * 50)

    # 测试异步音频流
    stream_ok = await debug_audio_stream()

    # 测试手动音频
    manual_ok = await test_manual_audio()

    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"  异步音频流: {'通过' if stream_ok else '失败'}")
    print(f"  手动音频测试: {'通过' if manual_ok else '失败'}")

    if stream_ok and manual_ok:
        print("\n[SUCCESS] 音频系统工作正常")
    else:
        print("\n[ERROR] 音频系统有问题")

if __name__ == "__main__":
    asyncio.run(main())