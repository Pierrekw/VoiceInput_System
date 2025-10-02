#TTTSengine.py
# 集成版 Piper 语音合成
# -------------------------------------------------------------------------
# 模型：
#   zh_CN-huayan-medium.onnx
# -------------------------------------------------------------------------

import os
from typing import Optional
from piper import PiperVoice, SynthesisConfig
import sounddevice as sd
import numpy as np

class TTS:
    """
    静默、高效的离线中文 TTS 引擎（基于官方 piper-tts Python API）
    """
    def __init__(self, model_path: str = "model/tts/zh_CN-huayan-medium.onnx") -> None:
        """
        初始化 TTS 引擎
        :param model_path: .onnx 模型文件路径（无需包含 .json，自动查找）
        """
        self.model_path = model_path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        if not os.access(model_path, os.R_OK):
            raise PermissionError(f"无权限读取模型文件: {model_path}")    
            
        config_path = model_path + ".json"
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"模型配置文件不存在: {config_path}")        
        if not os.access(config_path, os.R_OK):
            raise PermissionError(f"无权限读取模型配置文件: {config_path}")
        
        # 加载模型（只需一次，后续复用）
        self.voice = PiperVoice.load(
            model_path=model_path,
            config_path=config_path
        )
        print(f"[TTS] 模型加载成功: {os.path.basename(model_path)}")

    def speak(self, text: str, play: bool = True, output_wav: Optional[str] = None, 
              volume: float = 1.0, length_scale: float = 1.0, 
              noise_scale: float = 1.0, noise_w_scale: float = 1.0):
        """
        合成并播放/保存语音（完全静默，无黑窗）
        
        :param text: 要合成的文本
        :param play: 是否播放（使用 sounddevice）
        :param output_wav: 保存为 WAV 文件的路径（可选）
        :param volume: 音量级别 (0.0-1.0+)
        :param length_scale: 语速控制 (1.0=正常, <1=更快, >1=更慢)
        :param noise_scale: 音频变化程度
        :param noise_w_scale: 语音变化程度
        """
        if not text or not text.strip():
            return
            
        # 创建合成配置
        syn_config = SynthesisConfig(
            volume=volume,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w_scale,
            normalize_audio=True
        )
            
        # 保存WAV文件（可选，使用官方API）
        if output_wav:
            try:
                import wave
                # 获取当前运行程序目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # 构建WaveOutput文件夹路径
                wave_output_dir = os.path.join(current_dir, "WaveOutput")
                # 确保WaveOutput文件夹存在
                os.makedirs(wave_output_dir, exist_ok=True)
                # 构建完整的保存路径
                full_output_path = os.path.join(wave_output_dir, os.path.basename(output_wav))
                
                with wave.open(full_output_path, "wb") as wav_file:
                    self.voice.synthesize_wav(text, wav_file, syn_config=syn_config)
                print(f"[TTS] 音频已保存: {full_output_path}")
            except Exception as e:
                print(f"[TTS] 保存失败: {e}")
        
        # 播放音频（可选，使用流式API）
        if play:
            audio_data = bytearray()
            sample_rate = None
            
            for chunk in self.voice.synthesize(text, syn_config=syn_config):
                # 获取音频数据
                audio_data.extend(chunk.audio_int16_bytes)
                
                # 获取音频格式信息（只需获取一次）
                if sample_rate is None:
                    sample_rate = chunk.sample_rate
                    self.sample_width = chunk.sample_width
                    self.sample_channels = chunk.sample_channels
            
            # 如果没有获取到音频数据，直接返回
            if not audio_data or sample_rate is None:
                print(f"[TTS] 无法获取有效的音频数据")
                return
            
            try:
                # 将字节数据转换为numpy数组用于播放
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                # 转换为float32格式并归一化
                audio_float = audio_np.astype(np.float32) / 32767.0
                
                sd.play(audio_float, sample_rate, blocking=False)
                sd.wait()  # 阻塞直到播放完成
            except Exception as e:
                print(f"[TTS] 播放失败: {e}")

    def speak_number(self, number):
        self.speak(str(number))

    def speak_info(self, info):
        self.speak(str(info))

    def speak_number_with_info(self, number, info):
        self.speak(f"{info} {number}")

    def close(self):
        """Python API 无需显式关闭"""
        if hasattr(self.voice, 'close'):
            self.voice.close()
       

# ======================
# 测试代码
# ======================
if __name__ == "__main__":
    # 模型在 model/tts 目录下
    model_path = "model/tts/zh_CN-huayan-medium.onnx"
    
    try:
        tts = TTS(model_path)
        tts.speak("你好，欢迎使用集成版 Piper 语音合成！", play=True)
        tts.speak_number_with_info(42, "答案是")
        tts.speak("测试完成。", output_wav="output.wav")
    except Exception as e:
        print(f"错误: {e}")