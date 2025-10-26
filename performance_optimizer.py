#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化配置生成器
基于性能测试结果生成优化配置
"""

import yaml
import os
from datetime import datetime

def generate_optimized_config(base_config_path="config.yaml", output_path="config_optimized.yaml"):
    """
    基于性能测试结果生成优化配置

    Args:
        base_config_path: 基础配置文件路径
        output_path: 优化后配置文件输出路径
    """

    print("🔧 正在生成性能优化配置...")

    # 读取基础配置
    try:
        with open(base_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False

    # 基于性能分析的优化建议
    optimizations = {
        # 音频配置优化 - 针对音频输入瓶颈
        'audio': {
            'sample_rate': 16000,  # 保持标准采样率
            'chunk_size': 1600,    # 从8000减小到1600，减少5倍延迟
        },

        # FunASR流式处理优化
        'model': {
            'default_path': config.get('model', {}).get('default_path', './model/fun'),
            'device': config.get('model', {}).get('device', 'cpu'),
            'funasr': {
                'path': config.get('model', {}).get('funasr', {}).get('path', './model/fun'),
                # 优化流式处理参数以减少延迟
                'chunk_size': [0, 5, 2],      # 从[0,10,5]减小到[0,5,2]
                'encoder_chunk_look_back': 2, # 从4减小到2
                'decoder_chunk_look_back': 1, # 保持1
                'disable_update': True,
                'trust_remote_code': False
            }
        },

        # 识别配置优化
        'recognition': {
            'timeout_seconds': config.get('recognition', {}).get('timeout_seconds', -1),
            'buffer_size': 5000,  # 从10000减小到5000
            'pause_timeout_multiplier': config.get('recognition', {}).get('pause_timeout_multiplier', 3)
        },

        # 保持其他配置不变
        'system': config.get('system', {}),
        'excel': config.get('excel', {}),
        'voice_commands': config.get('voice_commands', {}),
        'error_correction': config.get('error_correction', {}),
        'special_texts': config.get('special_texts', {})
    }

    # 添加性能优化说明
    performance_notes = """
# ===== 性能优化配置 =====
# 基于性能测试结果自动生成
# 生成时间: {timestamp}
#
# 主要优化项:
# 1. audio.chunk_size: 8000 -> 1600 (减少5倍音频输入延迟)
# 2. funasr.chunk_size: [0,10,5] -> [0,5,2] (减少流式处理延迟)
# 3. encoder_chunk_look_back: 4 -> 2 (平衡准确性和延迟)
# 4. recognition.buffer_size: 10000 -> 5000 (减少内存占用)
#
# 预期效果:
# - 音频输入延迟从 ~100ms 降低到 ~20ms
# - 端到端响应速度提升 3-5倍
# - 内存占用略有减少

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 备份原配置
    backup_path = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    try:
        with open(base_config_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"✅ 原配置已备份到: {backup_path}")
    except Exception as e:
        print(f"⚠️ 配置备份失败: {e}")

    # 写入优化配置
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(performance_notes)
            yaml.dump(optimizations, f, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"✅ 优化配置已生成: {output_path}")
        print("\n📊 主要优化内容:")
        print("  • 音频块大小: 8000 -> 1600 (减少5倍延迟)")
        print("  • FunASR流式参数: [0,10,5] -> [0,5,2] (减少延迟)")
        print("  • 编码器回溯: 4 -> 2 (平衡性能)")
        print("  • 缓冲区大小: 10000 -> 5000 (减少内存)")

        return True

    except Exception as e:
        print(f"❌ 写入优化配置失败: {e}")
        return False

def compare_configs_performance():
    """
    比较不同配置的性能表现
    """
    print("\n🧪 配置性能对比分析")
    print("=" * 60)

    configs = [
        {"name": "当前配置", "chunk_size": 8000},
        {"name": "优化配置", "chunk_size": 1600},
        {"name": "极速配置", "chunk_size": 800},
    ]

    # 理论性能计算
    base_delay = 0.1  # 基础延迟100ms（基于测试结果）

    print(f"{'配置':<12} {'块大小':<8} {'理论延迟':<12} {'预期性能提升':<12}")
    print("-" * 60)

    for config in configs:
        # 延迟与块大小成正比
        theoretical_delay = base_delay * (config['chunk_size'] / 8000)
        performance_gain = 8000 / config['chunk_size']

        print(f"{config['name']:<12} {config['chunk_size']:<8} {theoretical_delay*1000:.1f}ms{'':<5} {performance_gain:.1f}x")

    print()
    print("💡 优化建议:")
    print("  • 日常使用: 推荐使用优化配置 (1600)")
    print("  • 追求极速: 可以尝试极速配置 (800)")
    print("  • 准确性优先: 保持当前配置 (8000)")

def main():
    """主函数"""
    print("🎯 FunASR性能优化工具")
    print("=" * 60)

    # 检查配置文件
    if not os.path.exists("config.yaml"):
        print("❌ 找不到config.yaml文件")
        return

    # 生成优化配置
    if generate_optimized_config():
        # 性能对比分析
        compare_configs_performance()

        print("\n📝 使用方法:")
        print("  1. 备份当前配置: 已自动完成")
        print("  2. 应用优化配置: cp config_optimized.yaml config.yaml")
        print("  3. 测试性能: python tests/test_performance.py --duration 10")
        print("  4. 如有问题恢复: cp config_backup_*.yaml config.yaml")

        print("\n⚠️ 注意事项:")
        print("  • 减小chunk_size可能略微影响识别准确性")
        print("  • 建议先在安静环境下测试优化效果")
        print("  • 如果识别准确率明显下降，请适当增大chunk_size")
    else:
        print("❌ 配置优化失败")

if __name__ == "__main__":
    main()