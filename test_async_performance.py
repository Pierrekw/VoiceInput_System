#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步系统性能测试
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

async def test_model_loading_time():
    """测试模型加载时间"""
    print("=== 测试异步模型加载时间 ===")

    start_time = time.time()

    try:
        from async_audio.async_audio_capture import AsyncRecognizer

        print("1. 创建AsyncRecognizer...")
        recognizer = AsyncRecognizer(model_path="model/cn")

        print("2. 开始初始化...")
        init_start = time.time()
        await recognizer.initialize()
        init_time = time.time() - init_start

        print(f"   模型初始化耗时: {init_time:.2f}秒")
        print(f"   识别器状态: {recognizer.is_initialized}")

        total_time = time.time() - start_time
        print(f"   总耗时: {total_time:.2f}秒")

        return init_time

    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None

async def test_sync_model_loading_time():
    """测试同步模型加载时间"""
    print("\n=== 测试同步模型加载时间 ===")

    start_time = time.time()

    try:
        import vosk

        print("1. 加载Vosk模型...")
        model_start = time.time()
        model = vosk.Model("model/cn")
        model_time = time.time() - model_start

        print(f"   模型加载耗时: {model_time:.2f}秒")

        print("2. 创建识别器...")
        recognizer_start = time.time()
        recognizer = vosk.KaldiRecognizer(model, 16000)
        recognizer_time = time.time() - recognizer_start

        print(f"   识别器创建耗时: {recognizer_time:.4f}秒")

        total_time = time.time() - start_time
        print(f"   总耗时: {total_time:.2f}秒")

        return model_time

    except Exception as e:
        print(f"❌ 同步模型加载失败: {e}")
        return None

async def test_recognition_latency():
    """测试识别延迟"""
    print("\n=== 测试识别延迟 ===")

    try:
        from async_audio.async_audio_capture import AsyncRecognizer, AudioChunk

        # 初始化识别器
        recognizer = AsyncRecognizer(model_path="model/cn")
        await recognizer.initialize()

        # 创建测试音频数据
        test_audio = AudioChunk(data=b'\x00' * 8000, timestamp=time.time(), size=8000)

        print("1. 测试单个音频块识别延迟...")
        latencies = []

        for i in range(5):
            start = time.time()
            result = await recognizer.process_audio(test_audio)
            latency = time.time() - start
            latencies.append(latency)
            print(f"   测试 {i+1}: {latency*1000:.1f}ms")

        avg_latency = sum(latencies) / len(latencies)
        print(f"   平均延迟: {avg_latency*1000:.1f}ms")

        return avg_latency

    except Exception as e:
        print(f"❌ 识别延迟测试失败: {e}")
        return None

async def test_audio_stream_latency():
    """测试音频流延迟"""
    print("\n=== 测试音频流延迟 ===")

    try:
        from async_audio.async_audio_capture import AsyncAudioStream

        # 创建音频流
        stream = AsyncAudioStream(sample_rate=16000, chunk_size=8000)

        print("1. 打开音频流...")
        open_start = time.time()
        await stream.open()
        open_time = time.time() - open_start

        print(f"   音频流打开耗时: {open_time*1000:.1f}ms")

        print("2. 测试音频块读取延迟...")
        latencies = []

        for i in range(3):
            start = time.time()
            chunk = await stream.read_chunk()
            latency = time.time() - start
            latencies.append(latency)
            print(f"   读取 {i+1}: {latency*1000:.1f}ms, 数据: {len(chunk.data) if chunk else 0} bytes")

        avg_latency = sum(latencies) / len(latencies)
        print(f"   平均读取延迟: {avg_latency*1000:.1f}ms")

        await stream.close()
        return avg_latency

    except Exception as e:
        print(f"❌ 音频流延迟测试失败: {e}")
        return None

async def main():
    """主函数"""
    print("开始异步系统性能分析...")
    print("=" * 60)

    # 测试模型加载时间
    async_load_time = await test_model_loading_time()
    sync_load_time = await test_sync_model_loading_time()

    # 测试识别延迟
    recognition_latency = await test_recognition_latency()

    # 测试音频流延迟
    stream_latency = await test_audio_stream_latency()

    print("\n" + "=" * 60)
    print("性能分析总结:")

    if async_load_time and sync_load_time:
        print(f"  模型加载时间:")
        print(f"    异步: {async_load_time:.2f}秒")
        print(f"    同步: {sync_load_time:.2f}秒")
        print(f"    差异: {async_load_time - sync_load_time:+.2f}秒")

    if recognition_latency:
        print(f"  识别延迟: {recognition_latency*1000:.1f}ms")

    if stream_latency:
        print(f"  音频流延迟: {stream_latency*1000:.1f}ms")

    # 给出建议
    print("\n性能建议:")
    if async_load_time and async_load_time > 15:
        print("  ⚠️  模型加载时间过长，建议:")
        print("    - 使用更小的模型")
        print("    - 预加载模型")
        print("    - 考虑模型缓存")

    if recognition_latency and recognition_latency > 0.1:
        print("  ⚠️  识别延迟过高，建议:")
        print("    - 优化音频块大小")
        print("    - 检查线程池配置")
        print("    - 减少不必要的处理步骤")

if __name__ == "__main__":
    asyncio.run(main())