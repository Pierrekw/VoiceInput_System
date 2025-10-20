#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI调试工具
帮助诊断GUI中识别结果不显示的问题
"""

import sys
import os
import time
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_voice_system():
    """测试语音系统"""
    print("🔍 测试语音系统...")

    try:
        from main_f import FunASRVoiceSystem
        voice_system = FunASRVoiceSystem()

        print("✅ FunASRVoiceSystem 导入成功")

        # 测试初始化
        if voice_system.initialize():
            print("✅ 语音系统初始化成功")

            # 检查recognizer
            if hasattr(voice_system, 'recognizer'):
                print("✅ recognizer 存在")

                # 测试回调设置
                def test_callback(result):
                    print(f"📞 测试回调被调用: {result}")

                try:
                    voice_system.recognizer.set_callbacks(on_final_result=test_callback)
                    print("✅ 回调设置成功")
                except Exception as e:
                    print(f"❌ 回调设置失败: {e}")
            else:
                print("❌ recognizer 不存在")
        else:
            print("❌ 语音系统初始化失败")

    except Exception as e:
        print(f"❌ 语音系统测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_simple_recognition():
    """测试简单识别"""
    print("\n🔍 测试简单识别...")

    try:
        from funasr_voice_module import FunASRVoiceRecognizer

        recognizer = FunASRVoiceRecognizer()
        print("✅ FunASRVoiceRecognizer 导入成功")

        if recognizer.initialize():
            print("✅ 识别器初始化成功")

            # 测试短时间识别
            print("🎙️ 开始3秒测试识别...")
            result = recognizer.recognize_speech(duration=3)

            if result and hasattr(result, 'text'):
                print(f"✅ 识别结果: {result.text}")
            else:
                print("⚠️ 无识别结果或结果格式异常")

        else:
            print("❌ 识别器初始化失败")

    except Exception as e:
        print(f"❌ 简单识别测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_gui_components():
    """测试GUI组件"""
    print("\n🔍 测试GUI组件...")

    try:
        from PySide6.QtWidgets import QApplication
        from voice_gui import VoiceRecognitionThread, MainWindow

        # 创建应用
        app = QApplication([])
        print("✅ QApplication 创建成功")

        # 测试工作线程
        thread = VoiceRecognitionThread()
        print("✅ VoiceRecognitionThread 创建成功")

        # 测试主窗口
        window = MainWindow()
        print("✅ MainWindow 创建成功")

        # 测试信号连接
        test_messages = []

        def test_log(msg):
            test_messages.append(msg)
            print(f"📝 日志信号: {msg}")

        def test_result(text, result_type, confidence):
            print(f"🎯 结果信号: {text} ({result_type})")

        thread.log_message.connect(test_log)
        thread.recognition_result.connect(test_result)

        print("✅ 信号连接成功")

        # 不显示窗口，直接退出
        app.quit()

    except Exception as e:
        print(f"❌ GUI组件测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🧪 GUI调试工具")
    print("=" * 50)

    # 抑制输出
    os.environ['TQDM_DISABLE'] = '1'
    os.environ['PYTHONWARNINGS'] = 'ignore'
    os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

    # 测试各个组件
    test_voice_system()
    test_simple_recognition()
    test_gui_components()

    print("\n✅ 调试测试完成")
    print("\n如果所有测试都通过，问题可能在于:")
    print("1. 音频设备权限")
    print("2. 麦克风硬件")
    print("3. GUI线程与语音识别线程的同步")
    print("4. 回调函数的调用时机")

if __name__ == "__main__":
    main()