#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音系统启动脚本
简化版本，易于使用
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_f import FunASRVoiceSystem

def main():
    """简化的启动函数"""
    print("🎤 FunASR语音输入系统")
    print("正在初始化...")

    # 创建系统实例（默认设置，生产模式）
    system = FunASRVoiceSystem(
        recognition_duration=60,  # 每次识别60秒
        continuous_mode=False,     # 单次模式
        debug_mode=False           # 生产模式
    )

    # 初始化
    print("⏳ 正在加载模型...")
    if not system.initialize():
        print("❌ 初始化失败，请检查:")
        print("  1. FunASR模型是否正确下载")
        print("  2. 依赖包是否完整安装")
        print("  3. 麦克风是否正常工作")
        return

    print("✅ 初始化成功！")
    print("\n📖 使用说明:")
    print("  • 空格键：暂停/恢复识别")
    print("  • ESC键：停止程序")
    print("  • 语音命令：'暂停'、'继续'、'停止'")
    print("\n🎯 准备开始语音识别...")

    try:
        # 运行系统
        system.run_continuous()
        system.show_results_summary()

    except KeyboardInterrupt:
        print("\n\n👋 用户退出")

    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        print("请检查系统配置和依赖")

    finally:
        print("🎤 系统已关闭")

if __name__ == "__main__":
    main()