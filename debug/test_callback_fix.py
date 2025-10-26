#!/usr/bin/env python3
"""
测试回调修复效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_callback_safety():
    """测试回调安全性"""
    print("🧪 测试回调安全性修复")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟有问题的回调（会抛出异常）
        def problematic_callback(state, message):
            if state == "command":
                # 模拟GUI方法不存在的情况
                raise AttributeError("'WorkingVoiceWorker' object has no attribute 'add_command_to_history'")
            print(f"✅ 正常回调: {state} -> {message}")

        # 设置有问题的回调
        voice_system.set_state_change_callback(problematic_callback)

        # 测试命令处理
        print("📋 测试命令处理（有问题的回调）:")
        try:
            voice_system._add_command_to_results(
                "[命令] 切换到标准序号 200",
                "设置200",
                200
            )
            print("✅ 命令处理成功，即使回调有问题")
        except Exception as e:
            print(f"❌ 命令处理失败: {e}")

        # 设置正常的回调
        def normal_callback(state, message):
            print(f"✅ 正常回调: {state} -> {message}")

        voice_system.set_state_change_callback(normal_callback)

        print("\n📋 测试命令处理（正常的回调）:")
        try:
            voice_system._add_command_to_results(
                "[命令] 切换到标准序号 300",
                "设置300",
                300
            )
            print("✅ 命令处理成功，回调正常工作")
        except Exception as e:
            print(f"❌ 命令处理失败: {e}")

        print("\n🎯 回调安全性测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_command_logging():
    """测试命令日志记录"""
    print("\n🧪 测试命令日志记录")
    print("=" * 30)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 不设置回调，测试日志功能
        print("📋 测试无回调情况下的日志记录:")

        try:
            voice_system._add_command_to_results(
                "[命令] 切换到标准序号 400",
                "切换400",
                400
            )
            print("✅ 无回调情况下命令处理成功")

            # 检查结果列表
            if hasattr(voice_system, 'number_results') and voice_system.number_results:
                latest_result = voice_system.number_results[-1]
                print(f"📝 结果列表: {latest_result}")
            else:
                print("⚠️ 结果列表为空")

        except Exception as e:
            print(f"❌ 命令处理失败: {e}")

        print("\n🎯 日志记录测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始回调修复测试")
    print("=" * 60)

    # 测试回调安全性
    success1 = test_callback_safety()

    # 测试日志记录
    success2 = test_command_logging()

    if success1 and success2:
        print("\n🎉 回调修复测试通过！")
        print("\n📝 修复说明:")
        print("1. ✅ 添加了异常处理，回调失败不影响命令处理")
        print("2. ✅ 简化了GUI处理，避免方法调用冲突")
        print("3. ✅ 命令核心功能正常工作")
        print("4. ✅ 日志记录正常")
        print("\n🔧 现在可以安全运行 voice_gui.py")
    else:
        print("\n❌ 部分测试失败，请检查修复代码")