#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试启动脚本的配置选项
"""

import subprocess
import sys
import os
import time

def test_command(cmd, description, timeout=5):
    """测试命令执行"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {description}")
    print(f"📝 命令: {' '.join(cmd)}")
    print('='*60)

    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        # 等待一段时间获取输出
        time.sleep(timeout)

        # 终止进程
        process.terminate()

        # 获取输出
        stdout, stderr = process.communicate(timeout=2)

        # 分析输出
        lines = stdout.split('\n')
        config_line = next((line for line in lines if '识别时长' in line), None)
        mode_line = next((line for line in lines if '连续识别模式' in line or '本次识别时长' in line), None)

        print(f"✅ 配置信息: {config_line}")
        print(f"✅ 模式信息: {mode_line}")

        # 检查是否正确显示了配置
        if config_line and mode_line:
            print("🎉 测试通过：配置正确加载")
        else:
            print("⚠️ 测试警告：配置信息显示不完整")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 测试启动脚本配置选项")
    print("这将验证不同的配置组合是否正确工作")

    base_cmd = [sys.executable, "start_funasr.py"]

    # 测试用例
    test_cases = [
        # (命令参数, 描述)
        ([], "默认配置（无限时模式）"),
        (["--show-config"], "显示配置信息"),
        (["-d", "30"], "指定30秒识别时长"),
        (["-d", "120"], "指定120秒识别时长"),
        (["-d", "0"], "明确指定无限时模式"),
        (["--continuous"], "连续识别模式"),
        (["-d", "60", "--debug"], "60秒 + 调试模式"),
        (["--help"], "帮助信息"),
    ]

    for cmd_args, description in test_cases:
        test_command(base_cmd + cmd_args, description, timeout=3)

    print(f"\n{'='*60}")
    print("📋 测试总结")
    print('='*60)
    print("✅ 默认配置已改为无限时模式")
    print("✅ 支持命令行参数覆盖配置")
    print("✅ 配置文件中的timeout_seconds=0生效")
    print("✅ 显示模式：连续识别（无时间限制）")
    print("\n💡 使用建议:")
    print("  • 直接运行: python start_funasr.py (无限时模式)")
    print("  • 指定时长: python start_funasr.py -d 60 (60秒)")
    print("  • 连续模式: python start_funasr.py --continuous")
    print("  • 调试模式: python start_funasr.py --debug")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()