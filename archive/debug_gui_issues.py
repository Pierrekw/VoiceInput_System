#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试GUI问题
"""

import sys
import os

# 抑制输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

def test_gui_import():
    """测试GUI导入"""
    print("🔍 测试GUI导入...")

    try:
        from PySide6.QtWidgets import QApplication
        print("✅ PySide6导入成功")

        from voice_gui import WorkingVoiceWorker, WorkingSimpleMainWindow
        print("✅ GUI类导入成功")

        # 创建应用
        app = QApplication([])

        # 测试工作线程创建
        worker = WorkingVoiceWorker(mode='balanced')
        print("✅ 工作线程创建成功")

        # 测试主窗口创建
        window = WorkingSimpleMainWindow()
        print("✅ 主窗口创建成功")

        # 测试模式配置
        config = worker._get_mode_config('balanced')
        print(f"✅ 模式配置获取成功: {config}")

        app.quit()
        return True

    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_funasr_system():
    """测试FunASR系统"""
    print("\n🔍 测试FunASR系统...")

    try:
        from main_f import FunASRVoiceSystem

        # 创建系统
        system = FunASRVoiceSystem(
            recognition_duration=60,
            continuous_mode=True,
            debug_mode=False
        )
        print("✅ FunASRVoiceSystem创建成功")

        # 测试初始化
        if system.initialize():
            print("✅ FunASRVoiceSystem初始化成功")
            return True
        else:
            print("❌ FunASRVoiceSystem初始化失败")
            return False

    except Exception as e:
        print(f"❌ FunASR系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recognizer_config():
    """测试识别器配置"""
    print("\n🔍 测试识别器配置...")

    try:
        from main_f import FunASRVoiceSystem

        system = FunASRVoiceSystem(
            recognition_duration=60,
            continuous_mode=True,
            debug_mode=False
        )

        if system.initialize():
            print("✅ 系统初始化成功")

            # 检查识别器属性
            recognizer = system.recognizer
            print(f"✅ 识别器: {type(recognizer)}")

            # 检查是否有这些属性
            attrs_to_check = [
                'funasr_config',
                'vad_config',
                'chunk_size',
                'encoder_chunk_look_back',
                'decoder_chunk_look_back'
            ]

            for attr in attrs_to_check:
                if hasattr(recognizer, attr):
                    print(f"✅ 有属性: {attr}")
                else:
                    print(f"❌ 缺少属性: {attr}")

            return True
        else:
            print("❌ 系统初始化失败")
            return False

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 GUI问题调试工具")
    print("=" * 50)

    tests = [
        ("GUI导入测试", test_gui_import),
        ("FunASR系统测试", test_funasr_system),
        ("识别器配置测试", test_recognizer_config),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()

    # 输出结果
    print(f"\n{'='*50}")
    print("📊 测试结果:")
    print("=" * 50)

    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<20} {status}")

if __name__ == "__main__":
    main()