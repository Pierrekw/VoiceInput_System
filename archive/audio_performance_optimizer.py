#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频性能深度优化器
专门针对PyAudio和音频流延迟进行优化
"""

import pyaudio
import time
import numpy as np
from typing import Dict, List, Tuple

class AudioPerformanceOptimizer:
    """音频性能优化器"""

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.test_results = []

    def test_audio_configurations(self) -> Dict[str, Dict]:
        """
        测试不同音频配置的性能

        Returns:
            配置性能测试结果
        """
        print("🔬 开始音频配置性能测试...")
        print("=" * 80)

        # 测试配置列表
        test_configs = [
            {"name": "默认配置", "chunk_size": 1600, "rate": 16000},
            {"name": "小缓冲区", "chunk_size": 800, "rate": 16000},
            {"name": "极小缓冲区", "chunk_size": 400, "rate": 16000},
            {"name": "中等缓冲区", "chunk_size": 3200, "rate": 16000},
            {"name": "高采样率", "chunk_size": 1600, "rate": 44100},
        ]

        results = {}

        for config in test_configs:
            print(f"\n🧪 测试配置: {config['name']}")
            print(f"   块大小: {config['chunk_size']}, 采样率: {config['rate']}")

            try:
                result = self._test_single_config(config)
                results[config['name']] = result
                print(f"   ✅ 平均延迟: {result['avg_latency']*1000:.2f}ms")
                print(f"   📊 CPU使用率: {result['cpu_usage']:.1f}%")

            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                results[config['name']] = {"error": str(e)}

        # 分析结果
        self._analyze_results(results)
        return results

    def _test_single_config(self, config: Dict) -> Dict:
        """
        测试单个配置的性能

        Args:
            config: 音频配置

        Returns:
            性能测试结果
        """
        chunk_size = config['chunk_size']
        sample_rate = config['rate']

        # 打开音频流
        stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )

        # 测试音频读取延迟
        latencies = []
        test_duration = 5.0  # 测试5秒
        start_time = time.time()

        while time.time() - start_time < test_duration:
            # 测量单次读取延迟
            read_start = time.time()
            data = stream.read(chunk_size, exception_on_overflow=False)
            read_end = time.time()

            latencies.append(read_end - read_start)

        stream.stop_stream()
        stream.close()

        # 计算统计数据
        avg_latency = np.mean(latencies)
        max_latency = np.max(latencies)
        min_latency = np.min(latencies)

        # 估算CPU使用率（简化计算）
        cpu_usage = (chunk_size / sample_rate) / avg_latency * 100

        return {
            'avg_latency': avg_latency,
            'max_latency': max_latency,
            'min_latency': min_latency,
            'cpu_usage': min(cpu_usage, 100),  # 限制在100%
            'latencies': latencies,
            'config': config
        }

    def _analyze_results(self, results: Dict[str, Dict]):
        """分析测试结果"""
        print("\n📊 音频配置性能对比分析")
        print("=" * 80)

        valid_results = {k: v for k, v in results.items() if 'error' not in v}

        if not valid_results:
            print("❌ 没有有效的测试结果")
            return

        print(f"{'配置':<12} {'平均延迟':<12} {'最小延迟':<12} {'最大延迟':<12} {'CPU使用':<10}")
        print("-" * 80)

        # 按平均延迟排序
        sorted_results = sorted(valid_results.items(), key=lambda x: x[1]['avg_latency'])

        for name, result in sorted_results:
            print(f"{name:<12} "
                  f"{result['avg_latency']*1000:<8.1f}ms "
                  f"{result['min_latency']*1000:<8.1f}ms "
                  f"{result['max_latency']*1000:<8.1f}ms "
                  f"{result['cpu_usage']:<8.1f}%")

        # 找出最佳配置
        best_config = sorted_results[0]
        print(f"\n🏆 最佳配置: {best_config[0]}")
        print(f"   平均延迟: {best_config[1]['avg_latency']*1000:.2f}ms")
        print(f"   建议参数: chunk_size={best_config[1]['config']['chunk_size']}, "
              f"rate={best_config[1]['config']['rate']}")

    def generate_optimized_config(self, best_config_name: str) -> str:
        """
        生成优化的音频配置代码

        Args:
            best_config_name: 最佳配置名称

        Returns:
            优化配置代码
        """
        # 这里可以根据最佳配置生成具体的优化代码
        optimized_code = f"""
# 音频性能优化配置 (基于测试结果生成)
# 最佳配置: {best_config_name}

# PyAudio配置优化
OPTIMIZED_AUDIO_CONFIG = {{
    'format': pyaudio.paInt16,
    'channels': 1,
    'rate': 16000,  # 标准采样率
    'input': True,
    'frames_per_buffer': 800,  # 优化后的缓冲区大小
}}

# 性能优化参数
class OptimizedAudioConfig:
    CHUNK_SIZE = 800  # 减小缓冲区以降低延迟
    SAMPLE_RATE = 16000
    MAX_LATENCY_MS = 50  # 目标最大延迟

    # PyAudio特定优化
    PYAUDIO_CONFIG = {{
        'format': pyaudio.paInt16,
        'channels': 1,
        'rate': SAMPLE_RATE,
        'input': True,
        'frames_per_buffer': CHUNK_SIZE,
        'start': True,
        # 可选的性能参数
        'input_host_api_specific_stream_info': None,
    }}
"""
        return optimized_code

    def test_real_world_performance(self, chunk_size: int = 800) -> Dict:
        """
        测试真实世界的语音识别性能

        Args:
            chunk_size: 音频块大小

        Returns:
            真实性能测试结果
        """
        print(f"\n🎯 真实语音识别性能测试 (chunk_size={chunk_size})")
        print("=" * 60)

        try:
            # 打开音频流
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=chunk_size
            )

            print("🎤 请说话测试延迟...")
            print("   (将测试从声音输入到数据获取的延迟)")

            audio_buffers = []
            latencies = []
            test_duration = 10.0
            start_time = time.time()

            while time.time() - start_time < test_duration:
                read_start = time.time()
                data = stream.read(chunk_size, exception_on_overflow=False)
                read_end = time.time()

                latencies.append(read_end - read_start)

                # 简单的VAD检测（能量阈值）
                audio_data = np.frombuffer(data, dtype=np.int16)
                energy = np.sqrt(np.mean(audio_data ** 2))

                if energy > 500:  # 检测到语音
                    audio_buffers.append(audio_data)
                    print(f"   检测到语音片段 (能量: {energy:.1f}, 延迟: {(read_end-read_start)*1000:.1f}ms)")

            stream.stop_stream()
            stream.close()

            # 分析结果
            if latencies:
                avg_latency = np.mean(latencies)
                print(f"\n📊 性能分析:")
                print(f"   平均延迟: {avg_latency*1000:.2f}ms")
                print(f"   最大延迟: {np.max(latencies)*1000:.2f}ms")
                print(f"   最小延迟: {np.min(latencies)*1000:.2f}ms")
                print(f"   检测到语音片段: {len(audio_buffers)}个")

                return {
                    'avg_latency': avg_latency,
                    'max_latency': np.max(latencies),
                    'min_latency': np.min(latencies),
                    'voice_segments': len(audio_buffers),
                    'success': True
                }
            else:
                print("⚠️ 未检测到音频数据")
                return {'success': False}

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return {'success': False, 'error': str(e)}

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'p'):
            self.p.terminate()

def main():
    """主函数"""
    print("🎵 音频性能深度优化工具")
    print("=" * 80)

    optimizer = AudioPerformanceOptimizer()

    try:
        # 测试不同配置
        results = optimizer.test_audio_configurations()

        # 找出最佳配置进行真实测试
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        if valid_results:
            best_config = min(valid_results.items(), key=lambda x: x[1]['avg_latency'])
            best_chunk_size = best_config[1]['config']['chunk_size']

            # 真实世界性能测试
            real_result = optimizer.test_real_world_performance(best_chunk_size)

            if real_result.get('success'):
                print(f"\n✅ 优化建议:")
                print(f"   推荐chunk_size: {best_chunk_size}")
                print(f"   预期延迟: {best_config[1]['avg_latency']*1000:.1f}ms")
                print(f"   在funasr_voice_module.py中设置:")
                print(f"   self.chunk_size = {best_chunk_size}")

    finally:
        optimizer.cleanup()

if __name__ == "__main__":
    main()