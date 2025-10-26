#!/usr/bin/env python3
"""
配置对比调试脚本
详细对比GUI版本和命令行版本最终应用的VAD参数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem
from config_loader import ConfigLoader

def get_system_vad_params(system):
    """获取系统实际应用的VAD参数"""
    if hasattr(system, 'recognizer') and hasattr(system.recognizer, '_vad_params'):
        return system.recognizer._vad_params
    return {}

def test_command_line_config():
    """测试命令行版本的配置"""
    print("=" * 60)
    print("🖥️ 命令行版本配置分析")
    print("=" * 60)

    # 命令行版本
    system = FunASRVoiceSystem(
        recognition_duration=60,
        continuous_mode=False,
        debug_mode=True
    )

    if not system.initialize():
        print("❌ 命令行版本初始化失败")
        return None

    # 获取实际应用的VAD参数
    vad_params = get_system_vad_params(system)
    print(f"📋 实际VAD参数: {vad_params}")

    # 获取config.yaml中的配置
    config = ConfigLoader()
    vad_config = config.get_vad_config()
    print(f"📋 config.yaml VAD配置: {vad_config}")

    return {
        'system_params': vad_params,
        'config_params': vad_config,
        'recognition_duration': system.recognition_duration,
        'continuous_mode': system.continuous_mode,
        'debug_mode': system.debug_mode
    }

def test_gui_config():
    """测试GUI版本的配置"""
    print("\n" + "=" * 60)
    print("🖥️ GUI版本配置分析")
    print("=" * 60)

    # 模拟GUI版本的配置逻辑
    from config_loader import config

    # 获取GUI版本的配置
    mode_config = {}
    try:
        if 'customized' in ['customized']:  # GUI版本使用的模式
            vad_config = config.get_vad_config()
            if vad_config:
                mode_config['vad_energy_threshold'] = vad_config.get('energy_threshold', 0.012)
                mode_config['vad_min_speech_duration'] = vad_config.get('min_speech_duration', 0.2)
                mode_config['vad_min_silence_duration'] = vad_config.get('min_silence_duration', 0.6)
                mode_config['vad_speech_padding'] = vad_config.get('speech_padding', 0.4)
                print(f"✅ GUI VAD配置: {mode_config}")
            else:
                print("⚠️ GUI版本未找到customized VAD配置")
    except Exception as e:
        print(f"⚠️ GUI版本VAD配置加载失败: {e}")
        mode_config['vad_energy_threshold'] = 0.015
        mode_config['vad_min_speech_duration'] = 0.3
        mode_config['vad_min_silence_duration'] = 0.6
        mode_config['vad_speech_padding'] = 0.3
        print(f"❌ GUI默认VAD配置: {mode_config}")

    # 创建GUI版本系统并获取实际参数
    system = FunASRVoiceSystem(
        recognition_duration=-1,
        continuous_mode=True,
        debug_mode=False
    )

    if not system.initialize():
        print("❌ GUI版本初始化失败")
        return None

    # 获取实际应用的VAD参数
    vad_params = get_system_vad_params(system)
    print(f"📋 GUI实际VAD参数: {vad_params}")

    # 模拟GUI版本的configure_vad调用
    recognizer = system.recognizer
    if hasattr(recognizer, 'configure_vad'):
        print(f"🔧 GUI版本调用了configure_vad()，参数: {mode_config}")

    return {
        'mode_config': mode_config,
        'system_params': vad_params,
        'config_params': config.get_vad_config(),
        'recognition_duration': system.recognition_duration,
        'continuous_mode': system.continuous_mode,
        'debug_mode': system.debug_mode
    }

def compare_configurations(cmd_config, gui_config):
    """对比两个版本的配置"""
    print("\n" + "=" * 60)
    print("📊 配置对比分析")
    print("=" * 60)

    print(f"参数类型\t\t命令行版本\t\tGUI版本\t\t差异")
    print("-" * 60)

    # 对比关键参数
    params = [
        ('recognition_duration', '识别时长(秒)'),
        ('continuous_mode', '连续模式'),
        ('debug_mode', '调试模式'),
        ('energy_threshold', 'VAD能量阈值'),
        ('min_speech_duration', '最小语音时长'),
        ('min_silence_duration', '最小静音时长'),
        ('speech_padding', '语音填充')
    ]

    for param, desc in params:
        cmd_val = cmd_config.get(param, 'N/A')
        gui_val = gui_config.get(param, 'N/A')

        # 获取VAD参数
        if param in ['energy_threshold', 'min_speech_duration', 'min_silence_duration', 'speech_padding']:
            if 'system_params' in cmd_config:
                cmd_val = cmd_config['system_params'].get(param, 'N/A')
            if 'system_params' in gui_config:
                gui_val = gui_config['system_params'].get(param, 'N/A')

        # 判断差异
        if cmd_val == gui_val:
            diff = "✅"
        elif cmd_val == 'N/A' or gui_val == 'N/A':
            diff = "❓"
        else:
            diff = f"⚠️ ({cmd_val} vs {gui_val})"

        print(f"{param}\t{cmd_val}\t\t{gui_val}\t\t{diff}")

    print("\n🔍 关键发现:")

    # 检查VAD能量阈值
    cmd_threshold = cmd_config.get('system_params', {}).get('energy_threshold')
    gui_threshold = gui_config.get('system_params', {}).get('energy_threshold')

    if cmd_threshold and gui_threshold:
        if abs(cmd_threshold - gui_threshold) > 0.001:
            print(f"⚠️ VAD能量阈值差异显著！")
            print(f"   命令行版本: {cmd_threshold}")
            print(f"   GUI版本: {gui_threshold}")
            print(f"   这可能是识别质量差异的关键原因！")
        else:
            print(f"✅ VAD能量阈值基本一致")

    # 检查模式差异
    if cmd_config.get('continuous_mode') != gui_config.get('continuous_mode'):
        print(f"⚠️ 连续模式设置不同！")
        print(f"   这可能影响音频处理方式")

    # 检查debug模式差异
    if cmd_config.get('debug_mode') != gui_config.get('debug_mode'):
        print(f"⚠️ Debug模式设置不同！")
        print(f"   这可能影响日志级别和性能")

if __name__ == "__main__":
    print("🔧 配置对比调试")
    print("详细分析GUI版本和命令行版本的VAD参数差异")
    print()

    cmd_config = test_command_line_config()
    gui_config = test_gui_config()

    if cmd_config and gui_config:
        compare_configurations(cmd_config, gui_config)

    print("\n✅ 配置对比完成！")