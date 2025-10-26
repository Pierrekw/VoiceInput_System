#!/usr/bin/env python3
"""
测试TEN VAD模块停止功能修复
"""

import sys
import os
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from funasr_voice_TENVAD import FunASRVoiceRecognizer

def test_stop_fix():
    """测试停止功能修复"""
    print("=== 测试TEN VAD模块停止功能修复 ===")

    # 创建识别器
    recognizer = FunASRVoiceRecognizer()

    # 启动识别
    print("1. 初始化识别器...")
    if not recognizer.initialize():
        print("❌ 识别器初始化失败")
        return

    print("✅ 识别器初始化成功")

    # 启动连续识别
    print("2. 启动连续识别...")
    thread = recognizer.start_continuous_recognition()

    # 等待系统启动
    print("   等待5秒...")
    time.sleep(5)

    # 测试停止
    print("3. 测试停止功能...")
    print("   调用stop_recognition()...")
    start_time = time.time()

    recognizer.stop_recognition()

    # 等待线程结束
    print("4. 等待线程结束...")
    if thread.is_alive():
        thread.join(timeout=3)
        if thread.is_alive():
            print("   ❌ 线程仍在运行")
        else:
            elapsed = time.time() - start_time
            print(f"   ✅ 线程在{elapsed:.1f}秒内正常结束")
    else:
        elapsed = time.time() - start_time
        print(f"   ✅ 线程已快速结束 ({elapsed:.1f}秒)")

    print("\n=== 停止功能测试完成 ===")

if __name__ == "__main__":
    test_stop_fix()