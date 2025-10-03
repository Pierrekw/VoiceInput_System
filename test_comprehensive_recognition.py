from audio_capture_v import extract_measurements
import logging

# 设置日志级别为WARNING以简化输出
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("🚀 全面语音识别测试")
print()

# 测试各种场景
test_scenarios = [
    # 基本数字测试
    ("5", "基本数字识别"),
    ("50", "两位数识别"),
    ("55", "相同数字识别"),
    
    # 误识别情况测试
    ("我", "'五'被误识别为'我'"),
    ("我是", "'五十'被误识别为'我是'"),
    ("我是我", "'五五'被误识别为'我是我'"),
    
    # 带前缀的情况
    ("我五", "带有'我'前缀的数字"),
    ("我五十", "带有'我'前缀的两位数"),
    ("你五", "带有'你'前缀的数字"),
    
    # 小数情况
    ("五点五", "小数识别"),
    ("我五点五", "带前缀的小数"),
    ("点八四", "特殊小数格式"),
    ("垫巴四", "语音模糊的小数")
]

# 运行测试
print("🎯 测试结果：")
print("=" * 80)
print(f"{'输入文本':<10} {'识别结果':<10} {'描述'}")
print("=" * 80)

for text, description in test_scenarios:
    result = extract_measurements(text)
    print(f"{text:<10} {str(result):<10} {description}")

print("=" * 80)
print("✅ 所有测试完成")