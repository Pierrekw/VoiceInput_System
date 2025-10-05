#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实音频输入
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

async def test_real_audio_input():
    """测试真实音频输入"""
    print("测试真实音频输入...")
    print("=" * 50)
    print("请对着麦克风说话或发出声音...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture
        from async_audio.async_audio_capture import AudioChunk

        # 创建音频捕获器（生产模式）
        capture = AsyncAudioCapture(test_mode=False)

        print("1. 初始化音频捕获器...")
        success = await capture.initialize()
        if not success:
            print("   初始化失败")
            return False
        print("   初始化成功")

        # 手动测试音频流
        print("2. 直接测试音频流...")
        audio_stream = capture.audio_stream

        # 检查音频流状态
        print(f"   音频流活跃: {audio_stream._is_active}")

        # 读取一些音频数据
        for i in range(10):
            try:
                chunk = await audio_stream.read_chunk()
                if chunk:
                    # 检查音频数据的能量（音量）
                    if hasattr(chunk, 'data') and chunk.data:
                        # 将音频数据转换为numpy数组计算音量
                        audio_array = np.frombuffer(chunk.data, dtype=np.int16)
                        volume = np.max(np.abs(audio_array))

                        if volume > 1000:  # 设置一个阈值
                            print(f"   检测到音频信号！音量: {volume}")

                            # 测试这段音频是否能被识别
                            result = await capture.recognizer.process_audio(chunk)
                            if result and result.strip():
                                print(f"   识别结果: '{result}'")
                                return True
                            else:
                                print(f"   音频数据已被处理，但没有识别结果")
                        else:
                            print(f"   静音数据，音量: {volume}")
                    else:
                        print(f"   空音频块")
                else:
                    print(f"   没有音频数据")
            except Exception as e:
                print(f"   读取音频数据失败: {e}")

            await asyncio.sleep(0.5)

        print("3. 开始完整的语音识别...")
        callback_results = []

        def test_callback(result):
            callback_results.append(result)
            print(f"   📞 识别结果: '{result.final_text}'")

        capture.add_recognition_callback(test_callback)

        # 开始识别
        start_result = await capture.start_recognition()
        print(f"   开始识别: {start_result.final_text}")

        # 监听10秒
        print("   监听10秒，请说话...")
        start_time = time.time()

        while time.time() - start_time < 10:
            await asyncio.sleep(1)
            stats = capture._stats
            print(f"   统计: 捕获={stats.get('captured_chunks', 0)}, 识别={stats.get('recognized_texts', 0)}")

        # 停止识别
        stop_result = await capture.stop_recognition()
        print(f"   停止识别: {stop_result.final_text}")

        # 清理
        await capture.cleanup()

        print(f"4. 最终结果:")
        print(f"   总回调数量: {len(callback_results)}")
        print(f"   捕获的音频块: {capture._stats.get('captured_chunks', 0)}")
        print(f"   识别的文本数: {capture._stats.get('recognized_texts', 0)}")

        return len(callback_results) > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    try:
        success = await test_real_audio_input()

        print("\n" + "=" * 50)
        if success:
            print("🎉 真实音频输入测试成功！")
        else:
            print("❌ 没有检测到有效的音频输入")
            print("可能的原因:")
            print("  1. 麦克风被静音")
            print("  2. 没有权限访问麦克风")
            print("  3. 麦克风设备有问题")
            print("  4. 系统环境问题")

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())