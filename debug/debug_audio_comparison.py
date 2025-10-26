#!/usr/bin/env python3
"""
音频数据流对比调试脚本
对比GUI版本和命令行版本的音频输入特征
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_f import FunASRVoiceSystem
import logging
import time

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioDataCollector:
    """音频数据收集器"""
    def __init__(self):
        self.audio_events = []
        self.energy_levels = []
        self.vad_events = []

    def record_vad_event(self, event_type: str, event_data: dict):
        """记录VAD事件"""
        energy = event_data.get('energy', 0)
        timestamp = time.time()

        event = {
            'timestamp': timestamp,
            'type': event_type,
            'energy': energy,
            'data': event_data
        }

        self.vad_events.append(event)
        self.energy_levels.append(energy)

        # 只记录关键事件
        if event_type in ['speech_start', 'speech_end']:
            logger.info(f"[音频调试] {event_type}: 能量={energy:.6f}")

def test_command_line_audio():
    """测试命令行版本的音频输入"""
    print("=" * 60)
    print("🎤 测试命令行版本音频输入 (main_f.py)")
    print("=" * 60)

    collector = AudioDataCollector()

    # 创建命令行版本系统
    system = FunASRVoiceSystem(
        recognition_duration=15,  # 15秒测试
        continuous_mode=False,
        debug_mode=True
    )

    if not system.initialize():
        print("❌ 命令行版本初始化失败")
        return None

    # 设置VAD回调收集数据
    def vad_callback(event_type: str, event_data: dict):
        collector.record_vad_event(event_type, event_data)

    system.set_vad_callback(vad_callback)

    print("✅ 开始15秒音频输入测试...")
    print("请说话进行测试...")

    start_time = time.time()

    # 运行15秒
    system.run_continuous()

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ 测试完成，耗时: {duration:.1f}秒")
    print(f"📊 收集到 {len(collector.vad_events)} 个VAD事件")
    print(f"📊 能量级别范围: {min(collector.energy_levels):.6f} - {max(collector.energy_levels):.6f}")

    return collector

def test_gui_audio_simulation():
    """模拟GUI版本的音频输入（使用相同参数）"""
    print("\n" + "=" * 60)
    print("🖥️ 模拟GUI版本音频输入 (相同参数)")
    print("=" * 60)

    collector = AudioDataCollector()

    # 创建GUI版本参数的系统
    system = FunASRVoiceSystem(
        recognition_duration=-1,  # GUI版本参数
        continuous_mode=True,     # GUI版本参数
        debug_mode=False          # GUI版本参数
    )

    if not system.initialize():
        print("❌ GUI版本模拟初始化失败")
        return None

    # 设置VAD回调收集数据
    def vad_callback(event_type: str, event_data: dict):
        collector.record_vad_event(event_type, event_data)

    system.set_vad_callback(vad_callback)

    print("✅ 开始15秒音频输入测试...")
    print("请说话进行测试...")

    start_time = time.time()

    # 运行15秒（GUI版本实际是连续运行，这里只测试15秒）
    original_duration = system.recognition_duration
    system.recognition_duration = 15
    system.continuous_mode = False  # 临时改为15秒模式便于测试

    try:
        system.run_continuous()
    except KeyboardInterrupt:
        print("⏹️ 测试被中断")
    finally:
        # 恢复原始参数
        system.recognition_duration = original_duration
        system.continuous_mode = True

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ 测试完成，耗时: {duration:.1f}秒")
    print(f"📊 收集到 {len(collector.vad_events)} 个VAD事件")
    print(f"📊 能量级别范围: {min(collector.energy_levels):.6f} - {max(collector.energy_levels):.6f}")

    return collector

def compare_audio_data(cmd_data, gui_data):
    """对比两个版本的音频数据"""
    print("\n" + "=" * 60)
    print("📊 音频数据对比分析")
    print("=" * 60)

    if not cmd_data or not gui_data:
        print("❌ 缺少对比数据")
        return

    # 基础统计
    print(f"命令行版本: {len(cmd_data.vad_events)} 个事件, 能量范围: {min(cmd_data.energy_levels):.6f}-{max(cmd_data.energy_levels):.6f}")
    print(f"GUI版本: {len(gui_data.vad_events)} 个事件, 能量范围: {min(gui_data.energy_levels):.6f}-{max(gui_data.energy_levels):.6f}")

    # 语音事件统计
    cmd_speech_start = len([e for e in cmd_data.vad_events if e['type'] == 'speech_start'])
    cmd_speech_end = len([e for e in cmd_data.vad_events if e['type'] == 'speech_end'])
    gui_speech_start = len([e for e in gui_data.vad_events if e['type'] == 'speech_start'])
    gui_speech_end = len([e for e in gui_data.vad_events if e['type'] == 'speech_end'])

    print(f"\n语音事件统计:")
    print(f"命令行版本: speech_start={cmd_speech_start}, speech_end={cmd_speech_end}")
    print(f"GUI版本: speech_start={gui_speech_start}, speech_end={gui_speech_end}")

    # 能量级别对比
    cmd_avg_energy = sum(cmd_data.energy_levels) / len(cmd_data.energy_levels) if cmd_data.energy_levels else 0
    gui_avg_energy = sum(gui_data.energy_levels) / len(gui_data.energy_levels) if gui_data.energy_levels else 0

    print(f"\n能量级别对比:")
    print(f"命令行版本平均能量: {cmd_avg_energy:.6f}")
    print(f"GUI版本平均能量: {gui_avg_energy:.6f}")
    print(f"能量差异: {abs(cmd_avg_energy - gui_avg_energy):.6f}")

    # 关键发现
    print(f"\n🔍 关键发现:")
    if abs(cmd_avg_energy - gui_avg_energy) > 0.001:
        print(f"⚠️ 两个版本的平均能量差异显著！")
        print(f"   这可能是导致识别质量差异的原因")
    else:
        print(f"✅ 两个版本的平均能量基本一致")

    if cmd_speech_start != gui_speech_start:
        print(f"⚠️ 语音检测事件数量不同！")
        print(f"   这可能是VAD配置或线程处理的问题")
    else:
        print(f"✅ 语音检测事件数量一致")

if __name__ == "__main__":
    print("🎤 音频数据流对比调试")
    print("将分别测试命令行版本和GUI版本模拟的音频输入")
    print("请在相同环境下进行两次测试\n")

    print("🚀 开始命令行版本测试...")
    cmd_data = test_command_line_audio()

    print("\n🚀 开始GUI版本模拟测试...")
    gui_data = test_gui_audio_simulation()

    if cmd_data and gui_data:
        compare_audio_data(cmd_data, gui_data)

    print("\n✅ 调试完成！")