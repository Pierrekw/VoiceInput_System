#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR测试程序
用于测试FunASR模型的加载和基本语音识别功能
"""

import os
import sys
import time
import logging
import pyaudio
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
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    FUNASR_AVAILABLE = True
    logger.info("✅ 成功导入FunASR模块")
except ImportError as e:
    logger.error(f"❌ 无法导入FunASR模块: {e}")
    logger.error("请执行: pip install funasr torch 或 uv add funasr torch 安装该模块")
    # 导入时使用类型注解，运行时不影响行为
    AutoModel = None
    rich_transcription_postprocess = None

# 音频流上下文管理器
@contextmanager
def audio_stream(sample_rate=16000, chunk_size=8000):
    """打开PyAudio输入流并自动清理"""
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

class FunASRTest:
    """FunASR测试类"""
    
    def __init__(self, model_path="f:\\04_AI\\01_Workplace\\Voice_Input\\model\\fun", model_revision="v2.0.4"):
        """初始化测试类
        
        Args:
            model_path: FunASR模型路径
            model_revision: 模型版本
        """
        self.model_path = model_path
        self.model_revision = model_revision
        self._model = None
        self.model_loaded = False
        self.load_time = 0.0
        self.sample_rate = 16000
        self.chunk_size = 8000
        
    def load_model(self):
        """加载FunASR模型"""
        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR模块不可用，无法加载模型")
            return False
        
        if self.model_loaded and self._model is not None:
            logger.info("✅ FunASR模型已加载，无需重复加载")
            return True
        
        logger.info(f"📦 开始加载FunASR模型: {self.model_path} (版本: {self.model_revision})")
        start_time = time.time()
        
        try:
            # 创建FunASR模型
            logger.info("🔄 正在初始化模型...")
            logger.info(f"  - model: {self.model_path}")
            logger.info(f"  - model_revision: None (本地模型)")
            logger.info(f"  - device: cpu")
            logger.info("  - 使用本地模型，避免下载额外文件")
            
            # 使用本地模型，不指定额外的vad_model和punc_model以避免下载
            # 根据configuration.json文件，模型应该已经包含了所需的组件
            self._model = AutoModel(
                model=self.model_path,
                model_revision=None,  # 本地模型不需要版本号
                device="cpu",
                trust_remote_code=False  # 确保使用本地代码
            )
            
            self.model_loaded = True
            self.load_time = time.time() - start_time
            logger.info(f"✅ FunASR模型加载完成 (耗时: {self.load_time:.2f}秒)")
            return True
            
        except Exception as e:
            logger.error(f"❌ FunASR模型加载失败: {e}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            self._model = None
            self.model_loaded = False
            
            # 分析可能的错误原因
            if "Could not find model" in str(e) or "No such file or directory" in str(e):
                logger.error("💡 可能的原因: 模型路径不存在或模型未下载")
                logger.error("   请确保模型已正确下载到指定路径")
            elif "CUDA" in str(e) or "GPU" in str(e).upper():
                logger.error("💡 可能的原因: GPU相关错误")
                logger.error("   请确保CUDA正确安装或尝试使用device='cpu'")
            elif "memory" in str(e).lower() or "OOM" in str(e).upper():
                logger.error("💡 可能的原因: 内存不足")
                logger.error("   请尝试使用更小的模型或增加可用内存")
            
            return False
    
    def unload_model(self):
        """卸载FunASR模型"""
        if not FUNASR_AVAILABLE:
            return
        
        try:
            self._model = None
            self.model_loaded = False
            import gc
            gc.collect()
            logger.info(f"🧹 FunASR模型已卸载")
        except KeyboardInterrupt:
            print("\n⏹️  模型卸载过程被中断")
        except Exception as e:
            logger.error(f"❌ 模型卸载过程中发生错误: {e}")
    
    def test_recognition(self, duration=60):
        """测试语音识别功能 - 修复版本，支持实时麦克风输入

        Args:
            duration: 录音测试时长（秒）
        """
        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR模块不可用，无法进行识别测试")
            return False

        if not self.model_loaded or self._model is None:
            logger.warning("⚠️ 模型未加载，尝试加载...")
            if not self.load_model():
                logger.error("❌ 无法加载模型，测试终止")
                return False

        logger.info("🎤 准备进行语音识别测试...")

        # 增加更明显的提示
        print("=" * 60)
        print("📢 语音识别测试准备")
        print("=" * 60)
        print("🔊 请确保您的麦克风已开启并正常工作")
        print(f"⏱️  测试将持续 {duration} 秒")
        print("💬 请在提示开始后对着麦克风说话")
        print("🎯 您可以说一些中文句子，如'你好世界'、'语音识别测试'等")
        print("⚠️  注意: 系统会检测语音活动，只在检测到说话时进行识别")
        print("=" * 60)
        print("\n请按Enter键开始测试...")
        input()  # 等待用户确认

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
        logger.info(f"✅ 开始录音测试，持续{duration}秒")

        # FunASR流式处理参数 - 模仿Vosk，处理完整语音段
        chunk_size = [0, 10, 5]  # [0ms, 200ms, 100ms] - 推荐的流式处理参数
        encoder_chunk_look_back = 4
        decoder_chunk_look_back = 1
        funasr_cache = {}  # FunASR缓存，需要在整个会话中保持

        # 语音活动检测参数 - 平衡响应速度和完整性
        speech_energy_threshold = 0.015  # 提高阈值，降低敏感度，避免误识别
        min_speech_duration = 0.4  # 最小语音时长，确认是真正的语音
        min_silence_duration = 0.8  # 减少静音时长，提高响应速度

        # 识别状态控制 - 模仿Vosk的AcceptWaveform逻辑
        speech_segment_audio = []  # 当前语音段的音频数据
        is_speech_segment = False  # 是否在语音段中
        speech_start_time = 0
        last_speech_time = 0
        recognition_count = 0
        last_recognized_text = ""
        collected_text = []

        # 去重和相似度检测
        text_similarity_threshold = 0.7  # 稍微降低相似度阈值，避免过度过滤

        start_time = time.time()
        frames_processed = 0
        speech_frames = 0

        # 文本后处理函数
        def calculate_text_similarity(text1, text2):
            """计算两个文本的相似度"""
            if not text1 or not text2:
                return 0.0

            # 移除空格和标点符号进行比较
            import re
            clean1 = re.sub(r'[^\w]', '', text1.lower())
            clean2 = re.sub(r'[^\w]', '', text2.lower())

            if not clean1 or not clean2:
                return 0.0

            # 计算Jaccard相似度
            set1 = set(clean1)
            set2 = set(clean2)
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))

            return intersection / union if union > 0 else 0.0

        def is_duplicate_text(new_text, previous_text):
            """判断是否为重复文本"""
            if not previous_text:
                return False

            similarity = calculate_text_similarity(new_text, previous_text)
            return similarity >= text_similarity_threshold

        def remove_duplicate_chars(text):
            """移除文本中的重复字符"""
            if not text:
                return text

            result = []
            prev_char = None
            for char in text:
                if char != prev_char:
                    result.append(char)
                prev_char = char
            return ''.join(result)

        def is_valid_text(text):
            """检查文本是否有效，过滤低质量识别结果"""
            if not text or len(text.strip()) < 2:
                return False

            # 过滤明显的误识别结果
            invalid_patterns = ['e', 'yeah', '嗯', '啊', '哦', '呃', '额', '嘿嘿', '哈哈']
            text_clean = text.strip().lower()
            for pattern in invalid_patterns:
                if text_clean == pattern or text_clean.count(pattern) > 2:
                    return False

            # 检查是否有实际内容字符（中文、数字、英文）
            import re
            meaningful_chars = re.findall(r'[\u4e00-\u9fff\w]', text)
            if len(meaningful_chars) < 2:
                return False

            return True

        def post_process_text(text):
            """后处理识别结果"""
            if not text:
                return text

            # 移除重复字符
            text = remove_duplicate_chars(text)

            # 移除多余空格
            text = ' '.join(text.split())

            return text

        try:
            with audio_stream(sample_rate=self.sample_rate, chunk_size=self.chunk_size) as stream:
                while time.time() - start_time < duration:
                    try:
                        # 读取音频数据
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames_processed += 1

                        # 转换为numpy数组
                        audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                        # 计算音频能量
                        audio_energy = np.sqrt(np.mean(audio_data**2))
                        current_time = time.time() - start_time

                        # === 模仿Vosk的语音活动检测逻辑 ===
                        is_speech = audio_energy > speech_energy_threshold

                        if is_speech and not is_speech_segment:
                            # 开始新的语音段
                            is_speech_segment = True
                            speech_start_time = current_time
                            speech_segment_audio = []  # 清空之前的音频段
                            logger.info(f"🎯 开始语音段，能量: {audio_energy:.4f}")

                        elif is_speech and is_speech_segment:
                            # 在语音段中，继续收集音频
                            last_speech_time = current_time

                        elif not is_speech and is_speech_segment:
                            # 语音可能结束，检查静音时长
                            silence_duration = current_time - last_speech_time
                            speech_duration = current_time - speech_start_time

                            # 智能判断：如果语音段足够长(>2秒)或静音时间足够长，就结束识别
                            should_end = (
                                silence_duration >= min_silence_duration or  # 静音时间足够
                                (silence_duration >= 0.5 and speech_duration >= 2.0)  # 语音较长且短暂停顿
                            )

                            if should_end:
                                # 确认语音段结束，进行识别（模仿Vosk的AcceptWaveform）
                                is_speech_segment = False

                                # 检查语音段时长是否足够
                                if speech_duration >= min_speech_duration and len(speech_segment_audio) > 0:
                                    recognition_count += 1
                                    logger.info(f"语音段结束，时长: {speech_duration:.2f}s，音频样本: {len(speech_segment_audio)}")

                                    # 进行识别
                                    try:
                                        result = self._model.generate(
                                            input=np.array(speech_segment_audio),
                                            cache=funasr_cache,
                                            is_final=False,
                                            chunk_size=chunk_size,
                                            encoder_chunk_look_back=encoder_chunk_look_back,
                                            decoder_chunk_look_back=decoder_chunk_look_back
                                        )

                                        if result and isinstance(result, list) and len(result) > 0 and "text" in result[0]:
                                            raw_text = result[0]["text"].strip()
                                            if raw_text:
                                                processed_text = post_process_text(raw_text)

                                                # 文本质量检查
                                                if is_valid_text(processed_text):
                                                    # 检查是否为重复文本
                                                    if not is_duplicate_text(processed_text, last_recognized_text):
                                                        last_recognized_text = processed_text
                                                        collected_text.append(processed_text)

                                                        # 显示识别结果
                                                        print(f"\n🎯 识别: {processed_text}")
                                                        logger.info(f"FunASR识别结果: '{processed_text}' (原始: '{raw_text}')")
                                                    else:
                                                        logger.debug(f"跳过重复文本: {processed_text}")
                                                else:
                                                    logger.debug(f"跳过低质量文本: {processed_text}")

                                    except Exception as e:
                                        logger.debug(f"FunASR识别异常: {e}")
                                else:
                                    logger.info(f"⚠️ 语音段过短，跳过识别: 时长={speech_duration:.2f}s < {min_speech_duration}s, 样本数={len(speech_segment_audio)}")

                        # 如果在语音段中，收集音频数据
                        if is_speech_segment:
                            speech_segment_audio.extend(audio_data)
                            speech_frames += 1

                        # 实时状态显示
                        remaining_time = duration - current_time
                        if frames_processed % 50 == 0:  # 每50帧更新一次状态
                            if is_speech_segment:
                                status = "🗣️ 说话中"
                                speech_duration = current_time - speech_start_time
                                extra_info = f"({speech_duration:.1f}s)"
                            else:
                                status = "🔇 静音"
                                extra_info = ""

                            speech_rate = (speech_frames / max(1, frames_processed)) * 100
                            print(f"\r{status}{extra_info} | 能量:{audio_energy:.4f} | 语音活动率:{speech_rate:.1f}% | 剩余:{remaining_time:.1f}s | 识别次数:{recognition_count} | ", end="", flush=True)

                    except Exception as e:
                        logger.error(f"❌ 音频处理错误: {e}")
                        continue

                # 处理结束时的最终识别
                print(f"\n🏁 录音结束，处理最终识别结果...")

                # 如果还有未处理的语音段，进行最终识别
                if is_speech_segment and len(speech_segment_audio) > 0:
                    speech_duration = time.time() - start_time - speech_start_time
                    if speech_duration >= min_speech_duration:
                        try:
                            final_result = self._model.generate(
                                input=np.array(speech_segment_audio),
                                cache=funasr_cache,
                                is_final=True,
                                chunk_size=chunk_size,
                                encoder_chunk_look_back=encoder_chunk_look_back,
                                decoder_chunk_look_back=decoder_chunk_look_back
                            )

                            if final_result and isinstance(final_result, list) and len(final_result) > 0 and "text" in final_result[0]:
                                final_text = final_result[0]["text"].strip()
                                if final_text and final_text != last_recognized_text:
                                    collected_text.append(final_text)
                                    print(f"🎯 最终识别: {final_text}")
                                    logger.info(f"FunASR最终识别结果: '{final_text}'")

                        except Exception as e:
                            logger.debug(f"FunASR最终识别异常: {e}")

                # 最终结果后处理
                final_collected_text = []
                if collected_text:
                    # 合并相似的文本片段
                    for text in collected_text:
                        if not final_collected_text or not is_duplicate_text(text, final_collected_text[-1]):
                            final_collected_text.append(text)

                # 输出统计信息
                print("\n" + "=" * 60)
                print("📊 测试结果统计")
                print("=" * 60)

                if final_collected_text:
                    final_text = " ".join(final_collected_text)
                    print(f"📝 识别到的所有文本: {final_text}")
                    print(f"🔢 识别片段数量: {len(final_collected_text)} (去重后)")
                    print(f"🎯 识别到的片段:")
                    for i, text in enumerate(final_collected_text, 1):
                        print(f"   {i}. {text}")

                    # 显示优化效果
                    if len(final_collected_text) < len(collected_text):
                        reduction_count = len(collected_text) - len(final_collected_text)
                        print(f"✨ 去重效果: 移除了 {reduction_count} 个重复片段")
                else:
                    print("❌ 未识别到任何语音内容")
                    print("\n💡 可能的原因:")
                    print("   - 麦克风未正确连接或权限不足")
                    print("   - 说话音量太小或距离麦克风太远")
                    print("   - 环境噪音过大")
                    print("   - 模型路径或配置有问题")

                print(f"\n📈 音频处理统计:")
                print(f"   - 总处理帧数: {frames_processed}")
                print(f"   - 语音活动帧数: {speech_frames}")
                print(f"   - 语音活动率: {(speech_frames / max(1, frames_processed)) * 100:.1f}%")
                print(f"   - 测试时长: {duration}秒")

                return True

        except KeyboardInterrupt:
            print("\n⏹️  测试被用户中断")
            return True
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_status(self):
        """获取当前状态信息"""
        return {
            "funasr_available": FUNASR_AVAILABLE,
            "model_loaded": self.model_loaded,
            "model_path": self.model_path,
            "model_revision": self.model_revision,
            "load_time": self.load_time,
            "python_version": sys.version
        }
    
    def print_status(self):
        """打印当前状态信息"""
        status = self.get_status()
        print("\n📊 FunASR测试状态信息:")
        print(f"  - FunASR可用: {'✅ 是' if status['funasr_available'] else '❌ 否'}")
        print(f"  - 模型加载: {'✅ 已加载' if status['model_loaded'] else '❌ 未加载'}")
        print(f"  - 模型路径: {status['model_path']}")
        print(f"  - 模型版本: {status['model_revision']}")
        print(f"  - 加载时间: {status['load_time']:.2f}秒" if status['load_time'] > 0 else "  - 加载时间: 未加载")
        print(f"  - Python版本: {status['python_version'].split(' ')[0]}")
        print(f"  - 当前目录: {os.getcwd()}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 FunASR 语音识别测试工具")
    print("=" * 60)
    print("📝 说明: 此工具使用本地FunASR模型通过麦克风进行实时语音识别")
    print("\n")
    
    # 创建测试实例
    tester = FunASRTest()
    tester.print_status()
    
    # 测试模型加载
    print("\n🔄 开始测试模型加载...")
    load_success = tester.load_model()
    
    if load_success:
        tester.print_status()
        
        # 测试语音识别
        try:
            print("\n")
            tester.test_recognition(duration=30)  # 改为30秒，给用户更多测试时间
        except KeyboardInterrupt:
            print("\n⏹️  测试被用户中断")
        finally:
            # 卸载模型
            tester.unload_model()
            print("\n🧹 测试完成，资源已清理")
    else:
        print("\n❌ 模型加载失败，无法进行语音识别测试")
        print("💡 提示: ")
        print("   1. 确保已安装FunASR: pip install funasr")
        print("   2. 检查本地模型路径是否正确")
        print("   3. 确保有足够的磁盘空间和内存")

if __name__ == "__main__":
    main()