# test_correction_simple.py - 简化版纠错测试
import sys
import os

# 将上级目录添加到 Python 路径中，以便导入 audio_capture_v
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 重新实现纠错功能，避免导入整个 audio_capture_v 模块
def load_voice_correction_dict(file_path="voice_correction_dict.txt"):
    """
    从外部文件加载语音纠错词典
    文件格式：每行一个映射，格式为 "错误词=正确词"
    """
    correction_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    wrong, correct = line.split('=', 1)
                    correction_dict[wrong.strip()] = correct.strip()
        print(f"✅ 成功加载 {len(correction_dict)} 个语音纠错规则")
    except FileNotFoundError:
        print(f"⚠️ 未找到词典文件 {file_path}，将使用空词典")
        correction_dict = {
            "其实": "七十",
            "一起": "一七",
            "是": "十",
            "我": "五",
            "支": "七",
            "期": "七",
            "而": "二",
            "就": "九",
            "吧": "八",
            "义务": "一五",
            "起舞": "七五",
            "奇葩": "七八",
            "三六": "三十六",
        }
        print(f"ℹ️ 使用内置默认词典，包含 {len(correction_dict)} 个规则")
    except Exception as e:
        print(f"❌ 加载词典文件出错: {e}，将使用空词典")
        correction_dict = {}
    
    return correction_dict

# 加载纠错词典
VOICE_CORRECTION_DICT = load_voice_correction_dict()

def correct_voice_errors(text: str) -> str:
    """把常见误识别的词替换为正确的数字表达。"""
    original_text = text
    for wrong, correct in VOICE_CORRECTION_DICT.items():
        text = text.replace(wrong, correct)
    
    # 显示纠错详情
    if original_text != text:
        print(f"🔧 纠错详情: '{original_text}' -> '{text}'")
    else:
        print(f"ℹ️ 无纠错内容: '{original_text}'")
    
    return text

# 测试用例
test_cases = [
    "其实这是一个测试",
    "我们一起学习",
    "这是我支期而就吧",
    "义务起舞奇葩三六",
    "没有需要纠错的内容",
    "其实我期期期期期"
]

if __name__ == "__main__":
    print("=== 语音纠错测试 (简化版) ===")
    for case in test_cases:
        result = correct_voice_errors(case)
        print(f"输入: {case}")
        print(f"输出: {result}")
        print("-" * 40)