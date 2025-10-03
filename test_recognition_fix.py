from audio_capture_v import extract_measurements, load_voice_correction_dict

# 验证语音纠错词典加载情况
dictionary = load_voice_correction_dict()
print(f"\n✅ 已加载 {len(dictionary)} 个语音纠错规则")
print("最近添加的规则示例:")
new_rules = list(dictionary.items())[-5:]
for wrong, correct in new_rules:
    print(f"  '{wrong}' → '{correct}'")

# 测试数值提取改进
print("\n🔍 测试数值提取改进:")
test_cases = [
    ("我垫巴四", "应该识别为点八四"),
    ("垫巴四", "应该识别为点八四"),
    ("点八四", "应该识别为0.84"),
    ("八点四", "应该识别为8.4"),
    ("我八点四", "应该识别为8.4"),
    ("我五", "应该移除前缀'我'并识别为5"),
    ("垫巴士", "应该识别为点八四")
]

for text, description in test_cases:
    result = extract_measurements(text)
    print(f"- '{text}' → {result} ({description})")

print("\n✅ 测试完成")