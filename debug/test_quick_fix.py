#!/usr/bin/env python3
"""
快速测试修复效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem

def test_fix():
    """测试修复效果"""
    print("🎤 测试修复效果 - 禁用FFmpeg预处理")
    print("=" * 50)

    # 模拟GUI版本参数
    system = FunASRVoiceSystem(
        recognition_duration=-1,
        continuous_mode=True,
        debug_mode=False
    )

    if not system.initialize():
        print("❌ 系统初始化失败")
        return

    print("✅ 开始5秒测试...")
    print("请说话进行测试...")

    # 临时修改为5秒测试
    original_duration = system.recognition_duration
    original_continuous = system.continuous_mode
    system.recognition_duration = 5
    system.continuous_mode = False

    try:
        system.run_continuous()
    except:
        pass
    finally:
        # 恢复原始参数
        system.recognition_duration = original_duration
        system.continuous_mode = original_continuous

    print("✅ 测试完成！")

if __name__ == "__main__":
    test_fix()