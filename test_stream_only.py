#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只测试音频流性能
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_stream_only():
    """只测试音频流"""
    print("=== 测试优化后的音频流延迟 ===")

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
        successful_reads = 0

        for i in range(10):  # 测试10次
            start = time.time()
            try:
                chunk = await asyncio.wait_for(stream.read_chunk(), timeout=0.2)
                latency = time.time() - start
                latencies.append(latency)
                successful_reads += 1
                if chunk:
                    print(f"   读取 {i+1}: {latency*1000:.1f}ms, 数据: {len(chunk.data)} bytes")
                else:
                    print(f"   读取 {i+1}: {latency*1000:.1f}ms, 无数据")
            except asyncio.TimeoutError:
                print(f"   读取 {i+1}: 超时 (>200ms)")
            except Exception as e:
                print(f"   读取 {i+1}: 错误 - {e}")

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            print(f"\n性能统计:")
            print(f"   成功读取: {successful_reads}/10")
            print(f"   平均延迟: {avg_latency*1000:.1f}ms")
            print(f"   最小延迟: {min_latency*1000:.1f}ms")
            print(f"   最大延迟: {max_latency*1000:.1f}ms")

            if avg_latency < 0.1:  # 100ms
                print("   ✅ 优化成功！延迟已降到可接受范围")
            else:
                print("   ⚠️  仍需进一步优化")

        await stream.close()
        return avg_latency if latencies else None

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_stream_only())