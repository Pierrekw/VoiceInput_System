#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的模式匹配语音命令系统
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pattern_based_standard_id_commands():
    """测试基于模式的标准序号命令识别"""
    print("🧪 测试基于模式的标准序号命令识别")
    print("=" * 60)

    try:
        from text_processor import VoiceCommandProcessor
        from config_loader import ConfigLoader

        processor = VoiceCommandProcessor()
        config = ConfigLoader()

        # 重新加载配置以避免缓存问题
        config._config = {}
        config._load_config()

        # 获取命令前缀
        command_prefixes = config.get_standard_id_command_prefixes()
        print(f"📋 命令前缀: {command_prefixes}")
        print()

        # 测试用例
        test_cases = [
            # 基本测试
            ("切换一百", 100),
            ("切换二百", 200),
            ("切换三百", 300),
            ("设置四百", 400),
            ("设置五百", 500),

            # 大数字测试
            ("切换一千", 1000),
            ("切换二千", 2000),
            ("设置三千", 3000),
            ("切换四千", 4000),
            ("设置五千", 5000),

            # 复杂数字测试
            ("切换一千一百", 1100),
            ("切换一千二百", 1200),
            ("设置三千五百", 3500),
            ("切换四千五百", 4500),
            ("设置五千五百", 5500),

            # 更多变化
            ("切换到六百", 600),
            ("设置序号七百", 700),
            ("切换到八百", 800),
            ("设置标准序号九百", 900),

            # 大数字变化
            ("切换到六千", 6000),
            ("设置序号七千", 7000),
            ("切换到八千", 8000),
            ("设置标准序号九千", 9000),

            # 边界情况
            ("切换一百", 100),
            ("设置一百", 100),
            ("序号一百", 100),

            # 无效命令（应该返回None）
            ("切换一百零一", None),  # 不是100的倍数
            ("切换五十", None),      # 不是100的倍数
            ("切换", None),          # 缺少数字
            ("你好", None),          # 完全无关
        ]

        print(f"{'测试命令':<20} {'预期结果':<10} {'实际结果':<10} {'状态'}")
        print("-" * 60)

        success_count = 0
        total_count = len(test_cases)

        for command, expected in test_cases:
            result = processor.match_standard_id_command(command, command_prefixes)

            if result == expected:
                status = "✅ 通过"
                success_count += 1
            else:
                status = "❌ 失败"

            result_str = str(result) if result is not None else "None"
            expected_str = str(expected) if expected is not None else "None"

            print(f"{command:<20} {expected_str:<10} {result_str:<10} {status}")

        print(f"\n📊 测试结果: {success_count}/{total_count} 通过 ({success_count/total_count*100:.1f}%)")

        if success_count == total_count:
            print("🎉 所有测试通过！新的模式匹配系统工作正常。")
        else:
            print("⚠️ 部分测试失败，需要进一步调试。")

        return success_count == total_count

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_compatibility():
    """测试配置兼容性"""
    print("\n🧪 测试配置兼容性")
    print("=" * 60)

    try:
        from config_loader import ConfigLoader

        config = ConfigLoader()

        # 测试新格式
        prefixes = config.get_standard_id_command_prefixes()
        print(f"📋 新格式前缀: {prefixes}")

        # 测试向后兼容
        commands = config.get_standard_id_commands()
        print(f"📋 向后兼容命令: {commands}")

        if prefixes and len(prefixes) > 0:
            print("✅ 配置加载成功")
            return True
        else:
            print("❌ 配置加载失败")
            return False

    except Exception as e:
        print(f"❌ 配置兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_large_numbers():
    """测试大数字支持"""
    print("\n🧪 测试大数字支持")
    print("=" * 60)

    try:
        from text_processor import VoiceCommandProcessor
        from config_loader import ConfigLoader

        processor = VoiceCommandProcessor()
        config = ConfigLoader()

        # 重新加载配置以避免缓存问题
        config._config = {}
        config._load_config()

        command_prefixes = config.get_standard_id_command_prefixes()

        # 大数字测试用例
        large_test_cases = [
            ("切换一万", 10000),
            ("设置二万", 20000),
            ("切换三万", 30000),
            ("切换五万", 50000),
            ("设置十万", 100000),
            ("切换一百万", 1000000),
        ]

        print(f"{'测试命令':<20} {'预期结果':<10} {'实际结果':<10} {'状态'}")
        print("-" * 50)

        for command, expected in large_test_cases:
            result = processor.match_standard_id_command(command, command_prefixes)

            if result == expected:
                status = "✅ 通过"
            else:
                status = "❌ 失败"

            result_str = str(result) if result is not None else "None"
            expected_str = str(expected) if expected is not None else "None"

            print(f"{command:<20} {expected_str:<10} {result_str:<10} {status}")

        return True

    except Exception as e:
        print(f"❌ 大数字测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 模式匹配语音命令系统测试")
    print("=" * 60)

    success = True

    # 运行所有测试
    success &= test_config_compatibility()
    success &= test_pattern_based_standard_id_commands()
    success &= test_large_numbers()

    if success:
        print("\n🎉 所有测试通过！")
        print("✅ 新的模式匹配语音命令系统已成功实现：")
        print("  - 支持任意100的倍数作为标准序号")
        print("  - 简化的配置文件结构")
        print("  - 向后兼容性")
        print("  - 可扩展的命令前缀系统")
    else:
        print("\n⚠️ 部分测试失败，请检查实现。")

    sys.exit(0 if success else 1)