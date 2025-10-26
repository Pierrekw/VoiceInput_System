#!/usr/bin/env python3
"""
GUI版本音频处理优化方案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem

def test_optimized_gui():
    """测试优化后的GUI版本"""
    print("🔧 测试GUI版本音频处理优化")
    print("=" * 50)

    # 方案1：使用较短的识别时长，定期重启音频流
    print("🚀 方案1：使用较短的识别时长，定期重启音频流")

    system = FunASRVoiceSystem(
        recognition_duration=30,  # 30秒后重新初始化
        continuous_mode=True,   # 仍然是连续模式
        debug_mode=False
    )

    if not system.initialize():
        print("❌ 系统初始化失败")
        return

    print("✅ 开始30秒测试...")
    print("请说话进行测试，30秒后会自动重启")

    # 运行30秒
    try:
        system.run_continuous()
    except:
        pass

    print("✅ 方案1测试完成")

def test_alternative_gui():
    """测试替代方案：使用类命令行模式但保持GUI界面"""
    print("\n🚀 方案2：使用类命令行模式但保持GUI界面")
    print("=" * 50)

    # 方案2：使用与命令行相同的参数
    system = FunASRVoiceSystem(
        recognition_duration=60,  # 与命令行一致
        continuous_mode=False,  # 与命令行一致
        debug_mode=False          # 生产模式
    )

    if not system.initialize():
        print("❌ 系统初始化失败")
        return

    print("✅ 开始60秒测试...")
    print("请说话进行测试...")

    # 运行60秒
    try:
        system.run_continuous()
    except:
        pass

    print("✅ 方案2测试完成")

def compare_with_original():
    """与原始GUI版本对比"""
    print("\n" + "=" * 50)
    print("📊 与原始GUI版本对比")
    print("=" * 50)

    # 原始GUI参数
    print("原始GUI版本参数:")
    print("  recognition_duration=-1")
    print("  continuous_mode=True")
    print("  debug_mode=False")
    print("  问题: 音频输入质量差，识别效果不佳")

    print("\n优化建议:")
    print("1. 使用方案1：较短的识别时长(30秒)，定期重启音频流")
    print("   - 优点: 保持GUI的连续性")
    print("   - 缺点: 会有短暂的中断")
    print("\n2. 使用方案2：类命令行模式(60秒)")
    print("   - 优点: 音频质量与命令行版本一致")
    print("   - 缺点: 60秒后需要重新启动")

    print("\n🎯 推荐: 先测试方案2，如果效果好则修改GUI版本")

if __name__ == "__main__":
    print("🎤 GUI版本音频处理优化")
    print("测试不同的音频处理方案")
    print()

    # 测试方案1
    test_optimized_gui()

    # 测试方案2
    test_alternative_gui()

    # 对比分析
    compare_with_original()

    print("\n✅ 优化测试完成！")
    print("请根据测试结果选择最佳的修复方案")