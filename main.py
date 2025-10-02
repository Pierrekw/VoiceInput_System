# -*- coding: utf-8 -*-
# Voice Input System Main Module / 语音输入系统主模块
# Main entry point with enhanced pause/resume and voice command features
# 主程序入口，具备增强的暂停/恢复和语音命令功能

import logging
import sys
import os
import io
import threading
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter


# ---------- Basic Configuration / 基础配置 ----------
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
os.environ["VOSK_LOG_LEVEL"] = "-1"   # -1 = 完全静默

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Logging format / 日志格式
    handlers=[
        logging.FileHandler('voice_input.log', encoding='utf-8'),
        logging.StreamHandler(stream=sys.stdout)  # 确保使用已配置UTF-8的标准输出
    ]
)

logger = logging.getLogger(__name__)

class VoiceInputSystem:
    """
    Program entry point: Create ExcelExporter → Inject AudioCapture → Register callback → Start recognition
    All measurement value caching and writing is handled by AudioCapture, the system itself only controls
    the start/stop process flow
    程序入口：创建 ExcelExporter → 注入 AudioCapture → 注册回调 → 启动识别。
    所有测量值的缓存与写入均交由 AudioCapture 完成，系统本身只负责
    启动/停止的流程控制。
    """

    def __init__(self, timeout_seconds=300):
        self.excel_exporter = ExcelExporter()                     # 统一的 Excel 实例
        self.audio_capture = AudioCapture(
            timeout_seconds=timeout_seconds,
            excel_exporter=self.excel_exporter,                  # 注入
        )
        
        # 在Main函数运行时预加载模型
        print("📦 正在预加载语音识别模型...")
        if not self.audio_capture.load_model():
            print("❌ 模型加载失败，系统可能无法正常工作")
        else:
            print("✅ 模型加载成功")

    # ------------------------------------------------------------------
    # 1️⃣ 回调：收到数值时直接打印（不再自行缓存）
    # ------------------------------------------------------------------
    def on_data_detected(self, values)  -> None:
        """
        Callback function: print values when detected (no longer maintains self.buffered_values)
        回调函数：收到数值时直接打印（不再自行缓存）
        
        注意：当前实现为空（pass），原有的打印逻辑已被注释掉，
        以避免与AudioCapture类中输出的测量值信息重复。
        如需恢复原有功能，请取消下面的注释。
        
        这里不再维护 self.buffered_values，交给 AudioCapture 处理
        """
        # 以下代码已被注释掉，避免重复输出测量值
        # if values:
        #     clean = [str(v) for v in values if isinstance(v, (int, float))]
        #     print(f"📦 实时测量值: {' '.join(clean)}")
        pass
    # ------------------------------------------------------------------
    # 2️⃣ Start Recognition / 启动识别
    # Keyboard controls available / 键盘控制可用（空格/ESC）
    # ------------------------------------------------------------------
    def start_realtime_vosk(self) -> None:
        """
        Start real-time voice recognition system
        启动实时语音识别系统
        """
        print("🎤 系统启动中...")
        self.audio_capture.set_callback(self.on_data_detected)

        # 启动键盘监听器 / Start keyboard listener
        keyboard_listener = start_keyboard_listener(self.audio_capture)

        # 直接调用内部的实时监听（阻塞式），结束后会自动写入 Excel
        result = self.audio_capture.listen_realtime_vosk()

        # 打印Excel数据存储状态和最终输入Excel的数字信息
        buffered_values = result.get('buffered_values', [])
        if buffered_values:
            print(f"\n🛑 监听结束，共捕获 {len(buffered_values)} 个数值")
            print(f"📊 输入Excel的数字信息：{buffered_values}")
            # 检查Excel数据是否成功存储（通过检查原缓存是否已清空）
            if len(self.audio_capture.buffered_values) == 0:
                print("✅ Excel数据存储成功")
            else:
                print("⚠️ Excel数据存储可能未成功，缓存尚未清空")
        else:
            print("\n🛑 监听结束，未捕获到数值")
            
        # 停止键盘监听器（如果存在）
        if keyboard_listener:
            keyboard_listener.stop()
            keyboard_listener.join()  # ✅ 确保线程结束

    # ------------------------------------------------------------------
    # 3️⃣ 停止（若外部需要手动调用）
    # ------------------------------------------------------------------
    def stop(self) -> None:
        """
        Stop the system (if manual call is needed externally)
        停止系统（若外部需要手动调用）
        """
        self.audio_capture.stop()
        logging.info("=== 系统已停止 ===")


if __name__ == "__main__":
    system = VoiceInputSystem(timeout_seconds=0)  # 0表示关闭超时功能
    system.start_realtime_vosk()
    system.audio_capture.unload_model()  # 释放模型内存
    sys.exit(0)
