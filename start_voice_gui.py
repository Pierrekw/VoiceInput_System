#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音识别系统 - 单一GUI启动脚本
直接启动最佳版本的GUI界面
"""

import sys
import os

# 抑制输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

def main():
    """主函数"""
    try:
        print("🎤 启动FunASR语音识别系统GUI...")

        # 直接启动主GUI
        from voice_gui import main as gui_main
        gui_main()

    except ImportError as e:
        print(f"❌ 导入GUI失败: {e}")
        print("请确保已安装PySide6: pip install PySide6==6.8.2")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()