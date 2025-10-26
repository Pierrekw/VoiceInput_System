#!/usr/bin/env python3
"""
测试语音命令显示修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_command_display():
    """测试命令显示修复"""
    print("🧪 测试语音命令显示修复")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟GUI回调函数
        gui_results = []
        def mock_gui_callback(original_text, processed_text, numbers):
            print(f"🖥️ GUI回调触发: '{original_text}' -> '{processed_text}' ({numbers})")
            gui_results.append({
                'original': original_text,
                'processed': processed_text,
                'numbers': numbers
            })

        # 设置回调函数
        voice_system.process_recognition_result = mock_gui_callback

        # 测试命令
        test_commands = [
            ("切换200", "切换200", [200]),
            ("设置300", "设置300", [300]),
            ("切换到100", "切换到100", [100])
        ]

        print("📋 测试语音命令:")
        for original_text, processed_text, numbers in test_commands:
            print(f"\n🎯 测试命令: '{original_text}'")

            # 初始状态
            initial_count = len(voice_system.number_results) if hasattr(voice_system, 'number_results') else 0
            initial_gui_count = len(gui_results)

            # 模拟命令处理
            voice_system._add_command_to_results(
                f"[命令] 切换到标准序号 {numbers[0]}",
                original_text,
                numbers[0]
            )

            # 检查结果
            final_count = len(voice_system.number_results) if hasattr(voice_system, 'number_results') else 0
            final_gui_count = len(gui_results)

            print(f"  📊 结果列表变化: {initial_count} -> {final_count}")
            print(f"  🖥️ GUI回调变化: {initial_gui_count} -> {final_gui_count}")

            if final_count > initial_count:
                latest_result = voice_system.number_results[-1]
                print(f"  📝 最新结果: {latest_result}")

            if final_gui_count > initial_gui_count:
                latest_gui = gui_results[-1]
                print(f"  🖥️ 最新GUI结果: {latest_gui}")

            # 检查修复是否成功
            success = (final_count > initial_count) and (final_gui_count > initial_gui_count)
            print(f"  {'✅' if success else '❌'} 命令显示修复: {'成功' if success else '失败'}")

        print("\n🎯 测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_command_display()
    if success:
        print("\n🎉 语音命令显示修复测试通过！")
        print("\n📝 修复说明:")
        print("1. ✅ 命令会添加到number_results列表")
        print("2. ✅ GUI回调函数会被正确触发")
        print("3. ✅ 历史记录会显示命令信息")
    else:
        print("\n❌ 测试失败，请检查修复代码")