#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步测试Vosk语音识别
"""

import sys
import os
import time
import numpy as np
import json
import threading

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_vosk_sync():
    """同步测试Vosk语音识别"""
    print("同步测试Vosk语音识别...")
    print("=" * 50)
    print("请对着麦克风持续说话5-10秒...")

    try:
        import vosk
        import pyaudio

        # 直接使用Vosk进行连续识别
        print("1. 加载Vosk模型...")
        model_path = "model/cn"
        model = vosk.Model(model_path)
        print("   模型加载成功")

        print("2. 创建识别器...")
        recognizer = vosk.KaldiRecognizer(model, 16000)
        print("   识别器创建成功")

        print("3. 开始连续音频采集和识别...")

        # 直接使用PyAudio进行音频采集
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000,
                start=True
            )

            print("   开始采集音频，请说话...")
            recognized_any = False
            total_chunks = 0
            voice_detected = False

            start_time = time.time()
            while time.time() - start_time < 10:  # 10秒测试
                try:
                    # 读取音频数据
                    data = stream.read(8000, exception_on_overflow=False)
                    total_chunks += 1

                    if data:
                        # 计算音量
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        volume = np.max(np.abs(audio_array))

                        # 检查是否有语音
                        if volume > 500:  # 语音阈值
                            if not voice_detected:
                                print(f"   [VOICE] 检测到语音信号 (音量: {volume})")
                                voice_detected = True
                            else:
                                print(f"   继续检测语音 (音量: {volume})")

                        # 将音频数据喂给Vosk识别器
                        result = recognizer.AcceptWaveform(data)

                        if result:
                            # 有最终识别结果
                            final_result = recognizer.Result()
                            result_json = json.loads(final_result)
                            if 'text' in result_json and result_json['text'].strip():
                                print(f"   [RECOGNIZED] '{result_json['text']}'")
                                recognized_any = True
                        else:
                            # 获取部分识别结果（可选）
                            if total_chunks % 10 == 0:  # 每10个块检查一次部分结果
                                partial_result = recognizer.PartialResult()
                                partial_json = json.loads(partial_result)
                                if 'partial' in partial_json and partial_json['partial'].strip() and len(partial_json['partial']) > 1:
                                    print(f"   [PARTIAL] '{partial_json['partial']}'")
                    else:
                        print(f"   无音频数据")

                except Exception as e:
                    print(f"   音频处理错误: {e}")

            print(f"   音频采集完成，总共处理了 {total_chunks} 个音频块")

            # 获取最终结果
            final_result = recognizer.FinalResult()
            if final_result:
                final_json = json.loads(final_result)
                if 'text' in final_json and final_json['text'].strip():
                    print(f"   [FINAL] '{final_json['text']}'")
                    recognized_any = True

            stream.stop_stream()
            stream.close()

        finally:
            p.terminate()

        print(f"\n4. 测试结果:")
        print(f"   处理音频块数: {total_chunks}")
        print(f"   检测到语音信号: {'是' if voice_detected else '否'}")
        print(f"   识别到文字: {'是' if recognized_any else '否'}")

        return recognized_any

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始同步Vosk语音识别测试...")
    print("=" * 50)

    # 测试连续识别
    success = test_vosk_sync()

    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] Vosk语音识别工作正常！")
    else:
        print("[ERROR] Vosk语音识别失败")
        print("可能的原因:")
        print("  1. 麦克风权限问题")
        print("  2. 音频设备问题")
        print("  3. 环境太安静或说话不清晰")
        print("  4. Vosk模型配置问题")

if __name__ == "__main__":
    main()