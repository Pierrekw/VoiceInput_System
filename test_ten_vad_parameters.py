#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEN VAD 参数测试工具
用于测试不同threshold和hop_size参数对语音检测效果的影响
"""

import os
import sys
import time
import numpy as np
import logging
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_ten_vad_parameters():
    """测试不同TEN VAD参数的效果"""

    print("=" * 80)
    print("🔬 TEN VAD 参数测试工具")
    print("=" * 80)

    try:
        from ten_vad import TenVad
        print("✅ TEN VAD 模块加载成功")
    except ImportError as e:
        print(f"❌ TEN VAD 不可用: {e}")
        return

    # 测试配置
    test_configs = [
        {"hop_size": 128, "threshold": 0.3, "name": "低延迟高敏感 (实时对话)"},
        {"hop_size": 128, "threshold": 0.4, "name": "低延迟中等敏感"},
        {"hop_size": 256, "threshold": 0.5, "name": "当前默认配置"},
        {"hop_size": 256, "threshold": 0.6, "name": "安静环境优化"},
        {"hop_size": 512, "threshold": 0.3, "name": "嘈杂环境适应"},
        {"hop_size": 512, "threshold": 0.5, "name": "低功耗配置"},
    ]

    print("\n📋 测试配置:")
    for i, config in enumerate(test_configs, 1):
        print(f"  {i}. {config['name']}")
        print(f"     Hop Size: {config['hop_size']} ({config['hop_size']/16000*1000:.1f}ms)")
        print(f"     Threshold: {config['threshold']}")
        print()

    try:
        choice = input("请选择要测试的配置编号 (1-6)，或按Enter测试所有配置: ").strip()

        if choice == "":
            test_configs_to_test = test_configs
            print("\n🚀 测试所有配置...")
        else:
            config_index = int(choice) - 1
            if 0 <= config_index < len(test_configs):
                test_configs_to_test = [test_configs[config_index]]
                print(f"\n🎯 测试配置: {test_configs_to_test[0]['name']}")
            else:
                print("❌ 无效配置编号")
                return

    except ValueError:
        print("❌ 无效输入，将测试所有配置")
        test_configs_to_test = test_configs

    # 执行测试
    print("\n" + "=" * 80)
    print("🧪 开始参数测试...")
    print("=" * 80)

    for config in test_configs_to_test:
        test_single_config(config)

    print("\n" + "=" * 80)
    print("✅ 参数测试完成！")
    print("💡 建议根据你的具体使用场景选择合适的参数配置")
    print("=" * 80)

def test_single_config(config: Dict):
    """测试单个配置"""

    print(f"\n🔬 测试配置: {config['name']}")
    print(f"   Hop Size: {config['hop_size']} ({config['hop_size']/16000*1000:.1f}ms)")
    print(f"   Threshold: {config['threshold']}")
    print("-" * 60)

    try:
        # 创建VAD模型
        model = TenVad(hop_size=config['hop_size'], threshold=config['threshold'])

        # 测试模拟数据
        test_scenarios = [
            {
                "name": "静音测试",
                "description": "完全静音，应该返回无语音",
                "data": create_silence_audio(2.0),
                "expected_speech": False
            },
            {
                "name": "轻声语音测试",
                "description": "模拟轻声说话，中等敏感度可能检测不到",
                "data": create_quiet_speech_audio(),
                "expected_speech": "可能检测到"
            },
            {
                "name": "正常语音测试",
                "description": "正常音量语音，应该检测到",
                "data": create_normal_speech_audio(),
                "expected_speech": True
            },
            {
                "name": "噪音测试",
                "description": "模拟环境噪音，应该返回无语音",
                "data": create_noise_audio(),
                "expected_speech": False
            }
        ]

        results = []

        for scenario in test_scenarios:
            result = test_vad_scenario(model, scenario, config['hop_size'])
            results.append(result)

        # 输出结果总结
        print(f"\n📊 配置 '{config['name']}' 测试结果:")
        for result in results:
            status = "✅" if result['passed'] else "❌"
            print(f"   {status} {result['scenario']}: {result['summary']}")

        print(f"   🎯 平均置信度: {np.mean([r['confidence'] for r in results]):.3f}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_vad_scenario(model, scenario: Dict, hop_size: int) -> Dict:
    """测试单个VAD场景"""

    audio_data = scenario['data']
    scenario_name = scenario['name']

    # 处理音频数据
    speech_count = 0
    total_confidence = 0.0
    frame_count = 0

    # 按hop_size分帧处理
    for i in range(0, len(audio_data), hop_size):
        frame = audio_data[i:i+hop_size]
        if len(frame) < hop_size:
            frame = np.pad(frame, (0, hop_size - len(frame)), 'constant')

        # 转换为int16格式
        frame_int16 = (frame * 32767).astype(np.int16)

        # 获取VAD结果
        confidence, flag = model.process(frame_int16)

        total_confidence += confidence
        frame_count += 1

        if flag == 1:  # 检测到语音
            speech_count += 1

    avg_confidence = total_confidence / frame_count if frame_count > 0 else 0.0
    speech_ratio = speech_count / frame_count if frame_count > 0 else 0.0

    # 判断测试是否通过
    if isinstance(scenario['expected_speech'], bool):
        passed = (speech_ratio > 0.3) == scenario['expected_speech']
    else:  # "可能检测到"
        passed = 0.1 <= speech_ratio <= 0.7

    return {
        'scenario': scenario_name,
        'passed': passed,
        'speech_ratio': speech_ratio,
        'confidence': avg_confidence,
        'summary': f"语音帧比例={speech_ratio:.1%}, 平均置信度={avg_confidence:.3f}"
    }

def create_silence_audio(duration: float) -> np.ndarray:
    """创建静音"""
    sample_rate = 16000
    samples = int(duration * sample_rate)
    return np.zeros(samples, dtype=np.float32)

def create_quiet_speech_audio() -> np.ndarray:
    """创建轻声语音模拟数据"""
    sample_rate = 16000
    duration = 1.0
    samples = int(duration * sample_rate)

    # 生成低振幅正弦波模拟轻声
    t = np.linspace(0, duration, samples)
    frequency = 200  # Hz
    amplitude = 0.05  # 低振幅
    signal = amplitude * np.sin(2 * np.pi * frequency * t)

    # 添加一些变化
    signal += 0.02 * np.random.randn(samples)
    return signal.astype(np.float32)

def create_normal_speech_audio() -> np.ndarray:
    """创建正常音量语音模拟数据"""
    sample_rate = 16000
    duration = 1.5
    samples = int(duration * sample_rate)

    # 生成中等振幅的复合信号模拟语音
    t = np.linspace(0, duration, samples)

    # 多个频率分量模拟语音特征
    signal = np.zeros(samples)
    frequencies = [150, 300, 600, 1200]  # 基频和泛音
    amplitudes = [0.3, 0.2, 0.15, 0.1]

    for freq, amp in zip(frequencies, amplitudes):
        signal += amp * np.sin(2 * np.pi * freq * t)

    # 添加包络和变化
    envelope = np.ones(samples)
    envelope[:int(samples*0.1)] = np.linspace(0, 1, int(samples*0.1))
    envelope[-int(samples*0.1):] = np.linspace(1, 0, int(samples*0.1))

    signal *= envelope
    signal += 0.05 * np.random.randn(samples)

    return signal.astype(np.float32)

def create_noise_audio() -> np.ndarray:
    """创建噪音音频"""
    sample_rate = 16000
    duration = 1.0
    samples = int(duration * sample_rate)

    # 生成白噪音
    noise = 0.1 * np.random.randn(samples)
    return noise.astype(np.float32)

def print_parameter_recommendations():
    """打印参数建议"""

    print("\n" + "=" * 80)
    print("💡 参数选择建议")
    print("=" * 80)

    recommendations = [
        {
            "场景": "实时视频会议",
            "推荐": "hop_size=128, threshold=0.4",
            "原因": "低延迟确保即时响应，中等敏感度捕捉自然说话"
        },
        {
            "场景": "办公室录音",
            "推荐": "hop_size=256, threshold=0.6",
            "原因": "高阈值避免键盘声等误判，标准hop_size平衡性能"
        },
        {
            "场景": "户外嘈杂环境",
            "推荐": "hop_size=512, threshold=0.3",
            "原因": "低敏感度在噪音中检测语音，大hop_size节省资源"
        },
        {
            "场景": "语音助手/智能家居",
            "推荐": "hop_size=256, threshold=0.5",
            "原因": "平衡配置适合大多数家庭环境"
        },
        {
            "场景": "移动设备应用",
            "推荐": "hop_size=512, threshold=0.4",
            "原因": "节省电池，在移动环境中保持较好检测效果"
        }
    ]

    for rec in recommendations:
        print(f"\n🎯 {rec['场景']}:")
        print(f"   推荐配置: {rec['推荐']}")
        print(f"   原因: {rec['原因']}")

if __name__ == "__main__":
    try:
        test_ten_vad_parameters()
        print_parameter_recommendations()

    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()