#!/usr/bin/env python3
"""
测试修复后的GUI参数效果
使用与GUI修复后相同的参数进行测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_gui_params():
    """测试修复后的GUI参数"""
    print("🎤 测试修复后的GUI参数")
    print("=" * 50)
    print("使用参数:")
    print("  recognition_duration=60  (与命令行版本一致)")
    print("  continuous_mode=False    (与命令行版本一致)")
    print("  debug_mode=False         (GUI生产模式)")
    print()

    # 使用修复后的参数
    system = FunASRVoiceSystem(
        recognition_duration=60,   # 60秒识别时长（与命令行版本一致）
        continuous_mode=False,     # 批次模式（与命令行版本一致）
        debug_mode=False           # 调式模式
    )

    if not system.initialize():
        print("❌ 系统初始化失败")
        return False

    print("✅ 开始15秒测试（缩短测试时间）...")
    print("请说话进行测试...")
    print()

    # 临时修改为15秒测试以便快速验证
    original_duration = system.recognition_duration
    system.recognition_duration = 15

    start_time = time.time()
    try:
        system.run_continuous()
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        return False
    finally:
        # 恢复原始参数
        system.recognition_duration = original_duration

    duration = time.time() - start_time
    print(f"\n✅ 测试完成，实际运行时间: {duration:.1f}秒")

    # 检查识别结果
    if hasattr(system, 'number_results') and system.number_results:
        print(f"📊 识别到 {len(system.number_results)} 条结果")
        for i, (record_id, record_number, record_text) in enumerate(system.number_results):
            print(f"  {i+1}. ID:{record_id}, 数字:{record_number}, 文本:{record_text}")
    else:
        print("📊 未识别到语音内容（可能没有说话或声音太小）")

    return True

def compare_with_original():
    """与原始GUI参数对比"""
    print("\n" + "=" * 50)
    print("📊 参数对比")
    print("=" * 50)

    print("原始GUI参数:")
    print("  recognition_duration=-1  (无限时长)")
    print("  continuous_mode=True    (连续模式)")
    print("  问题: 音频质量差，识别效果不佳")
    print()

    print("修复后GUI参数:")
    print("  recognition_duration=60  (60秒时长)")
    print("  continuous_mode=False    (批次模式)")
    print("  优势: 与命令行版本相同的音频质量")
    print()

    print("实现方式:")
    print("  - 使用与命令行版本相同的音频处理参数")
    print("  - 通过循环实现GUI的连续性")
    print("  - 每60秒自动重启音频流，保持音频质量")

if __name__ == "__main__":
    print("🔧 GUI音频质量修复验证")
    print("测试修改后的参数是否能解决识别质量问题\n")

    success = test_fixed_gui_params()

    if success:
        compare_with_original()
        print("\n🎉 修复验证完成！")
        print("如果测试中识别效果良好，说明修复成功。")
        print("现在GUI版本应该具有与命令行版本相同的识别质量。")
    else:
        print("\n❌ 修复验证失败")
        print("请检查模型路径和系统配置。")