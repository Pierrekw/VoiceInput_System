#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEN VAD 参数配置工具
用于轻松修改TEN VAD的threshold和hop_size参数
"""

import os
import sys
from typing import Dict, Any

def read_current_config() -> Dict[str, Any]:
    """读取当前TEN VAD配置"""

    config_file = "funasr_voice_TENVAD.py"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析当前配置
        lines = content.split('\n')
        current_hop_size = 256
        current_threshold = 0.5

        for line in lines:
            if 'TenVad(' in line:
                # 提取hop_size
                if 'hop_size=' in line:
                    hop_part = line.split('hop_size=')[1].split(',')[0].strip()
                    current_hop_size = int(hop_part)
                # 提取threshold
                if 'threshold=' in line:
                    threshold_part = line.split('threshold=')[1].split(')')[0].strip()
                    current_threshold = float(threshold_part)
                break

        return {
            'hop_size': current_hop_size,
            'threshold': current_threshold,
            'content': content,
            'config_file': config_file
        }

    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return None

def update_config(config: Dict[str, Any], new_hop_size: int, new_threshold: float):
    """更新TEN VAD配置"""

    try:
        content = config['content']
        lines = content.split('\n')

        # 找到TenVad行并更新参数
        for i, line in enumerate(lines):
            if 'TenVad(' in line:
                # 替换整行
                old_line = line.strip()
                new_line = f"        ten_vad_model = TenVad(hop_size={new_hop_size}, threshold={new_threshold})"
                lines[i] = new_line
                print(f"✅ 更新配置: {old_line} → {new_line}")
                break

        # 写回文件
        with open(config['config_file'], 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"\n✅ 配置已更新到 {config['config_file']}")
        print(f"   Hop Size: {config['hop_size']} → {new_hop_size}")
        print(f"   Threshold: {config['threshold']} → {new_threshold}")

        return True

    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False

def print_current_config(config: Dict[str, Any]):
    """打印当前配置"""

    print("\n📋 当前TEN VAD配置:")
    print(f"   Hop Size: {config['hop_size']} ({config['hop_size']/16000*1000:.1f}ms 延迟)")
    print(f"   Threshold: {config['threshold']}")

    # 分析当前配置特性
    hop_size = config['hop_size']
    threshold = config['threshold']

    print("\n🔍 配置分析:")

    # Hop Size 分析
    if hop_size <= 128:
        print("   ⚡ Hop Size: 极低延迟 (8ms)，适合实时应用")
    elif hop_size <= 256:
        print("   ⚡ Hop Size: 低延迟 (16ms)，平衡性能和精度")
    elif hop_size <= 512:
        print("   ⚡ Hop Size: 中等延迟 (32ms)，适合一般应用")
    else:
        print("   ⚡ Hop Size: 高延迟 (64ms+)，适合后台处理")

    # Threshold 分析
    if threshold <= 0.3:
        print("   🎯 Threshold: 高敏感度，能检测轻声但可能误判")
    elif threshold <= 0.5:
        print("   🎯 Threshold: 中等敏感度，适合大多数场景")
    elif threshold <= 0.7:
        print("   🎯 Threshold: 低敏感度，适合安静环境")
    else:
        print("   🎯 Threshold: 极低敏感度，仅检测明显语音")

def print_preset_configurations():
    """打印预设配置"""

    print("\n🎯 预设配置:")
    print("1. 实时对话 (hop_size=128, threshold=0.4)")
    print("   - 延迟: 8ms")
    print("   - 特点: 快速响应，适合视频会议")
    print()

    print("2. 当前默认 (hop_size=256, threshold=0.5)")
    print("   - 延迟: 16ms")
    print("   - 特点: 平衡配置，适合大多数场景")
    print()

    print("3. 安静环境 (hop_size=256, threshold=0.6)")
    print("   - 延迟: 16ms")
    print("   - 特点: 减少误报，适合办公室录音")
    print()

    print("4. 嘈杂环境 (hop_size=512, threshold=0.3)")
    print("   - 延迟: 32ms")
    print("   - 特点: 在噪音中检测语音，节省资源")
    print()

    print("5. 低功耗设备 (hop_size=512, threshold=0.5)")
    print("   - 延迟: 32ms")
    print("   - 特点: 节省CPU，适合移动设备")

def get_user_choice() -> tuple:
    """获取用户选择"""

    while True:
        try:
            choice = input("\n请选择配置 (1-5) 或输入自定义参数 (格式: hop_size,threshold): ").strip()

            # 预设配置
            if choice == "1":
                return (128, 0.4)
            elif choice == "2":
                return (256, 0.5)
            elif choice == "3":
                return (256, 0.6)
            elif choice == "4":
                return (512, 0.3)
            elif choice == "5":
                return (512, 0.5)

            # 自定义配置
            elif ',' in choice:
                parts = choice.split(',')
                if len(parts) == 2:
                    hop_size = int(parts[0].strip())
                    threshold = float(parts[1].strip())

                    # 验证参数范围
                    if hop_size not in [64, 128, 256, 512, 1024]:
                        print(f"⚠️ Hop Size {hop_size} 不在推荐范围 [64, 128, 256, 512, 1024]")
                        continue

                    if threshold < 0.1 or threshold > 0.9:
                        print(f"⚠️ Threshold {threshold} 不在推荐范围 [0.1, 0.9]")
                        continue

                    return (hop_size, threshold)

            print("❌ 无效输入，请重新选择")

        except ValueError:
            print("❌ 输入格式错误，请重新选择")

def main():
    """主函数"""

    print("=" * 80)
    print("🔧 TEN VAD 参数配置工具")
    print("=" * 80)

    # 读取当前配置
    config = read_current_config()
    if not config:
        return

    # 显示当前配置
    print_current_config(config)

    # 显示预设配置
    print_preset_configurations()

    # 获取用户选择
    new_hop_size, new_threshold = get_user_choice()

    # 确认更新
    print(f"\n🔍 确认更新:")
    print(f"   Hop Size: {config['hop_size']} → {new_hop_size}")
    print(f"   Threshold: {config['threshold']} → {new_threshold}")

    confirm = input("\n确认更新配置? (y/N): ").strip().lower()
    if confirm == 'y' or confirm == 'yes':
        if update_config(config, new_hop_size, new_threshold):
            print("\n✅ 配置更新成功！")
            print("💡 请重新启动语音识别系统以应用新配置")

            # 显示新配置的影响
            print(f"\n📊 新配置影响:")
            print(f"   延迟变化: {config['hop_size']/16:.1f}ms → {new_hop_size/16:.1f}ms")

            latency_change = (new_hop_size - config['hop_size']) / 16
            if latency_change > 0:
                print(f"   延迟增加 +{latency_change:.1f}ms")
            else:
                print(f"   延迟减少 {latency_change:.1f}ms")

            sensitivity_change = (new_threshold - config['threshold'])
            if sensitivity_change > 0:
                print(f"   敏感度降低 (更少误报但可能漏检)")
            else:
                print(f"   敏感度提高 (更好轻声检测但可能误报)")
        else:
            print("\n❌ 配置更新失败")
    else:
        print("\n⏹️ 取消更新")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 配置工具被用户中断")
    except Exception as e:
        print(f"\n❌ 配置工具出错: {e}")
        import traceback
        traceback.print_exc()