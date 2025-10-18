#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR CPU优化版本测试程序
针对集成显卡和低配置电脑优化，使用CPU推理
"""

import os
import sys
import time
import logging
import numpy as np
from contextlib import contextmanager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 尝试导入FunASR
FUNASR_AVAILABLE = False
try:
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
    logger.info("✅ 成功导入FunASR模块")
except ImportError as e:
    logger.error(f"❌ 无法导入FunASR模块: {e}")
    logger.error("请安装FunASR: pip install funasr")
    AutoModel = None

# 音频流上下文管理器
@contextmanager
def audio_stream(sample_rate=16000, chunk_size=8000):
    """打开PyAudio输入流并自动清理"""
    import pyaudio

    p = pyaudio.PyAudio()
    stream = None
    try:
        # 获取默认音频设备信息
        default_device = p.get_default_input_device_info()
        logger.info(f"🎤 使用音频设备: {default_device['name']} (索引: {default_device['index']})")

        # 打开音频流
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
            start=True
        )
        logger.info(f"🎧 音频流创建成功 - 活动状态: {stream.is_active()}")
        yield stream
    except Exception as e:
        logger.error(f"❌ 音频流创建失败: {e}")
        raise
    finally:
        # 资源清理
        if stream:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
        p.terminate()

class FunASRCpuOptimizedTest:
    """FunASR CPU优化测试类"""

    def __init__(self, model_path="f:\\04_AI\\01_Workplace\\Voice_Input\\model\\fun"):
        """初始化测试类"""
        self.model_path = model_path
        self._model = None
        self.model_loaded = False
        self.load_time = 0.0
        self.sample_rate = 16000
        self.chunk_size = 8000

    def load_model(self):
        """加载FunASR模型（CPU优化版本）"""
        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR模块不可用，无法加载模型")
            return False

        if self.model_loaded and self._model is not None:
            logger.info("✅ FunASR模型已加载，无需重复加载")
            return True

        logger.info(f"📦 开始加载FunASR CPU优化模型: {self.model_path}")
        start_time = time.time()

        try:
            # 创建FunASR模型，强制使用CPU
            logger.info("🔄 正在初始化CPU优化模型...")
            logger.info(f"  - model: {self.model_path}")
            logger.info("  - device: cpu (CPU优化模式)")
            logger.info("  - 适合: 集成显卡、低配置电脑")

            # 使用CPU设备，适合集成显卡
            self._model = AutoModel(
                model=self.model_path,
                device="cpu",
                trust_remote_code=False  # 确保使用本地代码
            )

            self.model_loaded = True
            self.load_time = time.time() - start_time
            logger.info(f"✅ FunASR CPU优化模型加载完成 (耗时: {self.load_time:.2f}秒)")
            return True

        except Exception as e:
            logger.error(f"❌ FunASR模型加载失败: {e}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            self._model = None
            self.model_loaded = False
            return False

    def test_recognition(self, duration=30):
        """测试语音识别功能 - CPU优化版本"""
        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR模块不可用，无法进行识别测试")
            return False

        if not self.model_loaded or self._model is None:
            logger.warning("⚠️ 模型未加载，尝试加载...")
            if not self.load_model():
                logger.error("❌ 无法加载模型，测试终止")
                return False

        logger.info("🎤 准备进行CPU优化版语音识别测试...")

        print("=" * 60)
        print("📢 FunASR CPU优化 语音识别测试")
        print("=" * 60)
        print("🔊 请确保您的麦克风已开启并正常工作")
        print(f"⏱️  测试将持续 {duration} 秒")
        print("💬 请在提示开始后对着麦克风说话")
        print("🎯 您可以说一些中文句子")
        print("⚡ 优化: CPU推理，适合集成显卡")
        print("🔧 集成功能: VAD + PUNC")
        print("=" * 60)

        # 检查是否为交互式环境
        import sys
        is_interactive = hasattr(sys, 'ps1') or sys.flags.interactive

        if is_interactive:
            print("\n请按Enter键开始测试...")
            input()

        # 倒计时
        countdown = 5
        print(f"\n⏰ 录音将在 {countdown} 秒后开始...")
        for i in range(countdown, 0, -1):
            print(f"🔴 准备中: {i}秒 ", end="\r")
            time.sleep(1)
        print()
        print("""
==================================================================
🔵 正在录音！请对着麦克风说话...🔵
==================================================================
        """)

        # 语音活动检测参数 - CPU优化版
        speech_energy_threshold = 0.02   # 略微提高阈值，减少误检测
        min_speech_duration = 0.4        # 最小语音时长
        min_silence_duration = 0.8       # 静音时长

        # 识别状态控制
        speech_segment_audio = []
        is_speech_segment = False
        speech_start_time = 0
        last_speech_time = 0
        recognition_count = 0
        last_recognized_text = ""
        collected_text = []

        # 文本相似度检测
        def calculate_text_similarity(text1, text2):
            """计算文本相似度"""
            if not text1 or not text2:
                return 0.0
            import re
            clean1 = re.sub(r'[^\w]', '', text1.lower())
            clean2 = re.sub(r'[^\w]', '', text2.lower())
            if not clean1 or not clean2:
                return 0.0
            set1, set2 = set(clean1), set(clean2)
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            return intersection / union if union > 0 else 0.0

        def is_duplicate_text(new_text, previous_text):
            """判断重复文本"""
            if not previous_text:
                return False
            similarity = calculate_text_similarity(new_text, previous_text)
            return similarity >= 0.8

        def post_process_text(text):
            """后处理文本"""
            if not text:
                return text
            # 移除重复字符
            result = []
            prev_char = None
            for char in text:
                if char != prev_char:
                    result.append(char)
                prev_char = char
            return ''.join(result)

        def is_valid_text(text):
            """检查文本有效性"""
            if not text or len(text.strip()) < 2:
                return False
            # 过滤误识别
            invalid_patterns = ['e', 'yeah', '嗯', '啊', '哦', '呃', '额']
            text_clean = text.strip().lower()
            for pattern in invalid_patterns:
                if text_clean == pattern or text_clean.count(pattern) > 2:
                    return False
            # 检查有意义字符
            import re
            meaningful_chars = re.findall(r'[\u4e00-\u9fff\w]', text)
            return len(meaningful_chars) >= 2

        try:
            with audio_stream(sample_rate=self.sample_rate, chunk_size=self.chunk_size) as stream:
                print("\n🔴 使用FunASR CPU优化版本进行语音识别...")
                print("💡 CPU推理模式，适合集成显卡和低配置电脑")

                start_time = time.time()
                frames_processed = 0

                while time.time() - start_time < duration:
                    try:
                        # 读取音频数据
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames_processed += 1

                        # 转换为numpy数组
                        audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                        current_time = time.time() - start_time

                        # 计算音频能量
                        audio_energy = np.sqrt(np.mean(audio_data**2))
                        is_speech = audio_energy > speech_energy_threshold

                        if is_speech and not is_speech_segment:
                            # 开始语音段
                            is_speech_segment = True
                            speech_start_time = current_time
                            speech_segment_audio = []
                            logger.info(f"🎯 开始语音段，能量: {audio_energy:.4f}")

                        elif is_speech and is_speech_segment:
                            # 继续语音段
                            last_speech_time = current_time

                        elif not is_speech and is_speech_segment:
                            # 检查语音是否结束
                            silence_duration = current_time - last_speech_time
                            speech_duration = current_time - speech_start_time

                            should_end = (
                                silence_duration >= min_silence_duration or
                                (silence_duration >= 0.5 and speech_duration >= 1.0)
                            )

                            if should_end:
                                # 语音段结束，进行识别
                                is_speech_segment = False

                                if speech_duration >= min_speech_duration and len(speech_segment_audio) > 0:
                                    recognition_count += 1
                                    logger.info(f"语音段结束，时长: {speech_duration:.2f}s")

                                    # 使用FunASR进行识别
                                    try:
                                        result = self._model.generate(
                                            input=np.array(speech_segment_audio)
                                        )

                                        if result and isinstance(result, list) and len(result) > 0 and "text" in result[0]:
                                            raw_text = result[0]["text"].strip()
                                            if raw_text:
                                                processed_text = post_process_text(raw_text)

                                                if is_valid_text(processed_text):
                                                    if not is_duplicate_text(processed_text, last_recognized_text):
                                                        last_recognized_text = processed_text
                                                        collected_text.append(processed_text)

                                                        print(f"\n🎯 CPU识别: {processed_text}")
                                                        logger.info(f"识别结果: '{processed_text}'")

                                    except Exception as e:
                                        logger.debug(f"识别异常: {e}")

                        # 收集语音数据
                        if is_speech_segment:
                            speech_segment_audio.extend(audio_data)

                        # 状态显示
                        remaining_time = duration - current_time
                        if frames_processed % 50 == 0:
                            if is_speech_segment:
                                status = "🗣️ 说话中"
                                speech_duration = current_time - speech_start_time
                                extra_info = f"({speech_duration:.1f}s)"
                            else:
                                status = "🔇 静音"
                                extra_info = ""

                            print(f"\r{status}{extra_info} | 能量:{audio_energy:.4f} | 剩余:{remaining_time:.1f}s | 识别:{recognition_count} | ", end="", flush=True)

                    except Exception as e:
                        logger.error(f"❌ 音频处理错误: {e}")
                        continue

                # 处理最终结果
                print(f"\n🏁 录音结束，处理最终结果...")

                if is_speech_segment and len(speech_segment_audio) > 0:
                    speech_duration = time.time() - start_time - speech_start_time
                    if speech_duration >= min_speech_duration:
                        try:
                            final_result = self._model.generate(
                                input=np.array(speech_segment_audio)
                            )
                            if final_result and isinstance(final_result, list) and len(final_result) > 0 and "text" in final_result[0]:
                                final_text = final_result[0]["text"].strip()
                                if final_text and final_text != last_recognized_text:
                                    collected_text.append(final_text)
                                    print(f"🎯 最终识别: {final_text}")
                        except Exception as e:
                            logger.debug(f"最终识别异常: {e}")

                # 输出统计信息
                print("\n" + "=" * 60)
                print("📊 CPU优化版测试结果")
                print("=" * 60)

                if collected_text:
                    # 去重
                    unique_texts = []
                    for text in collected_text:
                        if not unique_texts or not is_duplicate_text(text, unique_texts[-1]):
                            unique_texts.append(text)

                    final_text = " ".join(unique_texts)
                    print(f"📝 识别文本: {final_text}")
                    print(f"🔢 片段数量: {len(unique_texts)} (去重后)")

                    for i, text in enumerate(unique_texts, 1):
                        print(f"   {i}. {text}")
                else:
                    print("❌ 未识别到语音内容")
                    print("\n💡 可能原因:")
                    print("   - 麦克风问题")
                    print("   - 说话音量太小")
                    print("   - 环境噪音")
                    print("   - 模型配置问题")

                print(f"\n📈 CPU优化统计:")
                print(f"   - 测试时长: {duration}秒")
                print(f"   - 模型加载: {self.load_time:.2f}秒")
                print(f"   - 处理帧数: {frames_processed}")
                print(f"   - 识别次数: {recognition_count}")

                print(f"\n💡 CPU优化优势:")
                print(f"   - ✅ 适合集成显卡")
                print(f"   - ✅ 低内存占用")
                print(f"   - ✅ 稳定推理")
                print(f"   - ✅ 兼容性好")

                return True

        except KeyboardInterrupt:
            print("\n⏹️  测试被用户中断")
            return True
        except Exception as e:
            logger.error(f"❌ 测试错误: {e}")
            return False

    def get_status(self):
        """获取状态信息"""
        return {
            "funasr_available": FUNASR_AVAILABLE,
            "model_loaded": self.model_loaded,
            "model_path": self.model_path,
            "load_time": self.load_time
        }

    def print_status(self):
        """打印状态信息"""
        status = self.get_status()
        print("\n📊 CPU优化版状态:")
        print(f"  - FunASR可用: {'✅ 是' if status['funasr_available'] else '❌ 否'}")
        print(f"  - 模型加载: {'✅ 已加载' if status['model_loaded'] else '❌ 未加载'}")
        print(f"  - 模型路径: {status['model_path']}")
        print(f"  - 加载时间: {status['load_time']:.2f}秒" if status['load_time'] > 0 else "  - 加载时间: 未加载")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 FunASR CPU优化 语音识别测试")
    print("=" * 60)
    print("💻 适合: 集成显卡、低配置电脑")
    print("⚡ 优化: CPU推理、低内存占用")
    print("\n")

    # 创建测试实例
    tester = FunASRCpuOptimizedTest()
    tester.print_status()

    # 测试模型加载
    print("\n🔄 开始测试CPU优化模型加载...")
    load_success = tester.load_model()

    if load_success:
        tester.print_status()

        # 测试语音识别
        try:
            print("\n")
            tester.test_recognition(duration=30)
        except KeyboardInterrupt:
            print("\n⏹️  测试被用户中断")

        print("\n✅ CPU优化测试完成")
    else:
        print("\n❌ 模型加载失败")
        print("💡 请检查:")
        print("   1. FunASR是否安装: pip install funasr")
        print("   2. 模型路径是否正确")
        print("   3. Python环境是否兼容")

if __name__ == "__main__":
    main()