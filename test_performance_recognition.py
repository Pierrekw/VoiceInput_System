import time
import logging
from audio_capture_v import AudioCapture, extract_measurements, correct_voice_errors
from model_manager import global_model_manager
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试用例
TEST_CASES = [
    # 性能测试用例
    "十八",
    "三十点五",
    "三是七点五",
    "二点八四五",
    
    # 新修复的识别问题
    "五点五麒麟",
    "五点五机灵",
    "五点五七",  # 用于对比
    "五点五七零", # 预期结果参考
    
    # 之前的误识别测试
    "我",
    "我是",
    "我是我",
    
    # 特殊格式测试
    "点八四",
    "垫巴四"
]

def test_performance():
    """测试识别性能和准确性"""
    print("🚀 开始性能和识别准确性测试...\n")
    
    # 创建AudioCapture实例（使用测试模式）
    print("📦 初始化AudioCapture实例...")
    cap = AudioCapture(test_mode=True)
    
    # 验证模型管理器状态
    print(f"✅ 模型管理器状态: 已加载模型数 = {len(global_model_manager.get_loaded_models())}")
    
    # 测试响应速度
    print("\n📊 响应速度测试:")
    total_time = 0
    results = []
    
    for i, text in enumerate(TEST_CASES):
        start_time = time.time()
        
        # 使用与实时识别相同的处理流程
        corrected_text = correct_voice_errors(text)
        nums = extract_measurements(text)
        
        processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
        total_time += processing_time
        
        results.append({
            "输入文本": text,
            "纠错后文本": corrected_text,
            "提取数值": nums,
            "处理时间(ms)": round(processing_time, 2)
        })
        
        print(f"测试 {i+1}/{len(TEST_CASES)}: '{text}' 处理时间: {round(processing_time, 2)}ms")
    
    avg_time = total_time / len(TEST_CASES)
    print(f"\n✅ 平均处理时间: {round(avg_time, 2)}ms")
    print(f"✅ 总处理时间: {round(total_time, 2)}ms\n")
    
    # 打印详细结果表格
    print("📋 详细识别结果:")
    print("=" * 80)
    print(f"{'输入文本':<12} {'纠错后文本':<12} {'提取数值':<15} {'处理时间(ms)':<12}")
    print("=" * 80)
    
    for result in results:
        # 格式化数值输出
        nums_str = str(result['提取数值'])
        if len(result['提取数值']) > 0:
            nums_str = f"[{', '.join(f'{n}' for n in result['提取数值'])}]"
        else:
            nums_str = "[]"
        
        print(f"{result['输入文本']:<12} {result['纠错后文本']:<12} {nums_str:<15} {result['处理时间(ms)']:<12}")
    
    print("=" * 80)
    
    # 验证关键修复
    print("\n🔍 验证关键修复:")
    
    # 验证'五点五麒麟'和'五点五机灵'是否正确识别为5.570
    unicorn_result = extract_measurements("五点五麒麟")
    clever_result = extract_measurements("五点五机灵")
    
    print(f"'五点五麒麟' → {unicorn_result}")
    print(f"'五点五机灵' → {clever_result}")
    
    # 检查是否符合预期
    unicorn_passed = len(unicorn_result) > 0 and abs(unicorn_result[0] - 5.57) < 0.01
    clever_passed = len(clever_result) > 0 and abs(clever_result[0] - 5.57) < 0.01
    
    if unicorn_passed and clever_passed:
        print("✅ 成功修复：'五点五麒麟'和'五点五机灵'现在能正确识别为5.57!")
    else:
        print("❌ 修复未完全成功，仍需调整。")
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    test_performance()