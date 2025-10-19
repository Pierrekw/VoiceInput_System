#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FunASR主程序核心功能
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试FunASR语音系统")
    print("=" * 40)

    # 创建系统实例
    system = FunASRVoiceSystem(
        recognition_duration=10,  # 10秒测试
        continuous_mode=False      # 单次模式
    )

    # 初始化
    print("⏳ 初始化系统...")
    if not system.initialize():
        print("❌ 初始化失败")
        return

    print("✅ 初始化成功")
    print("\n📖 测试说明:")
    print("  • 请说话测试语音识别")
    print("  • 10秒后自动结束")
    print("  • 测试语音命令：'暂停'、'继续'、'停止'")
    print("-" * 40)

    try:
        # 运行单次识别
        system.run_recognition_cycle()

        # 显示结果
        system.show_results_summary()

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")