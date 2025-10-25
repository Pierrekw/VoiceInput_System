#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEN VAD 简单测试脚本
测试TEN VAD是否能正常加载和工作
"""

import os
import sys
import numpy as np
import time

def test_ten_vad():
    """测试TEN VAD功能"""
    print("🔧 TEN VAD 简单测试")
    print("=" * 40)

    try:
        # 设置TEN VAD路径
        ten_vad_path = "F:/04_AI/01_Workplace/ten-vad"
        if os.path.exists(ten_vad_path):
            sys.path.insert(0, os.path.join(ten_vad_path, "include"))
            print(f"✅ TEN VAD路径: {ten_vad_path}")
        else:
            print(f"❌ TEN VAD路径不存在: {ten_vad_path}")
            return False

        # 导入TEN VAD
        from ten_vad import TenVad
        print("✅ TEN VAD模块导入成功")

        # 创建TEN VAD实例
        ten_vad = TenVad(hop_size=256, threshold=0.5)
        print("✅ TEN VAD实例创建成功 (hop_size=256, threshold=0.5)")

        # 测试音频数据 (16位整数，256样本)
        print("\n🧪 测试TEN VAD处理...")

        # 生成测试音频数据
        # 1. 静音数据 (接近0的值)
        silence_audio = np.zeros(256, dtype=np.int16)
        print("\n🔇 测试静音音频:")
        prob, flag = ten_vad.process(silence_audio)
        print(f"   置信度: {prob:.6f}, 标志: {flag}")

        # 2. 模拟语音数据 (随机值模拟音频)
        speech_audio = np.random.randint(-1000, 1000, 256, dtype=np.int16)
        print("\n🎤 测试模拟语音音频:")
        prob, flag = ten_vad.process(speech_audio)
        print(f"   置信度: {prob:.6f}, 标志: {flag}")

        # 3. 测试连续处理 (模拟实时流)
        print("\n🔄 测试连续音频流处理...")
        speech_count = 0
        total_count = 10

        for i in range(total_count):
            # 交替生成静音和语音
            if i % 3 == 0:
                # 语音段
                test_audio = np.random.randint(-2000, 2000, 256, dtype=np.int16)
            else:
                # 静音段
                test_audio = np.random.randint(-100, 100, 256, dtype=np.int16)

            prob, flag = ten_vad.process(test_audio)
            if flag == 1:
                speech_count += 1
                print(f"   帧 {i+1}: 🎤 语音 (置信度: {prob:.6f})")
            else:
                print(f"   帧 {i+1}: 🔇 静音 (置信度: {prob:.6f})")

        print(f"\n📊 统计结果:")
        print(f"   总帧数: {total_count}")
        print(f"   语音帧数: {speech_count}")
        print(f"   静音帧数: {total_count - speech_count}")
        print(f"   语音比例: {speech_count/total_count*100:.1f}%")

        print("\n✅ TEN VAD测试完成")
        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 建议检查:")
        print("  1. ten-vad/include/ten_vad.py 是否存在")
        print("  2. numpy 是否已安装")
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")

    # 检查numpy
    try:
        import numpy as np
        print(f"✅ numpy: {np.__version__}")
    except ImportError:
        print("❌ numpy: 未安装")
        return False

    # 检查TEN VAD动态库
    dll_path = "F:/04_AI/01_Workplace/ten-vad/lib/Windows/x64/ten_vad.dll"
    if os.path.exists(dll_path):
        print(f"✅ TEN VAD DLL: {dll_path}")
    else:
        print(f"❌ TEN VAD DLL: {dll_path}")
        return False

    return True

if __name__ == "__main__":
    print("🎯 TEN VAD 集成测试")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的依赖")
        sys.exit(1)

    print("\n🧪 开始功能测试...")

    # 测试TEN VAD
    if test_ten_vad():
        print("\n🎉 TEN VAD 集成成功！")
        print("\n💡 下一步:")
        print("  1. 在FunASR中集成TEN VAD")
        print("  2. 测试实时语音识别")
        print("  3. 比较不同VAD的性能")
    else:
        print("\n❌ TEN VAD 集成失败")
        print("\n💡 解决建议:")
        print("  1. 检查TEN VAD安装")
        print("  2. 确认Python环境兼容性")
        print("  3. 检查动态库依赖")
        sys.exit(1)