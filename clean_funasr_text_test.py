#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清洁的FunASR + 文本处理集成测试
隐藏不必要输出，提供最终对比清单
"""

import sys
import os
import logging

# 隐藏所有不必要的日志输出
logging.getLogger().setLevel(logging.ERROR)
os.environ['PYTHONWARNINGS'] = 'ignore'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from funasr_voice_module import FunASRVoiceRecognizer
from text_processor import TextProcessor

def clean_test():
    """清洁的集成测试"""
    print("🎯 FunASR + 文本处理集成测试")
    print("测试语音识别到数字转换的完整流程")
    print("=" * 60)

    # 创建处理器
    recognizer = FunASRVoiceRecognizer()
    processor = TextProcessor()

    # 存储识别结果
    recognition_results = []

    # 设置回调函数
    def on_final_result(result):
        """处理识别结果"""
        if not result.text.strip():
            return

        # 文本处理
        processed_text = processor.process_text(result.text)

        # 提取数字
        numbers = processor.extract_numbers(processed_text)

        # 存储结果
        recognition_results.append({
            'original': result.text,
            'processed': processed_text,
            'numbers': numbers,
            'confidence': result.confidence
        })

        # 简洁输出
        if numbers:
            print(f"识别: {result.text}")
            print(f"转换: {processed_text}")
            print(f"数字: {numbers}")
            print("-" * 40)
        else:
            print(f"识别: {result.text} (无数字)")

    # 设置回调
    recognizer.set_callbacks(on_final_result=on_final_result)

    # 初始化识别器
    print("🔧 初始化语音识别器...")
    if not recognizer.initialize():
        print("❌ 初始化失败")
        return

    print("✅ 初始化完成")
    print("💡 请说中文数字，例如：")
    print("   - '三 十 七 点 五'")
    print("   - '一 百 二 十 三'")
    print("   - '价格是一 百二 十三点五元'")
    print("⏹️  按Ctrl+C结束测试")
    print("=" * 60)

    try:
        # 执行识别
        result = recognizer.recognize_speech(duration=30, real_time_display=False)

        # 显示最终对比清单
        print(f"\n" + "=" * 60)
        print("📋 最终识别与转换对比清单")
        print("=" * 60)

        if recognition_results:
            print("序号 | 原始识别文本          | 转换后文本           | 提取数字")
            print("-" * 60)

            for i, res in enumerate(recognition_results, 1):
                original = res['original'][:20] + "..." if len(res['original']) > 20 else res['original']
                processed = res['processed'][:20] + "..." if len(res['processed']) > 20 else res['processed']
                numbers = str(res['numbers']) if res['numbers'] else "无"

                print(f"{i:4d} | {original:<20} | {processed:<20} | {numbers}")

            # 统计信息
            total = len(recognition_results)
            with_numbers = sum(1 for res in recognition_results if res['numbers'])
            conversion_rate = (with_numbers / total) * 100 if total > 0 else 0

            print(f"\n📊 识别统计:")
            print(f"总识别次数: {total}")
            print(f"包含数字的识别: {with_numbers}")
            print(f"数字转换率: {conversion_rate:.1f}%")

            if with_numbers > 0:
                all_numbers = []
                for res in recognition_results:
                    all_numbers.extend(res['numbers'])

                print(f"提取的所有数字: {all_numbers}")
        else:
            print("❌ 未识别到任何语音内容")

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")

    # 清理资源
    recognizer.stop_recognition()
    recognizer.unload_model()

if __name__ == "__main__":
    clean_test()