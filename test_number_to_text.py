from audio_capture_v import extract_measurements, correct_voice_errors

print("🔍 测试数字被误识别为文本的情况：")

# 测试各种可能的情况
test_cases = [
    ("55", "数字'55'应该被正确识别"),
    ("50", "数字'50'应该被正确识别"),
    ("我是我", "文本'我是我'的数值提取情况"),
    ("我是", "文本'我是'的数值提取情况")
]

print("\n📊 数值提取测试结果：")
for text, description in test_cases:
    result = extract_measurements(text)
    print(f"- '{text}' → {result} ({description})")

print("\n🔄 语音纠错规则应用测试：")
for text, description in test_cases:
    result = correct_voice_errors(text)
    print(f"- '{text}' → '{result}'")

print("\n✅ 测试完成")