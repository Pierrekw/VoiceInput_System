# -*- coding: utf-8 -*-
# Audio Capture Module - 音频捕获模块
# Supports real-time voice recognition with pause/resume functionality
# 支持实时语音识别，具备暂停/恢复功能

import sys, os, json, threading, logging, re, gc
from collections import deque
import pyaudio
import cn2an
from vosk import Model, KaldiRecognizer
import vosk
from contextlib import contextmanager

# --------------------------------------------------------------
# 1️⃣ Audio Stream Context Manager / 音频流上下文管理器
# Ensures resources are properly released / 确保资源必定释放
# --------------------------------------------------------------
@contextmanager
def audio_stream():
    """Open PyAudio input stream with automatic cleanup / 打开 PyAudio 输入流，使用完毕后自动关闭、终止。"""
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000,
    )

    try:
        yield stream
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


# --------------------------------------------------------------
# 2️⃣ Keyboard Listener / 键盘监听器
# Import only when needed to avoid errors in unsupported environments
# 仅在需要时导入，避免在不支持的环境报错
# --------------------------------------------------------------
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError as e:
    print("⚠️ 警告: pynput 模块未安装，键盘快捷键将不可用")
    print("请执行: uv pip install pynput 或 pip install pynput 安装该模块")
    PYNPUT_AVAILABLE = False
    keyboard = None


# --------------------------------------------------------------
# 3️⃣ Basic Configuration / 基础配置
# Set up encoding and logging / 设置编码和日志
# --------------------------------------------------------------
sys.stdout.reconfigure(encoding="utf-8")
vosk.SetLogLevel(-1)  # Disable Vosk logs / 关闭 Vosk 日志

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("voice_input.log"), logging.StreamHandler()],
)

# --------------------------------------------------------------
# 4️⃣ Voice Correction Dictionary / 语音纠错词典
# Load voice error correction mappings from external file
# 从外部文件加载语音纠错映射
# --------------------------------------------------------------
def load_voice_correction_dict(file_path="voice_correction_dict.txt"):
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
        print(f"✅ 成功加载 {len(correction_dict)} 个语音纠错规则")
    except FileNotFoundError:
        print(f"⚠️ 未找到词典文件 {file_path}，将使用空词典")
        correction_dict = {}
    except Exception as e:
        print(f"❌ 加载词典文件出错: {e}，将使用空词典")
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
_NUM_PATTERN = re.compile(r"[零一二三四五六七八九十百千万点两\d\.]+")  # Chinese numbers + digits pattern / 中文数字+阿拉伯数字模式


def extract_measurements(text):
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
        excel_exporter=None,  # ← 这里注入 ExcelExporter（可为 None）
        model_path="model/cn",  # ← 模型路径可配置：
                               # model/cn - 中文数字识别标准模型
                               # model/cns - 中文数字识别小模型，加载快精度低
                               # model/us - 英文识别模型
                               # model/uss - 英文识别小模型
    ):
        self.timeout_seconds = timeout_seconds
        self.model_path = model_path        # 存储模型路径

        # ---------- 统一状态管理 ----------
        self.state = "idle"                # idle / recording / paused / stopped
        self._pause_event = threading.Event()
        self._pause_event.set()            # 初始为"未暂停"

        # ---------- 启动确认相关 ----------
        self._start_event = threading.Event()  # 启动确认事件
        self._start_event.clear()          # 初始为未确认

        self.callback_function = None
        self.buffered_values = deque(maxlen=10000)  # 最近 10k 条记录

        # ---------- Excel 导出器 ----------
        self._exporter = excel_exporter   # 可能为 None，保持解耦

    # ----------------------------------------------------------
    # 6.1 回调 & 过滤
    # ----------------------------------------------------------
    def set_callback(self, callback):
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
                print("🎤 语音命令：启动")
                self.confirm_start_by_voice()
                return True

        # 暂停命令
        elif any(word in text_lower for word in ["暂停录音", "暂停", "pause"]):
            if self.state == "recording":
                print("🎤 语音命令：暂停")
                self.pause()
                return True

        # 恢复命令
        elif any(word in text_lower for word in ["继续录音", "继续", "恢复", "resume"]):
            if self.state == "paused":
                print("🎤 语音命令：恢复")
                self.resume()
                return True

        # 停止命令
        elif any(word in text_lower for word in ["停止录音", "停止", "结束", "stop", "exit"]):
            print("🎤 语音命令：停止")
            self.stop()
            return True

        return False  # 不是语音命令，需要继续处理

    def filtered_callback(self, text: str):
        """对识别文本进行过滤、提取数值并回调。"""
        if not isinstance(text, str):
            return
        nums = extract_measurements(text)
        if nums:
            self.buffered_values.extend(nums)
            if self.callback_function:
                self.callback_function(nums)
            print(f"🗣️ 语音文本: {text}")
            print(f"🔢 测量值: {nums}")

    # ----------------------------------------------------------
    # 6.2 启动确认接口（统一状态管理）
    # ----------------------------------------------------------
    def confirm_start_by_space(self):
        """通过空格键确认启动"""
        if self.state == "idle":
            self._start_event.set()
            print("✅ 空格键确认启动")

    def confirm_start_by_voice(self):
        """通过语音命令确认启动"""
        if self.state == "idle":
            self._start_event.set()
            print("✅ 语音命令确认启动")

    def wait_for_start_confirmation(self, timeout=60):
        """等待启动确认（空格键或语音命令）"""
        print("🎤 等待启动确认...")
        print("   按空格键 或 说'开始录音'/'启动'/'开始' 来启动系统")

        # 等待启动确认
        if self._start_event.wait(timeout=timeout):
            self.state = "recording"
            print("🚀 系统已启动！")
            return True
        else:
            self.state = "stopped"
            print("⏰ 启动确认超时")
            return False

    # ----------------------------------------------------------
    # 6.3 控制接口（暂停/恢复/停止）
    # ----------------------------------------------------------
    def pause(self):
        """
        Pause real-time recognition and write buffer to Excel (if exporter is injected)
        暂停实时识别并把缓存写入 Excel（如果已注入 exporter）
        """
        if self.state != "recording":
            return
        self.state = "paused"
        self._pause_event.clear()
        print("⏸️ 已暂停识别")
        self._save_buffer_to_excel()

    def resume(self):
        """恢复实时识别。"""
        if self.state != "paused":
            return
        self.state = "recording"
        self._pause_event.set()
        print("▶️ 已恢复识别")

    def stop(self):
        """停止实时识别并写入缓存。"""
        if self.state == "stopped":
            return
        self.state = "stopped"
        self._pause_event.set()   # 防止在 pause 状态下卡死
        print("🛑 已停止识别")
        self._save_buffer_to_excel()

    @property
    def is_running(self):
        """外部用于判断当前是"运行中"还是"已暂停"。"""
        return self.state == "recording"

    # ----------------------------------------------------------
    # 6.3 写入 Excel（内部私有）
    # ----------------------------------------------------------
    def _save_buffer_to_excel(self):
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
            
            print(f"📝 正在写入 {len(values)} 条数据到 Excel...")
            # exporter 负责生成编号、时间戳等元信息
            result = self._exporter.append(values)
            if result:
                print(f"✅ Excel 写入成功: {len(values)} 条数据")
            else:
                print(f"⚠️ Excel 写入返回失败，将重试")
                return  # 不清空缓存，以便重试
        except Exception as e:
            print(f"❌ 写入 Excel 失败: {e}")
            print(f"📊 失败数据: {values}")
            # 若写入失败，保留缓存，后续仍有机会再次写入
            return

        # 写入成功后清空缓存
        self.buffered_values.clear()

    # ----------------------------------------------------------
    # 6.4 实时 Vosk 监听（核心实现）
    # ----------------------------------------------------------
    def listen_realtime_vosk(self):
        """
        Start real-time voice recognition, return final text and cached values list
        开启实时语音识别，返回最终文本与缓存的数值列表
        """
        # 等待启动确认（使用统一状态系统）
        if not self.wait_for_start_confirmation():
            return {"final": "", "buffered_values": []}

        self.state = "recording"
        self._pause_event.set()

        # ① 加载模型（使用完毕后手动置空，帮助内存释放）
        print("📦 正在加载模型...")
        try:
            model = Model(self.model_path)     # 使用可配置的模型路径
            print("✅ 模型加载完成！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print(f"💡 请检查：")
            print(f"   1. 模型路径是否正确: {self.model_path}")
            print(f"   2. 模型文件是否存在且完整")
            print(f"   3. 模型文件是否适用于当前VOSK版本")
            logging.error(f"模型加载失败: {e}")
            return {"final": "", "buffered_values": []}

        recognizer = KaldiRecognizer(model, 16000)
        recognizer.SetWords(False)

        print("✅ 系统已准备就绪！按空格键 或 说'开始录音'启动系统")

        try:
            with audio_stream() as stream:
                while self.state != "stopped":
                    # ---- 暂停控制 ----
                    self._pause_event.wait()          # 为 True 时立即返回，False 时阻塞

                    data = stream.read(8000, exception_on_overflow=False)

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = (result.get("text") or "").replace(" ", "")
                        if text:
                            # 先处理语音控制命令，避免与普通文本混合处理
                            if not self._process_voice_commands(text):
                                # 如果不是语音命令，再进行数值提取和回调
                                self.filtered_callback(text)
                    else:
                        partial = json.loads(recognizer.PartialResult()).get("partial") or ""
                        if partial:
                            print(f"🗣️ 部分结果: {partial}", end="\r")

                # 识别结束后获取最终结果
                final_text = json.loads(recognizer.FinalResult()).get("text", "")
                return {
                    "final": final_text,
                    "buffered_values": list(self.buffered_values),
                }

        except Exception as e:
            logging.exception("实时识别异常")
            return {"final": "", "buffered_values": []}
        finally:
            # 释放模型对象，帮助内存释放（尤其在长时间运行的服务中）
            model = None
            recognizer = None
            gc.collect()

    # ----------------------------------------------------------
    # 6.5 测试入口（可直接运行）
    # ----------------------------------------------------------
    def test_realtime_vosk(self):
        """简易测试入口，打印回调的数值。"""
        self.set_callback(lambda nums: print(f"👂 回调数值: {nums}"))
        try:
            result = self.listen_realtime_vosk()
            print("\n✅ 实时测试完成，最终文本：", result["final"])
        except Exception as e:
            print("❌ 测试异常:", e)


# --------------------------------------------------------------
# 7️⃣ Minimal Keyboard Listener Thread / 极简键盘监听线程
# Only space/ESC keys supported / 仅支持 space/ESC 键
# --------------------------------------------------------------
def start_keyboard_listener(capture: AudioCapture):
    """
    Minimal control:
        Space key – Start confirmation/pause/resume (one-key cycle control)
        ESC key – Stop and exit program
    极简控制：
        空格键 – 启动确认/暂停/恢复（一键循环控制）
        ESC键 – 停止并退出程序
    """
    if not PYNPUT_AVAILABLE:
        print("⚠️ 警告: 无法启动键盘监听器，pynput 模块未安装")
        return None

    def on_press(key):
        try:
            if key == keyboard.Key.space:        # 空格键 - 启动/暂停/恢复
                if capture.state == "idle":
                    print("\n🚀 按下空格键 → 启动确认")
                    capture.confirm_start_by_space()
                elif capture.state == "recording":
                    print("\n⏸️ 按下空格键 → 暂停")
                    capture.pause()
                elif capture.state == "paused":
                    print("\n▶️ 按下空格键 → 恢复")
                    capture.resume()
            elif key == keyboard.Key.esc:        # ESC键 - 停止
                print("\n🛑 按下ESC键 → 停止并退出")
                capture.stop()
                return False  # 停止监听器
        except Exception as exc:
            logging.warning(f"键盘回调异常: {exc}")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener


# --------------------------------------------------------------
# 8️⃣ 主入口 & 简易交互菜单
# --------------------------------------------------------------
if __name__ == "__main__":
    # 这里演示如何在独立运行时自行创建 ExcelExporter
    from excel_exporter import ExcelExporter

    exporter = ExcelExporter()
    cap = AudioCapture(excel_exporter=exporter)
    start_keyboard_listener(cap)

    # 简化的交互式菜单（可自行扩展）
    while True:
        print("\n=== AudioCapture 简易菜单 ===")
        print("1. 手动启动实时识别")
        print("2. 暂停")
        print("3. 恢复")
        print("4. 停止并退出")
        choice = input("请选择 (1-4): ").strip()
        if choice == "1":
            threading.Thread(target=cap.test_realtime_vosk, daemon=True).start()
        elif choice == "2":
            cap.pause()
        elif choice == "3":
            cap.resume()
        elif choice == "4":
            cap.stop()
            break
        else:
            print("无效选项")
