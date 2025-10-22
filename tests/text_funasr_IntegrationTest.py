#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试 - FunASR + 文本处理
只显示最终识别和转换结果，完全隐藏所有其他输出
"""

import sys
import os
import logging

# 完全禁用所有日志
logging.getLogger().handlers = []
logging.getLogger().addHandler(logging.NullHandler())
logging.disable(logging.CRITICAL)

# 禁用所有警告
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# 重定向FunASR可能产生的输出
class NullWriter:
    def write(self, text): pass
    def flush(self): pass

# 重定向标准输出
original_stdout = sys.stdout
original_stderr = sys.stderr

def suppress_output():
    """抑制输出的函数"""
    sys.stdout = NullWriter()
    sys.stderr = NullWriter()

def restore_output():
    """恢复输出的函数"""
    sys.stdout = original_stdout
    sys.stderr = original_stderr

# 抑制输出进行模块导入（隐藏初始化消息）
suppress_output()

# 导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from funasr_voice_module import FunASRVoiceRecognizer
    from text_processor_clean import TextProcessor
    IMPORT_SUCCESS = True
except ImportError as e:
    IMPORT_SUCCESS = False

# 恢复输出
restore_output()

def main():
    """主函数"""
    # 输出已经恢复，无需重复操作

    print("🎯 语音识别 + 文本转换")
    print("=" * 40)

    if not IMPORT_SUCCESS:
        print("❌ 模块导入失败")
        return

    # 创建处理器（启用静默模式）
    recognizer = FunASRVoiceRecognizer(silent_mode=True)
    processor = TextProcessor()

    # 存储结果
    results = []

    # 设置回调 - 只返回识别的文本内容，不显示任何标签
    def on_final_result(result):
        if result.text.strip():
            processed = processor.process_text(result.text)
            # 传递原文和处理后的文本来提取数字
            numbers = processor.extract_numbers(result.text, processed)
            results.append({
                'original': result.text,
                'processed': processed,
                'numbers': numbers
            })

            # 临时恢复输出以显示实时结果
            current_stdout = sys.stdout
            current_stderr = sys.stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            # 只显示识别的文本内容（无任何标签）
            print(f"{result.text}")

            # 显示处理策略
            if numbers:
                # 有数字：显示数字
                print(f"{numbers[0]}")
            else:
                # 没有提取到数字：检查是否需要文本处理
                if processor.is_pure_number_or_with_unit(result.text):
                    # 如果是数字格式但没有提取成功，显示处理后的文本
                    if processed != result.text:
                        print(f"{processed}")
                else:
                    # 对于描述性文本，去除空格但不转换数字
                    clean_text = processor.remove_spaces(result.text)
                    print(f"{clean_text}")

            # 刷新输出
            sys.stdout.flush()
            sys.stderr.flush()

            # 恢复到抑制状态（如果需要）
            sys.stdout = current_stdout
            sys.stderr = current_stderr

    # 设置回调
    recognizer.set_callbacks(on_final_result=on_final_result)

    # 抑制输出进行初始化（隐藏FunASR加载信息）
    suppress_output()
    init_success = recognizer.initialize()
    restore_output()

    if init_success:
        print("请说话...")
        print("Ctrl+C 结束")
        print("-" * 40)

        try:
            # 抑制输出进行识别（隐藏FunASR进度条，但回调函数可以临时恢复）
            suppress_output()
            recognizer.recognize_speech(duration=60, real_time_display=False)
            restore_output()

            # 显示汇总
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
            print("\n用户结束")
        except Exception as e:
            print(f"识别错误: {e}")

    # 清理
    try:
        recognizer.stop_recognition()
        recognizer.unload_model()
    except:
        pass

if __name__ == "__main__":
    main()