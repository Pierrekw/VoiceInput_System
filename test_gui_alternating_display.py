#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI显示修复测试脚本 - 文本和数字交替显示场景
模拟日志中的场景：文本 -> 数字 -> 文本 -> 数字...
"""

import sys
import time
from typing import List, Tuple, Union, Optional

# 模拟语音系统数据
class MockVoiceSystem:
    def __init__(self):
        self.number_results: List[Tuple[int, Union[int, float, str], str]] = []
        self.record_counter = 0

    def add_number_record(self, number: Union[int, float, str], text: str) -> Tuple[int, Union[int, float, str], str]:
        """添加数字记录"""
        self.record_counter += 1
        record = (self.record_counter, number, text)
        self.number_results.append(record)
        return record

def simulate_fixed_logic(original_text: str, processed_text: str, numbers: List[float],
                        voice_system: MockVoiceSystem) -> Optional[str]:
    """
    模拟修复后的GUI显示逻辑
    返回应该显示在GUI上的文本
    """
    # 步骤1：模拟原始处理结果方法
    has_new_record = False
    display_text = None

    # 检查是否产生新记录（数字或特殊文本）
    if numbers and len(numbers) > 0:
        # 有数字：添加到记录
        latest_record = voice_system.add_number_record(numbers[0], processed_text)
        has_new_record = True
        display_text = f"[{latest_record[0]}] {latest_record[1]}"
    elif processed_text in ["OK", "Not OK", "合格", "不合格", "ok", "not ok"]:
        # 特殊文本：添加到记录
        special_text = processed_text
        if processed_text in ["合格", "ok"]:
            special_text = "OK"
        elif processed_text in ["不合格", "not ok"]:
            special_text = "NOT OK"

        latest_record = voice_system.add_number_record(special_text, processed_text)
        has_new_record = True
        display_text = f"[{latest_record[0]}] {special_text}"

    # 步骤2：如果没有新记录，显示文本结果（这是修复的关键）
    if not has_new_record:
        if processed_text and processed_text.strip():
            display_text = processed_text
        elif original_text and original_text.strip():
            display_text = original_text

    return display_text

def simulate_old_logic(original_text: str, processed_text: str, numbers: List[float],
                      voice_system: MockVoiceSystem) -> Optional[str]:
    """
    模拟修复前的GUI显示逻辑（有问题的逻辑）
    """
    # 旧逻辑的问题：总是显示最新的记录，不区分是否为当前识别的结果
    if numbers and len(numbers) > 0:
        latest_record = voice_system.add_number_record(numbers[0], processed_text)
        return f"[{latest_record[0]}] {latest_record[1]}"
    elif processed_text in ["OK", "Not OK"]:
        latest_record = voice_system.add_number_record(processed_text, processed_text)
        return f"[{latest_record[0]}] {latest_record[1]}"
    else:
        # 旧逻辑的问题：即使有新的文本识别，如果之前有数字记录，还是会显示数字
        if voice_system.number_results:
            latest_record = voice_system.number_results[-1]
            return f"[{latest_record[0]}] {latest_record[1]}"
        else:
            return processed_text

def test_gui_display_fix():
    """测试GUI显示修复"""
    print("🧪 测试GUI显示修复 - 文本和数字交替显示场景")
    print("=" * 70)

    # 基于日志的测试场景
    test_cases = [
        ("ok 对", "ok对", []),                # 文本识别
        ("ok", "ok", []),                     # 特殊文本识别（会变成OK）
        ("很 多 都 ok", "很多都ok", []),      # 文本识别
        ("not ok", "notok", []),             # 特殊文本识别（会变成NOT OK）
        ("不 合 格", "不合格", []),           # 特殊文本识别（会变成NOT OK）
        ("你 好", "你好", []),                # 文本识别
        ("七 八 三", "783", [783.0]),         # 数字识别
        ("三 四 三", "343", [343.0]),        # 数字识别
        ("三 点 八 八", "三点八八", [3.88]),  # 数字识别
        ("四 点 五 三", "四点五三", [4.53]), # 数字识别
        ("五 点 八 八", "五点八八", [5.88]),  # 数字识别
        ("十 七 点 八 八", "十七点八八", [17.88]), # 数字识别
        ("你 好", "你好", []),                # 文本识别（关键测试：在多个数字后识别文本）
    ]

    print("📋 测试场景（基于日志数据）:")
    print("-" * 70)

    # 测试修复后的逻辑
    print("\n🟢 测试修复后的逻辑:")
    fixed_system = MockVoiceSystem()
    fixed_displays = []

    for i, (original, processed, numbers) in enumerate(test_cases, 1):
        display_result = simulate_fixed_logic(original, processed, numbers, fixed_system)
        fixed_displays.append(display_result)

        result_type = "数字" if numbers else ("特殊文本" if processed in ["OK", "Not OK", "合格", "不合格", "ok", "not ok", "notok"] else "文本")
        print(f"{i:2d}. {result_type:4s}: '{display_result}'")

    # 测试修复前的逻辑
    print("\n🔴 测试修复前的逻辑（有问题的版本）:")
    old_system = MockVoiceSystem()
    old_displays = []

    for i, (original, processed, numbers) in enumerate(test_cases, 1):
        display_result = simulate_old_logic(original, processed, numbers, old_system)
        old_displays.append(display_result)

        result_type = "数字" if numbers else ("特殊文本" if processed in ["OK", "Not OK", "合格", "不合格", "ok", "not ok", "notok"] else "文本")
        print(f"{i:2d}. {result_type:4s}: '{display_result}'")

    # 对比分析
    print("\n" + "=" * 70)
    print("📊 对比分析:")
    print("-" * 70)

    differences = []
    for i, (fixed, old) in enumerate(zip(fixed_displays, old_displays), 1):
        if fixed != old:
            differences.append((i, test_cases[i-1], old, fixed))

    if differences:
        print(f"发现 {len(differences)} 处差异:")
        for idx, (original, processed, numbers), old_display, fixed_display in differences:
            print(f"\n📍 位置 {idx}:")
            print(f"   输入: '{original}' -> '{processed}' (数字: {numbers})")
            print(f"   修复前: '{old_display}'")
            print(f"   修复后: '{fixed_display}'")

            if numbers:
                print(f"   ✅ 数字识别正确")
            else:
                print(f"   ✅ 文本识别修复：不再显示之前的数字信息")
    else:
        print("⚠️ 未发现差异，可能修复逻辑有问题")

    # 验证核心问题
    print(f"\n🎯 核心问题验证:")
    print("问题：识别数字后再次识别文字，是否显示之前的数字信息？")

    # 查找修复后逻辑中的数字 -> 文本场景
    text_after_number_fixed = False
    for i in range(1, len(fixed_displays)):
        prev_has_number = i > 0 and test_cases[i-1][2]  # 前一个有数字
        curr_no_number = not test_cases[i][2]           # 当前没有数字
        prev_display_has_brackets = "[" in str(fixed_displays[i-1]) and "]" in str(fixed_displays[i-1])
        curr_display_no_brackets = fixed_displays[i] and "[" not in str(fixed_displays[i]) and "]" not in str(fixed_displays[i])

        if prev_has_number and curr_no_number and prev_display_has_brackets and curr_display_no_brackets:
            text_after_number_fixed = True
            print(f"✅ 修复后：位置{i-1}数字'{fixed_displays[i-1]}' -> 位置{i}文本'{fixed_displays[i]}'")
            print(f"   文本显示正确，没有显示之前的数字信息")
            break

    # 查找修复前逻辑中的问题
    text_after_number_old = False
    for i in range(1, len(old_displays)):
        prev_has_number = i > 0 and test_cases[i-1][2]  # 前一个有数字
        curr_no_number = not test_cases[i][2]           # 当前没有数字
        prev_display_has_brackets = "[" in str(old_displays[i-1]) and "]" in str(old_displays[i-1])
        curr_display_has_brackets = "[" in str(old_displays[i]) and "]" in str(old_displays[i])

        if prev_has_number and curr_no_number and prev_display_has_brackets and curr_display_has_brackets:
            text_after_number_old = True
            print(f"❌ 修复前：位置{i-1}数字'{old_displays[i-1]}' -> 位置{i}数字'{old_displays[i]}'")
            print(f"   文本识别后仍显示之前的数字信息（这是问题）")
            break

    if not text_after_number_fixed:
        print("⚠️ 修复后的逻辑中未找到数字后的文本识别场景")
    if not text_after_number_old:
        print("⚠️ 修复前的逻辑中未发现问题场景")

    # 总结
    print(f"\n📋 总结:")
    if text_after_number_fixed and not text_after_number_old:
        print("🎉 修复成功！GUI显示问题已解决")
        print("   ✅ 文本识别后正确显示文本内容")
        print("   ✅ 不再显示之前的数字信息")
        return True
    elif text_after_number_old:
        print("⚠️ 修复前的逻辑确实存在问题")
        if text_after_number_fixed:
            print("✅ 修复后的逻辑已解决问题")
            return True
        else:
            print("❌ 修复后的逻辑仍有问题")
            return False
    else:
        print("⚠️ 测试场景可能不够全面，建议手动测试")
        return False

if __name__ == "__main__":
    success = test_gui_display_fix()
    print(f"\n{'='*70}")
    if success:
        print("🎉 测试通过：GUI显示修复有效")
    else:
        print("⚠️ 测试未完全通过，需要进一步检查")
    sys.exit(0 if success else 1)