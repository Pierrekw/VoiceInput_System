#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR + Silero VAD 语音识别模块
基于FunASR ASR + Silero VAD的语音录入和识别功能，可作为模块导入使用
结合神经网络VAD、流式识别和多种优化策略

Silero VAD优势：
- 神经网络VAD，比传统能量阈值更准确
- 抗噪音能力强，误检率低
- 能够检测轻声语音
- 无需手动调参，开箱即用
- 流式支持，低延迟
- Hugging Face维护，持续更新

使用示例:
    from funasr_voice_Silero import FunASRVoiceRecognizer

    recognizer = FunASRVoiceRecognizer()
    recognizer.initialize()
    result = recognizer.recognize_speech(duration=10)
    print(f"识别结果: {result}")
"""

import os
import sys
import warnings
import logging
import torch
import numpy as np

# 导入性能监控
from performance_monitor import performance_monitor, PerformanceStep

# 导入Debug性能追踪模块
try:
    from debug_performance_tracker import debug_tracker
except ImportError:
    debug_tracker = None

# Silero VAD相关
SILERO_VAD_AVAILABLE = False
silero_vad_model = None
silero_vad_utils = None

try:
    # 加载本地Silero VAD
    silero_vad_path = "F:/04_AI/01_Workplace/silero-vad"
    if os.path.exists(silero_vad_path):
        sys.path.insert(0, os.path.join(silero_vad_path, "src"))

        # 导入本地Silero VAD (基于真实API)
        from silero_vad import silero_vad, utils_vad

        # 创建Silero VAD实例
        silero_vad_model, silero_vad_utils = silero_vad()
        SILERO_VAD_AVAILABLE = True
        print("✅ Silero VAD 加载成功 (使用本地模型)")

    else:
        print(f"⚠️ Silero VAD路径不存在: {silero_vad_path}")
        print("🔄 尝试从torch hub加载...")
        # 备选：torch hub加载
        silero_vad_model, silero_vad_utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False
        )
        SILERO_VAD_AVAILABLE = True
        print("✅ Silero VAD 从torch hub加载成功")

except Exception as e:
    print(f"⚠️ Silero VAD加载失败: {e}")
    print("💡 建议检查:")
    print("  1. torch 和 torchaudio 是否已安装")
    print("  2. 网络连接是否正常")
    print("  3. 将自动回退到能量阈值VAD")
    SILERO_VAD_AVAILABLE = False

# 彻底抑制FunASR的进度条和调试输出
os.environ['TQDM_DISABLE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['HIDE_PROGRESS'] = '1'
os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

# 配置日志级别，只显示错误
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
            os.path.join(script_dir, "FunASR_Deployment",
                        "dependencies", "ffmpeg-master-latest-win64-gpl-shared", "bin"),
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
import pyaudio
import threading
from contextlib import contextmanager
from typing import List, Dict, Optional, Callable, Union, Tuple, Any
from dataclasses import dataclass
from collections import deque

# 使用统一的日志工具类
from logging_utils import LoggingManager

# 获取配置好的日志记录器（参考voice_gui.py的配置风格）
logger = LoggingManager.get_logger(
    name='funasr_voice_Silero',
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
    """Silero VAD配置"""
    # Silero VAD主要参数
    vad_threshold: float = 0.5           # VAD检测阈值 (0-1)
    min_speech_duration: float = 0.25    # 最小语音时长 (250ms)
    min_silence_duration: float = 0.1    # 最小静音时长 (100ms)
    speech_padding: float = 0.03          # 语音填充 (30ms)

    # 回退配置：当Silero VAD不可用时使用
    fallback_energy_threshold: float = 0.015  # 回退到能量阈值

    # Silero VAD特定配置
    use_silero_vad: bool = True        # 是否使用Silero VAD
    auto_fallback: bool = True          # 自动回退到能量阈值

    # Silero VAD高级参数
    window_size_samples: int = 512        # 窗口大小样本数
    min_speech_duration_ms: int = 250   # 最小语音时长毫秒
    min_silence_duration_ms: int = 100   # 最小静音时长毫秒
    speech_pad_ms: int = 30            # 语音填充毫秒

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
    FunASR + Silero VAD 语音识别器主类
    提供语音录入、识别和神经网络VAD功能
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

        # VAD配置 - 支持从配置文件加载
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

        # 音频处理
        self._audio_buffer: deque[np.ndarray] = deque(maxlen=sample_rate * 5)  # 5秒缓冲
        self._speech_buffer: List[np.ndarray] = []
        self._funasr_cache: Dict[str, Any] = {}

        # Silero VAD音频缓冲 (用于处理512样本的窗口)
        self._silero_vad_buffer: List[np.ndarray] = []
        self._silero_window_size = 512  # Silero VAD要求的窗口大小

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

        # Silero VAD初始化状态
        self._silero_vad_enabled = SILERO_VAD_AVAILABLE and self.vad_config.use_silero_vad

    def _load_vad_config(self):
        """从配置加载器加载VAD设置"""
        try:
            from config_loader import config

            return VADConfig(
                vad_threshold=0.5,  # Silero VAD默认阈值
                min_speech_duration=config.get_vad_min_speech_duration(),
                min_silence_duration=config.get_vad_min_silence_duration(),
                speech_padding=config.get_vad_speech_padding(),
                fallback_energy_threshold=config.get_vad_energy_threshold(),
                use_silero_vad=True,  # 默认使用Silero VAD
                auto_fallback=True
            )

        except Exception as e:
            logger.warning(f"加载VAD配置失败: {e}，使用默认配置")
            return VADConfig()

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

        logger.info("🚀 初始化FunASR + Silero VAD语音识别器...")
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
        logger.info(f"✅ FunASR + Silero VAD语音识别器初始化完成 (总耗时: {total_init_time:.2f}秒)")

        # 显示VAD状态
        if self._silero_vad_enabled:
            logger.info("🎯 Silero VAD已启用 (window_size=512, threshold=0.5)")
        else:
            logger.info("⚠️ Silero VAD不可用，使用回退的能量阈值VAD")

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

    def _detect_vad(self, audio_data: np.ndarray, current_time: float) -> Tuple[bool, Optional[str]]:
        """
        VAD语音活动检测 - 使用Silero VAD

        Args:
            audio_data: 音频数据
            current_time: 当前时间

        Returns:
            (is_speech, event_type): 是否有语音和事件类型
        """
        is_speech = False
        vad_confidence = 0.0

        # 优先使用Silero VAD
        if self._silero_vad_enabled and silero_vad_model and silero_vad_utils:
            try:
                # 将音频数据添加到Silero VAD缓冲区
                self._silero_vad_buffer.extend(audio_data)

                # 当缓冲区足够大时，处理Silero VAD
                is_speech = False
                while len(self._silero_vad_buffer) >= self._silero_window_size:
                    # 取出512个样本进行处理
                    window_audio = np.array(self._silero_vad_buffer[:self._silero_window_size])
                    self._silero_vad_buffer = self._silero_vad_buffer[self._silero_window_size:]

                    # 转换为torch tensor
                    if isinstance(window_audio, np.ndarray):
                        audio_tensor = torch.from_numpy(window_audio).float()
                    else:
                        audio_tensor = window_audio.float()

                    # 使用Silero VAD的get_speech_timestamps方法 (基于真实API)
                    try:
                        # get_speech_timestamps需要完整的音频，这里使用简化的VAD检测
                        # 实际上，我们需要的是实时的VAD判断
                        if hasattr(silero_vad_model, '__call__'):
                            # 直接调用模型进行VAD推理
                            with torch.no_grad():
                                vad_output = silero_vad_model(audio_tensor)
                                # vad_output通常是语音概率
                                if len(vad_output.shape) > 0:
                                    vad_confidence = float(vad_output.mean())
                                    is_speech = vad_confidence > self.vad_config.vad_threshold
                        else:
                            # 如果无法直接调用，回退到能量阈值
                            energy = np.sqrt(np.mean(audio_data ** 2))
                            vad_confidence = energy
                            is_speech = energy > self.vad_config.fallback_energy_threshold

                    except Exception as vad_error:
                        logger.debug(f"Silero VAD推理失败: {vad_error}")
                        # 回退到能量阈值
                        energy = np.sqrt(np.mean(audio_data ** 2))
                        vad_confidence = energy
                        is_speech = energy > self.vad_config.fallback_energy_threshold

                    if is_speech:
                        break  # 只要有一个窗口检测到语音，就认为当前有语音

                logger.debug(f"Silero VAD: 置信度={vad_confidence:.6f}, 检测语音={is_speech}")

            except Exception as e:
                logger.error(f"❌ Silero VAD检测失败: {e}")
                # 自动回退到能量阈值
                if self.vad_config.auto_fallback:
                    energy = np.sqrt(np.mean(audio_data ** 2))
                    is_speech = energy > self.vad_config.fallback_energy_threshold
                    vad_confidence = energy
                    logger.debug(f"回退到能量阈值: {energy:.6f}")

        else:
            # 回退到传统能量阈值VAD
            energy = np.sqrt(np.mean(audio_data ** 2))
            is_speech = energy > self.vad_config.fallback_energy_threshold
            vad_confidence = energy if is_speech else 0.0

        # 计算音频能量（用于显示和调试）
        audio_energy = np.sqrt(np.mean(audio_data ** 2))

        # 事件状态管理
        event_type = None
        if is_speech:
            if not hasattr(self, '_speech_detected') or not self._speech_detected:
                event_type = "speech_start"
                self._speech_detected = True
                self._speech_start_time = current_time
                vad_method = "Silero VAD" if self._silero_vad_enabled else "Energy Threshold"
                logger.info(f"🎤 语音开始 ({vad_method}: {vad_confidence:.3f}, 能量: {audio_energy:.6f})")
        else:
            if hasattr(self, '_speech_detected') and self._speech_detected:
                silence_duration = current_time - getattr(self, '_last_speech_time', current_time)
                if silence_duration >= self.vad_config.min_silence_duration:
                    event_type = "speech_end"
                    self._speech_detected = False
                    vad_method = "Silero VAD" if self._silero_vad_enabled else "Energy Threshold"
                    logger.info(f"🔇 语音结束 (静音{silence_duration:.2f}s, {vad_method}: {vad_confidence:.3f})")

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
            if vad_event == "speech_start" and debug_tracker:
                debug_tracker.record_voice_input_start(audio_energy)

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
                    # 记录语音输入结束和ASR开始
                    if debug_tracker:
                        debug_tracker.record_voice_input_end(len(self._speech_buffer) / self.sample_rate)
                        debug_tracker.record_asr_start(len(self._speech_buffer))

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

    def get_status(self) -> Dict[str, Any]:
        """获取识别器状态"""
        return {
            'initialized': self._is_initialized,
            'model_loaded': self._model_loaded,
            'model_path': self.model_path,
            'device': self.funasr_config.device,
            'vad_method': 'Silero VAD' if self._silero_vad_enabled else 'Energy Threshold',
            'silero_vad_available': SILERO_VAD_AVAILABLE,
            'stats': self.stats.copy(),
            'model_load_time': self._model_load_time,
            'dependencies': {
                'funasr': FUNASR_AVAILABLE,
                'pyaudio': PYAUDIO_AVAILABLE,
                'numpy': NUMPY_AVAILABLE,
                'silero_vad': SILERO_VAD_AVAILABLE
            }
        }

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

if __name__ == "__main__":
    # 示例用法
    print("🎯 FunASR + Silero VAD 语音识别模块测试")
    print("=" * 50)

    # 创建识别器
    recognizer = FunASRVoiceRecognizer()

    # 显示状态
    status = recognizer.get_status()
    print(f"📊 识别器状态: {status}")

    if recognizer.initialize():
        print("✅ 识别器初始化成功")
        print("🎤 Silero VAD集成完成，可以进行语音识别测试")
    else:
        print("❌ 识别器初始化失败")