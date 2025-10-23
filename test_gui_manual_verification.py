#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI手动验证测试脚本
启动GUI并提示用户进行文本和数字交替识别测试
"""

import sys
import subprocess
import time

def show_test_instructions():
    """显示测试说明"""
    print("🎯 GUI显示修复验证测试")
    print("=" * 50)
    print()
    print("📋 测试目标:")
    print("   验证修复后GUI能正确显示文本和数字交替识别")
    print()
    print("🎤 建议测试序列:")
    print("   1. 说出纯文本（如：'你好'、'测试'）")
    print("   2. 说出数字（如：'一二三'、'三四五'）")
    print("   3. 说出纯文本（如：'继续测试'、'好的'）")
    print("   4. 说出数字（如：'三点一四'、'五点六七'）")
    print("   5. 说出纯文本（如：'最后一个测试'）")
    print()
    print("✅ 预期结果:")
    print("   - 文本识别后应显示文本内容")
    print("   - 数字识别后应显示带ID的数字")
    print("   - 不应出现显示之前数字信息的问题")
    print()
    print("❌ 修复前的问题:")
    print("   - 识别数字后，再识别文本会显示之前的数字")
    print()
    print("🚀 启动GUI进行测试...")
    print("=" * 50)

def run_gui_test():
    """运行GUI测试"""
    try:
        # 显示测试说明
        show_test_instructions()

        # 等待用户确认
        input("按回车键启动GUI...")

        print("\n🚀 正在启动GUI...")
        print("提示：关闭GUI窗口后，脚本会显示测试总结")

        # 启动GUI
        result = subprocess.run([sys.executable, "voice_gui.py"],
                              cwd=".",
                              capture_output=False)

        print("\n" + "=" * 50)
        print("📊 测试完成")
        print("=" * 50)
        print()
        print("🤔 请回答以下问题:")
        print("1. 文本识别后是否正确显示文本内容？")
        print("2. 数字识别后是否正确显示数字？")
        print("3. 文本和数字交替识别时，显示是否正确切换？")
        print("4. 是否没有出现'显示之前数字信息'的问题？")
        print()
        print("如果以上问题答案都是'是'，则修复成功！")

        return result.returncode == 0

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = run_gui_test()

    if success:
        print("\n🎉 GUI测试完成")
    else:
        print("\n⚠️ GUI测试未完成或失败")

    sys.exit(0 if success else 1)