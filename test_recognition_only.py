#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语音识别器
"""

import asyncio
import sys
import os
import time
import numpy as np

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_recognizer_with_real_audio():
    """测试识别器处理真实音频"""
    print("测试语音识别器...")
    print("=" * 50)
    print("请对着麦克风说话...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture, AudioChunk

        # 创建音频捕获器
        capture = AsyncAudioCapture(test_mode=False)

        print("1. 初始化音频捕获器...")
        success = await capture.initialize()
        print(f"   初始化结果: {success}")

        if not success:
            print("   ❌ 初始化失败")
            return False

        print("2. 手动收集一些音频数据...")
        audio_chunks = []
        audio_stream = capture.audio_stream

        # 收集10个音频块
        for i in range(10):
            chunk = await audio_stream.read_chunk()
            if chunk and chunk.data:
                audio_chunks.append(chunk)
                # 计算音量
                audio_array = np.frombuffer(chunk.data, dtype=np.int16)
                volume = np.max(np.abs(audio_array))
                print(f"   收集音频 {i+1}: {len(chunk.data)} 字节, 音量: {volume}")

                if volume > 1000:  # 检测到说话
                    print(f"   [VOICE] 检测到语音信号！")
            else:
                print(f"   收集音频 {i+1}: 无数据")

            await asyncio.sleep(0.5)

        print(f"3. 收集到 {len(audio_chunks)} 个音频块")

        if not audio_chunks:
            print("   没有收集到音频数据")
            return False

        print("4. 直接测试识别器...")
        recognizer = capture.recognizer

        # 检查识别器状态
        print(f"   识别器已初始化: {recognizer._is_initialized}")
        if not recognizer._is_initialized:
            print("   识别器未初始化，尝试初始化...")
            await recognizer.initialize()
            print(f"   初始化后状态: {recognizer._is_initialized}")

        # 逐个测试音频块
        recognized_any = False
        for i, chunk in enumerate(audio_chunks):
            print(f"   处理音频块 {i+1}...")
            try:
                result = await recognizer.process_audio(chunk)
                if result and result.strip():
                    print(f"   识别结果: '{result}'")
                    recognized_any = True
                else:
                    print(f"   无识别结果")
            except Exception as e:
                print(f"   识别错误: {e}")

        print("5. 清理...")
        await capture.cleanup()

        print(f"\n6. 测试结果:")
        print(f"   识别到语音: {'是' if recognized_any else '否'}")

        return recognized_any

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_recognizer_directly():
    """直接测试识别器"""
    print("\n直接测试识别器...")
    print("=" * 50)

    try:
        from async_audio.async_audio_capture import AsyncRecognizer, AudioChunk
        import time

        # 创建识别器
        recognizer = AsyncRecognizer(model_path="model/cn")

        print("1. 初始化识别器...")
        await recognizer.initialize()
        print(f"   初始化结果: {recognizer._is_initialized}")

        if not recognizer._is_initialized:
            print("   ❌ 识别器初始化失败")
            return False

        print("2. 创建测试音频数据...")
        # 创建一些有模式的音频数据（模拟语音）
        test_patterns = [
            b'\x00\x01\x02\x03' * 2000,  # 简单模式
            b'\x10\x20\x30\x40' * 2000,  # 更大声的模式
            b'\x00\x00\x00\x00' * 2000,  # 静音
        ]

        print("3. 测试不同音频模式...")
        for i, pattern in enumerate(test_patterns):
            print(f"   测试模式 {i+1}...")
            chunk = AudioChunk(data=pattern, timestamp=time.time(), size=len(pattern))

            try:
                result = await recognizer.process_audio(chunk)
                if result and result.strip():
                    print(f"   识别结果: '{result}'")
                else:
                    print(f"   无识别结果")
            except Exception as e:
                print(f"   识别错误: {e}")

        return True

    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("开始语音识别器测试...")
    print("=" * 50)

    # 测试识别器
    direct_ok = await test_recognizer_directly()

    # 测试真实音频
    real_ok = await test_recognizer_with_real_audio()

    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"  直接识别器测试: {'通过' if direct_ok else '失败'}")
    print(f"  真实音频测试: {'通过' if real_ok else '失败'}")

    if direct_ok and real_ok:
        print("\n[SUCCESS] 语音识别器工作正常")
    else:
        print("\n[ERROR] 识别器有问题")

if __name__ == "__main__":
    asyncio.run(main())