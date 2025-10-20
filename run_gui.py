#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR GUI启动脚本
提供完整的GUI启动选项
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_gui_availability():
    """检查GUI可用性"""
    try:
        import PySide6
        print("✅ PySide6 GUI库可用")
        return True
    except ImportError:
        print("❌ PySide6未安装，请运行: pip install PySide6==6.8.2")
        return False

def start_simple_gui():
    """启动简化版GUI"""
    try:
        from simple_gui import main as simple_main
        print("🚀 启动简化版GUI...")
        simple_main()
        return True
    except Exception as e:
        print(f"❌ 简化版GUI启动失败: {e}")
        return False

def start_full_gui():
    """启动完整版GUI"""
    try:
        from voice_gui import main as full_main
        print("🚀 启动完整版GUI...")
        full_main()
        return True
    except Exception as e:
        print(f"❌ 完整版GUI启动失败: {e}")
        return False

def start_working_gui():
    """启动工作版GUI"""
    try:
        from working_simple_gui import main as working_main
        print("🚀 启动工作版GUI...")
        working_main()
        return True
    except Exception as e:
        print(f"❌ 工作版GUI启动失败: {e}")
        return False

def main():
    """主函数"""
    print("🎤 FunASR语音识别系统 GUI启动器")
    print("=" * 50)

    # 检查GUI库
    if not check_gui_availability():
        input("\n按回车键退出...")
        return

    # 抑制输出
    os.environ['TQDM_DISABLE'] = '1'
    os.environ['PYTHONWARNINGS'] = 'ignore'
    os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

    print("\n🚀 启动GUI界面...")
    success = start_working_gui()

    if not success:
        print("\n❌ GUI启动失败")
        print("\n可能的解决方案:")
        print("1. 检查Python环境是否正确")
        print("2. 确保所有依赖包已安装")
        print("3. 检查音频设备是否可用")
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()