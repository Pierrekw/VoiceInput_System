#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超清洁的FunASR + 文本处理测试
完全隐藏所有输出，只显示核心转换结果
"""

import sys
import os
import logging
import warnings

# 完全隐藏所有输出
logging.getLogger().handlers = []
logging.getLogger().addHandler(logging.NullHandler())
logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from funasr_voice_module import FunASRVoiceRecognizer
from text_processor_clean import TextProcessor

def main():
    print("🎯 语音识别 + 文本转换测试")
    print("只显示识别和转换结果")
    print("=" * 40)

    # 创建处理器
    recognizer = FunASRVoiceRecognizer()
    processor = TextProcessor()

    # 存储结果
    results = []

    # 静默回调函数
    def on_final_result(result):
        if result.text.strip():
            processed = processor.process_text(result.text)
            numbers = processor.extract_numbers(processed)

            results.append({
                'original': result.text,
                'processed': processed,
                'numbers': numbers
            })

            # 只显示转换结果
            print(f"{result.text} -> {processed}")
            if numbers:
                print(f"数字: {numbers}")

    # 设置回调
    recognizer.set_callbacks(on_final_result=on_final_result)

    # 静默初始化
    recognizer.initialize()

    print("请说话...")
    print("Ctrl+C 结束")
    print("-" * 40)

    try:
        # 执行识别
        recognizer.recognize_speech(duration=30, real_time_display=False)

        # 显示最终汇总
        print("\n" + "=" * 40)
        print("识别汇总")
        print("=" * 40)

        if results:
            for i, res in enumerate(results, 1):
                print(f"{i}. {res['original']}")
                print(f"   -> {res['processed']}")
                if res['numbers']:
                    print(f"   -> 数字: {res['numbers']}")

            # 统计
            total = len(results)
            with_numbers = sum(1 for r in results if r['numbers'])

            print(f"\n总计: {total} 次识别")
            print(f"包含数字: {with_numbers} 次")

            if with_numbers > 0:
                all_numbers = []
                for r in results:
                    all_numbers.extend(r['numbers'])
                print(f"所有数字: {all_numbers}")
        else:
            print("未识别到语音")

    except KeyboardInterrupt:
        print("\n结束")
    except Exception as e:
        print(f"错误: {e}")

    # 清理
    recognizer.stop_recognition()
    recognizer.unload_model()

if __name__ == "__main__":
    main()