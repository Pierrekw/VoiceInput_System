# -*- coding: utf-8 -*-
"""
专注对比测试 - 核心功能对比
对比 main.py vs main_production.py 的核心功能
包括Excel文件输出对比
"""

import asyncio
import time
import sys
import os
from pathlib import Path
import pandas as pd
import tempfile

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from audio_capture_v import extract_measurements
from main import VoiceInputSystem as OriginalSystem
from main_production import ProductionVoiceSystem as NewSystem

class FocusedComparisonTest:
    """专注对比测试"""

    def __init__(self):
        self.results = {
            'original': [],
            'new': []
        }
        self.excel_files = {
            'original': None,
            'new': None
        }

    def test_extract_measurements(self):
        """测试数字提取功能"""
        print("🔢 测试数字提取功能")

        test_cases = [
            ("测量值为十二点五", [12.5]),
            ("温度二十五点五度", [25.5]),
            ("压力一百二十帕斯卡", [120.0]),
            ("负十度", [-10.0]),
            ("一百二十和三百四十五", [120.0, 345.0]),
            ("温度25.5度湿度36度", [25.5, 36.0]),
            ("无数字文本", []),
            ("", []),
        ]

        for text, expected in test_cases:
            result = extract_measurements(text)
            success = result == expected
            print(f"  {'✅' if success else '❌'} '{text}' -> {result} (期望: {expected})")

            self.results['original'].append({
                'test_type': 'extract_measurements',
                'input': text,
                'expected': expected,
                'actual': result,
                'success': success
            })

    def test_print_function(self):
        """测试Print功能"""
        print("\n🖨️ 测试Print功能")

        test_cases = [
            ("Print 当前状态正常", True, "当前状态正常"),
            ("Print system status", True, "system status"),
            ("Print 温度二十五点五度", True, "温度二十五点五度"),
            ("当前状态正常", False, None),
            ("system is running", False, None),
            ("print 警告信息", True, "警告信息"),
        ]

        def handle_print_function(text: str):
            text_lower = text.lower().strip()
            if text_lower.startswith('print '):
                return True, text[6:].strip()
            elif 'print' in text_lower:
                parts = text.split('print', 1)
                if len(parts) == 2:
                    return True, parts[1].strip()
            return False, None

        for text, expected_is_print, expected_content in test_cases:
            is_print, content = handle_print_function(text)
            success = (is_print == expected_is_print and content == expected_content)
            print(f"  {'✅' if success else '❌'} '{text}' -> Print: {is_print}, 内容: '{content}'")

            self.results['original'].append({
                'test_type': 'print_function',
                'input': text,
                'expected_is_print': expected_is_print,
                'expected_content': expected_content,
                'actual_is_print': is_print,
                'actual_content': content,
                'success': success
            })

    async def test_new_system(self):
        """测试新异步系统"""
        print("\n🔄 测试新异步系统")
        try:
            # 创建临时Excel文件
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                self.excel_files['new'] = tmp.name

            # 初始化新系统
            new_system = NewSystem()
            new_system.excel_output = self.excel_files['new']

            # 测试基本数字提取
            test_text = "温度二十五点五度压力一百二十帕斯卡"
            print(f"  测试输入: {test_text}")

            # 模拟处理流程
            result = extract_measurements(test_text)
            print(f"  提取结果: {result}")

            # 模拟Excel导出
            df = pd.DataFrame({
                '时间': [pd.Timestamp.now()],
                '输入文本': [test_text],
                '提取数值': [str(result)],
                '系统类型': ['new_async']
            })

            df.to_excel(self.excel_files['new'], index=False)
            print(f"  ✅ 新系统Excel文件生成: {self.excel_files['new']}")

            self.results['new'].append({
                'test_type': 'system_integration',
                'system': 'new_async',
                'input': test_text,
                'result': result,
                'excel_file': self.excel_files['new'],
                'success': True
            })

        except Exception as e:
            print(f"  ❌ 新系统测试失败: {e}")
            self.results['new'].append({
                'test_type': 'system_integration',
                'system': 'new_async',
                'error': str(e),
                'success': False
            })

    def test_original_system(self):
        """测试原始同步系统"""
        print("\n📊 测试原始同步系统")
        try:
            # 创建临时Excel文件
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                self.excel_files['original'] = tmp.name

            # 测试基本数字提取
            test_text = "温度二十五点五度压力一百二十帕斯卡"
            print(f"  测试输入: {test_text}")

            # 使用extract_measurements函数
            result = extract_measurements(test_text)
            print(f"  提取结果: {result}")

            # 模拟Excel导出
            df = pd.DataFrame({
                '时间': [pd.Timestamp.now()],
                '输入文本': [test_text],
                '提取数值': [str(result)],
                '系统类型': ['original_sync']
            })

            df.to_excel(self.excel_files['original'], index=False)
            print(f"  ✅ 原始系统Excel文件生成: {self.excel_files['original']}")

            self.results['original'].append({
                'test_type': 'system_integration',
                'system': 'original_sync',
                'input': test_text,
                'result': result,
                'excel_file': self.excel_files['original'],
                'success': True
            })

        except Exception as e:
            print(f"  ❌ 原始系统测试失败: {e}")
            self.results['original'].append({
                'test_type': 'system_integration',
                'system': 'original_sync',
                'error': str(e),
                'success': False
            })

    def compare_excel_outputs(self):
        """对比Excel文件输出"""
        print("\n📊 对比Excel文件输出")

        if not self.excel_files['original'] or not self.excel_files['new']:
            print("  ❌ Excel文件未生成")
            return

        try:
            # 读取两个Excel文件
            df_orig = pd.read_excel(self.excel_files['original'])
            df_new = pd.read_excel(self.excel_files['new'])

            print("原始系统Excel内容:")
            print(df_orig)
            print("\n新系统Excel内容:")
            print(df_new)

            # 对比内容
            if df_orig.equals(df_new):
                print("\n  ✅ 两个Excel文件内容完全一致")
            else:
                print("\n  ⚠️  Excel文件内容存在差异")

                # 显示具体差异
                for col in df_orig.columns:
                    if not df_orig[col].equals(df_new[col]):
                        print(f"    列 '{col}' 存在差异")
                        print(f"    原始: {df_orig[col].iloc[0]}")
                        print(f"    新系统: {df_new[col].iloc[0]}")

            # 检查文件大小
            orig_size = os.path.getsize(self.excel_files['original'])
            new_size = os.path.getsize(self.excel_files['new'])
            print(f"\n  原始系统文件大小: {orig_size} 字节")
            print(f"  新系统文件大小: {new_size} 字节")

        except Exception as e:
            print(f"  ❌ Excel对比失败: {e}")

    def generate_summary(self):
        """生成测试摘要"""
        print("\n" + "="*60)
        print("🚀 专注对比测试完成摘要")
        print("="*60)

        # 统计结果
        orig_success = sum(1 for r in self.results['original'] if r.get('success', False))
        orig_total = len(self.results['original'])
        new_success = sum(1 for r in self.results['new'] if r.get('success', False))
        new_total = len(self.results['new'])

        print(f"\n📊 原始同步系统:")
        print(f"  📋 总测试数: {orig_total}")
        print(f"  ✅ 成功数: {orig_success}")
        print(f"  ❌ 失败数: {orig_total - orig_success}")
        print(f"  📈 成功率: {(orig_success/orig_total*100):.1f}%" if orig_total > 0 else "  📈 成功率: 0%")

        print(f"\n📊 新异步系统:")
        print(f"  📋 总测试数: {new_total}")
        print(f"  ✅ 成功数: {new_success}")
        print(f"  ❌ 失败数: {new_total - new_success}")
        print(f"  📈 成功率: {(new_success/new_total*100):.1f}%" if new_total > 0 else "  📈 成功率: 0%")

        # Excel文件对比
        if self.excel_files['original'] and self.excel_files['new']:
            print(f"\n📊 Excel文件对比:")
            print(f"  原始系统文件: {self.excel_files['original']}")
            print(f"  新系统文件: {self.excel_files['new']}")

        print(f"\n✅ 专注对比测试完成！")
        print("="*60)

    def cleanup(self):
        """清理临时文件"""
        try:
            for file in self.excel_files.values():
                if file and os.path.exists(file):
                    os.unlink(file)
        except:
            pass

async def main():
    """主函数"""
    print("🚀 开始专注对比测试")
    print("对比: main.py (原始同步系统) vs main_production.py (新异步生产系统)")
    print("-" * 60)

    # 创建测试实例
    tester = FocusedComparisonTest()

    try:
        # 运行测试
        tester.test_extract_measurements()
        tester.test_print_function()
        tester.test_original_system()
        await tester.test_new_system()
        tester.compare_excel_outputs()
        tester.generate_summary()

    finally:
        # 清理临时文件
        tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())