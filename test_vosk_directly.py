#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试Vosk识别器
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_vosk_directly():
    """直接测试Vosk识别器"""
    print("直接测试Vosk识别器...")

    try:
        # 直接导入和使用Vosk
        import vosk

        # 加载模型
        model_path = "model/cn"
        print(f"1. 加载模型: {model_path}")
        model = await asyncio.to_thread(lambda: vosk.Model(model_path))
        print("   模型加载成功")

        # 创建识别器
        print("2. 创建识别器...")
        recognizer = await asyncio.to_thread(lambda: vosk.KaldiRecognizer(model, 16000))
        print("   识别器创建成功")

        # 测试静音数据
        print("3. 测试静音数据...")
        silence_data = b'\x00' * 8000  # 静音数据

        result = await asyncio.to_thread(recognizer.AcceptWaveform, silence_data)
        print(f"   静音识别结果: {result}")

        if result:
            final_result = await asyncio.to_thread(recognizer.Result)
            print(f"   最终结果: {final_result}")
        else:
            print("   没有识别结果（静音数据正常）")

        # 测试一些模拟的音频数据
        print("4. 测试模拟音频数据...")
        # 创建一些简单的音频数据
        test_audio = b'\x00\x01\x02\x03\x04\x05' * 1600  # 简单的音频模式

        for i in range(3):
            result = await asyncio.to_thread(recognizer.AcceptWaveform, test_audio)
            print(f"   测试音频 {i+1}: {result}")

            if result:
                final_result = await asyncio.to_thread(recognizer.Result)
                print(f"      最终结果: {final_result}")

        print("Vosk识别器测试完成")
        return True

    except Exception as e:
        print(f"Vosk测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_recognizer():
    """测试异步识别器"""
    print("\n测试异步识别器...")

    try:
        from async_audio.async_audio_capture import AsyncRecognizer

        recognizer = AsyncRecognizer(model_path="model/cn")

        print("1. 初始化异步识别器...")
        await recognizer.initialize()
        print(f"   初始化结果: {recognizer._is_initialized}")

        if not recognizer._is_initialized:
            print("   异步识别器初始化失败")
            return False

        # 创建测试音频数据
        from async_audio.async_audio_capture import AudioChunk
        test_audio = AudioChunk(data=b'\x00' * 8000, timestamp=time.time(), size=8000)

        print("2. 测试异步识别...")
        result = await recognizer.process_audio(test_audio)
        print(f"   异步识别结果: '{result}'")

        print("异步识别器测试完成")
        return True

    except Exception as e:
        print(f"异步识别器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("开始Vosk识别器调试...")
    print("=" * 50)

    # 测试Vosk直接使用
    vosk_ok = await test_vosk_directly()

    # 测试异步识别器
    async_ok = await test_async_recognizer()

    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"  Vosk直接测试: {'通过' if vosk_ok else '失败'}")
    print(f"  异步识别器测试: {'通过' if async_ok else '失败'}")

    if vosk_ok and async_ok:
        print("\n识别器工作正常")
    else:
        print("\n识别器有问题")

if __name__ == "__main__":
    asyncio.run(main())