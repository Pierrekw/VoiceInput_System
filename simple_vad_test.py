#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单VAD对比测试
直接测试TEN VAD vs 能量阈值VAD的实际性能
"""

import os
import sys
import time
import numpy as np
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_energy_vad(audio_data: np.ndarray, threshold: float = 0.015) -> np.ndarray:
    """测试能量阈值VAD"""
    # 计算音频能量
    energy = np.sqrt(np.mean(audio_data ** 2, axis=1))
    is_speech = energy > threshold
    return is_speech.astype(int)

def test_ten_vad(audio_data: np.ndarray) -> np.ndarray:
    """测试TEN VAD"""
    try:
        # 导入TEN VAD
        ten_vad_path = "./onnx_deps/ten_vad"
        if os.path.exists(ten_vad_path):
            sys.path.insert(0, os.path.join(ten_vad_path, "include"))
            from ten_vad import TenVad
            ten_vad = TenVad(hop_size=256, threshold=0.5)
        else:
            raise ImportError("TEN VAD not found")

        # 处理音频数据
        chunk_size = 256  # TEN VAD要求的hop size
        num_chunks = audio_data.shape[1] // chunk_size
        speech_results = []

        print(f"🔧 TEN VAD: 处理{num_chunks}个音频块...")

        for i in range(num_chunks):
            chunk = audio_data[:, i * chunk_size:(i + 1) * chunk_size]

            # 确保音频长度为256
            if chunk.shape[1] < 256:
                chunk = np.pad(chunk, ((0, 0), (0, 256 - chunk.shape[1])), 'constant')
            elif chunk.shape[1] > 256:
                chunk = chunk[:, :256]

            # 转换为int16类型
            chunk_int16 = (chunk[0] * 32767).astype(np.int16)

            try:
                # 使用TEN VAD
                vad_confidence, vad_flag = ten_vad.process(chunk_int16)
                is_speech = (vad_flag == 1)
                speech_results.append(is_speech)

                if i % 100 == 0:  # 每100块打印一次进度
                    print(f"  块{i}: {'🎤' if is_speech else '🔇'} 置信度={vad_confidence:.3f}")
            except Exception as e:
                print(f"❌ TEN VAD处理错误: {e}")
                speech_results.append(False)

        return np.array(speech_results)

    except Exception as e:
        print(f"❌ TEN VAD测试失败: {e}")
        # 返回空的False数组
        return np.array([False] * (audio_data.shape[1] // 256))

def generate_test_audio() -> np.ndarray:
    """生成测试音频"""
    print("🎵 生成测试音频...")

    # 创建不同类型的测试音频
    duration = 10.0  # 10秒
    sample_rate = 16000
    total_samples = int(duration * sample_rate)

    # 音频数据 (1通道，时间轴)
    audio_data = np.zeros((1, total_samples), dtype=np.float32)

    # 语音段 (真实声音模拟)
    speech_segments = [
        (1.0, 2.5),   # 1-2.5秒
        (4.0, 6.0),   # 4-6秒
        (7.0, 8.5),   # 7-8.5秒
        (9.5, 11.0),  # 9.5-11秒
    ]

    for start_time, end_time in speech_segments:
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)

        # 生成类似语音的信号
        t = np.linspace(0, end_time - start_time, end_sample - start_sample)
        signal = (np.sin(2 * np.pi * 220 * t) +  # 基频
                 0.3 * np.sin(2 * np.pi * 440 * t) +  # 谐制1
                 0.2 * np.sin(2 * np.pi * 880 * t))   # 谐制2

        # 添加噪声使其更真实
        noise = np.random.normal(0, 0.1, len(signal))
        signal += noise

        # 归一化
        signal = signal / (np.max(np.abs(signal)) + 1e-10)
        signal *= 0.5  # 较大声量

        # 确保信号长度正确
        if len(signal) != (end_sample - start_sample):
            if len(signal) > (end_sample - start_sample):
                signal = signal[:(end_sample - start_sample)]
            else:
                signal = np.pad(signal, (0, (end_sample - start_sample) - len(signal)), 'constant')

        audio_data[0, start_sample:end_sample] += signal

    # 添加背景噪声
    background_noise = np.random.normal(0, 0.05, total_samples)
    audio_data[0] += background_noise

    # 归一化
    audio_data = np.clip(audio_data, -1.0, 1.0)

    print(f"✅ 测试音频生成完成: {duration}秒, {total_samples}样本")
    return audio_data

def run_comparison():
    """运行VAD对比测试"""
    print("🚀 开始VAD对比测试...")
    print("=" * 60)

    # 生成测试音频
    test_audio = generate_test_audio()

    # 测试能量阈值VAD
    print("\n" + "=" * 20 + " 测试能量阈值VAD " + "=" * 20)
    energy_start = time.time()
    energy_results = test_energy_vad(test_audio)
    energy_time = time.time() - energy_start

    # 测试TEN VAD
    print("\n" + "=" * 20 + " 测试TEN VAD " + "=" * 20)
    ten_vad_start = time.time()
    ten_vad_results = test_ten_vad(test_audio)
    ten_vad_time = time.time() - ten_vad_start

    # 计算性能指标
    print("\n" + "=" * 20 + " 性能对比分析 " + "=" * 20)

    # 基本统计
    energy_speech_count = np.sum(energy_results)
    ten_vad_speech_count = np.sum(ten_vad_results)
    total_chunks = len(energy_results)

    print(f"\n📊 基本统计:")
    print(f"   总音频块数: {total_chunks}")
    print(f"   能量阈值VAD检测语音: {energy_speech_count} 块")
    print(f"   TEN VAD检测语音: {ten_vad_speech_count} 块")

    # 假设语音段占总时间的比例
    expected_speech_ratio = 5.5 / 10.0  # 语音段总时长5.5秒 / 总时长10秒
    expected_speech_chunks = int(total_chunks * expected_speech_ratio)

    # 计算准确率 (简化版)
    energy_accuracy = 1.0 - abs(energy_speech_count - expected_speech_chunks) / total_chunks
    ten_vad_accuracy = 1.0 - abs(ten_vad_speech_count - expected_speech_chunks) / total_chunks

    print(f"\n🎯 性能指标:")
    print(f"   预期语音块数: {expected_speech_chunks}")
    print(f"   能量阈值VAD准确率: {energy_accuracy:.3f}")
    print(f"   TEN VAD准确率: {ten_vad_accuracy:.3f}")

    print(f"\n⏱️ 处理时间:")
    print(f"   能量阈值VAD: {energy_time:.3f}秒")
    print(f"   TEN VAD: {ten_vad_time:.3f}秒")

    # 性能提升分析
    accuracy_improvement = (ten_vad_accuracy - energy_accuracy) * 100
    time_ratio = ten_vad_time / energy_time if energy_time > 0 else 1.0

    print(f"\n📈 性能提升:")
    print(f"   准确率提升: {accuracy_improvement:+.1f}%")
    print(f"   处理时间比: {time_ratio:.2f}x")

    # 推荐结论
    print(f"\n🏆 推荐结论:")
    if ten_vad_accuracy > energy_accuracy:
        if accuracy_improvement > 10:
            print("   🌟 TEN VAD表现显著优于能量阈值VAD")
            print("   ⭐ 推荐在生产环境中使用TEN VAD")
        else:
            print("   ✅ TEN VAD优于能量阈值VAD")
            print("   ⭐ 推荐升级到TEN VAD")
    elif energy_accuracy > ten_vad_accuracy:
        print("   ⚠️ 能量阈值VAD在此测试中表现更好")
        print("   💡 建议调整TEN VAD参数或使用场景")
    else:
        print("   ➰️ 两种VAD性能相近")
        print("   💡 可以根据其他需求(延迟、资源占用)选择")

    return {
        'energy_accuracy': energy_accuracy,
        'ten_vad_accuracy': ten_vad_accuracy,
        'accuracy_improvement': accuracy_improvement,
        'energy_time': energy_time,
        'ten_vad_time': ten_vad_time
    }

if __name__ == "__main__":
    try:
        results = run_comparison()
        print("\n" + "=" * 60)
        print("🎉 VAD对比测试完成！")
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")