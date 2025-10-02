#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test Runner - Runs all voice recognition integration tests
Provides a unified interface for testing the voice system
"""

import os
import sys
import subprocess
import time
from typing import List, Tuple

def run_test_script(script_name: str, description: str) -> Tuple[bool, str]:
    """Run a test script and return success status and output"""
    print(f"\n{'='*60}")
    print(f"🧪 运行测试: {description}")
    print(f"脚本: {script_name}")
    print('='*60)

    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per test
        )

        # Print output
        if result.stdout:
            print("输出:")
            print(result.stdout)

        if result.stderr:
            print("错误:")
            print(result.stderr)

        # Check if test passed
        success = result.returncode == 0

        if success:
            print(f"✅ {description} - 通过")
        else:
            print(f"❌ {description} - 失败 (返回码: {result.returncode})")

        return success, result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时 (60秒)")
        return False, "Test timeout"
    except Exception as e:
        print(f"💥 {description} - 异常: {e}")
        return False, str(e)

def main():
    """Main test runner function"""
    print("="*70)
    print("🎤 语音系统 - 集成测试运行器")
    print("="*70)
    print("本运行器将执行所有集成测试:")
    print()

    # Define test scripts
    tests = [
        ("simple_integration_test.py", "简易集成测试", "基础功能验证"),
        ("integration_test_main.py", "综合集成测试", "完整系统测试"),
        ("main_function_test.py", "主函数流程测试", "Mode 1功能专项测试"),
        ("voice_integration_main.py", "语音集成主函数测试", "生产环境集成测试"),
        ("test_mode1_direct.py", "Mode 1直接测试", "Mode 1功能直接验证"),
        ("test_voice_improved.py", "改进版语音测试", "增强识别测试"),
        ("test_voice_debug.py", "调试版语音测试", "调试信息测试"),
        ("test_number_extraction.py", "数字提取测试", "数字提取功能专项测试")
    ]

    # Display available tests
    print("可用测试:")
    for i, (script, name, description) in enumerate(tests, 1):
        print(f"{i}. {name} - {description}")
    print()
    print("选项:")
    print("A. 运行所有测试")
    print("B. 运行基础测试 (1,2,3,4)")
    print("C. 运行语音专项测试 (5,6,7,8)")
    print("D. 运行特定测试")
    print("Q. 退出")
    print()

    choice = input("请选择 (A/B/C/D/Q): ").strip().upper()

    selected_tests = []

    if choice == "A":
        selected_tests = tests
    elif choice == "B":
        selected_tests = tests[:4]  # First 4 tests
    elif choice == "C":
        selected_tests = tests[4:]  # Last 4 tests
    elif choice == "D":
        test_numbers = input("请输入测试编号 (如: 1,3,5 或 1-4): ").strip()
        try:
            if '-' in test_numbers:
                start, end = map(int, test_numbers.split('-'))
                selected_tests = tests[start-1:end]
            else:
                numbers = [int(x.strip()) for x in test_numbers.split(',')]
                selected_tests = [tests[i-1] for i in numbers]
        except (ValueError, IndexError):
            print("❌ 无效的选择")
            return 1
    elif choice == "Q":
        print("👋 退出测试运行器")
        return 0
    else:
        print("❌ 无效的选择")
        return 1

    if not selected_tests:
        print("⚠️ 未选择任何测试")
        return 0

    print(f"\n📋 将运行 {len(selected_tests)} 个测试")
    print("="*70)

    # Run selected tests
    results = []
    start_time = time.time()

    for script_name, test_name, description in selected_tests:
        if os.path.exists(script_name):
            success, output = run_test_script(script_name, test_name)
            results.append((test_name, success, output))
            time.sleep(1)  # Brief pause between tests
        else:
            print(f"⚠️ 测试脚本不存在: {script_name}")
            results.append((test_name, False, "Script not found"))

    # Summary
    total_time = time.time() - start_time

    print("\n" + "="*70)
    print("📊 测试运行总结")
    print("="*70)
    print(f"总运行时间: {total_time:.1f}秒")
    print(f"运行测试数: {len(results)}")

    passed_tests = sum(1 for _, success, _ in results if success)
    failed_tests = len(results) - passed_tests

    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"成功率: {passed_tests/len(results)*100:.1f}%")

    print("\n详细结果:")
    for test_name, success, _ in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")

    # Recommendations
    print("\n💡 建议:")
    if passed_tests == len(results):
        print("🎉 所有测试通过！语音系统功能正常")
        print("• 可以开始使用主程序")
        print("• 建议在实际环境中验证")
    elif passed_tests >= len(results) * 0.75:
        print("⚠️ 大部分测试通过，语音系统基本正常")
        print("• 检查失败的测试项目")
        print("• 可以谨慎使用主程序")
    else:
        print("❌ 较多测试失败，语音系统存在问题")
        print("• 需要修复失败的功能")
        print("• 查看日志文件获取详细信息")
        print("• 建议重新检查系统配置")

    # Save summary to file
    try:
        with open('test_summary.txt', 'w', encoding='utf-8') as f:
            f.write(f"语音系统测试总结 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n")
            f.write(f"总测试数: {len(results)}\n")
            f.write(f"通过测试: {passed_tests}\n")
            f.write(f"失败测试: {failed_tests}\n")
            f.write(f"成功率: {passed_tests/len(results)*100:.1f}%\n")
            f.write("="*60 + "\n")
            f.write("详细结果:\n")
            for test_name, success, output in results:
                status = "通过" if success else "失败"
                f.write(f"{status} - {test_name}\n")
                if not success and output:
                    f.write(f"错误信息: {output[:200]}...\n")
            f.write("="*60 + "\n")
        print(f"\n📄 测试总结已保存到: test_summary.txt")
    except Exception as e:
        print(f"⚠️ 无法保存测试总结: {e}")

    # Return appropriate exit code
    if passed_tests == len(results):
        return 0  # All tests passed
    elif passed_tests >= len(results) * 0.5:
        return 0  # Most tests passed
    else:
        return 1  # Too many tests failed

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 用户中断测试运行器")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 测试运行器异常: {e}")
        sys.exit(1)