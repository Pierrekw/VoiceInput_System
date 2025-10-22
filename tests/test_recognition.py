#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语音识别回调功能
"""

import os
import time

# 抑制输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

def test_recognition_callback():
    """测试识别回调"""
    print("🔍 测试语音识别回调...")

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统
        voice_system = FunASRVoiceSystem()
        print("✅ 语音系统创建成功")

        # 初始化
        if voice_system.initialize():
            print("✅ 语音系统初始化成功")

            # 设置自定义回调
            def custom_callback(result):
                print(f"🎯 收到识别结果: {result}")
                if hasattr(result, 'text'):
                    print(f"📝 文本: {result.text}")
                else:
                    print(f"📝 原始结果: {result}")

            # 尝试设置回调
            if hasattr(voice_system, 'recognizer'):
                voice_system.recognizer.set_callbacks(on_final_result=custom_callback)
                print("✅ 回调设置成功")

                # 开始短时间识别测试
                print("🎙️ 开始5秒识别测试...")
                voice_system.start_recognition()

                # 等待5秒
                time.sleep(5)

                print("🛑 停止识别测试")
                voice_system.stop()

            else:
                print("❌ 无法找到recognizer")

        else:
            print("❌ 语音系统初始化失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_direct_recognizer():
    """直接测试识别器"""
    print("\n🔍 直接测试识别器...")

    try:
        from funasr_voice_module import FunASRVoiceRecognizer

        recognizer = FunASRVoiceRecognizer()
        print("✅ 识别器创建成功")

        if recognizer.initialize():
            print("✅ 识别器初始化成功")

            def callback(result):
                print(f"🎯 直接识别结果: {result}")

            recognizer.set_callbacks(on_final_result=callback)
            print("✅ 直接回调设置成功")

            # 短时间识别
            result = recognizer.recognize_speech(duration=3)
            print(f"📝 最终结果: {result}")

        else:
            print("❌ 识别器初始化失败")

    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 语音识别回调测试")
    print("=" * 50)

    test_recognition_callback()
    test_direct_recognizer()

    print("\n✅ 测试完成")