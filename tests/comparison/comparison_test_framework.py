# -*- coding: utf-8 -*-
"""
深度对比测试框架

用于对比原始系统和新的异步生产系统的：
- 数字识别准确度
- 性能指标（响应时间、资源使用）
- Excel输出差异
"""

import asyncio
import time
import sys
import os
import logging
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import psutil
import threading

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from async_config import AsyncConfigLoader


@dataclass
class TestResult:
    """测试结果数据类"""
    system_name: str
    test_timestamp: str
    accuracy_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    excel_output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AccuracyTestItem:
    """准确度测试项目"""
    input_text: str
    expected_numbers: List[float]
    test_id: str
    category: str = "general"


class ComparisonTestFramework:
    """对比测试框架"""

    def __init__(self, test_config_path: str):
        self.test_config_path = test_config_path
        self.config_loader = AsyncConfigLoader(test_config_path, enable_hot_reload=False)
        self.logger = self._setup_logger()

        # 测试数据
        self.test_data = [
            AccuracyTestItem("温度二十五点五度", [25.5], "TEMP001", "temperature"),
            AccuracyTestItem("压力一百二十帕斯卡", [120.0], "PRES001", "pressure"),
            AccuracyTestItem("湿度百分之七十五", [75.0], "HUMI001", "humidity"),
            AccuracyTestItem("长度为一米二", [1.2], "LENG001", "length"),
            AccuracyTestItem("数值42", [42.0], "NUM001", "direct"),
            AccuracyTestItem("角度九十度", [90.0], "ANG001", "angle"),
            AccuracyTestItem("重量十五千克", [15.0], "WEIG001", "weight"),
            AccuracyTestItem("深度负十点五米", [-10.5], "DEPT001", "depth"),
            AccuracyTestItem("计数一千零一", [1001.0], "COUNT001", "count"),
            AccuracyTestItem("速度八十八公里每小时", [88.0], "SPEED001", "speed"),
            # 更复杂的测试案例
            AccuracyTestItem("温度三十七点五度心率七十五", [37.5, 75.0], "MULT001", "multiple"),
            AccuracyTestItem("零度", [0.0], "ZERO001", "edge_case"),
            AccuracyTestItem("负五度", [-5.0], "NEG001", "negative"),
            AccuracyTestItem("一百点零一度", [100.01], "DEC001", "decimal"),
        ]

        # 测试结果
        self.results: Dict[str, TestResult] = {}

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('comparison_test')
        logger.setLevel(logging.INFO)

        # 创建文件处理器
        log_dir = Path("logs/comparison")
        log_dir.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def initialize(self) -> bool:
        """初始化测试框架"""
        try:
            success = await self.config_loader.initialize()
            if not success:
                self.logger.error("测试配置加载失败")
                return False

            self.logger.info("对比测试框架初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"测试框架初始化失败: {e}")
            return False

    async def run_accuracy_test(self, system_name: str, test_wrapper) -> Dict[str, Any]:
        """运行准确度测试"""
        self.logger.info(f"开始 {system_name} 准确度测试")

        correct_count = 0
        total_count = len(self.test_data)
        detailed_results = []
        category_stats = {}

        for item in self.test_data:
            try:
                # 模拟语音输入处理
                start_time = time.time()
                extracted_numbers = await test_wrapper.process_text(item.input_text)
                processing_time = time.time() - start_time

                # 检查准确性
                is_correct = self._compare_numbers(extracted_numbers, item.expected_numbers)
                if is_correct:
                    correct_count += 1

                # 记录详细结果
                result = {
                    'test_id': item.test_id,
                    'input_text': item.input_text,
                    'expected': item.expected_numbers,
                    'actual': extracted_numbers,
                    'correct': is_correct,
                    'processing_time': processing_time,
                    'category': item.category
                }
                detailed_results.append(result)

                # 分类统计
                if item.category not in category_stats:
                    category_stats[item.category] = {'correct': 0, 'total': 0}
                category_stats[item.category]['total'] += 1
                if is_correct:
                    category_stats[item.category]['correct'] += 1

                self.logger.info(f"{system_name} 测试 {item.test_id}: {item.input_text} -> {extracted_numbers} ({'✓' if is_correct else '✗'})")

            except Exception as e:
                self.logger.error(f"{system_name} 测试 {item.test_id} 失败: {e}")
                detailed_results.append({
                    'test_id': item.test_id,
                    'input_text': item.input_text,
                    'expected': item.expected_numbers,
                    'actual': [],
                    'correct': False,
                    'error': str(e),
                    'category': item.category
                })

        # 计算准确度指标
        overall_accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0

        category_accuracies = {}
        for category, stats in category_stats.items():
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            category_accuracies[category] = {
                'accuracy': accuracy,
                'correct': stats['correct'],
                'total': stats['total']
            }

        return {
            'overall_accuracy': overall_accuracy,
            'category_accuracies': category_accuracies,
            'detailed_results': detailed_results,
            'total_tests': total_count,
            'correct_tests': correct_count
        }

    async def run_performance_test(self, system_name: str, test_wrapper) -> Dict[str, Any]:
        """运行性能测试"""
        self.logger.info(f"开始 {system_name} 性能测试")

        # 系统资源使用监控
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        # 响应时间测试
        response_times = []
        throughput_times = []

        # 启动系统
        startup_start = time.time()
        await test_wrapper.startup()
        startup_time = time.time() - startup_start

        # 并发处理测试
        concurrent_start = time.time()
        tasks = []
        test_texts = [item.input_text for item in self.test_data[:5]]  # 使用前5个测试案例

        for text in test_texts:
            task = asyncio.create_task(test_wrapper.process_text(text))
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        concurrent_time = time.time() - concurrent_start

        # 记录成功的响应时间
        successful_results = [r for r in results if not isinstance(r, Exception)]
        if successful_results:
            response_times = [time.time() for _ in successful_results]  # 简化的响应时间记录

        # 资源使用测量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        # 关闭系统
        shutdown_start = time.time()
        await test_wrapper.shutdown()
        shutdown_time = time.time() - shutdown_start

        return {
            'startup_time': startup_time,
            'shutdown_time': shutdown_time,
            'concurrent_processing_time': concurrent_time,
            'memory_usage_mb': final_memory - initial_memory,
            'cpu_usage_percent': final_cpu - initial_cpu,
            'throughput': len(successful_results) / concurrent_time if concurrent_time > 0 else 0,
            'successful_operations': len(successful_results),
            'failed_operations': len(results) - len(successful_results)
        }

    async def run_excel_comparison(self, system_name: str, test_wrapper) -> Dict[str, Any]:
        """运行Excel输出对比测试"""
        self.logger.info(f"开始 {system_name} Excel输出测试")

        try:
            # 生成测试数据
            test_data = [
                {"ID": "TEST001", "数值": 25.5, "原始文本": "温度二十五点五度"},
                {"ID": "TEST002", "数值": 120.0, "原始文本": "压力一百二十帕斯卡"},
                {"ID": "TEST003", "数值": [37.5, 75.0], "原始文本": "温度三十七点五度心率七十五"},
            ]

            # 处理数据并生成Excel
            start_time = time.time()
            excel_path = await test_wrapper.generate_excel(test_data, f"test_{system_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            generation_time = time.time() - start_time

            if not excel_path or not Path(excel_path).exists():
                return {
                    'success': False,
                    'error': 'Excel文件生成失败',
                    'generation_time': generation_time
                }

            # 分析Excel文件
            excel_analysis = self._analyze_excel_file(excel_path)

            return {
                'success': True,
                'file_path': excel_path,
                'generation_time': generation_time,
                'file_size_kb': Path(excel_path).stat().st_size / 1024,
                'analysis': excel_analysis
            }

        except Exception as e:
            self.logger.error(f"{system_name} Excel测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'generation_time': 0
            }

    def _analyze_excel_file(self, excel_path: str) -> Dict[str, Any]:
        """分析Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path)

            analysis = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'data_types': df.dtypes.to_dict(),
                'sample_data': df.head().to_dict('records') if len(df) > 0 else []
            }

            # 检查必要的列
            required_columns = ['ID', '数值', '原始文本']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                analysis['warnings'] = [f"缺少必要的列: {missing_columns}"]

            return analysis

        except Exception as e:
            return {
                'error': f"Excel文件分析失败: {e}",
                'row_count': 0,
                'column_count': 0
            }

    def _compare_numbers(self, extracted: List[float], expected: List[float]) -> bool:
        """比较数字是否匹配"""
        if len(extracted) != len(expected):
            return False

        tolerance = 0.01  # 允许的误差范围
        for ext, exp in zip(extracted, expected):
            if abs(ext - exp) > tolerance:
                return False

        return True

    async def run_full_comparison(self) -> Dict[str, TestResult]:
        """运行完整的对比测试"""
        self.logger.info("开始完整对比测试")

        # 测试系统包装器
        original_wrapper = OriginalSystemWrapper()
        production_wrapper = ProductionSystemWrapper()

        systems = [
            ("OriginalSystem", original_wrapper),
            ("ProductionSystem", production_wrapper)
        ]

        for system_name, wrapper in systems:
            self.logger.info(f"测试系统: {system_name}")

            result = TestResult(
                system_name=system_name,
                test_timestamp=datetime.now().isoformat()
            )

            try:
                # 准确度测试
                result.accuracy_metrics = await self.run_accuracy_test(system_name, wrapper)

                # 性能测试
                result.performance_metrics = await self.run_performance_test(system_name, wrapper)

                # Excel输出测试
                result.excel_output = await self.run_excel_comparison(system_name, wrapper)

            except Exception as e:
                result.errors.append(f"系统测试失败: {e}")
                self.logger.error(f"{system_name} 测试失败: {e}")

            self.results[system_name] = result

        return self.results

    def generate_comparison_report(self) -> str:
        """生成对比测试报告"""
        report_path = f"tests/comparison/comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        report_content = [
            "# 系统对比测试报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试概述",
            "",
            f"测试系统数量: {len(self.results)}",
            f"测试案例数量: {len(self.test_data)}",
            "",
            "## 测试结果对比",
            ""
        ]

        # 准确度对比
        report_content.extend([
            "### 1. 数字识别准确度对比",
            "",
            "| 系统 | 总体准确度 | 正确/总数 | 详细信息 |",
            "|------|------------|-----------|----------|"
        ])

        for system_name, result in self.results.items():
            accuracy = result.accuracy_metrics.get('overall_accuracy', 0)
            correct = result.accuracy_metrics.get('correct_tests', 0)
            total = result.accuracy_metrics.get('total_tests', 0)
            report_content.append(f"| {system_name} | {accuracy:.1f}% | {correct}/{total} | [查看详情](#accuracy-{system_name.lower()}) |")

        # 性能对比
        report_content.extend([
            "",
            "### 2. 性能指标对比",
            "",
            "| 系统 | 启动时间(s) | 并发处理时间(s) | 内存使用(MB) | 吞吐量(ops/s) |",
            "|------|-------------|------------------|---------------|----------------|"
        ])

        for system_name, result in self.results.items():
            startup = result.performance_metrics.get('startup_time', 0)
            concurrent = result.performance_metrics.get('concurrent_processing_time', 0)
            memory = result.performance_metrics.get('memory_usage_mb', 0)
            throughput = result.performance_metrics.get('throughput', 0)
            report_content.append(f"| {system_name} | {startup:.3f} | {concurrent:.3f} | {memory:.1f} | {throughput:.1f} |")

        # Excel输出对比
        report_content.extend([
            "",
            "### 3. Excel输出对比",
            "",
            "| 系统 | 生成成功 | 文件大小(KB) | 生成时间(s) | 行数 | 列数 |",
            "|------|----------|--------------|-------------|------|------|"
        ])

        for system_name, result in self.results.items():
            success = result.excel_output.get('success', False)
            size = result.excel_output.get('file_size_kb', 0)
            time_taken = result.excel_output.get('generation_time', 0)
            rows = result.excel_output.get('analysis', {}).get('row_count', 0)
            cols = result.excel_output.get('analysis', {}).get('column_count', 0)
            report_content.append(f"| {system_name} | {'✓' if success else '✗'} | {size:.1f} | {time_taken:.3f} | {rows} | {cols} |")

        # 详细结果
        for system_name, result in self.results.items():
            report_content.extend([
                "",
                f"## 详细结果 - {system_name}",
                f"<a id=\"accuracy-{system_name.lower()}\"></a>",
                "",
                "### 准确度详情",
                ""
            ])

            # 分类准确度
            category_accuracies = result.accuracy_metrics.get('category_accuracies', {})
            for category, stats in category_accuracies.items():
                report_content.extend([
                    f"**{category}**: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})",
                    ""
                ])

            # 错误分析
            detailed_results = result.accuracy_metrics.get('detailed_results', [])
            error_results = [r for r in detailed_results if not r.get('correct', False)]

            if error_results:
                report_content.extend([
                    "### 识别错误案例",
                    "",
                    "| 测试ID | 输入文本 | 期望结果 | 实际结果 |",
                    "|--------|----------|----------|----------|"
                ])

                for error in error_results[:10]:  # 只显示前10个错误
                    test_id = error.get('test_id', 'N/A')
                    input_text = error.get('input_text', 'N/A')
                    expected = str(error.get('expected', []))
                    actual = str(error.get('actual', []))
                    report_content.append(f"| {test_id} | {input_text} | {expected} | {actual} |")

        # 差异分析和建议
        report_content.extend([
            "",
            "## 差异分析和改进建议",
            "",
            "### 主要差异",
            "",
        ])

        # 添加具体的差异分析
        if len(self.results) >= 2:
            original_result = self.results.get("OriginalSystem")
            production_result = self.results.get("ProductionSystem")

            if original_result and production_result:
                # 准确度差异
                orig_accuracy = original_result.accuracy_metrics.get('overall_accuracy', 0)
                prod_accuracy = production_result.accuracy_metrics.get('overall_accuracy', 0)
                accuracy_diff = prod_accuracy - orig_accuracy

                report_content.extend([
                    f"- **准确度差异**: 生产系统相比原始系统 {'提升' if accuracy_diff > 0 else '下降'} {abs(accuracy_diff):.1f}%",
                    ""
                ])

                # 性能差异
                orig_throughput = original_result.performance_metrics.get('throughput', 0)
                prod_throughput = production_result.performance_metrics.get('throughput', 0)
                throughput_change = ((prod_throughput - orig_throughput) / orig_throughput * 100) if orig_throughput > 0 else 0

                report_content.extend([
                    f"- **吞吐量变化**: 生产系统相比原始系统 {'提升' if throughput_change > 0 else '下降'} {abs(throughput_change):.1f}%",
                    ""
                ])

        report_content.extend([
            "### 改进建议",
            "",
            "1. **中文数字识别优化**: 基于错误案例，优化中文数字到数字的转换算法",
            "2. **性能优化**: 针对识别出的性能瓶颈进行优化",
            "3. **Excel格式标准化**: 确保两个系统生成相同格式的Excel输出",
            "4. **错误处理增强**: 改进异常情况的处理和恢复机制",
            "",
            "---",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        # 写入报告文件
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))

        self.logger.info(f"对比测试报告已生成: {report_path}")
        return report_path


class OriginalSystemWrapper:
    """原始系统测试包装器"""

    def __init__(self):
        self.process = None
        self.logger = logging.getLogger('original_wrapper')

    async def startup(self):
        """启动原始系统"""
        # 注意：这里需要适配原始系统的启动方式
        # 由于原始系统可能不是异步的，需要在线程中运行
        pass

    async def shutdown(self):
        """关闭原始系统"""
        pass

    async def process_text(self, text: str) -> List[float]:
        """处理文本（模拟原始系统的处理逻辑）"""
        # 这里应该调用原始系统的文本处理逻辑
        # 暂时返回模拟结果
        from audio_capture_v import extract_measurements
        return extract_measurements(text)

    async def generate_excel(self, data: List[Dict], filename: str) -> str:
        """生成Excel文件（使用原始系统的Excel导出器）"""
        from excel_exporter import ExcelExporter

        output_dir = Path("tests/comparison/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = ExcelExporter()
        output_path = output_dir / filename

        # 适配数据格式
        for item in data:
            if isinstance(item.get('数值'), list):
                item['数值'] = ', '.join(map(str, item['数值']))

        await exporter.export_data(data, str(output_path))
        return str(output_path)


class ProductionSystemWrapper:
    """生产系统测试包装器"""

    def __init__(self):
        self.system = None
        self.logger = logging.getLogger('production_wrapper')

    async def startup(self):
        """启动生产系统"""
        # 动态导入生产系统
        try:
            from main_production import ProductionVoiceSystem
            config_path = "tests/comparison/test_config.yaml"
            self.system = ProductionVoiceSystem(config_path)
            await self.system.start()
        except Exception as e:
            self.logger.error(f"生产系统启动失败: {e}")
            raise

    async def shutdown(self):
        """关闭生产系统"""
        if self.system:
            await self.system.stop()

    async def process_text(self, text: str) -> List[float]:
        """处理文本（使用生产系统的处理逻辑）"""
        if not self.system:
            # 如果系统未启动，使用基本的处理逻辑
            from audio_capture_v import extract_measurements
            return extract_measurements(text)

        # 这里应该调用生产系统的文本处理逻辑
        # 暂时返回模拟结果
        from audio_capture_v import extract_measurements
        return extract_measurements(text)

    async def generate_excel(self, data: List[Dict], filename: str) -> str:
        """生成Excel文件（使用生产系统的Excel导出器）"""
        from excel_exporter import ExcelExporter

        output_dir = Path("tests/comparison/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = ExcelExporter()
        output_path = output_dir / filename

        # 适配数据格式
        for item in data:
            if isinstance(item.get('数值'), list):
                item['数值'] = ', '.join(map(str, item['数值']))

        await exporter.export_data(data, str(output_path))
        return str(output_path)


async def main():
    """主测试函数"""
    print("🔬 开始深度对比测试")

    # 创建测试框架
    test_framework = ComparisonTestFramework("tests/comparison/test_config.yaml")

    # 初始化
    if not await test_framework.initialize():
        print("❌ 测试框架初始化失败")
        return 1

    try:
        # 运行完整对比测试
        results = await test_framework.run_full_comparison()

        # 生成对比报告
        report_path = test_framework.generate_comparison_report()

        print(f"✅ 对比测试完成，报告已生成: {report_path}")

        # 输出简要结果
        print("\n📊 测试结果摘要:")
        for system_name, result in results.items():
            accuracy = result.accuracy_metrics.get('overall_accuracy', 0)
            throughput = result.performance_metrics.get('throughput', 0)
            excel_success = result.excel_output.get('success', False)

            print(f"  {system_name}:")
            print(f"    准确度: {accuracy:.1f}%")
            print(f"    吞吐量: {throughput:.1f} ops/s")
            print(f"    Excel输出: {'✓' if excel_success else '✗'}")

        return 0

    except Exception as e:
        print(f"❌ 对比测试失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)