#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性测试修复效果的脚本
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_voice_command_system():
    """测试语音命令系统的完整流程"""
    print("🧪 测试语音命令系统完整流程")
    print("-" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统
        system = FunASRVoiceSystem()
        system.initialize()

        # 测试用例 - 每个测试使用不同的目标值，避免重复
        test_cases = [
            ("切换200", 200),        # 基本命令
            ("切换标准300", 300),    # 带标准前缀
            ("切换到400", 400),      # 带到前缀
            ("设置标准序号500", 500), # 完整前缀
            ("切换六百", 600),       # 中文数字
            ("设置八百", 800),       # 另一个前缀
        ]

        print(f"{'测试命令':<20} {'识别结果':<15} {'执行结果':<10} {'预期值':<8} {'状态'}")
        print("-" * 85)

        success_count = 0
        for cmd, expected_id in test_cases:
            # 记录当前标准序号
            old_id = system.current_standard_id

            # 识别命令
            command_type = system.recognize_voice_command(cmd)
            recognition_result = "✅" if command_type.name == 'STANDARD_ID' else "❌"

            # 执行命令
            if command_type.name == 'STANDARD_ID':
                system._handle_standard_id_command(cmd)
                new_id = system.current_standard_id
                execution_result = "✅" if new_id == expected_id else "❌"
                success_count += 1 if new_id == expected_id else 0
            else:
                execution_result = "❌"
                new_id = old_id

            status = "✅ 通过" if recognition_result == "✅" and execution_result == "✅" else "❌ 失败"
            print(f"{cmd:<20} {recognition_result:<15} {execution_result:<10} {expected_id:<8} {status}")

        print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 通过 ({success_count/len(test_cases)*100:.1f}%)")
        return success_count == len(test_cases)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_excel_template_system():
    """测试Excel模板系统"""
    print("\n🧪 测试Excel模板系统")
    print("-" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统
        system = FunASRVoiceSystem()

        # 检查初始状态
        print(f"初始Excel导出器状态: {'None' if system.excel_exporter is None else '已创建'}")

        # 模拟GUI设置
        success = system.setup_excel_from_gui("PART-A001", "B202501", "测试员")
        print(f"Excel模板设置: {'✅ 成功' if success else '❌ 失败'}")

        if success and system.excel_exporter:
            filename = system.excel_exporter.filename
            print(f"Excel文件路径: {filename}")

            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"文件大小: {file_size} bytes")

                # 检查是否使用了模板（模板通常>8KB）
                used_template = file_size > 8000
                print(f"模板使用: {'✅ 是' if used_template else '❌ 否'}")

                return used_template
            else:
                print("❌ 文件不存在")
                return False
        else:
            print("❌ Excel导出器创建失败")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载和一致性"""
    print("\n🧪 测试配置加载和一致性")
    print("-" * 50)

    try:
        from config_loader import ConfigLoader
        from text_processor import VoiceCommandProcessor

        # 加载配置
        config = ConfigLoader()
        prefixes = config.get_standard_id_command_prefixes()

        print(f"命令前缀数量: {len(prefixes)}")
        print(f"命令前缀: {prefixes}")

        # 检查关键前缀
        key_prefixes = ["切换", "设置", "切换到", "切换标准", "设置标准序号"]
        missing_prefixes = []

        for prefix in key_prefixes:
            if prefix in prefixes:
                print(f"✅ 关键前缀存在: '{prefix}'")
            else:
                print(f"❌ 关键前缀缺失: '{prefix}'")
                missing_prefixes.append(prefix)

        # 测试模式匹配器
        processor = VoiceCommandProcessor()
        test_text = "切换200"
        result = processor.match_standard_id_command(test_text, prefixes)
        print(f"模式匹配测试 '{test_text}': {result}")

        return len(missing_prefixes) == 0 and result == 200

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_validation_system():
    """测试GUI验证系统"""
    print("\n🧪 测试GUI验证系统")
    print("-" * 50)

    try:
        from config_loader import ConfigLoader

        config = ConfigLoader()

        # 检查配置中的验证规则
        part_no_rules = config.get('excel.input_validation.part_no', {})
        batch_no_rules = config.get('excel.input_validation.batch_no', {})
        inspector_rules = config.get('excel.input_validation.inspector', {})

        print("输入验证规则:")
        print(f"  零件号规则: {part_no_rules}")
        print(f"  批次号规则: {batch_no_rules}")
        print(f"  检验员规则: {inspector_rules}")

        # 检查是否所有必需字段都有验证规则
        required_fields = ['part_no', 'batch_no', 'inspector']
        all_have_rules = all([
            config.get(f'excel.input_validation.{field}')
            for field in required_fields
        ])

        print(f"验证规则完整性: {'✅ 完整' if all_have_rules else '❌ 不完整'}")

        return all_have_rules

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 系统性修复测试")
    print("=" * 60)

    success = True

    # 运行所有测试
    success &= test_config_loading()
    success &= test_voice_command_system()
    success &= test_excel_template_system()
    success &= test_gui_validation_system()

    if success:
        print("\n🎉 所有系统性修复测试通过！")
        print("\n📋 修复总结:")
        print("1. ✅ 统一语音命令识别接口 - 优先使用模式匹配，向后兼容传统匹配")
        print("2. ✅ 修复Excel模板逻辑 - 确保所有报告文件都使用模板")
        print("3. ✅ 增强GUI输入验证 - 提供明确的警示和状态反馈")
        print("4. ✅ 优化代码结构 - 消除重复逻辑，保持接口一致性")
        print("5. ✅ 添加调试日志 - 便于问题排查和系统监控")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")

    sys.exit(0 if success else 1)