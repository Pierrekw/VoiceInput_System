#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音系统启动脚本
简化版本，易于使用
支持配置文件和命令行参数
"""

import sys
import os
import argparse

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_f import FunASRVoiceSystem
from config_loader import config

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='FunASR语音输入系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python start_funasr.py                    # 使用默认配置（无限时模式）
  python start_funasr.py -d 120              # 识别120秒
  python start_funasr.py -d -1               # 连续识别模式（无限时）
  python start_funasr.py --debug             # 调试模式

配置说明:
  config.yaml中的timeout_seconds:
    -1: 无限时模式（连续识别）
    0或正数: 单次识别时长（秒）
        """
    )

    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=None,
        help='单次识别时长（秒），-1为无限时模式，默认从配置文件读取'
    )

    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式，显示详细日志'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='显示当前配置信息'
    )

    return parser.parse_args()

def main():
    """简化的启动函数"""
    # 解析命令行参数
    args = parse_arguments()

    print("🎤 FunASR语音输入系统")
    print("正在初始化...")

    # 从配置文件读取默认值
    config_duration = config.get_timeout_seconds()

    # 确定识别时长
    if args.duration is not None:
        recognition_duration = args.duration
        if recognition_duration == -1:
            print(f"📋 模式：连续识别（无限时模式）")
        else:
            print(f"📋 识别时长：{recognition_duration}秒（命令行指定）")
    else:
        recognition_duration = config_duration
        if recognition_duration == -1:
            print(f"📋 模式：连续识别（配置文件默认，无限时模式）")
        else:
            print(f"📋 识别时长：{recognition_duration}秒（配置文件默认）")

    # 显示配置信息
    if args.show_config:
        print("\n📋 当前配置:")
        if recognition_duration == -1:
            print(f"  识别模式: 连续识别（无限时模式）")
        else:
            print(f"  识别时长: {recognition_duration}秒")
        print(f"  调试模式: {args.debug}")
        print(f"  模型路径: {config.get_model_path()}")
        print(f"  设备类型: {config.get('model.device', 'cpu')}")
        print()

    # 创建系统实例
    system = FunASRVoiceSystem(
        recognition_duration=recognition_duration,
        continuous_mode=recognition_duration == -1,
        debug_mode=args.debug
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

    # 显示使用说明
    print("\n📖 使用说明:")
    print("  • 空格键：暂停/恢复识别")
    print("  • ESC键：停止程序")
    print("  • 语音命令：'暂停'、'继续'、'停止'（支持中英文）")

    if recognition_duration == -1:
        print("  • 连续识别模式：无限时模式，需要手动停止")
    else:
        print(f"  • 本次识别时长：{recognition_duration}秒")

    print("\n🎯 准备开始语音识别...")

    try:
        # 运行系统
        system.run_continuous()

        # 停止后显示识别结果汇总
        if system.results_buffer:
            system.show_results_summary()

    except KeyboardInterrupt:
        print("\n\n👋 用户退出")

    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        print("请检查系统配置和依赖")
        if args.debug:
            import traceback
            print("详细错误信息:")
            traceback.print_exc()

    finally:
        print("🎤 系统已关闭")

if __name__ == "__main__":
    main()