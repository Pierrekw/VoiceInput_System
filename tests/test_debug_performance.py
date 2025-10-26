#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug性能测试脚本
用于测试语音识别各步骤的详细延迟
"""

import time
import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_f import FunASRVoiceSystem

# 配置详细日志记录
logging.basicConfig(
    level=logging.DEBUG,  # 启用DEBUG级别以看到详细时间信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_performance_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_debug_performance_test():
    """运行debug性能测试"""
    print("🔍 开始Debug性能测试")
    print("=" * 80)
    print("📝 本测试将详细记录语音识别的每个步骤延迟")
    print("📝 包括：语音输入 → ASR识别 → 文本处理 → 终端显示 → Excel写入")
    print("=" * 80)

    # 创建debug测试配置
    config = {
        'duration': 30,        # 测试30秒
        'debug_mode': True,      # 启用debug模式
        'continuous_mode': False  # 单次模式
    }

    print(f"\n📋 测试配置:")
    print(f"  • 测试时长: {config['duration']}秒")
    print(f"  • Debug模式: {config['debug_mode']}")
    print(f"  • 模式: {'单次模式' if not config['continuous_mode'] else '连续模式'}")
    print(f"\n🎯 请准备说话，系统将记录每个步骤的详细时间戳")
    print("💡 建议说一些包含数字的句子，如：'今天温度是25度'")
    print("-" * 80)

    try:
        # 创建系统实例
        print("\n🔧 正在初始化系统...")
        system = FunASRVoiceSystem(
            recognition_duration=config['duration'],
            continuous_mode=config['continuous_mode'],
            debug_mode=config['debug_mode']
        )

        # 初始化
        if not system.initialize():
            print("❌ 系统初始化失败")
            return

        print("✅ 系统初始化成功")

        # 预热音频系统
        print("🔊 预热音频系统...")
        time.sleep(2)

        print(f"\n🎤 开始{config['duration']}秒Debug性能测试...")
        print("🎯 请说话，系统将详细记录每个步骤的时间消耗")
        print("⏱️ 测试结束后将显示详细的延迟分析报告")
        print("-" * 80)

        # 记录测试开始时间
        test_start_time = time.time()

        # 运行测试
        system.run_continuous()

        # 记录测试结束时间
        test_end_time = time.time()
        total_test_time = test_end_time - test_start_time

        print()
        print("✅ Debug性能测试完成")
        print(f"总测试时间: {total_test_time:.3f}秒")
        print()

        print("📝 详细日志已保存到:")
        print("  • logs/debug_performance_test.log")
        print("  • logs/voice_recognition_*.log")

        print("\n💡 查看日志文件以获取详细的步骤延迟分析")
        print("💡 寻找 [LATENCY] 和 [DEBUG_LATENCY] 标记的时间戳记录")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def analyze_debug_logs():
    """分析debug日志"""
    print("\n📊 分析Debug日志...")
    print("=" * 60)

    log_files = [
        "logs/debug_performance_test.log",
        "logs/voice_recognition.log"
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 分析文件: {log_file}")
            print("-" * 40)

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                latency_lines = [line for line in lines if '[LATENCY]' in line or '[DEBUG_LATENCY]' in line]

                if latency_lines:
                    print("找到延迟记录:")
                    for line in latency_lines[-10:]:  # 显示最后10条
                        print(f"  {line.strip()}")
                else:
                    print("未找到延迟记录")

            except Exception as e:
                print(f"读取日志文件失败: {e}")
        else:
            print(f"日志文件不存在: {log_file}")

def main():
    """主函数"""
    print("🎯 语音识别Debug性能测试工具")
    print("=" * 60)

    import argparse
    parser = argparse.ArgumentParser(description='语音识别Debug性能测试工具')
    parser.add_argument('--duration', type=int, default=30, help='测试时长（秒）')
    parser.add_argument('--analyze-only', action='store_true', help='仅分析现有日志')

    args = parser.parse_args()

    if args.analyze_only:
        analyze_debug_logs()
    else:
        # 确保logs目录存在
        os.makedirs('logs', exist_ok=True)

        # 运行测试
        run_debug_performance_test()

        # 分析日志
        analyze_debug_logs()

if __name__ == "__main__":
    main()