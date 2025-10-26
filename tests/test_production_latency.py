#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产模式延迟测试
测试在生产环境下的延迟记录功能
"""

import time
import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_f import FunASRVoiceSystem

# 配置生产环境日志（DEBUG级别以查看延迟信息）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_latency_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_production_test():
    """运行生产模式测试"""
    print("🏭 生产模式延迟测试")
    print("=" * 60)
    print("📝 本测试模拟正常使用场景，记录延迟信息到日志")
    print("📝 延迟记录将在后台进行，不影响系统性能")
    print("=" * 60)

    # 创建测试配置
    config = {
        'duration': 20,        # 测试20秒
        'debug_mode': False,    # 生产模式（非debug）
        'continuous_mode': False
    }

    print(f"\n📋 测试配置:")
    print(f"  • 测试时长: {config['duration']}秒")
    print(f"  • 模式: 生产模式（非debug）")
    print(f"  • 延迟记录: 启用（轻量级）")
    print(f"\n🎯 请正常说话，系统将在后台记录延迟信息")
    print("💡 完成后查看 logs/production_latency_test.log 文件")
    print("💡 搜索 [LATENCY] 标记查看延迟记录")
    print("-" * 60)

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
        print("✅ 延迟记录系统已启用")

        # 预热音频系统
        print("🔊 预热音频系统...")
        time.sleep(2)

        print(f"\n🎤 开始{config['duration']}秒生产模式测试...")
        print("🎯 请说话，系统将正常工作并记录延迟")
        print("-" * 60)

        # 运行测试
        system.run_continuous()

        print()
        print("✅ 生产模式测试完成")

        print("\n📝 延迟记录已保存到:")
        print("  • logs/production_latency_test.log")
        print("  • logs/voice_recognition_*.log")

        print("\n💡 查看延迟信息:")
        print("  1. 打开日志文件")
        print("  2. 搜索 [LATENCY] 标记")
        print("  3. 查看端到端延迟信息")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def show_latency_analysis_example():
    """显示延迟分析示例"""
    print("\n📊 延迟分析示例:")
    print("=" * 50)
    print("在日志文件中，您会看到类似这样的记录：")
    print()
    print("2025-10-19 22:20:00,123 - LATENCY - 语音输入完成 | 音频时长: 2.3s | 输入延迟: 3500.1ms")
    print("2025-10-19 22:20:00,267 - LATENCY - ASR完成: '今天天气很好...' | ASR延迟: 144.0ms | 总延迟: 3644.1ms")
    print("2025-10-19 22:20:00,268 - LATENCY - 终端显示: '今天天气很好...' | 显示延迟: 0.5ms | 端到端延迟: 3644.6ms")
    print()
    print("📖 如何解读:")
    print("  • 音频时长: 您说话的实际时间")
    print("  • 输入延迟: 从开始录音到语音结束的时间")
    print("  • ASR延迟: FunASR模型处理时间")
    print("  • 端到端延迟: 从开始说话到显示的总时间")
    print()
    print("⚠️  注意: 端到端延迟包含您说话的时间，")
    print("    如果延迟超过预期，请检查是否说话时间较长")

def main():
    """主函数"""
    print("🎯 生产模式延迟测试工具")
    print("=" * 60)

    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)

    # 运行测试
    run_production_test()

    # 显示分析示例
    show_latency_analysis_example()

if __name__ == "__main__":
    main()