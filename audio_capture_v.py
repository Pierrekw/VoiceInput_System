# -*- coding: utf-8 -*-
# Audio Capture Module - 音频捕获模块
# Supports real-time voice recognition with pause/resume functionality
 
import sys, os, io, json, threading, logging, re, gc, time
from collections import deque
from typing import List, Tuple, Optional, Callable, Deque, Any, Union
import pyaudio
import cn2an
from vosk import Model, KaldiRecognizer
import vosk
from contextlib import contextmanager
from TTSengine import TTS
from config_loader import config  # 导入配置系统
 
logger = logging.getLogger(__name__)
# --------------------------------------------------------------
# 1️⃣ Audio Stream Context Manager / 音频流上下文管理器
# --------------------------------------------------------------
@contextmanager
def audio_stream():
    """Open PyAudio input stream with automatic cleanup"""
    p = pyaudio.PyAudio()
 
    try:
        default_device = p.get_default_input_device_info()
        logger.debug(f"🎤 使用音频设备: {default_device['name']} (索引: {default_device['index']})")
 
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000,
            start=True,
        )
 
        logger.debug(f"🎧 音频流创建成功 - 活动状态: {stream.is_active()}")
 
    except Exception as e:
        logger.error(f"❌ 音频流创建失败: {e}")
        p.terminate()
        raise
 
    try:
        yield stream
    
    finally:
            # 资源清理不输出详细日志，只在debug模式下输出
            if stream.is_active():
                stream.stop_stream()
            stream.close()
            p.terminate()
# --------------------------------------------------------------
# 2️⃣ Keyboard Listener / 键盘监听器
# --------------------------------------------------------------
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError as e:
    print("⚠️ 警告: pynput 模块未安装，键盘快捷键将不可用")
    print("请执行: uv pip install pynput 或 pip install pynput 安装该模块")
    PYNPUT_AVAILABLE = False
    # 导入时使用类型注解，运行时不影响行为
    keyboard = None  # type: ignore
# 全局变量存储按键状态（按下但未释放）
_key_pressed = {
    'space': False,
    'esc': False,
    't': False
}
# --------------------------------------------------------------
# 3️⃣ Basic Configuration / 基础配置
# --------------------------------------------------------------
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
vosk.SetLogLevel(-1)
# --------------------------------------------------------------
# 4️⃣ Voice Correction Dictionary / 语音纠错词典
# --------------------------------------------------------------
def load_voice_correction_dict(file_path=None) -> dict[str, str]:
    """Load voice error correction dictionary from external file"""
    # 检查错误修正功能是否启用
    if not config.get("error_correction.enabled", True):
        logger.info("🔇 语音错误修正功能已禁用")
        return {}
    
    # 使用配置文件中的词典路径，如果未指定则使用默认值
    if file_path is None:
        file_path = config.get("error_correction.dictionary_path", "voice_correction_dict.txt")
    
    correction_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    wrong, correct = line.split('=', 1)
                    correction_dict[wrong.strip()] = correct.strip()
        logger.info(f"✅ 成功加载 {len(correction_dict)} 个语音纠错规则")
    except FileNotFoundError:
        logger.warning(f"⚠️ 未找到词典文件 {file_path}，将使用空词典")
        correction_dict = {}
    except Exception as e:
        logger.error(f"❌ 加载词典文件出错: {e}，将使用空词典")
        correction_dict = {}
    
    return correction_dict
 
# 加载语音纠错词典
VOICE_CORRECTION_DICT = load_voice_correction_dict()
 
def correct_voice_errors(text: str) -> str:
    """Replace commonly misrecognized words with correct number expressions"""
    # 检查错误修正功能是否启用
    if not config.get("error_correction.enabled", True):
        return text
        
    for wrong, correct in VOICE_CORRECTION_DICT.items():
        text = text.replace(wrong, correct)
    return text
# --------------------------------------------------------------
# 5️⃣ Number Extraction / 数值提取
# --------------------------------------------------------------
_NUM_PATTERN = re.compile(r"[零一二三四五六七八九十百千万点两\d]+(?:\.[零一二三四五六七八九十百千万点两\d]+)*")
# 单位正则表达式，用于提取带单位的数值
_UNIT_PATTERN = re.compile(r"([零一二三四五六七八九十百千万点两\d]+(?:\.[零一二三四五六七八九十百千万点两\d]+)*)(?:公斤|克|吨|米|厘米|毫米|升|毫升|秒|分钟|小时|天|月|年)")

# 特殊处理模式：处理"点八四"这种格式
def handle_special_formats(text: str) -> str:
    """处理特殊的数字表达格式，如'点八四'"""
    # 处理"点X"格式
    if text.startswith("点") and len(text) > 1:
        # 将"点八四"转换为"零点八四"
        return "零" + text
    return text
 
def extract_measurements(text: Any) -> List[float]:
    """Extract all possible numbers (Chinese or Arabic) from text and return as float list"""
    if not isinstance(text, (str, int, float)):
        return []

    try:
        txt = str(text).strip()
        
        # 特殊处理：当前不支持负数，检测到负数关键词时返回空列表
        negative_keywords = ['负数', '负']
        for keyword in negative_keywords:
            if keyword in txt:
                logger.debug(f"检测到负数关键词 '{keyword}'，不提取数字")
                return []
        
        # 优先尝试直接转换整个文本
        try:
            num = cn2an.cn2an(txt, "smart")
            num_float = float(num)
            # 增加上限以支持更大的数值，如连续数字
            if 0 <= num_float <= 1000000000000:  # 10^12，足够大的数值范围
                logger.debug(f"直接转换整个文本得到数值: {num_float} (文本: '{txt}')")
                return [num_float]
            else:
                logger.debug(f"直接转换数值超出范围: {num_float} (文本: '{txt}')")
        except Exception as e:
            logger.debug(f"直接转换失败: {e} (文本: '{txt}')")
        
        # 特殊处理：尝试按字符逐个转换连续中文数字
        try:
            # 检查文本是否全是中文数字字符
            chinese_nums = set("零一二三四五六七八九十百千万")
            if all(char in chinese_nums for char in txt):
                result = ""
                for char in txt:
                    num = cn2an.cn2an(char, "smart")
                    result += str(num)
                if result.isdigit():
                    num_float = float(result)
                    if 0 <= num_float <= 1000000000000:
                        logger.debug(f"按字符逐个转换连续中文数字得到数值: {num_float} (文本: '{txt}')")
                        return [num_float]
        except Exception as e:
            logger.debug(f"按字符逐个转换失败: {e} (文本: '{txt}')")
        # 专门处理常见的误识别模式
        # 1. '我'可能是'五'的误识别
        if txt == '我':
            logger.debug(f"检测到可能的误识别：'我' → 尝试作为'五'处理")
            try:
                num = cn2an.cn2an('五', "smart")
                num_float = float(num)
                if 0 <= num_float <= 10000000000:
                    logger.debug(f"成功将'我'识别为数值: {num_float}")
                    return [num_float]
            except Exception:
                pass
        
        # 2. '我是'可能是'五十'的误识别
        elif txt == '我是':
            logger.debug(f"检测到可能的误识别：'我是' → 尝试作为'五十'处理")
            try:
                num = cn2an.cn2an('五十', "smart")
                num_float = float(num)
                if 0 <= num_float <= 1000000:
                    logger.debug(f"成功将'我是'识别为数值: {num_float}")
                    return [num_float]
            except Exception:
                pass
        
        # 3. '我是我'可能是'五五'的误识别
        elif txt == '我是我':
            logger.debug(f"检测到可能的误识别：'我是我' → 尝试作为'五五'处理")
            try:
                num = cn2an.cn2an('五五', "smart")
                num_float = float(num)
                if 0 <= num_float <= 1000000:
                    logger.debug(f"成功将'我是我'识别为数值: {num_float}")
                    return [num_float]
            except Exception:
                pass
        
        # 移除常见的误识别前缀
        for prefix in ['我', '你']:
            if txt.startswith(prefix):
                txt = txt[len(prefix):]
                logger.debug(f"移除前缀 '{prefix}' 后: '{txt}'")
        
        # 应用语音纠错
        txt = correct_voice_errors(txt)
        logger.debug(f"语音纠错后: '{txt}'")
 
        # 先检查整个文本是否是一个数字表达式
        try:
            # 处理特殊格式如"点八四"
            special_handled = handle_special_formats(txt)
            if special_handled != txt:
                logger.debug(f"特殊格式处理后: '{special_handled}'")
                num = cn2an.cn2an(special_handled, "smart")
                num_float = float(num)
                if 0 <= num_float <= 1000000:
                    logger.debug(f"成功提取整个文本的数值: {num_float}")
                    return [num_float]
        except Exception:
            # 如果整个文本不是数字表达式，再使用正则提取
            pass
        
        # 先尝试使用单位正则提取带单位的数值
        unit_matches = _UNIT_PATTERN.findall(txt)
        if unit_matches:
            candidates = unit_matches
        else:
            # 如果没有带单位的数值，再使用普通数字正则
            candidates = _NUM_PATTERN.findall(txt)
        nums = []
        seen_numbers = set()  # 用于去重
        
        for cand in candidates:
            try:
                # 处理特殊格式
                cand_handled = handle_special_formats(cand)
                if cand_handled != cand:
                    logger.debug(f"处理候选 '{cand}' 为 '{cand_handled}'")
                
                num = cn2an.cn2an(cand_handled, "smart")
                num_float = float(num)
                
                # 过滤掉不合理的数值（增加上限以支持更大的数值，如千克、吨等单位的数值）
                if 0 <= num_float <= 1000000:
                    # 去重：避免同一数值被多次提取
                    if num_float not in seen_numbers:
                        seen_numbers.add(num_float)
                        nums.append(num_float)
                        logger.debug(f"成功提取数值: {num_float} 来自候选: '{cand}'")
                else:
                    logger.debug(f"过滤掉不合理的数值: {num_float}")
            except Exception as e:
                logger.debug(f"数值转换失败 '{cand}': {e}")
                continue
        
        # 如果使用正则没有提取到数值，尝试直接转换整个文本
        if not nums and txt:
            try:
                txt_handled = handle_special_formats(txt)
                num = cn2an.cn2an(txt_handled, "smart")
                num_float = float(num)
                if 0 <= num_float <= 1000000:
                    nums.append(num_float)
                    logger.debug(f"直接转换整个文本得到数值: {num_float}")
            except Exception:
                # 特殊处理：尝试直接转换整个文本中的每个数字部分
                try:
                    # 对于连续的中文数字，直接使用cn2an转换整个字符串
                    num = cn2an.cn2an(txt, "smart")
                    num_float = float(num)
                    if 0 <= num_float <= 1000000:
                        nums.append(num_float)
                        logger.debug(f"特殊处理连续中文数字得到数值: {num_float}")
                except Exception:
                    pass
        
        return nums
    except Exception as e:
        logger.error(f"数值提取过程出错: {e}")
        return []
# --------------------------------------------------------------
# 6️⃣ Main Class: AudioCapture / 主类：AudioCapture
# --------------------------------------------------------------
class AudioCapture:
    """
    Real-time voice recognition based on Vosk with pause/resume functionality
    """
 
    def __init__(
        self, timeout_seconds=None, 
        excel_exporter: Optional['ExcelExporter'] = None, 
        model_path=None, 
        test_mode=None, 
        device_index: int | None = None, 
        sample_rate: Optional[int] = None, 
        audio_chunk_size=None, 
        tts_state: str = "on"):
        
        self.tts_state: str = "on"
        self.tts = TTS()
        self._tts_lock = threading.Lock()  # 新增：TTS锁
        self._tts_playing = False  # 新增：TTS播放状态
        # 从配置系统获取参数，允许外部传入覆盖
        self.timeout_seconds: int = timeout_seconds if timeout_seconds is not None else config.get_timeout_seconds()
        self.model_path: str = model_path if model_path is not None else config.get_model_path()
        self.test_mode: bool = test_mode if test_mode is not None else config.get_test_mode()
        # 从配置系统获取音频块大小默认值
        self.audio_chunk_size = audio_chunk_size if audio_chunk_size is not None else config.get("audio.chunk_size", 8000)
        self.device_index = device_index
        # 从配置系统获取采样率默认值
        self.sample_rate: int = sample_rate if sample_rate is not None else config.get("audio.sample_rate", 16000)

        # ---------- 统一状态管理 ----------
        self.state: str = "idle"  # 初始状态为idle
        self._pause_event: threading.Event = threading.Event()
        self._pause_event.set()
        self._start_event: threading.Event = threading.Event()
        self._start_event.clear()
        
        # 新增：暂停超时计时
        self._pause_start_time: Optional[float] = None
        # 从配置系统获取暂停超时乘数
        self._pause_timeout_multiplier: int = config.get("recognition.pause_timeout_multiplier", 3)

        self.callback_function: Callable[[list[float]], None] | None = None
        # 从配置系统获取缓冲区大小
        self.buffered_values: Deque[float] = deque(maxlen=config.get("recognition.buffer_size", 10000))
        
        # 新增：存储带原始文本的数据
        self.buffered_data_with_text: List[Tuple[float, str]] = []
        

        # ---------- Excel 导出器 ----------
        # 如果没有提供导出器但配置了自动导出，则自动创建
        self._exporter: Optional['ExcelExporter'] = excel_exporter
        if excel_exporter is None:
            auto_export = config.get("excel.auto_export", True)
            if auto_export:
                try:
                    from excel_exporter import ExcelExporter
                    self._exporter = ExcelExporter()
                    logger.info("📊 根据配置自动创建Excel导出器")
                except ImportError:
                    logger.warning("⚠️ 无法导入Excel导出器")
                    self._exporter = None

        # ---------- 模型相关 ----------
        self._model: Optional['Model'] = None
        self._recognizer: Optional['KaldiRecognizer'] = None
        self._model_loaded: bool = False
 
    # ----------------------------------------------------------
    # 动态设置音频块大小
    # ----------------------------------------------------------
    def set_audio_chunk_size(self, size: int):
        if size <= 0:
            raise ValueError("音频块大小必须大于0")
        self.audio_chunk_size = size
        logger.info(f"音频块大小已设置为: {size}")

        if self.test_mode:
            print(f"[设置] 音频块大小: {size}")
    
    # ----------------------------------------------------------
    # 模型预加载方法
    # ----------------------------------------------------------

    def load_model(self) -> bool:
        """预加载Vosk模型和识别器，返回是否成功"""
        # 检查本地是否已经加载了模型
        if self._model_loaded and self._model is not None and self._recognizer is not None:
            logger.info("✅ 本地模型已加载，无需重复加载")
            return True

        logger.info("📦 正在加载Vosk模型...")
        try:
            # 检查模型路径是否存在
            if not os.path.exists(self.model_path):
                logger.error(f"❌ 模型路径不存在: {self.model_path}")
                return False
            
            start_time = time.time()
            # 直接在本地加载模型
            self._model = Model(self.model_path)
            self._recognizer = KaldiRecognizer(self._model, self.sample_rate)
            self._model_loaded = True
            
            load_time = time.time() - start_time
            logger.info(f"✅ 模型加载成功: {self.model_path} (耗时: {load_time:.2f}秒)")
            
            if self.test_mode:
                print(f"[模型] 模型 '{self.model_path}' 已加载")
                print(f"[模型] 加载耗时: {load_time:.2f}秒")
                
            return True
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            self._model = None
            self._recognizer = None
            self._model_loaded = False
            return False
    
    def unload_model(self) -> None:
        """卸载模型以释放内存"""
        self._model = None
        self._recognizer = None
        self._model_loaded = False
        import gc
        gc.collect()
        logger.info("🧹 模型已卸载，内存已释放")
 
    # ----------------------------------------------------------
    # 新增TTS控制方法
    def toggle_tts(self) -> None:
        """切换TTS开关状态"""
        old_state = self.tts_state
        self.tts_state = "off" if self.tts_state == "on" else "on"
        logger.info(f"🔊 TTS状态已切换至: {'开启' if self.tts_state == 'on' else '关闭'}")
        if self.test_mode:
            print(f"TTS: {old_state} -> {self.tts_state}")
 
    def enable_tts(self) -> None:
        """启用TTS功能"""
        self.tts_state = "on"
        logger.info("🔊 TTS功能已启用")
 
    def disable_tts(self) -> None:
        """禁用TTS功能"""
        self.tts_state = "off"
        logger.info("🔇 TTS功能已禁用")
 
    def get_tts_status(self) -> str:
        """获取当前TTS状态"""
        return self.tts_state
    
    # 6.1 回调 & 过滤
    # ----------------------------------------------------------
    def set_callback(self, callback: Callable[[List[float]], None]) -> None:
        """外部注册一个回调函数，收到数值时触发。"""
        self.callback_function = callback
 
    def _process_voice_commands(self, text: str) -> bool:
        """Process voice control commands"""
        if not text:
            return False

        text_lower = text.lower()
        
        # 使用配置文件中的语音命令
        pause_commands = config.get("voice_commands.pause_commands", ["暂停录音", "暂停", "pause"])
        resume_commands = config.get("voice_commands.resume_commands", ["继续录音", "继续", "恢复", "resume"])
        stop_commands = config.get("voice_commands.stop_commands", ["停止录音", "停止", "结束", "stop", "exit"])
        
        if any(word in text_lower for word in pause_commands):
            if self.state == "recording":
                logger.info("🎤 语音命令：暂停")
                self.pause()
                return True
        elif any(word in text_lower for word in resume_commands):
            if self.state == "paused":
                logger.info("🎤 语音命令：恢复")
                self.resume()
                return True
        elif any(word in text_lower for word in stop_commands):
            logger.info("🎤 语音命令：停止")
            self.stop()
            return True

        return False
 
    def filtered_callback(self, text: str) -> List[Tuple[int, float, str]]:
        """
        对识别文本进行过滤、提取数值并回调。
        返回写入Excel的记录列表 [(ID, 数值, 原始文本)]
        """
        if not isinstance(text, str):
            return []
        
        nums = extract_measurements(text)
        written_records = []          
        
        if self.test_mode:            
            if nums:
                print(f"[提取数值] {nums}")
            else:
                print("[提示] 未检测到数值")


        if nums:
            # 记录原始文本和数值
            for num in nums:
                self.buffered_data_with_text.append((num, text))
                self.buffered_values.append(num)
            
            # 如果有导出器，立即写入Excel
            if self._exporter:
                try:
                    # 准备写入数据 [(数值, 原始文本)]
                    data_to_write = [(num, text) for num in nums]
                    written_records = self._exporter.append_with_text(data_to_write)
                    
                    # 记录写入结果
                    for i, (record_id, value, original_text) in enumerate(written_records):
                        logger.info(f"识别文字：{original_text} -> ID {record_id}, 数值 {value}，已写入Excel")
                        
                except Exception as e:
                    logger.error(f"❌ 写入Excel失败: {e}")
            
            # 触发回调
            if self.callback_function:
                self.callback_function(nums)
            
            # TTS播报
            if self.tts_state == "on" and nums:
                try:
                    # 使用锁机制，避免TTS声音被识别
                    with self._tts_lock:
                        self._tts_playing = True
                              
                        # 暂停Vosk识别
                        original_state = self.state
                        if original_state == "recording":
                            self.state = "paused"  # 临时暂停识别
                                  
                            if self.test_mode:
                                print(f"[TTS] 开始播报，暂停识别")
                          
                    numbers_text = "，".join(str(num) for num in nums)
                    self.tts.speak(f"测量值: {numbers_text}")
                          
                    if self.test_mode:
                        print(f"[TTS] 播报完成")
                except Exception as e:
                    logger.error(f"❌ TTS播报出错: {e}")
                finally:
                    # 恢复识别状态
                    with self._tts_lock:
                        if original_state == "recording":
                            self.state = "recording"
                            self._pause_start_time = time.time()  # 重置暂停计时器
                                
                            if self.test_mode:
                                print(f"[TTS] 恢复识别")
                          
                        self._tts_playing = False
            elif self.test_mode:
                    print(f"[TTS跳过] 检测到可能的误识别，跳过播报: '{text}'")
        elif not nums:
            if text.strip(): #只有非空白文本才显示
                print(f"[实时识别] '{text}'")
        
        return written_records
 
    # ----------------------------------------------------------
    # 重置TTS状态（确保系统始终可以响应语音）
    # ----------------------------------------------------------
    def reset_tts_state(self):
        """重置TTS状态，确保_tts_playing被设为False"""
        with self._tts_lock:
            if self._tts_playing:
                logger.warning("🔄 强制重置TTS状态")
                self._tts_playing = False
                if self.state == "paused" and self._pause_start_time:
                    # 如果是因为TTS暂停的，尝试恢复
                    self.state = "recording"
                    self._pause_start_time = time.time()
                    logger.info("▶️ 已恢复识别状态")
    
    # ----------------------------------------------------------
    # 6.3 控制接口（暂停/恢复/停止）
    # ----------------------------------------------------------
        
    def pause(self) -> None:
        """暂停实时识别"""
        if self.state != "recording":
            return
        old_state = self.state
        self.state = "paused"
        self._pause_event.clear()
        self._pause_start_time = time.time()
        logger.info("⏸️ 已暂停识别")
        if self.test_mode:
            print(f"状态: {old_state} -> {self.state}")
 
    def resume(self) -> None:
        """恢复实时识别。"""
        if self.state != "paused":
            return
        old_state = self.state
        self.state = "recording"
        self._pause_event.set()
        self._pause_start_time = None
        # 同时重置TTS状态
        self.reset_tts_state()
        logger.info("▶️ 已恢复识别")
        if self.test_mode:
            print(f"状态: {old_state} -> {self.state}")
 
    def stop(self) -> None:
        """停止实时识别。"""
        if self.state == "stopped":
            return
        old_state = self.state
        self.state = "stopped"
        self._pause_event.set()
        self._pause_start_time = None
        if self.state == "idle": #如果提前启动阶段，检测到ESC，则直接停止。
            return
            logger.info("🛑用户强制退出")
        logger.info("🛑 已停止识别")
        if self.test_mode:
            print(f"状态: {old_state} -> {self.state}")

    def monitor_esc_key(self):
        #监听ESC键，如果按下则停止识别，并退出程序。
        self.stop()
        return
        

    @property
    def is_running(self) -> bool:
        """外部用于判断当前是"运行中"还是"已暂停"。"""
        return self.state == "recording"
 
    # ----------------------------------------------------------
    # 6.4 实时 Vosk 监听（核心实现）
    # ----------------------------------------------------------
    def listen_realtime_vosk(self) -> dict[str, Union[str, List[float], List[str], List[Tuple[int, float, str]]]]:
        """Start real-time voice recognition, return final text and cached values list"""
        import time

        logger.info("=" * 60)
        logger.info("🎤 开始实时语音识别流程...")
        logger.info(f"📊 当前状态: {self.state}")
        logger.info(f"🎯 模型路径: {self.model_path}")
        logger.info(f"⏱️  超时时间设定: {self.timeout_seconds}秒")
        if self.test_mode:
            logger.info(f"🧪 测试模式:开启")           
        
        try:
            with audio_stream() as stream:
                                
                audio_frames = 0
                recognition_count = 0
                collected_text = []
                recognition_start_time = time.time()               
                # 会话数据收集
                session_records: List[Tuple[int, float, str]] = []                
                        # 从配置系统获取倒计时秒数
                countdown_seconds = config.get("recognition.countdown_seconds", 5)
                logger.info(f"🚀 系统将在 {countdown_seconds} 秒后开始识别...")      
                
                print(f"⏰ {countdown_seconds}秒后自动开始录音")              
                               
                self.state = "idle"
                logger.debug("✅ 系统状态已设置为 idle")

                while countdown_seconds > 0:
                    print(f"⏰ 倒计时: {countdown_seconds}秒 ", end="\r")
                    countdown_seconds -= 1
                    time.sleep(1)
                    
                    if self.state == "stopped":
                        break
                
                logger.info("⏰✅ 倒计时结束")
                    
                self.state = "recording"
                logger.debug("✅ 系统状态已设置为 recording")
                
                if self.test_mode:
                    print(f"状态: idle -> recording")      

                logger.info("🎤 开始音频流监听...")
                while self.state != "stopped":
                # 检查暂停超时（仅在paused状态下）
                    if self.state == "paused":
                        if self._pause_start_time is not None:
                            pause_duration = time.time() - self._pause_start_time
                            if pause_duration > self.timeout_seconds:
                                logger.info(f"⏰ 暂停超时（{pause_duration:.1f}秒），自动停止")
                                self.stop()
                                break                 
                
                        # 新增：在暂停状态下检测是否有音频输入
                        try:
                            if stream.is_active():
                                # 尝试读取一小段音频数据（非阻塞）
                                data = stream.read(self.audio_chunk_size, exception_on_overflow=False) #8000->4000 减少延迟
                                # 如果有音频输入，重置暂停计时器
                                if data and any(b != 0 for b in data):
                                    if self.test_mode and audio_frames % 5000 == 0:  # 每1000帧输出一次:
                                        print("[调试] 检测到音频输入，重置暂停计时器")
                                    self._pause_start_time = time.time()
                        except Exception as e:
                            logger.debug(f"暂停状态音频检测错误: {e}")        

                        # 使用配置中的medium睡眠值，兼顾识别速度和键盘响应
                        time.sleep(config.get("recognition.sleep_times.production", 0.05))
                    
                    # 检查暂停事件
                    if not self._pause_event.is_set():
                        # 暂停状态，等待恢复
                        continue
                    # 检查超时
                    try:
                        # 新增：如果TTS正在播报，跳过音频处理
                        if self._tts_playing:
                            if self.test_mode and audio_frames % 1000 == 0:
                                print("[调试] TTS播报中，跳过音频处理")
                            
                            time.sleep(config.get("recognition.sleep_times.production", 0.05))
                            continue                        
                        
                        data = stream.read(self.audio_chunk_size, exception_on_overflow=False)
                        audio_frames += 1

                        if audio_frames % 50 == 0:
                            logger.debug(f"🎧 音频流正常 - 帧数: {audio_frames}")

                        if self._recognizer and self._recognizer.AcceptWaveform(data):
                            recognition_count += 1
                            result = json.loads(self._recognizer.Result())
                            text = (result.get("text") or "").replace(" ", "")

                            if text:
                                collected_text.append(text)

                                # 处理语音命令
                                if not self._process_voice_commands(text):
                                    # 处理数值提取和Excel写入
                                    written_records = self.filtered_callback(text)
                                    # 收集会话数据
                                    session_records.extend(written_records)
                        else:
                            if self._recognizer:
                                partial = json.loads(self._recognizer.PartialResult()).get("partial") or ""
                                if partial:
                                    pass

                    except Exception as e:
                        logger.error(f"❌ 音频流读取错误: {e}")
                        continue

                # 识别结束后获取最终结果
                final_text = ""
                if self._recognizer:
                    final_result = self._recognizer.FinalResult()
                    final_data = json.loads(final_result)
                    final_text = final_data.get("text", "")

                if not final_text and collected_text:
                    final_text = " ".join(collected_text)

                # 获取会话数据
                if self._exporter:
                    session_records = self._exporter.get_session_data()

                result_dict: dict[str, Union[str, List[float], List[str], List[Tuple[int, float, str]]]] = {
                    "final": final_text,
                    "buffered_values": list(self.buffered_values),
                    "collected_text": collected_text,
                    "session_data": session_records
                }

                return result_dict
                
        except Exception as e:
            logger.error(f"❌ 实时识别过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "final": "",
                "buffered_values": list(self.buffered_values),
                "collected_text": [],
                "session_data": []
            }
        finally:
            # 简化结束日志输出
            if self.test_mode:
                logger.info("🧹 识别会话结束，预加载模型仍保留在内存中")
 
    # ----------------------------------------------------------
 
    def test_voice_recognition_pipeline(self) -> dict[str, Any]:
        """Comprehensive test function to debug voice recognition pipeline"""
        from typing import Dict, List, Any
        test_results: Dict[str, Any] = {
            "audio_input_working": False,
            "model_loading_success": False,
            "recognition_attempts": 0,
            "successful_recognitions": 0,
            "audio_frames_processed": 0,
            "partial_results": [],
            "final_results": [],
            "errors": [],
            "audio_device_info": [],
            "test_duration": 0,
            "vosk_result": {}
        }
 
        import time
        start_time = time.time()
 
        try:
            # Test 1: Audio Input Device
            try:
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
 
                for i in range(device_count):
                    try:
                        device_info = p.get_device_info_by_index(i)
                        max_channels = device_info['maxInputChannels']
                        if isinstance(max_channels, (int, float)) and max_channels > 0:
                            test_results["audio_device_info"].append({"index": i, "name": device_info['name']})
                    except:
                        continue
 
                try:
                    default_device = p.get_default_input_device_info()
                    test_results["audio_input_working"] = True
                except Exception as e:
                    test_results["errors"].append(f"Audio device error: {str(e)}")
 
                p.terminate()
            except Exception as e:
                test_results["errors"].append(f"Audio device test failed: {str(e)}")
 
            # Test 2: Use existing listen_realtime_vosk() function
            logger.info("🎤 语音识别测试中... 请对着麦克风说话")
 
            original_state = self.state
            original_pause_event = self._pause_event.is_set()
            original_start_event = self._start_event.is_set()
 
            self.state = "recording"
            self._pause_event.set()
            self._start_event.set()
 
            try:
                vosk_result = self.listen_realtime_vosk()
                test_results["vosk_result"] = vosk_result
 
                if vosk_result["final"]:
                    test_results["final_results"].append(vosk_result["final"])
                    test_results["successful_recognitions"] += 1
                    logger.info(f"🎯 识别成功: '{vosk_result['final']}'")
 
                if vosk_result["buffered_values"]:
                    logger.info(f"🔢 提取到的数字: {vosk_result['buffered_values']}")
 
                test_results["model_loading_success"] = True
 
                logger.info(f"📊 Vosk 测试结果: 最终文本='{vosk_result['final']}', 数字={vosk_result['buffered_values']}")
 
            except Exception as e:
                error_msg = f"Vosk 测试失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                test_results["errors"].append(error_msg)
 
            finally:
                self.state = original_state
                if not original_pause_event:
                    self._pause_event.clear()
                if not original_start_event:
                    self._start_event.clear()
 
            # Test 3: Voice Commands
            logger.info("🎤 测试3: 语音命令识别测试...")
            voice_commands = ["开始录音", "暂停录音", "继续录音", "停止录音"]
            for cmd in voice_commands:
                logger.info(f"🗣️ 测试命令: '{cmd}'")
                is_command = self._process_voice_commands(cmd)
                logger.info(f"{'✅' if is_command else '❌'} 命令识别: {cmd} -> {'成功' if is_command else '失败'}")
 
        except Exception as e:
            error_msg = f"综合测试异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            test_results["errors"].append(error_msg)
 
        finally:
            test_duration = time.time() - start_time
            test_results["test_duration"] = round(test_duration, 2)
 
            if test_results["successful_recognitions"] > 0:
                logger.info("🎉 语音识别功能正常")
            elif test_results["audio_input_working"]:
                logger.info("✅ 音频输入正常")
            else:
                logger.error("❌ 语音识别功能异常")
 
        return test_results
# --------------------------------------------------------------
# 7️⃣ Minimal Keyboard Listener Thread / 极简键盘监听线程
# --------------------------------------------------------------
def start_keyboard_listener(capture: AudioCapture, test_mode: bool = False):
    """
    Minimal control:
        Space key – Start confirmation/pause/resume
        ESC key – Stop and exit program
        't' key - Toggle TTS on/off
    """
    if not PYNPUT_AVAILABLE:
        print("⚠️ 警告: 无法启动键盘监听器，pynput 模块未安装")
        return None
 
    def on_press(key):
        try:
            # 在函数开始添加调试输出
            #if test_mode:
                #print(f"[调试] 键盘事件触发: {key}")            
            
            # 更新全局按键状态（按下但未释放）
            if key == keyboard.Key.space:
                # 防止重复触发
                if not _key_pressed.get('space', False):
                    _key_pressed['space'] = True
                    
                    # 立即处理按键
                    if capture and capture.state != "stopped":
                        if test_mode:
                            print("空格键")                        
                        if capture.state == "paused":
                            capture.resume()
                        elif capture.state == "recording":
                            capture.pause()      
                    
            elif key == keyboard.KeyCode.from_char('t'):
                if not _key_pressed['t']:  # 避免重复触发
                    _key_pressed['t'] = True
                    if test_mode:
                        print("T键")
                    capture.toggle_tts()
            
            elif key == keyboard.Key.esc:
                if not _key_pressed['esc']:  # 避免重复触发
                    _key_pressed['esc'] = True
                    if test_mode:
                        print("ESC键")
                    capture.stop()
                    return False
        except AttributeError:
            # 处理特殊键
            pass
        except Exception as exc:
            logger.warning(f"键盘回调异常: {exc}")
    
    def on_release(key):
        try:
            # 清除全局按键状态（释放后）
            if key == keyboard.Key.space:
                _key_pressed['space'] = False
            elif key == keyboard.KeyCode.from_char('t'):
                _key_pressed['t'] = False
            elif key == keyboard.Key.esc:
                _key_pressed['esc'] = False
        except Exception as exc:
            logger.warning(f"键盘释放回调异常: {exc}")
 
    # 修复：确保键盘监听器在独立线程中运行
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True  # 设置为守护线程
    listener.start()
    
    return listener
# --------------------------------------------------------------
# 8️⃣ Safe input function
# --------------------------------------------------------------
def safe_input(prompt: str = "") -> str:
    """Safe input function that handles EOFError gracefully"""
    try:
        return input(prompt).strip()
    except EOFError:
        print(f"\n⚠️  检测到非交互式环境，跳过输入: {prompt}")
        return ""
    except KeyboardInterrupt:
        print(f"\n👋 用户中断操作")
        return "0"
# --------------------------------------------------------------
# 9️⃣ Main entry & interactive menu
# --------------------------------------------------------------
if __name__ == "__main__":
    try:
        from excel_exporter import ExcelExporter
        from typing import Optional
        exporter: Optional[ExcelExporter] = ExcelExporter()
    except ImportError:
        print("⚠️  ExcelExporter 未找到，将以无导出模式运行")
        exporter = None
 
    # 创建 AudioCapture 实例
    cap = AudioCapture(excel_exporter=exporter)
    cap.test_mode = True  # 设置为测试模式
    
    # 启动键盘监听器
    listener = start_keyboard_listener(cap, test_mode=True)
 
    def number_callback(numbers: list):
        # print(f"📋 回调接收到数值: {numbers}")
        pass
    
    cap.set_callback(number_callback)
    
    print("🎙️ 语音识别测试程序")
    print("1.实时语音识别 2.TTS检查 3.键盘检查 4.综合诊断 0.退出")
 
    def mode_realtime_voice():
        cap.load_model()
        print("\n🎙️ 实时语音识别测试")
        print("请说'开始录音'或按空格键启动，说数字如'二十五点五'")
        
        # 重置状态
        cap.state = "paused"
        cap._start_event.clear()
        cap._pause_event.set()
 
        try:
            result = cap.listen_realtime_vosk()
            print(f"\n识别结果: '{result.get('final', '')}'")
            print(f"提取数值: {result.get('buffered_values', [])}")
            print(f"会话数据: {result.get('session_data', [])}")
 
        except KeyboardInterrupt:
            print("\n用户中断测试")
            cap.stop()     
 
    def mode_tts_check():
        print(f"\n🔊 TTS状态: {'开启' if cap.get_tts_status() == 'on' else '关闭'}")
        while True:
            print("1.测试播报 2.自定义文本 3.切换开关 4.返回")
            choice = safe_input("请选择: ")
            if choice == "1":
                cap.tts.speak("测量值: 25.5, 100.2, 50.75")
                print("✅ 播报完成")
            elif choice == "2":
                text = safe_input("输入文本: ")
                if text.strip():
                    cap.tts.speak(text)
                    print("✅ 播报完成")
            elif choice == "3":
                cap.toggle_tts()
                print(f"TTS: {'开' if cap.get_tts_status() == 'on' else '关'}")
            elif choice == "4":
                break
 
    def mode_keyboard_check():        
        print("\n⌨️ 键盘监听测试")
        print("操作说明: 空格键-开始/暂停/恢复 | ESC键-停止 | 't'键-TTS切换")
        print(f"当前状态: {cap.state}")
        
        if listener:
            print("✅ 键盘监听器已启动，按ESC键结束测试")
            try:
                import time
                while True:
                    # 使用配置中的short睡眠值
                    time.sleep(config.get("recognition.sleep_times.production", 0.05))
                    if cap.state == "stopped":
                        break
            except KeyboardInterrupt:
                pass
            listener.stop()
            print("✅ 键盘监听器已停止")
        else:
            print("❌ 键盘监听器启动失败")
        return listener
 
    def mode_voice_diagnostic():
        print("\n🔬 语音识别综合诊断")
        print("请对着麦克风说几个数字如: 25.5 或 三十点二")
        
        try:
            results = cap.test_voice_recognition_pipeline()
            print(f"\n📊 诊断结果:")
            print(f"🎤 音频输入: {'✅ 正常' if results['audio_input_working'] else '❌ 异常'}")
            print(f"✅ 成功识别: {results['successful_recognitions']}")
            if results['final_results']:
                print("📝 识别到的文本:")
                for text in results['final_results']:
                    print(f"   '{text}'")
        except KeyboardInterrupt:
            print("\n👋 用户中断诊断")
        except Exception as e:
            print(f"\n❌ 诊断出错: {e}")
        print("诊断结束")
 
    global_listener = None
    
    while True:
        print(f"\nTTS:{'开' if cap.get_tts_status() == 'on' else '关'} | 状态:{cap.state} 1.语音识别 2.TTS 3.键盘 4.诊断 0.退出")
        choice = safe_input("选择: ")
        if choice == "1":
            mode_realtime_voice()
        elif choice == "2":
            mode_tts_check()
        elif choice == "3":
            global_listener = mode_keyboard_check()
        elif choice == "4":
            mode_voice_diagnostic()
        elif choice == "0":
            cap.stop()
            if global_listener:
                global_listener.stop()
            break