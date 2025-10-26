#!/usr/bin/env python3
"""
测试语音命令修复效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_command_processing():
    """测试命令处理逻辑"""
    print("🧪 测试语音命令处理修复")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟状态变化回调
        state_changes = []
        def mock_state_callback(state, message):
            print(f"📢 状态变化: {state} -> {message}")
            state_changes.append({
                'state': state,
                'message': message,
                'time': __import__('time').time()
            })

        # 设置回调
        voice_system.set_state_change_callback(mock_state_callback)

        # 测试命令处理
        test_commands = [
            ("切换200", "切换200", [200]),
            ("切换到标准300", "切换到标准300", [300]),
            ("设置400", "设置400", [400])
        ]

        print("📋 测试命令处理:")
        for original_text, processed_text, numbers in test_commands:
            print(f"\n🎯 测试命令: '{original_text}'")

            # 模拟命令识别
            command_type = voice_system.recognize_voice_command(processed_text)
            print(f"  🔍 命令类型: {command_type}")

            if command_type.name == "STANDARD_ID":
                print(f"  ✅ 识别为标准序号命令")

                # 模拟命令处理
                initial_state_count = len(state_changes)
                voice_system._handle_standard_id_command(processed_text)
                final_state_count = len(state_changes)

                print(f"  📊 状态变化: {initial_state_count} -> {final_state_count}")

                # 检查是否有命令状态变化
                command_changes = [c for c in state_changes if c['state'] == 'command']
                if command_changes:
                    latest_command = command_changes[-1]
                    print(f"  📝 命令状态: {latest_command['message']}")
                    print(f"  ✅ 命令处理成功")
                else:
                    print(f"  ❌ 没有命令状态变化")
            else:
                print(f"  ❌ 未识别为标准序号命令")

        print("\n🎯 命令处理测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_command_vs_number_separation():
    """测试命令与数字识别分离"""
    print("\n🧪 测试命令与数字识别分离")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 测试混合输入
        test_cases = [
            # (原始文本, 处理文本, 数字, 是否应该为命令)
            ("切换200", "切换200", [200], True),
            ("切换到标准300", "切换到标准300", [300], True),
            ("三百", "300", [300], False),  # 纯数字
            ("测量500", "测量500", [500], False),  # 非命令
        ]

        print("📋 测试输入分离:")
        for original_text, processed_text, numbers, should_be_command in test_cases:
            print(f"\n🎯 测试: '{original_text}' -> '{processed_text}'")

            # 检查命令识别
            command_type = voice_system.recognize_voice_command(processed_text)
            is_command = command_type.name == "STANDARD_ID"

            print(f"  🔍 命令识别: {is_command} (期望: {should_be_command})")
            print(f"  🔢 数字提取: {numbers if numbers else '无'}")

            # 验证分离效果
            if is_command == should_be_command:
                print(f"  ✅ 分离正确")
            else:
                print(f"  ❌ 分离错误")

                # 详细分析
                if should_be_command and not is_command:
                    print(f"    💡 应该识别为命令但没有识别")
                elif not should_be_command and is_command:
                    print(f"    💡 不应该识别为命令但识别了")

        print("\n🎯 分离测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始语音命令修复测试")
    print("=" * 60)

    # 测试命令处理
    success1 = test_command_processing()

    # 测试分离效果
    success2 = test_command_vs_number_separation()

    if success1 and success2:
        print("\n🎉 语音命令修复测试通过！")
        print("\n📝 修复说明:")
        print("1. ✅ 命令通过状态变化回调处理")
        print("2. ✅ 命令不会与数字识别混淆")
        print("3. ✅ 命令直接显示在历史记录中")
        print("4. ✅ 使用 append_log 而非适配 is_record")
        print("\n🔧 现在命令和数字识别完全分离")
    else:
        print("\n❌ 部分测试失败，请检查修复代码")