import cn2an

# 测试cn2an库对连续中文数字的转换
text = "一二三四五六七八九十"
print(f"测试文本: '{text}'")

try:
    # 使用smart模式
    num = cn2an.cn2an(text, "smart")
    print(f"smart模式转换结果: {num}")
except Exception as e:
    print(f"smart模式转换失败: {e}")

try:
    # 使用strict模式
    num = cn2an.cn2an(text, "strict")
    print(f"strict模式转换结果: {num}")
except Exception as e:
    print(f"strict模式转换失败: {e}")

try:
    # 尝试按字符逐个转换
    result = ""
    for char in text:
        num = cn2an.cn2an(char, "smart")
        result += str(num)
    print(f"按字符逐个转换结果: {result}")
    if result.isdigit():
        print(f"转换为整数: {int(result)}")
except Exception as e:
    print(f"按字符逐个转换失败: {e}")