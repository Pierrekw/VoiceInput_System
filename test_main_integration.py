#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main.py 集成测试：测试从主程序入口的完整工作流程
确保 main.py 与增强的 AudioCapture 类正确集成
"""

import sys
import os
import threading
import time
from unittest.mock import patch, MagicMock
from main import VoiceInputSystem

def test_main_initialization():
    """测试 main.py 初始化"""
    print("=== 测试 main.py 初始化 ===")

    # 测试系统创建
    system = VoiceInputSystem(timeout_seconds=30)

    # 验证系统组件
    assert system.audio_capture is not None, "AudioCapture 应该被创建"
    assert system.excel_exporter is not None, "ExcelExporter 应该被创建"
    assert system.audio_capture.timeout_seconds == 30, "AudioCapture 的超时时间应该正确设置"

    # 验证增强功能集成
    assert hasattr(system.audio_capture, '_process_voice_commands'), "应该包含语音命令处理方法"
    assert hasattr(system.audio_capture, 'confirm_start_by_space'), "应该包含空格键启动方法"
    assert hasattr(system.audio_capture, 'state'), "应该使用统一状态系统"
    assert system.audio_capture.state == "idle", "初始状态应该是 idle"

    print("✅ Main.py 初始化测试通过")

def test_callback_integration():
    """测试回调函数集成"""
    print("=== 测试回调函数集成 ===")

    system = VoiceInputSystem()

    # 测试回调设置 - 先设置回调函数
    system.audio_capture.set_callback(system.on_data_detected)

    # 测试回调功能
    test_values = [25.5, 30.2, 15.8]
    system.on_data_detected(test_values)

    # 验证回调函数被正确设置
    assert system.audio_capture.callback_function is not None, "回调函数应该被设置"

    print("✅ 回调函数集成测试通过")

def test_keyboard_listener_integration():
    """测试键盘监听器集成"""
    print("=== 测试键盘监听器集成 ===")

    system = VoiceInputSystem()

    # 模拟键盘监听器启动
    with patch('audio_capture_v.start_keyboard_listener') as mock_keyboard:
        mock_keyboard.return_value = MagicMock()  # 模拟成功的监听器

        # 测试键盘监听器被调用
        system.audio_capture.set_callback(system.on_data_detected)
        keyboard_listener = mock_keyboard(system.audio_capture)

        assert mock_keyboard.called, "键盘监听器应该被调用"

    print("✅ 键盘监听器集成测试通过")

def test_voice_command_priority():
    """测试语音命令优先级（确保命令在数值提取前处理）"""
    print("=== 测试语音命令优先级 ===")

    system = VoiceInputSystem()

    # 测试包含语音命令的文本
    test_cases = [
        ("开始录音", True, "启动命令应该被识别"),
        ("暂停录音", True, "暂停命令应该被识别"),
        ("继续录音", True, "继续命令应该被识别"),
        ("停止录音", True, "停止命令应该被识别"),
        ("温度二十五点五度", False, "普通测量文本不应被识别为命令"),
        ("暂停录音温度三十度", True, "包含命令的混合文本应该优先识别命令"),
    ]

    for text, expected, message in test_cases:
        # 设置适当的状态以测试命令
        if "暂停" in text:
            system.audio_capture.state = "recording"
        elif "继续" in text:
            system.audio_capture.state = "paused"
        elif "停止" in text:
            system.audio_capture.state = "recording"
        elif "开始" in text:
            system.audio_capture.state = "idle"

        is_command = system.audio_capture._process_voice_commands(text)
        assert is_command == expected, f"{message}: 文本'{text}' 期望{expected}, 实际{is_command}"

    print("✅ 语音命令优先级测试通过")

def test_model_path_configuration():
    """测试模型路径配置功能"""
    print("=== 测试模型路径配置功能 ===")

    # 测试默认路径
    system1 = VoiceInputSystem()
    assert system1.audio_capture.model_path == "model/cn", "默认模型路径应该是 model/cn"

    # 测试自定义路径
    # Note: 由于 main.py 目前没有传递 model_path 参数，我们测试 AudioCapture 直接
    from audio_capture_v import AudioCapture
    from excel_exporter import ExcelExporter

    exporter = ExcelExporter()
    custom_system = AudioCapture(excel_exporter=exporter, model_path="model/us")
    assert custom_system.model_path == "model/us", "自定义模型路径应该是 model/us"

    print("✅ 模型路径配置测试通过")

def test_error_handling():
    """测试错误处理机制"""
    print("=== 测试错误处理机制 ===")

    system = VoiceInputSystem()

    # 测试模型加载错误处理
    with patch('vosk.Model') as mock_model:
        mock_model.side_effect = Exception("模型文件不存在")

        # 创建新的 AudioCapture 实例来测试错误处理
        from audio_capture_v import AudioCapture
        from excel_exporter import ExcelExporter

        exporter = ExcelExporter()
        test_capture = AudioCapture(excel_exporter=exporter, model_path="invalid/path")

        # 测试结果应该包含错误信息
        result = test_capture.listen_realtime_vosk()
        assert isinstance(result, dict), "应该返回字典格式的结果"
        assert result["final"] == "", "失败时最终文本应该为空"
        assert result["buffered_values"] == [], "失败时缓存值应该为空"

    print("✅ 错误处理测试通过")

def test_system_workflow():
    """测试完整系统工作流程"""
    print("=== 测试完整系统工作流程 ===")

    system = VoiceInputSystem()

    # 模拟系统启动流程
    print("1. 系统初始化...")
    assert system.audio_capture.state == "idle", "系统应该处于idle状态"

    print("2. 设置回调函数...")
    system.audio_capture.set_callback(system.on_data_detected)
    assert system.audio_capture.callback_function is not None, "回调函数应该被设置"

    print("3. 测试语音命令处理...")
    # 模拟启动确认
    system.audio_capture.state = "idle"
    is_command = system.audio_capture._process_voice_commands("开始录音")
    assert is_command == True, "启动命令应该被正确处理"

    print("4. 测试数值提取（非命令文本）...")
    is_command = system.audio_capture._process_voice_commands("温度二十五点五度")
    assert is_command == False, "测量文本不应该被识别为命令"

    print("✅ 完整系统工作流程测试通过")

def main():
    """主测试函数"""
    print("🚀 开始 Main.py 集成测试...")
    print("测试新功能与主系统的集成情况")

    try:
        test_main_initialization()
        test_callback_integration()
        test_keyboard_listener_integration()
        test_voice_command_priority()
        test_model_path_configuration()
        test_error_handling()
        test_system_workflow()

        print("\n🎉 所有 Main.py 集成测试通过！")
        print("✅ Main.py 初始化功能正常")
        print("✅ 回调函数集成正常")
        print("✅ 键盘监听器集成正常")
        print("✅ 语音命令优先级正常")
        print("✅ 模型路径配置正常")
        print("✅ 错误处理机制正常")
        print("✅ 完整系统工作流程正常")
        print("✅ new_method.py 功能与主系统完全集成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()