# -*- coding: utf-8 -*-
"""
统一测试运行器

运行所有核心测试套件。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_test_module(module_name, display_name):
    """运行单个测试模块"""
    print(f"\n{display_name}")
    print("=" * len(display_name))

    try:
        # 动态导入模块
        module = __import__(module_name)

        # 查找运行函数
        run_functions = [
            f'run_{module_name.replace("test_", "")}_tests',
            f'run_{module_name.replace("test_", "")}',
        ]

        run_func = None
        for func_name in run_functions:
            if hasattr(module, func_name):
                run_func = getattr(module, func_name)
                break

        if run_func:
            success = run_func()
            return success
        else:
            print(f"  未找到运行函数")
            return False

    except Exception as e:
        print(f"  运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("事件驱动语音输入系统 - 测试套件")
    print("=" * 50)
    print("使用虚拟环境运行: .venv\\Scripts\\python.exe run_tests.py")
    print("=" * 50)

    results = {}

    # 核心测试模块
    test_modules = [
        ("test_basic", "基础功能测试"),
        ("test_event_system", "事件系统测试"),
        ("test_async_audio", "异步音频组件测试"),
        ("test_full_async_audio", "完整异步音频测试"),
        ("test_integration", "集成测试"),
    ]

    # 运行各个测试
    for module_name, display_name in test_modules:
        results[module_name] = run_test_module(module_name, display_name)

    # 输出总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)

    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)

    for test_name, result in results.items():
        status = "通过" if result else "失败"
        print(f"  {test_name:<25} {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 测试套件通过")

    if passed_tests == total_tests:
        print("\n所有测试通过! 系统核心功能正常。")
        print("\n建议运行演示程序验证完整功能:")
        print("  .venv\\Scripts\\python.exe -m examples.event_driven_demo")
        return True
    else:
        print(f"\n有 {total_tests - passed_tests} 个测试套件失败。")
        print("请检查相关模块或查看详细错误信息。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)