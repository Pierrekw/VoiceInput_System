#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
用于测试和分析语音识别系统的性能指标
"""

import time
import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_f import FunASRVoiceSystem
from performance_monitor import performance_monitor, PerformanceStep

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 启用DEBUG级别日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/performance_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_performance_test():
    """运行性能测试"""
    print("🚀 开始语音识别性能测试")
    print("=" * 60)

    # 创建性能测试配置
    config = {
        'duration': 30,        # 测试30秒
        'debug_mode': True,      # 启用调试模式
        'continuous_mode': False  # 单次模式
    }

    print(f"测试配置:")
    print(f"  • 测试时长: {config['duration']}秒")
    print(f"  • 调试模式: {config['debug_mode']}")
    print(f" • 模式: {'单次模式' if not config['continuous_mode'] else '连续模式'}")
    print()

    try:
        # 创建系统实例
        print("🔧 正在初始化系统...")
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
        print()

        # 设置性能监控
        print("🔍 配置性能监控...")

        # 添加测试专用日志记录器
        test_logger = logging.getLogger("performance_test")

        # 预热音频系统
        print("🔊 预热音频系统...")
        time.sleep(2)

        print(f"🎤 开始{config['duration']}秒性能测试...")
        print("请说话，系统将记录每个步骤的性能数据")
        print("-" * 60)

        # 记录测试开始时间
        test_start_time = time.time()
        performance_monitor.start_timer("性能测试", {
            'test_duration': config['duration'],
            'debug_mode': config['debug_mode']
        })

        # 运行测试
        system.run_continuous()

        # 记录测试结束时间
        test_end_time = performance_monitor.end_timer("性能_test")
        total_test_time = test_end_time - test_start_time if test_end_time else 0

        print()
        print("✅ 性能测试完成")
        print(f"总测试时间: {total_test_time:.3f}秒")
        print()

        # 输出详细性能报告
        print("📊 详细性能分析报告:")
        print("=" * 80)
        report = performance_monitor.export_performance_report()
        print(report)
        print("=" * 80)

        # 分析建议
        print("💡 性能优化建议:")

        # 获取性能汇总
        summaries = performance_monitor.get_all_summaries()

        if summaries:
            print()
            print("📈 关键性能指标:")

            for i, summary in enumerate(summaries[:5], 1):  # 显示前5个最耗时的步骤
                print(f"{i}. {summary.step_name}")
                print(f"   - 平均耗时: {summary.avg_duration:.6f}s")
                print(f"   - 最大耗时: {summary.max_duration:.6f}s")
                print(f"   - 出现次数: {summary.total_count}")

                # 针对性建议
                if summary.step_name == "语音识别":
                    if summary.avg_duration > 2.0:
                        print(f"   ⚠️  语音识别较慢，建议:")
                        print(f"      - 减小FunASR的chunk_size参数")
                        print(f"      - 调整encoder_chunk_look_back参数")
                        print(f"      - 考虑使用更小的音频缓冲区")
                    elif summary.avg_duration > 1.0:
                        print(f"   ⚠️ 语音识别可以优化:")
                        print(f"      - 微调FunASR模型参数")
                        print(f"      - 检查音频质量")

                elif summary.step_name == "音频输入":
                    if summary.avg_duration > 0.01:
                        print(f"   ⚠️ 音频输入较慢，建议:")
                        print(f"      - 检查音频驱动程序")
                        print(f"      - 减小chunk_size参数")
                        print(f"      - 优化PyAudio配置")

                elif summary.step_name == "Excel写入":
                    if summary.avg_duration > 0.05:
                        print(f"   ⚠️ Excel写入较慢，建议:")
                        print(f"      - 使用批量写入而非单条写入")
                        print(f"      - 考虑异步写入")
                        print(f"      - 定期清理Excel文件")

                elif summary.step_name == "音频处理":
                    if summary.avg_duration > 0.005:
                        print(f"   ⚠️ 音频处理较慢，建议:")
                        print(f"      - 优化numpy数组操作")
                        print(f"      - 避免不必要的类型转换")
                        print(f"      - 使用更高效的库函数")

                elif summary.step_name == "结果处理":
                    if summary.avg_duration > 0.001:
                        print(f"   ⚠️ 结果处理较慢，建议:")
                        print(f"      - 简化文本处理逻辑")
                        print(f"      - 缓存常用转换结果")
                        print(f"      - 避免重复计算")

            print()

        # 流水线分析
        pipeline_steps = ["音频输入", "音频处理", "语音识别", "结果处理", "Excel写入"]
        pipeline_analysis = performance_monitor.analyze_pipeline(pipeline_steps)

        if pipeline_analysis['sessions']:
            print("🔄 流水线性能分析:")

            total_sessions = pipeline_analysis['total_sessions']
            if total_sessions > 0:
                sessions = pipeline_analysis['sessions']

                # 计算端到端延迟
                end_to_end_times = [s['total_duration'] for s in sessions if s['total_duration'] > 0]

                if end_to_end_times:
                    print(f"   - 会话数量: {total_sessions}")
                    print(f"   - 平均端到端延迟: {sum(end_to_end_times)/len(end_to_end_times):.6f}s")
                    print(f"   - 最快端到端延迟: {min(end_to_end_times):.6f}s")
                    print(f"   - 最慢端到端延迟: {max(end_to_end_times):.6f}s")

                    # 计算延迟分布
                    if len(end_to_end_times) >= 3:
                        fast_sessions = [t for t in end_to_end_times if t <= 1.0]
                        slow_sessions = [t for t in end_to_end_times if t > 3.0]

                        print(f"   - 快速会话(<1.0s): {len(fast_sessions)} ({len(fast_sessions)/len(end_to_end_times)*100:.1f}%)")
                        print(f"   - 正常会话(1.0-3.0s): {len(end_to_end_times)-len(fast_sessions)-len(slow_sessions)} ({(len(end_to_end_times)-len(fast_sessions)-len(slow_sessions))/len(end_to_end_times)*100:.1f}%)")
                        print(f"   - 慢速会话(>3.0s): {len(slow_sessions)} ({len(slow_sessions)/len(end_to_end_times)*100:.1f}%)")

        print()
        print("📝 测试数据已保存到日志文件: logs/performance_test.log")
        print("💡 建议根据报告结果优化配置参数")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保输出性能报告
        try:
            final_report = performance_monitor.export_performance_report()
            if final_report:
                print("\n" + "="*80)
                print("📊 最终性能报告")
                print("="*80)
                print(final_report)
                print("="*80)
        except:
            print("\n⚠️ 无法生成性能报告")

def analyze_config_performance():
    """分析不同配置的性能"""
    print("🔍 配置性能对比分析")
    print("=" * 60)

    configs = [
        {"name": "小缓冲区", "chunk_size": 800},
        {"name": "标准缓冲区", "chunk_size": 1600},
        {"name": "大缓冲区", "chunk_size": 3200},
    ]

    results = []

    for config in configs:
        print(f"\n🧪 测试配置: {config['name']} (chunk_size: {config['chunk_size']})")

        try:
            # 临时修改配置
            from funasr_voice_module import FunASRVoiceRecognizer
            recognizer = FunASRVoiceRecognizer()
            recognizer.chunk_size = config['chunk_size']

            # 短时间测试
            start_time = time.time()

            with PerformanceStep(f"配置测试-{config['name']}"):
                # 模拟一次音频处理循环
                for i in range(100):  # 模拟100次音频块处理
                    with PerformanceStep("模拟音频输入"):
                        time.sleep(0.001)  # 模拟音频读取延迟

            duration = time.time() - start_time
            results.append({
                'config': config['name'],
                'chunk_size': config['chunk_size'],
                'duration': duration,
                'avg_per_operation': duration / 100
            })

            print(f"✅ 测试完成，耗时: {duration:.6f}s, 平均每次: {duration/100:.6f}s")

        except Exception as e:
            print(f"❌ 测试失败: {e}")

    # 分析结果
    if results:
        print(f"\n📊 配置性能对比:")
        print("-" * 80)
        print(f"{'配置':<12} {'块大小':<8} {'总耗时':<12} {'平均耗时':<12} {'相对性能':<12}")
        print("-" * 80)

        fastest = min(results, key=lambda x: x['avg_per_operation'])

        for result in results:
            relative = fastest['avg_per_operation'] / result['avg_per_operation']
            print(f"{result['config']:<12} {result['chunk_size']:<8} {result['duration']:<12.6f} "
                 f"{result['avg_per_operation']:<12.6f} {relative:.2f}x")

        print()
        print("💡 建议:")
        fastest_config = results[0]
        print(f"   最快配置: {fastest_config['name']} (块大小: {fastest_config['chunk_size']})")

        if fastest_config['chunk_size'] != 1600:
            print(f"   建议将chunk_size设置为 {fastest_config['chunk_size']}")

def main():
    """主函数"""
    print("🎯 语音识别系统性能测试工具")
    print("=" * 60)

    import argparse
    parser = argparse.ArgumentParser(description='语音识别系统性能测试工具')
    parser.add_argument('--config-only', action='store_true', help='仅进行配置性能分析')
    parser.add_argument('--duration', type=int, default=30, help='测试时长（秒）')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    try:
        if args.config_only:
            analyze_config_performance()
        else:
            run_performance_test()
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()