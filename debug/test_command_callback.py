#!/usr/bin/env python3
"""
测试命令回调功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_command_callback():
    """测试命令回调功能"""
    print("🧪 测试命令回调功能")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟GUI回调
        callback_received = []
        def mock_callback(state, message):
            callback_received.append({
                'state': state,
                'message': message,
                'time': __import__('time').time()
            })
            print(f"📡 回调触发: state='{state}', message='{message}'")

        # 设置状态变化回调
        voice_system.set_state_change_callback(mock_callback)
        print("✅ 状态变化回调已设置")

        # 测试命令处理
        print("\n📋 测试标准序号命令:")
        test_commands = [
            ("设置200", 200),
            ("切换300", 300),
        ]

        for original_text, expected_id in test_commands:
            print(f"\n🎯 测试命令: '{original_text}' (期望ID: {expected_id})")

            # 清空回调记录
            callback_received.clear()

            # 处理命令
            voice_system._handle_standard_id_command(original_text)

            # 检查回调是否被触发
            if callback_received:
                latest_callback = callback_received[-1]
                print(f"  ✅ 回调已触发")
                print(f"  📝 状态: {latest_callback['state']}")
                print(f"  📝 消息: {latest_callback['message']}")

                # 检查消息格式
                message = latest_callback['message']
                if '🎤 [CMD]' in message and '🎤 语音命令:' in message:
                    print(f"  ✅ 消息格式正确")
                else:
                    print(f"  ❌ 消息格式不正确")

                # 检查是否包含期望的ID
                if str(expected_id) in message:
                    print(f"  ✅ 包含期望的ID: {expected_id}")
                else:
                    print(f"  ❌ 不包含期望的ID: {expected_id}")
            else:
                print(f"  ❌ 回调未触发")

        print("\n🎯 命令回调测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始命令回调测试")
    print("=" * 60)
    test_command_callback()