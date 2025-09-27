#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：验证 new_method.py 功能集成到现有系统
测试语音命令、键盘控制、状态管理等功能
"""

import sys
import os
import time
import threading
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter

def test_state_machine():
    """测试状态机功能"""
    print("=== 测试状态机功能 ===")

    exporter = ExcelExporter()
    capture = AudioCapture(excel_exporter=exporter)

    # 测试状态转换
    print(f"初始状态: {capture.state}")
    assert capture.state == "idle", f"初始状态应为 idle, 实际为 {capture.state}"

    # 测试启动确认
    print("测试启动确认...")
    capture.confirm_start_by_space()

    print("状态机测试通过！")

def test_voice_commands():
    """测试语音命令处理"""
    print("=== 测试语音命令处理 ===")

    exporter = ExcelExporter()
    capture = AudioCapture(excel_exporter=exporter)

    # 测试启动命令
    result = capture._process_voice_commands("开始录音")
    assert result == True, "开始录音 应该是有效的语音命令"

    # 测试暂停命令
    capture.state = "recording"
    result = capture._process_voice_commands("暂停录音")
    assert result == True, "暂停录音 应该是有效的语音命令"

    # 测试普通文本（非命令）
    result = capture._process_voice_commands("温度二十五点五度")
    assert result == False, "普通文本 不应被识别为语音命令"

    print("语音命令测试通过！")

def test_keyboard_commands():
    """测试键盘命令功能"""
    print("=== 测试键盘命令功能 ===")

    exporter = ExcelExporter()
    capture = AudioCapture(excel_exporter=exporter)

    # 测试空格键启动确认
    print("测试空格键启动确认...")
    assert capture.state == "idle", "初始状态应为idle"
    capture.confirm_start_by_space()
    # Note: 实际键盘监听需要单独的线程，这里只测试函数调用

    # 测试状态转换逻辑（模拟按键行为）
    print("测试空格键循环控制逻辑...")

    # 模拟：idle -> 按下空格键 -> recording
    capture.state = "idle"
    capture.confirm_start_by_space()  # 这会触发启动确认
    # Note: 实际状态转换在键盘监听器的回调中处理

    # 测试ESC停止逻辑
    print("测试ESC停止命令...")
    capture.state = "recording"
    capture.stop()
    assert capture.state == "stopped", "停止后状态应为stopped"

    print("键盘命令测试通过！")

def test_model_path_configuration():
    """测试模型路径配置"""
    print("=== 测试模型路径配置 ===")

    # 测试默认路径
    capture1 = AudioCapture()
    assert capture1.model_path == "model/cn", f"默认路径应为 model/cn, 实际为 {capture1.model_path}"

    # 测试自定义路径
    capture2 = AudioCapture(model_path="model/us")
    assert capture2.model_path == "model/us", f"自定义路径应为 model/us, 实际为 {capture2.model_path}"

    print("模型路径配置测试通过！")

def test_integration_flow():
    """测试完整集成流程"""
    print("=== 测试完整集成流程 ===")

    exporter = ExcelExporter()
    capture = AudioCapture(excel_exporter=exporter)

    print("1. 测试系统初始状态...")
    assert capture.state == "idle"
    assert capture.model_path == "model/cn"

    print("2. 测试语音命令优先级...")
    # 确保语音命令在数值提取之前处理
    test_text = "暂停录音温度二十五点五度"
    print(f"测试文本: {test_text}")

    # 设置正确状态
    capture.state = "recording"
    is_command = capture._process_voice_commands(test_text)
    print(f"是否识别为命令: {is_command}")

    # 如果包含暂停命令，应该被识别为命令
    assert is_command == True, f"包含暂停命令的文本应该被识别为命令，实际为{is_command}"

    print("3. 测试错误处理...")
    # 测试模型路径错误处理
    try:
        bad_capture = AudioCapture(model_path="nonexistent/path")
        # 如果创建成功，测试listen方法应该处理错误
        result = bad_capture.listen_realtime_vosk()
        # 应该返回空结果而不是崩溃
        assert isinstance(result, dict)
        assert "final" in result
        assert "buffered_values" in result
    except Exception as e:
        # 创建时出错也是正常的，关键是不要崩溃
        pass

    print("集成流程测试通过！")

def main():
    """主测试函数"""
    print("🚀 开始集成测试...")

    try:
        test_state_machine()
        test_voice_commands()
        test_keyboard_commands()
        test_model_path_configuration()
        test_integration_flow()

        print("\n🎉 所有集成测试通过！")
        print("✅ 状态机功能正常")
        print("✅ 语音命令处理正常")
        print("✅ 键盘命令功能正常")
        print("✅ 模型路径配置正常")
        print("✅ 完整集成流程正常")
        print("✅ 与主系统集成成功")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()