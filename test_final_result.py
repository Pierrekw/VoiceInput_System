#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试最终识别结果获取
"""

import asyncio
import sys
import os
import time
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

async def test_final_result():
    """测试最终识别结果获取"""
    print("测试最终识别结果获取...")
    print("=" * 50)
    print("请对着麦克风说话，然后等待系统停止...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture

        # 创建音频捕获器
        capture = AsyncAudioCapture(model_path="model/cn", test_mode=False)

        print("1. 初始化音频捕获器...")
        success = await capture.initialize()
        print(f"   初始化结果: {success}")

        if not success:
            print("   [ERROR] 初始化失败")
            return False

        print("2. 开始语音识别...")
        start_result = await capture.start_recognition()
        print(f"   开始结果: {start_result.final_text}")

        print("3. 录音5秒，请说话...")
        await asyncio.sleep(5)

        print("4. 停止语音识别...")
        stop_result = await capture.stop_recognition()
        print(f"   停止结果: '{stop_result.final_text}'")

        print("5. 清理...")
        await capture.cleanup()

        print(f"\n6. 测试结果:")
        if stop_result.final_text and stop_result.final_text != "Recognition stopped successfully":
            print(f"   [SUCCESS] 获得最终识别结果: '{stop_result.final_text}'")
            return True
        else:
            print(f"   [INFO] 停止结果: '{stop_result.final_text}'")
            print("   [WARN] 没有获得有效的最终识别结果")
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("开始最终识别结果测试...")
    print("=" * 50)

    # 测试最终结果
    success = await test_final_result()

    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] 最终识别结果测试成功！")
    else:
        print("[INFO] 最终识别结果测试完成，但没有识别到语音")

if __name__ == "__main__":
    asyncio.run(main())