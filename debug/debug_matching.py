#!/usr/bin/env python3
"""
调试GUI匹配逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_gui_matching():
    """调试GUI匹配逻辑"""
    print("🔍 调试GUI匹配逻辑")
    print("=" * 50)

    try:
        from main_f import FunASRVoiceSystem

        # 创建语音系统实例
        voice_system = FunASRVoiceSystem(
            recognition_duration=-1,
            continuous_mode=True,
            debug_mode=True
        )

        # 模拟GUI回调
        gui_calls = []
        def mock_gui_callback(original_text, processed_text, numbers):
            gui_calls.append({
                'original': original_text,
                'processed': processed_text,
                'numbers': numbers,
                'time': __import__('time').time()
            })
            print(f"🖥️ GUI回调: '{original_text}' -> '{processed_text}' ({numbers})")

        # 设置回调
        voice_system.process_recognition_result = mock_gui_callback

        # 模拟命令处理
        print("\n📋 模拟命令处理:")
        voice_system._add_command_to_results(
            "[命令] 切换到标准序号 200",
            "设置200",
            200
        )

        if gui_calls:
            latest_call = gui_calls[-1]
            print(f"📝 最新GUI调用: {latest_call}")

            # 模拟GUI匹配逻辑
            print(f"\n🔍 模拟GUI匹配逻辑:")

            # 模拟number_results中的最新记录
            mock_record = ("CMD_12345", 200, "[CMD] [命令] 切换到标准序号 200")
            record_id, record_number, record_text = mock_record

            print(f"📋 记录详情:")
            print(f"  record_id: {record_id}")
            print(f"  record_number: {record_number}")
            print(f"  record_text: {record_text}")

            print(f"\n📋 GUI回调参数:")
            print(f"  original_text: '{latest_call['original']}'")
            print(f"  processed_text: '{latest_call['processed']}'")
            print(f"  numbers: {latest_call['numbers']}")

            # 模拟匹配逻辑
            is_matching_record = False
            if record_text:
                print(f"\n🔍 开始匹配:")
                print(f"  检查 record_text.startswith('[CMD]'): {record_text.startswith('[CMD]')}")

                if record_text.startswith("[CMD]"):
                    print(f"  ✅ 是CMD格式")
                    if latest_call['numbers'] and len(latest_call['numbers']) > 0:
                        print(f"  有数字: {latest_call['numbers']}")
                        if isinstance(record_number, (int, float)):
                            print(f"  record_number类型: {type(record_number)}")
                            try:
                                record_num_float = float(record_number)
                                numbers_float = float(latest_call['numbers'][0])
                                print(f"  比较: {record_num_float} == {numbers_float} = {record_num_float == numbers_float}")
                                if record_num_float == numbers_float:
                                    is_matching_record = True
                                    print(f"  ✅ 数字匹配成功")
                            except Exception as e:
                                print(f"  ❌ 数字比较异常: {e}")
                        else:
                            print(f"  ❌ record_number不是数字类型")
                    else:
                        print(f"  ❌ 没有数字")
                else:
                    print(f"  ❌ 不是CMD格式")

            print(f"\n🎯 最终匹配结果: {'✅ 匹配成功' if is_matching_record else '❌ 匹配失败'}")

        return True

    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始GUI匹配调试")
    print("=" * 60)
    debug_gui_matching()