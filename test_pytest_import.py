import os
import sys
print('当前工作目录:', os.getcwd())
print('Python路径:', sys.path)
try:
    from audio_capture_v import AudioCapture
    print('AudioCapture导入成功')
except ImportError as e:
    print('AudioCapture导入失败:', e)
try:
    from TTSengine import TTS
    print('TTS导入成功')
except ImportError as e:
    print('TTS导入失败:', e)