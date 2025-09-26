import logging
from audio_capture_v import AudioCapture, extract_measurements
from excel_exporter import ExcelExporter
import sys
import os
import re
sys.stdout.reconfigure(encoding='utf-8')

os.environ["VOSK_LOG_LEVEL"] = "-1"   # -1 = 完全静默

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('voice_input.log'), logging.StreamHandler()]
)

class VoiceInputSystem:
    def __init__(self, timeout_seconds=30):
        self.audio_capture = AudioCapture(timeout_seconds=timeout_seconds)
        self.excel_exporter = ExcelExporter()
        self.timeout_seconds = timeout_seconds
        self.is_listening = False
        self.buffered_values = []  # 用于缓存测量值

    def on_data_detected(self, values):
        if values:
            #clean_values = [f"{v:.2f}" for v in values if isinstance(v, (int, float))]    #2f，只有两位小数，用于显示参考。
            clean_values = [str(v) for v in values if isinstance(v, (int, float))]
            #print(f"🧪 原始 values: {values} ({[type(v) for v in values]})")
            #print(f"🔢 实时测量值: {' '.join(clean_values)}")
            self.buffered_values.extend(values)

    def start_realtime_vosk(self):
        self.is_listening = True
        self.audio_capture.set_callback(self.on_data_detected)
        print("🎤 系统启动中...")

        try:
            # ✅ 正确调用并赋值
            result = self.audio_capture.listen_realtime_vosk()

            # ✅ 安全判断 result 是否为 None
            if result:
                final_text = result.get('final', '')
                buffered_values = result.get('buffered_values', [])
            else:
                final_text = ''
                buffered_values = []
            
            print("\n🛑 监听结束")
            #print("\n🛑 监听结束，最终文本：", final_text)

            # 写入缓存的测量值
            if self.buffered_values:
                print(f"📦 缓存测量值: {self.buffered_values}")
                existing_ids = self.excel_exporter.get_existing_ids()
                next_id = max(existing_ids) + 1 if existing_ids else 1
                data_pairs = [(next_id + i, val) for i, val in enumerate(self.buffered_values)]
                print(f"📋 数据对: {data_pairs}")
                if self.excel_exporter.append_to_excel(data_pairs):
                    logging.info(f"数据保存成功: {data_pairs}")  # ✅ 移除 emoji，避免编码错误
                    print("✅ 已保存到 Excel")
                else:
                    logging.error("数据保存失败")
                    print("❌ 保存失败，请查看日志")
            else:
                print("⚠️ 没有缓存测量值可写入")

        except KeyboardInterrupt:
            print("\n🛑 用户中断")
            self.stop()

        self.stop()

    def stop(self):
        self.is_listening = False
        logging.info("=== 系统停止 ===")

if __name__ == "__main__":
    system = VoiceInputSystem(timeout_seconds=30)
    system.start_realtime_vosk()
    sys.exit(0)  # 或 exit(0)