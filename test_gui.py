#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI测试脚本
测试GUI是否能正常启动和基本功能
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")

    try:
        import PySide6
        print(f"✅ PySide6 {PySide6.__version__}")
    except ImportError as e:
        print(f"❌ PySide6 导入失败: {e}")
        return False

    try:
        from PySide6.QtWidgets import QApplication, QMainWindow
        print("✅ PySide6.QtWidgets")
    except ImportError as e:
        print(f"❌ PySide6.QtWidgets 导入失败: {e}")
        return False

    return True

def test_basic_gui():
    """测试基本GUI功能"""
    print("\n🎨 测试基本GUI功能...")

    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

        # 创建应用
        app = QApplication([])

        # 创建简单窗口
        window = QMainWindow()
        window.setWindowTitle("测试窗口")
        window.resize(400, 300)

        # 添加标签
        label = QLabel("GUI测试成功！", window)
        window.setCentralWidget(label)

        print("✅ 基本GUI组件创建成功")

        # 不显示窗口，直接退出
        app.quit()
        return True

    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False

def test_voice_modules():
    """测试语音模块导入"""
    print("\n🎤 测试语音模块...")

    try:
        from main_f import VoiceRecognitionSystem
        print("✅ VoiceRecognitionSystem")
    except ImportError as e:
        print(f"⚠️ VoiceRecognitionSystem 导入失败: {e}")

    try:
        from funasr_voice_module import FunASRVoiceRecognizer
        print("✅ FunASRVoiceRecognizer")
    except ImportError as e:
        print(f"⚠️ FunASRVoiceRecognizer 导入失败: {e}")

    return True

def main():
    """主函数"""
    print("🧪 GUI功能测试")
    print("=" * 40)

    # 测试导入
    if not test_imports():
        print("\n❌ 基础模块导入失败，无法运行GUI")
        return

    # 测试GUI
    if not test_basic_gui():
        print("\n❌ GUI基本功能测试失败")
        return

    # 测试语音模块
    test_voice_modules()

    print("\n✅ 基础测试通过，可以尝试启动完整GUI")
    print("运行命令: python start_gui.py")

if __name__ == "__main__":
    main()