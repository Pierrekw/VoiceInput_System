#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR语音识别模块
基于FunASR的语音录入和识别功能，可作为模块导入使用
结合VAD、流式识别和多种优化策略

使用示例:
    from funasr_voice_module import FunASRVoiceRecognizer

    recognizer = FunASRVoiceRecognizer()
    recognizer.initialize()
    result = recognizer.recognize_speech(duration=10)
    print(f"识别结果: {result}")
"""

import os
import sys
import warnings

# 彻底抑制FunASR的进度条和调试输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['HIDE_PROGRESS'] = '1'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

# 配置日志级别，只显示错误
import logging
logging.getLogger("funasr").setLevel(logging.ERROR)
logging.getLogger("modelscope").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

warnings.filterwarnings('ignore')

# ============================================================================
# 🔧 关键：FFmpeg环境必须在FunASR导入前设置
# ============================================================================
def setup_ffmpeg_environment():
    """设置FFmpeg环境（必须在导入FunASR之前调用）"""
    # 方法1：使用环境变量永久设置（最快）
    # 如果已经设置过FFmpeg路径，直接跳过
    if os.environ.get('FFMPEG_PATH_SET') == '1':
        return True
    
    try:
        # 方法2：配置固定路径（推荐用于快速启动）
        # 这里设置一个固定的FFmpeg路径，避免多次检查
        # 用户可以根据实际情况修改这个路径
        FIXED_FFMPEG_PATH = "F:/onnx_deps/ffmpeg-master-latest-win64-gpl-shared/bin"
        
        if FIXED_FFMPEG_PATH and os.path.exists(FIXED_FFMPEG_PATH):
            current_path = os.environ.get('PATH', '')
            if FIXED_FFMPEG_PATH not in current_path:
                os.environ['PATH'] = FIXED_FFMPEG_PATH + os.pathsep + current_path
            # 标记FFmpeg路径已设置
            os.environ['FFMPEG_PATH_SET'] = '1'
            return True
        
        # 方法3：快速检查（仅检查最可能的位置）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fast_check_paths = [
            # 主要检查FunASR_Deployment目录
            os.path.join(script_dir, "FunASR_Deployment", "dependencies",
                        "ffmpeg-master-latest-win64-gpl-shared", "bin"),
        ]
        
        for ffmpeg_path in fast_check_paths:
            if os.path.exists(ffmpeg_path):
                current_path = os.environ.get('PATH', '')
                if ffmpeg_path not in current_path:
                    os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path
                os.environ['FFMPEG_PATH_SET'] = '1'
                return True
        
        # 注意：系统PATH检查已移除，因为它较慢
        # 建议：将FFmpeg添加到系统环境变量PATH中
        print("⚠️ 未找到FFmpeg快速路径")
        print("💡 性能优化建议：")
        print("  1. 将FFmpeg安装到系统PATH环境变量中")
        print(f"  2. 或修改代码中的FIXED_FFMPEG_PATH为您的FFmpeg路径")
        
        return False

    except Exception:
        # 静默失败，避免影响启动速度
        return False

# 立即执行FFmpeg环境设置
setup_ffmpeg_environment()

# ============================================================================
# 📦 导入其他依赖
# ============================================================================
import io
import time
import logging
import numpy as np
import pyaudio
import threading
from contextlib import contextmanager
from typing import List, Dict, Optional, Callable, Union, Tuple, Any
from dataclasses import dataclass
from collections import deque

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局可用性检查
FUNASR_AVAILABLE = False
PYAUDIO_AVAILABLE = False
NUMPY_AVAILABLE = False

# 检查依赖
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    logger.error("❌ numpy 不可用，请安装: pip install numpy")
    # 不设置 np 变量，避免类型冲突

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.error("❌ pyaudio 不可用，请安装: pip install pyaudio")

try:
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
    logger.info("✅ FunASR 模块可用")
except ImportError as e:
    logger.error(f"❌ FunASR 不可用: {e}")
    AutoModel = None

@dataclass
class RecognitionResult:
    """语音识别结果数据类"""
    text: str                    # 最终识别文本
    partial_results: List[str]   # 部分识别结果列表
    confidence: float            # 置信度
    duration: float              # 识别时长
    timestamp: float             # 时间戳
    audio_buffer: List[np.ndarray]  # 音频缓冲区

@dataclass
class VADConfig:
    """VAD配置"""
    energy_threshold: float = 0.015
    min_speech_duration: float = 0.3
    min_silence_duration: float = 0.6
    speech_padding: float = 0.3

@dataclass
class FunASRConfig:
    """FunASR配置"""
    model_path: str = "f:/04_AI/01_Workplace/Voice_Input/model/fun"
    device: str = "cpu"
    chunk_size: Optional[List[int]] = None
    encoder_chunk_look_back: int = 4
    decoder_chunk_look_back: int = 1
    disable_update: bool = True
    trust_remote_code: bool = False

    def __post_init__(self):
        if self.chunk_size is None:
            self.chunk_size = [0, 10, 5]  # 默认流式参数

class FunASRVoiceRecognizer:
    """
    FunASR语音识别器主类
    提供语音录入、识别和VAD功能
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 device: str = "cpu",
                 sample_rate: int = 16000,
                 chunk_size: int = 1600,
                 silent_mode: bool = True):
        """
        初始化语音识别器

        Args:
            model_path: FunASR模型路径
            device: 设备类型 ("cpu" 或 "cuda")
            sample_rate: 音频采样率
            chunk_size: 音频块大小
            silent_mode: 静默模式，隐藏中间过程信息
        """
        # 基础配置
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model_path = model_path or "./model/fun"
        self.silent_mode = silent_mode

        # FunASR配置
        self.funasr_config = FunASRConfig(
            model_path=self.model_path,
            device=device
        )

        # VAD配置
        self.vad_config = VADConfig()

        # 模型相关
        self._model: Optional[Any] = None
        self._model_loaded = False
        self._model_load_time = 0.0

        # 运行状态
        self._is_initialized = False
        self._is_running = False
        self._stop_event = threading.Event()
        self._speech_detected = False

        # 音频处理
        self._audio_buffer: deque[np.ndarray] = deque(maxlen=sample_rate * 5)  # 5秒缓冲
        self._speech_buffer: List[np.ndarray] = []
        self._funasr_cache: Dict[str, Any] = {}

        # 识别结果
        self._current_text = ""
        self._partial_results: List[str] = []
        self._final_results: List[RecognitionResult] = []

        # 统计信息
        self.stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'total_audio_time': 0.0,
            'total_processing_time': 0.0,
            'average_confidence': 0.0
        }

        # 回调函数
        self._on_partial_result: Optional[Callable[[str], None]] = None
        self._on_final_result: Optional[Callable[[RecognitionResult], None]] = None
        self._on_vad_event: Optional[Callable[[str, Dict], None]] = None

    def set_callbacks(self,
                     on_partial_result: Optional[Callable[[str], None]] = None,
                     on_final_result: Optional[Callable[[RecognitionResult], None]] = None,
                     on_vad_event: Optional[Callable[[str, Dict], None]] = None):
        """
        设置回调函数

        Args:
            on_partial_result: 部分结果回调
            on_final_result: 最终结果回调
            on_vad_event: VAD事件回调
        """
        self._on_partial_result = on_partial_result
        self._on_final_result = on_final_result
        self._on_vad_event = on_vad_event

    def setup_environment(self) -> bool:
        """设置运行环境"""
        try:
            # 设置FFmpeg路径（如果需要）
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_ffmpeg_bin = os.path.join(script_dir, "FunASR_Deployment",
                                          "dependencies", "ffmpeg-master-latest-win64-gpl-shared", "bin")

            if os.path.exists(local_ffmpeg_bin):
                current_path = os.environ.get('PATH', '')
                if local_ffmpeg_bin not in current_path:
                    os.environ['PATH'] = local_ffmpeg_bin + os.pathsep + current_path
                    logger.info(f"🔧 设置本地FFmpeg: {local_ffmpeg_bin}")

            return True

        except Exception as e:
            logger.warning(f"环境设置失败: {e}")
            return False

    def check_dependencies(self) -> bool:
        """检查依赖是否满足"""
        missing_deps = []

        if not NUMPY_AVAILABLE:
            missing_deps.append("numpy")
        if not PYAUDIO_AVAILABLE:
            missing_deps.append("pyaudio")
        if not FUNASR_AVAILABLE:
            missing_deps.append("funasr")

        if missing_deps:
            logger.error(f"❌ 缺少依赖: {', '.join(missing_deps)}")
            logger.error("请执行: pip install " + " ".join(missing_deps))
            return False

        return True

    def initialize(self) -> bool:
        """初始化识别器"""
        if self._is_initialized:
            logger.info("✅ 识别器已初始化")
            return True

        logger.info("🚀 初始化FunASR语音识别器...")

        # 检查依赖
        if not self.check_dependencies():
            return False

        # 设置环境
        self.setup_environment()

        # 加载模型
        if not self._load_model():
            return False

        self._is_initialized = True
        logger.info("✅ FunASR语音识别器初始化完成")
        return True

    def _load_model(self) -> bool:
        """加载FunASR模型"""
        if self._model_loaded:
            return True

        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR不可用")
            return False

        logger.info(f"📦 加载FunASR模型: {self.model_path}")
        start_time = time.time()

        try:
            # 检查模型路径
            if not os.path.exists(self.model_path):
                logger.error(f"❌ 模型路径不存在: {self.model_path}")
                return False

            # 加载模型
            self._model = AutoModel(
                model=self.funasr_config.model_path,
                device=self.funasr_config.device,
                trust_remote_code=self.funasr_config.trust_remote_code,
                disable_update=self.funasr_config.disable_update
            )

            self._model_loaded = True
            self._model_load_time = time.time() - start_time

            logger.info(f"✅ 模型加载成功 (耗时: {self._model_load_time:.2f}秒)")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def unload_model(self):
        """卸载模型释放内存"""
        if self._model:
            self._model = None
            self._model_loaded = False
            import gc
            gc.collect()
            logger.info("🧹 模型已卸载")

    @contextmanager
    def _audio_stream(self):
        """音频流上下文管理器，增强异常处理和重连机制"""
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio不可用")

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            p = None
            stream = None

            try:
                p = pyaudio.PyAudio()

                # 获取默认音频设备
                try:
                    default_device = p.get_default_input_device_info()
                    logger.info(f"🎤 使用音频设备: {default_device['name']} (索引: {default_device['index']})")
                except Exception as device_error:
                    logger.error(f"❌ 无法获取音频设备信息: {device_error}")
                    raise RuntimeError("音频设备不可用")

                # 打开音频流，增加错误容错
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=default_device['index'],
                    frames_per_buffer=self.chunk_size,
                    start=True
                )

                # 验证音频流是否正常工作
                if not stream.is_active():
                    raise RuntimeError("音频流创建失败：流未激活")

                logger.info(f"🎧 音频流创建成功 (重试 {retry_count + 1}/{max_retries})")
                yield stream
                break  # 成功则退出重试循环

            except Exception as e:
                retry_count += 1
                error_msg = f"❌ 音频流创建失败 (重试 {retry_count}/{max_retries}): {e}"

                if retry_count >= max_retries:
                    logger.error(error_msg + " - 已达到最大重试次数")
                    raise RuntimeError(f"音频流创建失败，已重试{max_retries}次: {e}")
                else:
                    logger.warning(error_msg + " - 正在重试...")
                    time.sleep(1)  # 重试前等待1秒

            finally:
                # 确保资源正确释放
                if stream:
                    try:
                        if stream.is_active():
                            stream.stop_stream()
                        stream.close()
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ 音频流清理异常: {cleanup_error}")

                if p:
                    try:
                        p.terminate()
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ PyAudio清理异常: {cleanup_error}")

    def _detect_vad(self, audio_data: np.ndarray, current_time: float) -> Tuple[bool, Optional[str]]:
        """
        VAD语音活动检测

        Args:
            audio_data: 音频数据
            current_time: 当前时间

        Returns:
            (is_speech, event_type): 是否有语音和事件类型
        """
        # 计算音频能量
        energy = np.sqrt(np.mean(audio_data ** 2))

        # 简单的能量阈值VAD
        is_speech = energy > self.vad_config.energy_threshold

        event_type = None
        if is_speech:
            if not hasattr(self, '_speech_detected') or not self._speech_detected:
                event_type = "speech_start"
                self._speech_detected = True
                self._speech_start_time = current_time
        else:
            if hasattr(self, '_speech_detected') and self._speech_detected:
                silence_duration = current_time - getattr(self, '_last_speech_time', current_time)
                if silence_duration >= self.vad_config.min_silence_duration:
                    event_type = "speech_end"
                    self._speech_detected = False

        if is_speech:
            self._last_speech_time = current_time

        return is_speech, event_type

    def _process_audio_chunk(self, audio_data: np.ndarray, current_time: float):
        """
        处理音频块

        Args:
            audio_data: 音频数据
            current_time: 当前时间
        """
        # 添加到音频缓冲区
        self._audio_buffer.extend(audio_data)

        # VAD检测
        is_speech, vad_event = self._detect_vad(audio_data, current_time)

        if vad_event and self._on_vad_event:
            self._on_vad_event(vad_event, {
                'time': current_time,
                'energy': np.sqrt(np.mean(audio_data ** 2))
            })

        # 如果检测到语音，添加到语音缓冲区
        if is_speech:
            self._speech_buffer.extend(audio_data)

            # 定期进行流式识别
            if len(self._speech_buffer) >= self.sample_rate * 1:  # 1秒音频
                self._perform_streaming_recognition()
        else:
            # 如果静音时间足够长且有语音缓冲区，进行最终识别
            if (len(self._speech_buffer) > 0 and
                hasattr(self, '_last_speech_time') and
                current_time - self._last_speech_time >= self.vad_config.min_silence_duration):

                if len(self._speech_buffer) >= self.sample_rate * self.vad_config.min_speech_duration:
                    self._perform_final_recognition()

    def _perform_streaming_recognition(self):
        """执行流式识别"""
        if not self._model or not self._model_loaded:
            return

        try:
            # 取最近的音频数据进行识别
            audio_array = np.array(list(self._speech_buffer))

            result = self._model.generate(
                input=audio_array,
                cache=self._funasr_cache,
                is_final=False,
                chunk_size=self.funasr_config.chunk_size,
                encoder_chunk_look_back=self.funasr_config.encoder_chunk_look_back,
                decoder_chunk_look_back=self.funasr_config.decoder_chunk_look_back
            )

            if result and isinstance(result, list) and len(result) > 0:
                text = result[0].get("text", "").strip()
                if text and text != self._current_text:
                    self._current_text = text
                    self._partial_results.append(text)

                    # 触发部分结果回调
                    if self._on_partial_result:
                        self._on_partial_result(text)

                    if not self.silent_mode:
                        logger.info(f"🗣️ 流式识别: '{text}'")

        except Exception as e:
            logger.debug(f"流式识别异常: {e}")

    def _perform_final_recognition(self):
        """执行最终识别"""
        if not self._model or not self._model_loaded or not self._speech_buffer:
            return

        try:
            start_time = time.time()

            audio_array = np.array(list(self._speech_buffer))

            result = self._model.generate(
                input=audio_array,
                cache=self._funasr_cache,
                is_final=True,
                chunk_size=self.funasr_config.chunk_size,
                encoder_chunk_look_back=self.funasr_config.encoder_chunk_look_back,
                decoder_chunk_look_back=self.funasr_config.decoder_chunk_look_back
            )

            processing_time = time.time() - start_time

            if result and isinstance(result, list) and len(result) > 0:
                text = result[0].get("text", "").strip()
                if text:
                    # 创建识别结果
                    recognition_result = RecognitionResult(
                        text=text,
                        partial_results=self._partial_results.copy(),
                        confidence=0.9,  # FunASR暂不提供置信度，使用默认值
                        duration=len(self._speech_buffer) / self.sample_rate,
                        timestamp=time.time(),
                        audio_buffer=self._speech_buffer.copy()
                    )

                    self._final_results.append(recognition_result)
                    self.stats['total_recognitions'] += 1
                    self.stats['successful_recognitions'] += 1
                    self.stats['total_processing_time'] += processing_time

                    # 触发最终结果回调
                    if self._on_final_result:
                        self._on_final_result(recognition_result)

                    if not self.silent_mode:
                        logger.info(f"✅ 最终识别: '{text}' (耗时: {processing_time:.3f}s)")

        except Exception as e:
            logger.error(f"最终识别异常: {e}")
        finally:
            # 清空语音缓冲区
            self._speech_buffer = []
            self._current_text = ""

    def recognize_speech(self, duration: int = 10,
                        real_time_display: bool = True) -> RecognitionResult:
        """
        识别语音（同步模式）

        Args:
            duration: 识别时长（秒）
            real_time_display: 是否实时显示识别结果

        Returns:
            RecognitionResult: 识别结果
        """
        if not self._is_initialized:
            if not self.initialize():
                raise RuntimeError("初始化失败")

        if not self.silent_mode:
            logger.info(f"🎙️ 开始语音识别，时长: {duration}秒")

        # 重置状态
        self._stop_event.clear()
        self._audio_buffer.clear()
        self._speech_buffer = []
        self._current_text = ""
        self._partial_results = []

        start_time = time.time()

        try:
            with self._audio_stream() as stream:
                # 支持duration=-1表示无限时模式
                while (duration == -1 or time.time() - start_time < duration) and not self._stop_event.is_set():
                    try:
                        # 读取音频数据
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        current_time = time.time() - start_time

                        # 转换为numpy数组
                        audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                        # 处理音频
                        self._process_audio_chunk(audio_data, current_time)

                        # 实时显示
                        if real_time_display and self._current_text:
                            if duration == -1:
                                # 无限时模式：显示运行时间
                                print(f"\r🗣️ 识别中: '{self._current_text}' | 运行时间: {current_time:.1f}s",
                                     end="", flush=True)
                            else:
                                # 限时模式：显示剩余时间
                                remaining = duration - current_time
                                print(f"\r🗣️ 识别中: '{self._current_text}' | 剩余: {remaining:.1f}s",
                                     end="", flush=True)

                    except OSError as audio_error:
                        # 专门处理音频流相关的系统错误
                        logger.error(f"🎤 音频流异常: {audio_error}")
                        # 检查是否是设备断开连接
                        if "Input overflowed" in str(audio_error):
                            logger.warning("⚠️ 音频缓冲区溢出，继续处理...")
                            continue
                        elif "No such device" in str(audio_error) or "Device unavailable" in str(audio_error):
                            logger.error("❌ 音频设备断开连接或不可用")
                            raise RuntimeError("音频设备断开连接")
                        else:
                            logger.warning(f"⚠️ 音频流错误，尝试继续: {audio_error}")
                            continue

                    except Exception as e:
                        logger.error(f"❌ 音频处理错误: {e}")
                        # 对于其他异常，记录详细信息但尝试继续
                        import traceback
                        logger.debug(f"错误详情: {traceback.format_exc()}")
                        continue

                # 处理最后的音频
                if self._speech_buffer:
                    self._perform_final_recognition()

        except KeyboardInterrupt:
            logger.info("⏹️ 识别被用户中断 (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"❌ 识别过程出错: {e}")
            raise

        # 记录识别结束原因
        end_time = time.time()
        actual_duration = end_time - start_time

        if self._stop_event.is_set():
            logger.info(f"⏹️ 识别被系统停止信号中断 (运行时间: {actual_duration:.2f}秒)")
        elif duration == -1:
            logger.info(f"⏹️ 无限时模式识别结束 (运行时间: {actual_duration:.2f}秒)")
        elif actual_duration >= duration:
            logger.info(f"⏹️ 识别达到指定时长 (设定: {duration}秒, 实际: {actual_duration:.2f}秒)")
        else:
            logger.info(f"⏹️ 识别提前结束 (设定: {duration}秒, 实际: {actual_duration:.2f}秒)")

        # 返回最终结果
        if self._final_results:
            final_result = self._final_results[-1]
            print(f"\n✅ 识别完成: '{final_result.text}'")
            return final_result
        else:
            # 如果没有最终结果，使用部分结果
            if self._partial_results:
                text = self._partial_results[-1] if self._partial_results else ""
                result = RecognitionResult(
                    text=text,
                    partial_results=self._partial_results,
                    confidence=0.5,
                    duration=duration,
                    timestamp=time.time(),
                    audio_buffer=[]
                )
                print(f"\n⚠️ 无最终结果，返回部分结果: '{text}'")
                return result
            else:
                logger.warning("⚠️ 未识别到任何语音内容")
                return RecognitionResult(
                    text="",
                    partial_results=[],
                    confidence=0.0,
                    duration=0.0,
                    timestamp=time.time(),
                    audio_buffer=[]
                )

    def start_continuous_recognition(self):
        """开始连续识别（异步模式）"""
        if not self._is_initialized:
            if not self.initialize():
                raise RuntimeError("初始化失败")

        if self._is_running:
            logger.warning("⚠️ 连续识别已在运行")
            return

        logger.info("🔄 开始连续识别模式")
        self._is_running = True
        self._stop_event.clear()

        def recognition_thread():
            try:
                with self._audio_stream() as stream:
                    while self._is_running and not self._stop_event.is_set():
                        try:
                            data = stream.read(self.chunk_size, exception_on_overflow=False)
                            current_time = time.time()

                            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                            self._process_audio_chunk(audio_data, current_time)

                        except OSError as audio_error:
                            # 专门处理音频流相关的系统错误
                            logger.error(f"🎤 连续识别音频流异常: {audio_error}")

                            # 检查严重错误类型
                            if "No such device" in str(audio_error) or "Device unavailable" in str(audio_error):
                                logger.error("❌ 音频设备断开连接，停止连续识别")
                                self._is_running = False
                                break
                            elif "Input overflowed" in str(audio_error):
                                logger.warning("⚠️ 音频缓冲区溢出，继续处理...")
                                continue
                            else:
                                logger.warning(f"⚠️ 音频流错误，尝试继续: {audio_error}")
                                continue

                        except Exception as e:
                            logger.error(f"❌ 连续识别错误: {e}")
                            import traceback
                            logger.debug(f"错误详情: {traceback.format_exc()}")
                            continue

            except Exception as e:
                logger.error(f"连续识别线程异常: {e}")
            finally:
                self._is_running = False
                logger.info("🔄 连续识别线程结束")

        # 启动识别线程
        thread = threading.Thread(target=recognition_thread, daemon=True)
        thread.start()

        return thread

    def stop_recognition(self):
        """停止识别"""
        logger.info("⏹️ 停止识别")
        self._stop_event.set()
        self._is_running = False

        # 处理最后的音频
        if self._speech_buffer:
            self._perform_final_recognition()

    def get_status(self) -> Dict[str, Any]:
        """获取识别器状态"""
        return {
            'initialized': self._is_initialized,
            'model_loaded': self._model_loaded,
            'model_path': self.model_path,
            'device': self.funasr_config.device,
            'running': self._is_running,
            'stats': self.stats.copy(),
            'model_load_time': self._model_load_time,
            'dependencies': {
                'funasr': FUNASR_AVAILABLE,
                'pyaudio': PYAUDIO_AVAILABLE,
                'numpy': NUMPY_AVAILABLE
            }
        }

    def configure_vad(self, **kwargs):
        """配置VAD参数"""
        for key, value in kwargs.items():
            if hasattr(self.vad_config, key):
                setattr(self.vad_config, key, value)
                logger.info(f"🔧 VAD配置更新: {key} = {value}")
            else:
                logger.warning(f"⚠️ 未知的VAD参数: {key}")

    def configure_funasr(self, **kwargs):
        """配置FunASR参数"""
        for key, value in kwargs.items():
            if hasattr(self.funasr_config, key):
                setattr(self.funasr_config, key, value)
                logger.info(f"🔧 FunASR配置更新: {key} = {value}")
            else:
                logger.warning(f"⚠️ 未知的FunASR参数: {key}")

    def __del__(self):
        """析构函数"""
        try:
            self.stop_recognition()
            self.unload_model()
        except:
            pass

# 便捷函数
def create_recognizer(model_path: Optional[str] = None,
                     device: str = "cpu") -> FunASRVoiceRecognizer:
    """
    创建并初始化语音识别器

    Args:
        model_path: 模型路径
        device: 设备类型

    Returns:
        FunASRVoiceRecognizer: 已初始化的识别器
    """
    recognizer = FunASRVoiceRecognizer(model_path=model_path, device=device)
    if not recognizer.initialize():
        raise RuntimeError("识别器初始化失败")
    return recognizer

def quick_recognize(duration: int = 10,
                   model_path: Optional[str] = None) -> str:
    """
    快速语音识别

    Args:
        duration: 识别时长
        model_path: 模型路径

    Returns:
        str: 识别结果文本
    """
    recognizer = create_recognizer(model_path=model_path)
    result = recognizer.recognize_speech(duration=duration)
    return result.text

if __name__ == "__main__":
    # 示例用法
    print("🎯 FunASR语音识别模块测试")
    print("=" * 50)

    # 创建识别器
    recognizer = FunASRVoiceRecognizer()

    # 设置回调
    def on_partial(text):
        print(f"🗣️ 实时: {text}")

    def on_final(result):
        print(f"✅ 最终: {result.text}")

    def on_vad(event, data):
        print(f"🎯 VAD: {event}")

    recognizer.set_callbacks(on_partial, on_final, on_vad)

    # 初始化
    if recognizer.initialize():
        print("✅ 识别器初始化成功")
        print(f"📊 状态: {recognizer.get_status()}")

        # 进行识别测试
        try:
            result = recognizer.recognize_speech(duration=15)
            print(f"\n🎯 最终识别结果: '{result.text}'")
            print(f"📊 识别时长: {result.duration:.2f}秒")
            print(f"📊 部分结果数: {len(result.partial_results)}")
        except KeyboardInterrupt:
            print("\n⏹️ 测试被中断")
    else:
        print("❌ 识别器初始化失败")