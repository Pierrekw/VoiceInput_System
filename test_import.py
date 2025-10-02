import sys
print('当前Python路径:', sys.path)
try:
    from TTSengine import TTS
    print('导入成功')
except ImportError as e:
    print('导入失败:', e)