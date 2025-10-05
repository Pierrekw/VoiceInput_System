#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的语音识别测试
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def main():
    """主函数"""
    print("开始简化语音识别测试...")
    print("=" * 50)

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture, AudioChunk

        # 创建音频捕获器
        capture = AsyncAudioCapture(test_mode=False)

        print("1. 初始化音频捕获器...")
        success = await capture.initialize()
        print(f"   初始化结果: {success}")

        if not success:
            print("   ❌ 初始化失败")
            return

        # 检查识别器状态
        print("2. 检查识别器状态...")
        print(f"   识别器已初始化: {capture.recognizer._is_initialized if capture.recognizer else 'None'}")
        print(f"   识别器对象: {type(capture.recognizer)}")

        # 添加回调
        callback_count = 0

        def test_callback(result):
            nonlocal callback_count
            callback_count += 1
            print(f"   📞 收到回调 {callback_count}: '{result.final_text}'")

        capture.add_recognition_callback(test_callback)
        print("3. 回调已设置")

        # 开始识别
        print("4. 开始语音识别...")
        start_result = await capture.start_recognition()
        print(f"   开始结果: {start_result.final_text}")

        # 等待并监控统计信息
        print("5. 监控5秒...")
        start_time = time.time()

        while time.time() - start_time < 5:
            await asyncio.sleep(1)

            stats = capture._stats
            print(f"   统计信息: 捕获={stats.get('captured_chunks', 0)}, "
                  f"识别={stats.get('recognized_texts', 0)}, "
                  f"错误={stats.get('errors', 0)}")

        # 停止识别
        print("6. 停止识别...")
        stop_result = await capture.stop_recognition()
        print(f"   停止结果: {stop_result.final_text}")

        print(f"7. 总回调数量: {callback_count}")

        # 清理
        await capture.cleanup()

        print("\n" + "=" * 50)
        if callback_count > 0:
            print("[SUCCESS] 语音识别系统正常工作！")
            return True
        else:
            print("[ERROR] 没有收到任何识别回调，系统可能有问题")
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)