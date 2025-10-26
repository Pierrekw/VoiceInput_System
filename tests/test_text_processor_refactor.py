#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文本处理器重构后的功能
确保向后兼容性和新功能正常工作
"""

import sys
import os

# 添加父目录到路径（因为tests是子目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_text_processor_new_methods():
    """测试TextProcessor新增的方法"""
    print("🧪 测试TextProcessor新增方法...")

    from text_processor_clean import TextProcessor

    processor = TextProcessor()

    # 测试相似度计算
    print("\n1. 测试相似度计算:")
    test_cases = [
        ("暂停", "暂停"),
        ("暂停", "暂停一下"),
        ("暂停识别", "暂停"),
        ("stop", "停止"),
        ("", "测试"),
        ("测试", ""),
    ]

    for text1, text2 in test_cases:
        similarity = processor.calculate_similarity(text1, text2)
        print(f"  '{text1}' vs '{text2}' = {similarity:.3f}")

    # 测试命令文本清理
    print("\n2. 测试命令文本清理:")
    text_cases = [
        "暂停一下。",
        "继续识别！",
        "停止，谢谢",
        "  请暂停  ",
        "开始，继续",
    ]

    for text in text_cases:
        cleaned = processor.clean_text_for_command_matching(text)
        print(f"  '{text}' -> '{cleaned}'")

    # 测试特殊文本检查
    print("\n3. 测试特殊文本检查:")
    exportable_texts = [
        {
            'base_text': 'OK',
            'variants': ['OK', '好的', '可以', '没问题']
        },
        {
            'base_text': 'Not OK',
            'variants': ['Not OK', '不行', '有问题', '错误']
        }
    ]

    test_texts = ['OK', '好的', '不行', '测试', '可以']
    for text in test_texts:
        result = processor.check_special_text(text, exportable_texts, True)
        print(f"  '{text}' -> '{result}'")

    print("✅ TextProcessor新方法测试完成\n")

def test_voice_command_processor():
    """测试语音命令处理器"""
    print("🧪 测试VoiceCommandProcessor...")

    from text_processor_clean import VoiceCommandProcessor

    processor = VoiceCommandProcessor()

    # 配置处理器
    processor.configure(
        match_mode="fuzzy",
        min_match_length=2,
        confidence_threshold=0.8
    )

    # 测试命令
    commands = {
        "pause": ["暂停", "暂停一下", "等一下", "停一下"],
        "resume": ["继续", "继续识别", "开始", "接着来"],
        "stop": ["停止", "结束", "退出", "停止识别"]
    }

    test_inputs = [
        "暂停一下",
        "继续识别",
        "停止，谢谢",
        "测试一下",
        "请暂停",
        "开始",
        "结束吧",
        "等一等",
        "接着识别"
    ]

    print("测试语音命令匹配:")
    for text in test_inputs:
        result = processor.match_command(text, commands)
        print(f"  '{text}' -> '{result}'")

    print("✅ VoiceCommandProcessor测试完成\n")

def test_backward_compatibility():
    """测试向后兼容性"""
    print("🧪 测试向后兼容性...")

    try:
        # 尝试导入原有的模块
        from text_processor_clean import process_text, TextProcessor

        # 测试原有的process_text函数
        print("\n1. 测试原有process_text函数:")
        test_texts = [
            "三十七点五",
            "今天气温二十五度",
            "价格是一百二十三点五元"
        ]

        for text in test_texts:
            result = process_text(text)
            print(f"  '{text}' -> '{result}'")

        # 测试TextProcessor原有方法
        print("\n2. 测试TextProcessor原有方法:")
        processor = TextProcessor()

        for text in test_texts:
            processed = processor.process_text(text)
            numbers = processor.extract_numbers(text, processed)
            print(f"  '{text}' -> '{processed}' -> 数字: {numbers}")

        print("✅ 向后兼容性测试完成\n")

    except ImportError as e:
        print(f"❌ 向后兼容性测试失败: {e}\n")
        return False

    return True

def test_main_f_integration():
    """测试与main_f.py的集成"""
    print("🧪 测试main_f.py集成...")

    try:
        from main_f import FunASRVoiceSystem, VoiceCommandType

        # 创建系统实例（但不初始化模型）
        system = FunASRVoiceSystem(
            recognition_duration=1,  # 短时间用于测试
            continuous_mode=False,
            debug_mode=True
        )

        # 测试语音命令识别
        print("\n测试语音命令识别:")
        test_commands = [
            "暂停一下",
            "继续识别",
            "停止",
            "测试文本"
        ]

        for text in test_commands:
            command_type = system.recognize_voice_command(text)
            print(f"  '{text}' -> {command_type.value}")

        # 测试文本处理
        print("\n测试文本处理:")
        test_texts = [
            "合格产品",
            "二十五点五",
            "OK"
        ]

        for text in test_texts:
            processed = system.processor.process_text(text)
            special_match = system._check_special_text(text)
            print(f"  '{text}' -> '{processed}' (特殊匹配: {special_match})")

        print("✅ main_f.py集成测试完成\n")
        return True

    except Exception as e:
        print(f"❌ main_f.py集成测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔧 文本处理器重构功能测试")
    print("=" * 60)

    success = True

    try:
        # 运行所有测试
        test_text_processor_new_methods()
        test_voice_command_processor()

        # 测试向后兼容性
        if not test_backward_compatibility():
            success = False

        # 测试集成
        if not test_main_f_integration():
            success = False

        # 输出测试结果
        print("=" * 60)
        if success:
            print("✅ 所有测试通过！重构成功，功能正常")
        else:
            print("⚠️ 部分测试失败，需要检查重构")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        success = False

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)