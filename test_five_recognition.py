from audio_capture_v import extract_measurements

print("🔍 测试'五'被识别成'我'的修复情况：")

# 测试各种可能的情况
test_cases = [
    ("五", "正常的'五'应该被识别为5.0"),
    ("我", "误识别为'我'的情况应该被修正为5.0"),
    ("五点五", "带小数点的情况"),
    ("我点五", "前缀误识别的情况")
]

for text, description in test_cases:
    result = extract_measurements(text)
    print(f"- '{text}' → {result} ({description})")

print("\n✅ 测试完成")