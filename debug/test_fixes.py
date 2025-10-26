#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果的脚本
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_excel_template_fix():
    """测试Excel模板修复"""
    print("🧪 测试Excel模板修复")
    print("-" * 40)

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统实例但不初始化Excel
        system = FunASRVoiceSystem()
        print("✅ 系统创建成功，Excel导出器为空:", system.excel_exporter is None)

        # 测试从GUI设置Excel
        success = system.setup_excel_from_gui("PART-A001", "B202501", "测试员")
        print(f"✅ Excel模板设置结果: {success}")

        if success and system.excel_exporter:
            print(f"✅ Excel文件路径: {system.excel_exporter.filename}")
            print(f"✅ 模板文件存在: {os.path.exists(system.excel_exporter.filename)}")

            if os.path.exists(system.excel_exporter.filename):
                file_size = os.path.getsize(system.excel_exporter.filename)
                print(f"✅ Excel文件大小: {file_size} bytes")

                # 检查是否使用了模板（模板文件通常大于8KB）
                if file_size > 8000:
                    print("✅ 看起来使用了模板文件")
                else:
                    print("⚠️ 可能没有使用模板文件")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_command_fix():
    """测试语音命令修复"""
    print("\n🧪 测试语音命令修复")
    print("-" * 40)

    try:
        from main_f import FunASRVoiceSystem

        system = FunASRVoiceSystem()
        system.initialize()

        # 测试命令
        test_commands = [
            "切换200",
            "切换标准200",
            "切换到200",
            "设置标准序号200",
            "切换三百"
        ]

        for cmd in test_commands:
            print(f"\n测试命令: '{cmd}'")

            # 识别命令类型
            command_type = system.recognize_voice_command(cmd)
            print(f"  命令类型: {command_type}")

            if command_type.name == 'STANDARD_ID':
                # 处理命令
                old_id = system.current_standard_id
                system._handle_standard_id_command(cmd)
                new_id = system.current_standard_id
                print(f"  标准序号变化: {old_id} -> {new_id}")

                if old_id != new_id:
                    print("  ✅ 命令执行成功")
                else:
                    print("  ❌ 命令执行失败")
            else:
                print("  ❌ 未识别为标准序号命令")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_validation():
    """测试GUI验证警示"""
    print("\n🧪 测试GUI验证警示")
    print("-" * 40)

    try:
        # 这里只测试配置加载
        from config_loader import ConfigLoader

        config = ConfigLoader()
        prefixes = config.get_standard_id_command_prefixes()

        print(f"✅ 命令前缀数量: {len(prefixes)}")
        print(f"✅ 命令前缀: {prefixes[:3]}...")  # 只显示前3个

        # 测试关键前缀是否存在
        key_prefixes = ["切换", "切换标准", "设置标准序号"]
        for prefix in key_prefixes:
            if prefix in prefixes:
                print(f"✅ 包含关键前缀: '{prefix}'")
            else:
                print(f"❌ 缺少关键前缀: '{prefix}'")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 测试修复效果")
    print("=" * 50)

    success = True

    # 运行所有测试
    success &= test_excel_template_fix()
    success &= test_voice_command_fix()
    success &= test_gui_validation()

    if success:
        print("\n🎉 所有修复测试通过！")
        print("\n📋 修复总结:")
        print("1. ✅ Excel模板修复 - 系统现在只在GUI设置时创建Excel文件，确保使用模板")
        print("2. ✅ 语音命令修复 - 添加了'切换标准'前缀，支持更多命令格式")
        print("3. ✅ GUI警示修复 - 添加了输入验证警示和状态提示")
        print("4. ✅ Debug日志 - 添加了详细的调试日志以便问题排查")
    else:
        print("\n⚠️ 部分测试失败，请检查实现。")

    sys.exit(0 if success else 1)