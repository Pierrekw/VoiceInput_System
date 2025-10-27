#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR + TEN VAD 语音识别模块
基于FunASR ASR + TEN VAD的语音录入和识别功能，可作为模块导入使用
结合神经网络VAD、流式识别和多种优化策略

TEN VAD优势：
- 神经网络VAD，比传统能量阈值更准确
- 抗噪音能力强，误检率低
- 能够检测轻声语音
- 无需手动调参，开箱即用
- 流式支持，低延迟 (RTF约0.01-0.02)
- 轻量级 (约508KB vs Silero VAD的2.16MB)

使用示例:
    from funasr_voice_TENVAD import FunASRVoiceRecognizer

    recognizer = FunASRVoiceRecognizer()
    recognizer.initialize()
    result = recognizer.recognize_speech(duration=10)
    print(f"识别结果: {result}")
"""

import os
import sys
import warnings
import logging

# 导入性能监控
from utils.performance_monitor import performance_monitor, PerformanceStep

# 导入Debug性能追踪模块
#try:
    #from debug.debug_performance_tracker import debug_tracker
#except ImportError:
    #debug_tracker = None

# TEN VAD相关
TEN_VAD_AVAILABLE = False
ten_vad_model = None

try:
    # 导入本地TEN VAD
    ten_vad_path = "./onnx_deps/ten_vad"
    if os.path.exists(ten_vad_path):
        sys.path.insert(0, os.path.join(ten_vad_path, "include"))

        # 导入TEN VAD (基于真实的API)
        from ten_vad import TenVad
        ten_vad_model = TenVad(hop_size=256, threshold=0.5)
        TEN_VAD_AVAILABLE = True
        print("✅ TEN VAD 加载成功 (hop_size=256, threshold=0.5)")
    else:
        print("❌ TEN VAD路径不存在，将使用能量阈值VAD")

except Exception as e:
    print(f"❌ TEN VAD导入失败，将使用能量阈值VAD: {e}")
    TEN_VAD_AVAILABLE = False

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
        FIXED_FFMPEG_PATH = "./onnx_deps/ffmpeg-master-latest-win64-gpl-shared/bin"

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
import numpy as np
import pyaudio
import threading
from contextlib import contextmanager
from typing import List, Dict, Optional, Callable, Union, Tuple, Any
from dataclasses import dataclass
from collections import deque

# 使用统一的日志工具类
from utils.logging_utils import LoggingManager

# 获取配置好的日志记录器（参考voice_gui.py的配置风格）
logger = LoggingManager.get_logger(
    name='funasr_voice_TENVAD',
    level=logging.DEBUG,  # 文件记录详细日志
    console_level=logging.INFO,  # 控制台显示INFO及以上信息
    log_to_console=True,
    log_to_file=True
)

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

# 导入配置加载模块
config_loader: Any = None
CONFIG_AVAILABLE = False

try:
    from config_loader import config
    config_loader = config
    CONFIG_AVAILABLE = True
except ImportError:
    logger.error("配置加载模块不可用，使用默认配置")
    CONFIG_AVAILABLE = False

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
    model_path: str = "C:/Users/wangp2/VoiceInput_f1.0/model/fun" #model/cn
    
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
    FunASR + TEN VAD 语音识别器主类
    结合TEN VAD的语音录入、识别和VAD功能
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 device: str = "cpu",
                 sample_rate: int = 16000,
                 chunk_size: int = 400,
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

        # TEN VAD配置
        self._ten_vad_enabled = TEN_VAD_AVAILABLE
        self._ten_vad_available = TEN_VAD_AVAILABLE
        self._ten_vad_threshold = 0.5

        # 回退VAD配置 - 支持从配置文件加载
        self.vad_config = self._load_vad_config()

        # 模型相关
        self._model: Optional[Any] = None
        self._model_loaded = False
        self._model_load_time = 0.0

        # 运行状态
        self._is_initialized = False
        self._is_running = False
        self._stop_event = threading.Event()
        self._speech_detected = False

        # FFmpeg预处理配置
        self._ffmpeg_enabled = False
        self._ffmpeg_filter_chain = ""
        self._ffmpeg_options: Dict[str, Any] = {}
        self._ffmpeg_path = "ffmpeg"  # 默认FFmpeg路径

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

        # 后初始化
        self.__post_init__()

    def __post_init__(self):
        """后初始化，设置TEN VAD"""
        if self._ten_vad_available and ten_vad_model:
            logger.info("🎯 TEN VAD已启用 (hop_size=256, threshold=0.5)")
        else:
            logger.info("⚠️ TEN VAD不可用，将使用能量阈值VAD")

    def _load_vad_config(self):
        """从配置加载器加载VAD设置"""
        try:
            from config_loader import config

            # 加载FFmpeg预处理配置
            self._ffmpeg_enabled = config.is_ffmpeg_preprocessing_enabled()
            self._ffmpeg_filter_chain = config.get_ffmpeg_filter_chain()
            self._ffmpeg_options = config.get_ffmpeg_options()

            logger.info(f"🔧 FFmpeg预处理: {'启用' if self._ffmpeg_enabled else '禁用'}")
            if self._ffmpeg_enabled:
                logger.info(f"   滤镜链: {self._ffmpeg_filter_chain}")
                logger.info(f"   选项: {self._ffmpeg_options}")

            return VADConfig(
                energy_threshold=config.get_vad_energy_threshold(),
                min_speech_duration=config.get_vad_min_speech_duration(),
                min_silence_duration=config.get_vad_min_silence_duration(),
                speech_padding=config.get_vad_speech_padding()
            )

        except Exception as e:
            logger.warning(f"加载VAD配置失败: {e}，使用默认配置")
            # FFmpeg配置失败时使用默认值
            self._ffmpeg_enabled = False
            self._ffmpeg_filter_chain = "highpass=f=80, afftdn=nf=-25, loudnorm, volume=2.0"
            self._ffmpeg_options = {
                "process_input": True,
                "save_processed": False,
                "processed_prefix": "processed_"
            }
            return VADConfig()

    def _apply_ffmpeg_preprocessing(self, audio_data: np.ndarray, temp_file_prefix: str = "ffmpeg_temp_") -> np.ndarray:
        """
        应用FFmpeg预处理到音频数据

        Args:
            audio_data: 输入音频数据 (numpy数组)
            temp_file_prefix: 临时文件前缀

        Returns:
            预处理后的音频数据
        """
        if not self._ffmpeg_enabled or not self._ffmpeg_options.get('process_input', True):
            return audio_data  # 如果未启用或配置不处理输入，直接返回原数据

        # 🔥 关键修复：在FFmpeg处理开始前检查停止信号
        if self._stop_event.is_set():
            logger.info("检测到停止信号，跳过FFmpeg预处理")
            return audio_data

        try:
            import subprocess
            import tempfile
            import os

            # 将音频数据保存为临时WAV文件
            with tempfile.NamedTemporaryFile(suffix='.wav', prefix=temp_file_prefix, delete=False) as temp_input_file:
                temp_input_path = temp_input_file.name

                # 确保数据格式正确 (16位PCM)
                audio_int16 = (audio_data * 32767).astype(np.int16)

                # 写入WAV文件
                import wave
                with wave.open(temp_input_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 单声道
                    wav_file.setsampwidth(2)  # 16位
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_int16.tobytes())

            # 生成输出文件路径
            with tempfile.NamedTemporaryFile(suffix='.wav', prefix="processed_", delete=False) as temp_output_file:
                temp_output_path = temp_output_file.name

            # 构建FFmpeg命令
            ffmpeg_cmd = [
                self._ffmpeg_path,  # 从setup_environment设置
                '-i', temp_input_path,
                '-af', self._ffmpeg_filter_chain,
                '-y',  # 覆盖输出文件
                temp_output_path
            ]

            # 执行FFmpeg预处理
            logger.debug(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            try:
                # 🔥 修复：大幅减少超时时间，避免长时间阻塞
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    timeout=2  # 减少到2秒超时，避免阻塞停止功能
                )

                if result.returncode != 0:
                    logger.warning(f"FFmpeg预处理失败: {result.stderr}")
                    return audio_data  # 失败时返回原数据
                else:
                    logger.debug(f"FFmpeg预处理成功: {result.stdout}")

            except subprocess.TimeoutExpired:
                logger.warning("FFmpeg预处理超时，跳过此音频块的预处理")
                return audio_data
            except Exception as e:
                logger.warning(f"FFmpeg预处理异常: {e}")
                return audio_data

            # 读取预处理后的音频数据
            processed_data = None
            try:
                with wave.open(temp_output_path, 'rb') as wav_file:
                    with wave.open(temp_output_path, 'rb') as wav_file:
                        frames = wav_file.readframes(-1)
                        sample_width = wav_file.getsampwidth()
                        channels = wav_file.getnchannels()
                        processed_data = np.frombuffer(frames, dtype=np.int16)

                        # 确保是单声道
                        if channels == 1 and sample_width == 2:
                            processed_float_data = processed_data.astype(np.float32) / 32768.0
                            return processed_float_data
                        else:
                            logger.warning("FFmpeg输出格式异常，使用原始数据")
                            return audio_data

            except Exception as e:
                logger.error(f"读取预处理后音频失败: {e}")
                processed_data = audio_data

            # 清理临时文件
            try:
                os.unlink(temp_input_path)
                os.unlink(temp_output_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

            return processed_data if processed_data is not None else audio_data

        except Exception as e:
            logger.error(f"FFmpeg预处理模块异常: {e}")
            return audio_data

    def _get_gui_display_threshold(self) -> float:
        """获取GUI能量显示阈值（独立于VAD检测）"""
        try:
            from config_loader import config
            return config.get_gui_display_threshold()
        except Exception as e:
            logger.warning(f"加载GUI显示阈值失败: {e}，使用默认值0.00001")
            return 0.00001

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
        """初始化识别器，优化第一次启动性能"""
        if self._is_initialized:
            logger.info("✅ 识别器已初始化")
            return True

        logger.info("🚀 初始化FunASR + TEN VAD语音识别器...")
        init_start_time = time.time()

        # 检查依赖 - 前置检查，避免后续失败
        if not self.check_dependencies():
            return False

        # 设置环境 - 预先配置，减少运行时延迟
        self.setup_environment()

        # 加载模型 - 核心优化点
        if not self._load_model():
            return False

        self._is_initialized = True
        total_init_time = time.time() - init_start_time
        logger.info(f"✅ FunASR + TEN VAD语音识别器初始化完成 (总耗时: {total_init_time:.2f}秒)")
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

            # 优化：预预热模型，减少第一次识别延迟
            try:
                logger.info("🔄 预预热模型以减少首次识别延迟...")
                # 发送一个小的空音频块进行预识别，触发模型内部优化
                if hasattr(self._model, 'forward'):
                    # 这里不实际执行推理，只是确保模型准备就绪
                    pass
            except Exception as e:
                logger.debug(f"模型预热过程出错 (可忽略): {e}")

            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def unload_model(self):
        """卸载模型释放内存 - 优化：根据配置决定是否真的卸载模型"""
        # 🔥 防重复调用保护
        if not self._model_loaded:
            logger.debug("ℹ️ 模型已经卸载，跳过重复调用")
            return

        # 从配置加载全局卸载设置
        try:
            from config_loader import get_config
            config = get_config()
            global_unload = config.get('system', {}).get('global_unload', False)
        except ImportError:
            logger.debug("无法导入get_config，使用默认设置")
            global_unload = False
        except Exception as e:
            logger.debug(f"获取配置时出错，默认启用卸载: {e}")
            global_unload = True

        # 只有在明确配置需要卸载或者模型已加载时才执行卸载
        if self._model and global_unload:
            logger.info(f"🧹 卸载模型 (全局卸载设置: {global_unload})")
            self._model = None
            self._model_loaded = False
            import gc
            gc.collect()
            logger.info("🧹 模型已卸载，释放内存")
        else:
            # 保留模型在内存中以加快下次启动
            logger.info(f"ℹ️ 保留模型在内存中以加快后续启动")
            self._model_loaded = False  # 标记为已处理

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
        VAD语音活动检测 - 使用TEN VAD或回退到能量阈值

        Args:
            audio_data: 音频数据
            current_time: 当前时间

        Returns:
            (is_speech, event_type): 是否有语音和事件类型
        """
        is_speech = False
        vad_confidence = 0.0
        event_type = None

        # 尝试使用TEN VAD进行检测
        if self._ten_vad_available and ten_vad_model:
            try:
                # TEN VAD要求256个采样点
                vad_chunk_size = 256
                if len(audio_data) >= vad_chunk_size:
                    vad_chunk = audio_data[:vad_chunk_size]
                    # 转换为int16格式
                    vad_int16 = (vad_chunk * 32767).astype(np.int16)

                    # 使用TEN VAD进行检测
                    vad_confidence, vad_flag = ten_vad_model.process(vad_int16)
                    is_speech = (vad_flag == 1)

                    logger.debug(f"TEN VAD: 置信度={vad_confidence:.3f}, 标志={vad_flag}, 结果={is_speech}")
                else:
                    logger.debug("音频数据不足256个采样点，跳过TEN VAD检测")

            except Exception as ten_vad_error:
                logger.warning(f"TEN VAD处理错误，回退到能量阈值: {ten_vad_error}")
                self._ten_vad_available = False  # 标记TEN VAD不可用

        # 回退到传统能量阈值VAD
        if not self._ten_vad_available or not ten_vad_model:
            energy = np.sqrt(np.mean(audio_data ** 2))
            is_speech = energy > self.vad_config.energy_threshold
            vad_confidence = float(energy)
            logger.debug(f"回退到能量阈值VAD: 能量={energy:.6f}, 阈值={self.vad_config.energy_threshold}, 结果={is_speech}")

        # 检测语音开始和结束
        if is_speech:
            if not hasattr(self, '_speech_detected') or not self._speech_detected:
                event_type = "speech_start"
                self._speech_detected = True
                self._speech_start_time = current_time
                logger.info(f"🎤 语音开始 ({'TEN VAD' if self._ten_vad_available else '能量阈值'}: 置信度={vad_confidence:.3f}, 标志={is_speech})")
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
        # 应用FFmpeg预处理（如果启用）
        if self._ffmpeg_enabled:
            with PerformanceStep("FFmpeg预处理", {
                'data_length': len(audio_data),
                'current_time': current_time
            }):
                audio_data = self._apply_ffmpeg_preprocessing(audio_data, f"chunk_{current_time:.0f}")

        # 添加到音频缓冲区
        self._audio_buffer.extend(audio_data)

        # VAD检测
        is_speech, vad_event = self._detect_vad(audio_data, current_time)

        # 计算音频能量
        audio_energy = np.sqrt(np.mean(audio_data ** 2))

        # 检查是否应该发送GUI能量更新
        gui_threshold = self._get_gui_display_threshold()
        should_send_gui_update = not vad_event and audio_energy > gui_threshold

        # 如果没有VAD事件但能量超过显示阈值，也发送能量更新用于显示
        if should_send_gui_update:
            if self._on_vad_event:
                self._on_vad_event("energy_update", {
                    'time': current_time,
                    'energy': audio_energy
                })

        if vad_event and self._on_vad_event:
            self._on_vad_event(vad_event, {
                'time': current_time,
                'energy': audio_energy
            })

        # 如果检测到语音，添加到语音缓冲区
        if is_speech:
            # 记录语音输入开始（如果是新的语音段）
            #if vad_event == "speech_start":and debug_tracker:
                #debug_tracker.record_voice_input_start(audio_energy)

            self._speech_buffer.extend(audio_data)

            # 定期进行流式识别
            if len(self._speech_buffer) >= self.sample_rate * 1:  # 0.5-1秒音频
                self._perform_streaming_recognition()
        else:
            # 如果静音时间足够长且有语音缓冲区，进行最终识别
            if (len(self._speech_buffer) > 0 and
                hasattr(self, '_last_speech_time') and
                current_time - self._last_speech_time >= self.vad_config.min_silence_duration):

                if len(self._speech_buffer) >= self.sample_rate * self.vad_config.min_speech_duration:
                    # 记录语音输入结束和ASR开始
                    #if debug_tracker:
                    #    debug_tracker.record_voice_input_end(len(self._speech_buffer) / self.sample_rate)
                    #    debug_tracker.record_asr_start(len(self._speech_buffer))

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

            # 🔥 架构修复：在语音段结束时进行FFmpeg批量预处理
            if self._ffmpeg_enabled and len(audio_array) > 0:
                logger.debug("对完整语音段进行FFmpeg预处理")
                with PerformanceStep("FFmpeg批量预处理", {
                    'audio_length': len(audio_array),
                    'duration_seconds': len(audio_array) / self.sample_rate
                }):
                    # 使用完整的语音段进行预处理，而不是每个chunk
                    audio_array = self._apply_ffmpeg_preprocessing(audio_array, "final_segment")

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

    def get_status(self) -> Dict[str, Any]:
        """获取识别器状态"""
        return {
            'initialized': self._is_initialized,
            'model_loaded': self._model_loaded,
            'model_path': self.model_path,
            'device': self.funasr_config.device,
            'vad_method': 'TEN VAD' if self._ten_vad_enabled else 'Energy Threshold',
            'ten_vad_available': TEN_VAD_AVAILABLE,
            'stats': self.stats.copy(),
            'model_load_time': self._model_load_time,
            'dependencies': {
                'funasr': FUNASR_AVAILABLE,
                'pyaudio': PYAUDIO_AVAILABLE,
                'numpy': NUMPY_AVAILABLE,
                'ten_vad': TEN_VAD_AVAILABLE
            }
        }

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
        current_time = 0.0  # 初始化current_time变量

        try:
            with self._audio_stream() as stream:
                # 支持duration=-1表示无限时模式
                while (duration == -1 or time.time() - start_time < duration) and not self._stop_event.is_set():
                    try:
                        # 更新当前时间
                        current_time = time.time() - start_time

                        # 读取音频数据
                        with PerformanceStep("音频输入", {
                            'chunk_size': self.chunk_size,
                            'current_time': current_time
                        }):
                            data = stream.read(self.chunk_size, exception_on_overflow=False)

                        # 转换为numpy数组
                        with PerformanceStep("音频处理", {
                            'data_length': len(data),
                            'current_time': current_time
                        }):
                            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                        # 🔥 架构修复：移除实时循环中的FFmpeg预处理
                        # FFmpeg预处理将在语音段结束时批量进行，而不是在每个音频chunk时处理
                        # 这样保持了实时音频处理的连续性，避免了stream.read()阻塞问题

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
                            # 🔥 关键修复：在音频读取前检查停止信号
                            if self._stop_event.is_set():
                                logger.info("连续识别检测到停止信号，退出循环")
                                break

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
    print("🎯 FunASR + TEN VAD 语音识别模块测试")
    print("=" * 50)

    # 创建识别器
    recognizer = FunASRVoiceRecognizer()

    # 显示状态
    status = recognizer.get_status()
    print(f"📊 识别器状态: {status}")

    if recognizer.initialize():
        print("✅ 识别器初始化成功")
        print("🎤 TEN VAD集成完成，可以进行语音识别测试")
    else:
        print("❌ 识别器初始化失败")