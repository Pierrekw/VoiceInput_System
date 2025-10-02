# -*- coding: utf-8 -*-
# Audio Capture Module - 音频捕获模块
# Supports real-time voice recognition with pause/resume functionality
# 支持实时语音识别，具备暂停/恢复功能

import sys, os, io, json, threading, logging, re, gc, time
from collections import deque
from typing import List, Tuple, Optional, Callable, Deque, Any, Union
import pyaudio
import cn2an
from vosk import Model, KaldiRecognizer
import vosk
from contextlib import contextmanager
from TTSengine import TTS

logger = logging.getLogger(__name__)

# --------------------------------------------------------------
# 1️⃣ Audio Stream Context Manager / 音频流上下文管理器
# Ensures resources are properly released / 确保资源必定释放
# --------------------------------------------------------------
@contextmanager
def audio_stream():
    """Open PyAudio input stream with automatic cleanup / 打开 PyAudio 输入流，使用完毕后自动关闭、终止。"""
    p = pyaudio.PyAudio()

    try:
        # Get default input device info for debugging
        default_device = p.get_default_input_device_info()
        logger.info(f"🎤 使用音频设备: {default_device['name']} (索引: {default_device['index']})")

        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000,
            start=True,  # Explicitly start the stream
        )

        logger.info(f"🎧 音频流创建成功 - 活动状态: {stream.is_active()}")

    except Exception as e:
        logger.error(f"❌ 音频流创建失败: {e}")
        p.terminate()
        raise

    try:
        yield stream
    
    finally:
        status_messages = []
        if stream.is_active():
            stream.stop_stream()
            status_messages.append("音频流已停止")
        stream.close()
        status_messages.append("音频流已关闭")
        p.terminate()
        status_messages.append("PyAudio 已终止")
        logger.info("🔧 资源清理完成: " + ", ".join(status_messages))


# --------------------------------------------------------------
# 2️⃣ Keyboard Listener / 键盘监听器
# Import only when needed to avoid errors in unsupported environments
# 仅在需要时导入，避免在不支持的环境报错
# --------------------------------------------------------------
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError as e:
    # 此处保留 print，因为日志系统可能尚未配置
    print("⚠️ 警告: pynput 模块未安装，键盘快捷键将不可用")
    print("请执行: uv pip install pynput 或 pip install pynput 安装该模块")
    PYNPUT_AVAILABLE = False
    keyboard = None  # type: ignore[assignment]
   


# --------------------------------------------------------------
# 3️⃣ Basic Configuration / 基础配置
# Set up encoding and logging / 设置编码和日志
# --------------------------------------------------------------
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
vosk.SetLogLevel(-1)  # Disable Vosk logs / 关闭 Vosk 日志


# --------------------------------------------------------------
# 4️⃣ Voice Correction Dictionary / 语音纠错词典
# Load voice error correction mappings from external file
# 从外部文件加载语音纠错映射
# --------------------------------------------------------------
def load_voice_correction_dict(file_path="voice_correction_dict.txt") -> dict[str, str]:
    """
    Load voice error correction dictionary from external file
    File format: one mapping per line, format "wrong_word=correct_word"
    从外部文件加载语音纠错词典
    文件格式：每行一个映射，格式为 "错误词=正确词"
    """
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

# 从外部文件加载语音纠错词典
VOICE_CORRECTION_DICT = load_voice_correction_dict()

def correct_voice_errors(text: str) -> str:
    """Replace commonly misrecognized words with correct number expressions / 把常见误识别的词替换为正确的数字表达。"""
    for wrong, correct in VOICE_CORRECTION_DICT.items():
        text = text.replace(wrong, correct)
    return text

# --------------------------------------------------------------
# 5️⃣ Number Extraction / 数值提取
# Using pre-compiled regex and deque buffer / 使用预编译正则表达式和双端队列缓冲区
# --------------------------------------------------------------
_NUM_PATTERN = re.compile(r"[零一二三四五六七八九十百千万点两\d]+(?:\.[零一二三四五六七八九十百千万两\d]+)*")  # 优化后的中文数字+阿拉伯数字模式，确保能正确识别小数


def extract_measurements(text: Any) -> List[float]:
    """
    Extract all possible numbers (Chinese or Arabic) from text and return as float list
    从文本中提取所有可能的数字（中文或阿拉伯），返回 float 列表。
    """
    if not isinstance(text, (str, int, float)):
        return []  # Return empty list for invalid input / 无效输入返回空列表

    try:
        txt = str(text).strip()  # Convert to string and strip whitespace / 转换为字符串并去除空白
        txt = correct_voice_errors(txt)  # Apply voice error corrections / 应用语音纠错

        candidates = _NUM_PATTERN.findall(txt)  # Find all number patterns / 查找所有数字模式
        nums = []
        for cand in candidates:
            try:
                num = cn2an.cn2an(cand, "smart")  # Convert Chinese numbers to Arabic / 中文数字转阿拉伯数字
                nums.append(float(num))
            except Exception:
                continue  # Skip conversion errors / 跳过转换错误
        return nums
    except Exception:
        return []  # Return empty list on any error / 任何错误都返回空列表


# --------------------------------------------------------------
# 6️⃣ Main Class: AudioCapture / 主类：AudioCapture
# Real-time voice recognition with pause/resume functionality
# 基于 Vosk 的实时语音识别，支持暂停/恢复功能
# --------------------------------------------------------------
class AudioCapture:
    """
    Real-time voice recognition based on Vosk with pause/resume functionality
    Supports keyboard shortcuts (space/ESC) and voice commands
    Injects ExcelExporter through constructor to achieve "pause/stop → auto-write to Excel"
    基于 Vosk 的实时语音识别，支持键盘快捷键（空格/ESC）和语音命令
    通过构造函数注入 ExcelExporter，实现"暂停/停止 → 自动写入 Excel"
    """

    def __init__(
        self,
        timeout_seconds=30,
        excel_exporter: Optional['ExcelExporter'] = None,  # ← 这里注入 ExcelExporter（可为 None）
        model_path: str = "model/cn",  # ← 模型路径可配置：
                               # model/cn - 中文数字识别标准模型
                               # model/cns - 中文数字识别小模型，加载快精度低
                               # model/us - 英文识别模型
                               # model/uss - 英文识别小模型
    ):
        self.tts_state: str = "on" # 当前 TTS 状态, off or on
        self.tts = TTS() # 初始化TTS引擎实例
        self.timeout_seconds: int = timeout_seconds
        self.model_path: str = model_path        # 存储模型路径

        # ---------- 统一状态管理 ----------
        self.state: str = "idle"                # idle / recording / paused / stopped
        self._pause_event: threading.Event = threading.Event()
        self._pause_event.set()            # 初始为"未暂停"
        self._start_event: threading.Event = threading.Event()
        self._start_event.clear()          # 初始为"未开始"



        self.callback_function: Callable[[list[float]], None] | None = None
        self.buffered_values: Deque[float] = deque(maxlen=10000)  # 最近 10k 条记录

        # ---------- Excel 导出器 ----------
        self._exporter: Optional['ExcelExporter'] = excel_exporter   # 可能为 None，保持解耦

        # ---------- 模型相关（预加载）----------
        self._model: Optional['Model'] = None      # 预加载的模型
        self._recognizer: Optional['KaldiRecognizer'] = None  # 预加载的识别器

    # ----------------------------------------------------------
    # 模型预加载方法
    # ----------------------------------------------------------
    def load_model(self) -> bool:
        """
        预加载Vosk模型和识别器，返回是否成功
        """
        if self._model is not None and self._recognizer is not None:
            logger.info("✅ 模型已预加载，无需重复加载")
            return True

        logger.info("📦 正在预加载模型...")
        try:
            from vosk import Model, KaldiRecognizer
            self._model = Model(self.model_path)
            self._recognizer = KaldiRecognizer(self._model, 16000)
            self._recognizer.SetWords(False)
            logger.info(f"✅ 模型预加载完成: {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 模型预加载失败: {e}")
            self._model = None
            self._recognizer = None
            return False

    def unload_model(self) -> None:
        """卸载模型以释放内存"""
        if self._model is not None:
            self._model = None
        if self._recognizer is not None:
            self._recognizer = None
        import gc
        gc.collect()
        logger.info("🧹 模型已卸载")

    # ----------------------------------------------------------
    # 新增TTS控制方法
    def toggle_tts(self) -> None:
        """切换TTS开关状态"""
        self.tts_state = "off" if self.tts_state == "on" else "on"
        logger.info(f"🔊 TTS状态已切换至: {'开启' if self.tts_state == 'on' else '关闭'}")

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
        """
        Process voice control commands, return True if it's a command, otherwise False
        处理语音控制命令，如果是命令返回True，否则返回False
        """
        if not text:
            return False

        text_lower = text.lower()

        # 启动命令
        if any(word in text_lower for word in ["开始录音", "启动", "开始", "start"]):
            if self.state == "idle":
                logger.info("🎤 语音命令：启动")
                logger.info("🚀 启动确认收到！")
                return True

        # 暂停命令
        elif any(word in text_lower for word in ["暂停录音", "暂停", "pause"]):
            if self.state == "recording":
                logger.info("🎤 语音命令：暂停")
                self.pause()
                return True

        # 恢复命令
        elif any(word in text_lower for word in ["继续录音", "继续", "恢复", "resume"]):
            if self.state == "paused":
                logger.info("🎤 语音命令：恢复")
                self.resume()
                return True

        # 停止命令
        elif any(word in text_lower for word in ["停止录音", "停止", "结束", "stop", "exit"]):
            logger.info("🎤 语音命令：停止")
            self.stop()
            return True

        return False  # 不是语音命令，需要继续处理

    def filtered_callback(self, text: str)-> None:
        """对识别文本进行过滤、提取数值并回调。"""
        if not isinstance(text, str):
            return
        nums = extract_measurements(text)
        if nums:
            self.buffered_values.extend(nums)
            if self.callback_function:
                self.callback_function(nums)
            logger.info(f"🗣️ 语音文本: {text}")
            logger.info(f"🔢 测量值: {nums}")
            if self.tts_state == "on":
                numbers_text = "，".join(str(num) for num in nums)  # Chinese comma for natural speech
                self.tts.speak(f"测量值: {numbers_text}")
            #新增tts语音输出测量值

    # ----------------------------------------------------------
    # 6.2 启动确认接口（统一状态管理）
    # ----------------------------------------------------------


    def wait_for_start_confirmation(self)-> bool:
        """等待启动确认（空格键），并提供10秒倒计时准备时间"""
        logger.info("🎤 等待启动确认...")
        logger.info("   按空格键来启动系统")

        # 确保初始状态正确
        if self.state != "idle":
            logger.warning(f"⚠️ 当前状态不是idle，重置状态: {self.state}")
            self.state = "idle"

        # 确认启动（无需等待事件触发）
        logger.info("🚀 启动确认收到！")
        
        # 添加10秒倒计时启动，支持空格键立即开始
        countdown_seconds = 10
        logger.info(f"🚀 系统将在 {countdown_seconds} 秒后开始识别...")
        logger.info("   按空格键可立即开始识别")
        
        # 创建临时键盘监听器用于在倒计时期间检测空格键
        import keyboard
        start_early = False
        
        for i in range(countdown_seconds, 0, -1):
            print(f"⏰ 倒计时: {i}秒 (按空格键立即开始)", end="\r")
            
            # 非阻塞检查是否按下了空格键
            if keyboard.is_pressed('space'):
                start_early = True
                break
                
            # 短暂睡眠以减少CPU使用率，但保持响应速度
            for _ in range(10):
                if keyboard.is_pressed('space'):
                    start_early = True
                    break
                time.sleep(0.1)
            
            if start_early:
                break
                
        if start_early:
            print("✅ 已通过空格键立即开始识别！       ")
            logger.info("✅ 用户通过空格键立即开始识别！")
        else:
            print("⏰ 倒计时结束，开始识别！       ")
            logger.info("✅ 倒计时结束，系统已开始识别！")
            
        # 设置为录音状态
        self.state = "recording"
        logger.info("✅ 系统状态已设置为 recording")
        
        return True

    # ----------------------------------------------------------
    # 6.3 控制接口（暂停/恢复/停止）
    # ----------------------------------------------------------
    def pause(self)-> None:
        """
        Pause real-time recognition and write buffer to Excel (if exporter is injected)
        暂停实时识别并把缓存写入 Excel（如果已注入 exporter）
        """
        if self.state != "recording":
            return
        self.state = "paused"
        self._pause_event.clear()
        logger.info("⏸️ 已暂停识别")
        self._save_buffer_to_excel()

    def resume(self)-> None:
        """恢复实时识别。"""
        if self.state != "paused":
            return
        self.state = "recording"
        self._pause_event.set()
        logger.info("▶️ 已恢复识别")

    def stop(self)-> None:
        """停止实时识别并写入缓存。"""
        if self.state == "stopped":
            return
        self.state = "stopped"
        self._pause_event.set()   # 防止在 pause 状态下卡死
        logger.info("🛑 已停止识别")
        self._save_buffer_to_excel()

    @property
    def is_running(self)-> bool:
        """外部用于判断当前是"运行中"还是"已暂停"。"""
        return self.state == "recording"

    # ----------------------------------------------------------
    # 6.3 写入 Excel（内部私有）
    # ----------------------------------------------------------
    def _save_buffer_to_excel(self) -> None:
        """
        Write buffered_values to Excel and clear the buffer
        把 buffered_values 写入 Excel 并清空缓存
        """
        if not self._exporter:
            # 没有注入 exporter，直接清空缓存防止重复写入
            self.buffered_values.clear()
            return

        if not self.buffered_values:
            return  # 缓存为空，无需写入

        try:
            # 将 deque 转为普通 list 供 exporter 使用
            values = list(self.buffered_values)
            if not values:
                return  # 缓存为空，无需写入
            
            logger.info(f"📝 正在写入 {len(values)} 条数据到 Excel...")
            # exporter 负责生成编号、时间戳等元信息
            result = self._exporter.append(values)
            if result:
                logger.info(f"✅ Excel 写入成功: {len(values)} 条数据")
            else:
                logger.warning(f"⚠️ Excel 写入返回失败，将重试")
                return  # 不清空缓存，以便重试
        except Exception as e:
            logger.error(f"❌ 写入 Excel 失败: {e}")
            logger.error(f"📊 失败数据: {values}")
            # 若写入失败，保留缓存，后续仍有机会再次写入
            return

        # 写入成功后清空缓存
        self.buffered_values.clear()

    # ----------------------------------------------------------
    # 6.4 实时 Vosk 监听（核心实现）
    # ----------------------------------------------------------
    def listen_realtime_vosk(self)-> dict[str, Union[str, List[float], List[str]]]:
        """
        Start real-time voice recognition, return final text and cached values list
        开启实时语音识别，返回最终文本与缓存的数值列表
        """
        import time  # 导入time模块用于超时控制


        logger.info("=" * 60)
        logger.info("🎤 开始实时语音识别流程...")
        logger.info(f"📊 当前状态: {self.state}")
        logger.info(f"🎯 模型路径: {self.model_path}")
        logger.info(f"⏱️  超时时间: {self.timeout_seconds}秒")

        # 检查模型是否已加载
        if self._model is None or self._recognizer is None:
            logger.warning("⚠️ 模型未加载，尝试重新加载...")
            if not self.load_model():
                logger.error("❌ 无法加载模型")
                return {"final": "", "buffered_values": []}
        else:
            logger.info("✅ 模型已加载")

        # 确保状态正确设置
        self.state = "idle"
        self._pause_event.set()
        logger.info("✅ 系统状态已重置为 idle")

        # 等待启动确认（使用统一状态管理，包含10秒倒计时准备）
        if not self.wait_for_start_confirmation():
            logger.warning("⚠️ 启动确认失败或超时")
            return {"final": "", "buffered_values": []}

        try:
            with audio_stream() as stream:
                logger.info("🎤 开始音频流监听...")
                
                audio_frames = 0
                recognition_count = 0
                collected_text = []  # 收集所有识别的文本
                recognition_start_time = time.time()  # 记录识别开始时间
                

                while self.state != "stopped":
                    # ---- 超时检查 ----
                    if time.time() - recognition_start_time > self.timeout_seconds:
                        logger.info(f"⏰ 识别超时（{self.timeout_seconds}秒），自动停止")
                        
                        self.state = "stopped"
                        break

                    # ---- 暂停控制 ----
                    self._pause_event.wait()          # 为 True 时立即返回，False 时阻塞

                    try:
                        data = stream.read(8000, exception_on_overflow=False)
                        audio_frames += 1

                        # 每50帧记录一次音频接收状态
                        if audio_frames % 50 == 0:
                            logger.info(f"🎧 音频流正常 - 帧数: {audio_frames}")

                        if self._recognizer and self._recognizer.AcceptWaveform(data):
                            recognition_count += 1
                            result = json.loads(self._recognizer.Result())
                            text = (result.get("text") or "").replace(" ", "")

                            if text:
                                # 收集识别的文本
                                collected_text.append(text)

                                # 先处理语音控制命令，避免与普通文本混合处理
                                if not self._process_voice_commands(text):
                                    # 如果不是语音命令，再进行数值提取和回调
                                    self.filtered_callback(text)
                        else:
                            if self._recognizer:
                                partial = json.loads(self._recognizer.PartialResult()).get("partial") or ""
                                if partial:
                                    # 部分结果可选记录
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

                # 如果 final_text 为空，使用收集的文本作为备选
                if not final_text and collected_text:
                    final_text = " ".join(collected_text)

                # 明确类型以帮助mypy正确推断
                result_dict: dict[str, Union[str, List[float], List[str]]] = {
                    "final": final_text,
                    "buffered_values": list(self.buffered_values),
                    "collected_text": collected_text,
                }

                return result_dict

        except Exception as e:
            logger.exception("实时识别异常")
            return {"final": "", "buffered_values": []}
        finally:
            # 识别结束时将数据写入Excel
            self._save_buffer_to_excel()
            # 注意：不再清理模型对象，因为模型是预加载的
            logger.info("🧹 识别会话结束，预加载模型仍保留在内存中")

    # ----------------------------------------------------------

    def test_voice_recognition_pipeline(self) -> dict[str, Any]:
        """
        Comprehensive test function to debug voice recognition pipeline
        Uses the existing listen_realtime_vosk() function to avoid code duplication
        综合测试函数，使用现有的 listen_realtime_vosk() 函数避免代码重复
        """

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
                        # 确保maxInputChannels是数字类型后再比较
                        max_channels = device_info['maxInputChannels']
                        if isinstance(max_channels, (int, float)) and max_channels > 0:
                            test_results["audio_device_info"].append({"index": i, "name": device_info['name']})
                    except:
                        continue

                # Test default input device
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

            # Manually trigger start to bypass confirmation wait
            original_state = self.state
            original_pause_event = self._pause_event.is_set()
            original_start_event = self._start_event.is_set()

            # Set state to recording and trigger events to bypass confirmation
            self.state = "recording"
            self._pause_event.set()
            self._start_event.set()

            try:
                # Use the existing listen_realtime_vosk function
                vosk_result = self.listen_realtime_vosk()
                test_results["vosk_result"] = vosk_result

                # Analyze results
                if vosk_result["final"]:
                    test_results["final_results"].append(vosk_result["final"])
                    test_results["successful_recognitions"] += 1
                    logger.info(f"🎯 识别成功: '{vosk_result['final']}'")

                if vosk_result["buffered_values"]:
                    logger.info(f"🔢 提取到的数字: {vosk_result['buffered_values']}")

                # Model loading is successful if we got here
                test_results["model_loading_success"] = True

                logger.info(f"📊 Vosk 测试结果: 最终文本='{vosk_result['final']}', 数字={vosk_result['buffered_values']}")

            except Exception as e:
                error_msg = f"Vosk 测试失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                test_results["errors"].append(error_msg)

            finally:
                # Restore original state
                self.state = original_state
                if not original_pause_event:
                    self._pause_event.clear()
                if not original_start_event:
                    self._start_event.clear()

            # Test 3: Voice Commands (same as before)
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

            # Simple summary
            if test_results["successful_recognitions"] > 0:
                logger.info("🎉 语音识别功能正常")
            elif test_results["audio_input_working"]:
                logger.info("✅ 音频输入正常")
            else:
                logger.error("❌ 语音识别功能异常")

        return test_results

    # ----------------------------------------------------------


# --------------------------------------------------------------
# 7️⃣ Minimal Keyboard Listener Thread / 极简键盘监听线程
# Only space/ESC keys supported / 仅支持 space/ESC 键
# --------------------------------------------------------------
def start_keyboard_listener(capture: AudioCapture):
    """
    Minimal control:
        Space key – Start confirmation/pause/resume (one-key cycle control)
        ESC key – Stop and exit program
        't' key - Toggle TTS on/off
    极简控制：
        空格键 – 启动确认/暂停/恢复（一键循环控制）
        ESC键 – 停止并退出程序
         't'键 - 切换TTS开关
    """
    if not PYNPUT_AVAILABLE:
        # 此处保留 print，因为日志系统可能尚未配置
        print("⚠️ 警告: 无法启动键盘监听器，pynput 模块未安装")
        return None

    def on_press(key):
        try:
            if key == keyboard.Key.space:        # 空格键 - 启动/暂停/恢复
                if capture.state == "idle":
                    logger.info("🚀 启动确认收到！")
                    # 不再需要等待，直接开始
                elif capture.state == "recording":
                    capture.pause()
                elif capture.state == "paused":
                    capture.resume()
            elif key == keyboard.KeyCode.from_char('t'):  # TTS切换按键
                capture.toggle_tts()
            elif key == keyboard.Key.esc:        # ESC键 - 停止
                capture.stop()
                return False  # 停止监听器
        except Exception as exc:
            logger.warning(f"键盘回调异常: {exc}")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener

# --------------------------------------------------------------
# 8️⃣ 安全输入函数 - 处理EOFError
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
        return "0"  # Return exit code instead of sys.exit to allow cleanup

# --------------------------------------------------------------
# 9️⃣ 主入口 & 简易交互菜单
# --------------------------------------------------------------
if __name__ == "__main__":
    # 这里演示如何在独立运行时自行创建 ExcelExporter
    try:
        from excel_exporter import ExcelExporter
        from typing import Optional
        exporter: Optional[ExcelExporter] = ExcelExporter()
    except ImportError:
        print("⚠️  ExcelExporter 未找到，将以无导出模式运行")
        exporter = None

    # 创建 AudioCapture 实例
    cap = AudioCapture(excel_exporter=exporter)
    
    # 启动键盘监听器
    listener = start_keyboard_listener(cap)

    # 定义回调函数，用于接收识别到的数值
    def number_callback(numbers):
        print(f"📋 回调接收到数值: {numbers}")
    
    # 注册回调函数
    cap.set_callback(number_callback)
    
    # 标志位，用于跟踪是否正在运行识别
    recognition_running = False

    # 测试程序主循环 - 4模式手动测试界面
    print("🎙️ 语音识别测试程序")
    print("1.实时语音识别 2.TTS检查 3.键盘检查 4.综合诊断 0.退出")

    def mode_realtime_voice():
        """模式1: 实时语音识别测试"""
        global recognition_running

        cap.load_model()

        print("\n🎙️ 实时语音识别测试")
        print("请说'开始录音'或按空格键启动，说数字如'二十五点五'")

        # 重置状态
        cap.state = "idle"
        cap._start_event.clear()
        cap._pause_event.set()

        try:
            result = cap.listen_realtime_vosk()

            print(f"\n识别结果: '{result.get('final', '')}'")
            print(f"提取数值: {result.get('buffered_values', [])}")

        except KeyboardInterrupt:
            print("\n用户中断测试")
            cap.stop()     


    def mode_tts_check():
        """模式2: TTS检查和测试"""
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
        """模式3: 键盘检查"""
        print("\n⌨️ 键盘监听测试")
        print("操作说明: 空格键-开始/暂停/恢复 | ESC键-停止 | 't'键-TTS切换")

        # 启动键盘监听器
        listener = start_keyboard_listener(cap)

        if listener:
            print("✅ 键盘监听器已启动，按ESC键结束测试")
            try:
                import time
                while True:
                    time.sleep(1)
                    if cap.state == "stopped":
                        break
            except KeyboardInterrupt:
                pass

            listener.stop()
            print("✅ 键盘监听器已停止")
        else:
            print("❌ 键盘监听器启动失败")
        
        return listener  # 返回listener引用以便主循环可以停止它

    def mode_voice_diagnostic():
        """模式4: 语音识别管道综合诊断"""
        print("\n🔬 语音识别综合诊断")
        print("请对着麦克风说几个数字如: 25.5 或 三十点二")

        try:
            # Run the comprehensive test
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

    # 初始化listener变量
    global_listener = None
    
    # 主菜单循环
    while True:
        print(f"\nTTS:{'开' if cap.get_tts_status() == 'on' else '关'} 1.语音识别 2.TTS 3.键盘 4.诊断 0.退出")
        choice = safe_input("选择: ")

        if choice == "1":
            mode_realtime_voice()
        elif choice == "2":
            mode_tts_check()
        elif choice == "3":
            # 保存listener引用以便退出时停止
            global_listener = mode_keyboard_check()
        elif choice == "4":
            mode_voice_diagnostic()
        elif choice == "0":
            cap.stop()
            if global_listener:
                global_listener.stop()
            break