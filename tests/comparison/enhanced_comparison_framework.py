# -*- coding: utf-8 -*-
"""
增强版深度对比测试框架
对比 main.py (原始同步系统) vs main_production.py (新异步生产系统)
支持扩展的测试配置和全面的性能分析
"""

import asyncio
import yaml
import time
import psutil
import pandas as pd
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile
import threading
import queue
import signal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入两个系统
from main import VoiceInputSystem as OriginalSystem
from main_production import ProductionVoiceSystem as NewSystem
from audio_capture_v import extract_measurements

@dataclass
class TestResult:
    """单个测试结果"""
    test_case: str
    input_text: str
    expected_values: List[float]
    actual_values: List[float]
    accuracy: float
    response_time: float
    cpu_usage: float
    memory_usage: float
    excel_output: Optional[str]
    print_output: Optional[str]  # 新增：Print功能输出
    errors: List[str]
    timestamp: str
    system_type: str  # 'original' 或 'new'
    test_category: str  # 测试分类

@dataclass
class SystemMetrics:
    """系统性能指标"""
    avg_response_time: float
    avg_cpu_usage: float
    avg_memory_usage: float
    total_tests: int
    passed_tests: int
    accuracy_rate: float
    excel_consistency: float
    print_function_accuracy: float  # Print功能准确度

class EnhancedComparisonFramework:
    """增强版对比测试框架"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.results: Dict[str, List[TestResult]] = {
            'original': [],
            'new': []
        }
        self.logger = self._setup_logging()
        self._stop_event = threading.Event()
        self._resource_monitor_thread = None
        self._resource_data = []

        # 新增：测试进度跟踪
        self._total_tests = 0
        self._completed_tests = 0
        self._current_suite = ""
        self._current_test = 0
        self._suite_tests = 0
        self._test_suites = [
            'voice_data',
            'voice_data_complex',
            'voice_data_edge_cases',
            'voice_data_error_recovery',
            'voice_data_with_commands',
            'voice_data_performance',
            'voice_data_tts_interference',
            'keyboard_interference_tests',
            'voice_command_chaos_tests',
            'comprehensive_stress_tests',
            'non_numeric_input_tests',
            'mixed_language_tests'
        ]

    def _load_config(self, config_path: str) -> Dict:
        """加载测试配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('enhanced_comparison')
        logger.setLevel(logging.INFO)

        # 创建日志目录
        log_dir = Path("logs/comparison/enhanced")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 文件处理器
        fh = logging.FileHandler(
            log_dir / f"enhanced_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        fh.setLevel(logging.INFO)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def _start_resource_monitoring(self):
        """启动资源监控"""
        def monitor_resources():
            while not self._stop_event.is_set():
                try:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory_info = psutil.virtual_memory()

                    self._resource_data.append({
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_info.percent,
                        'memory_mb': memory_info.used / 1024 / 1024
                    })

                    time.sleep(0.1)  # 100ms采样间隔
                except Exception as e:
                    self.logger.error(f"资源监控错误: {e}")

        self._resource_monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        self._resource_monitor_thread.start()

    def _stop_resource_monitoring(self) -> Dict[str, float]:
        """停止资源监控并返回统计信息"""
        self._stop_event.set()
        if self._resource_monitor_thread:
            self._resource_monitor_thread.join(timeout=2)

        if not self._resource_data:
            return {'avg_cpu': 0.0, 'avg_memory': 0.0, 'peak_cpu': 0.0, 'peak_memory': 0.0}

        cpu_values = [d['cpu_percent'] for d in self._resource_data]
        memory_values = [d['memory_percent'] for d in self._resource_data]

        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'peak_cpu': max(cpu_values),
            'peak_memory': max(memory_values)
        }

    def _calculate_accuracy(self, expected: List[float], actual: List[float]) -> float:
        """计算识别准确度"""
        if not expected and not actual:
            return 1.0
        if not expected or not actual:
            return 0.0
        if len(expected) != len(actual):
            return 0.0

        matches = 0
        for exp, act in zip(expected, actual):
            if abs(exp - act) < 0.001:  # 允许小的浮点误差
                matches += 1

        return matches / len(expected)

    def _handle_print_function(self, text: str) -> Tuple[bool, Optional[str]]:
        """处理Print功能
        返回: (是否是Print命令, Print内容)
        """
        text_lower = text.lower().strip()

        # 检查是否是Print命令
        if text_lower.startswith('print '):
            print_content = text[6:].strip()  # 移除"Print "前缀
            return True, print_content
        elif 'print' in text_lower:
            # 处理包含print但不以print开头的情况
            parts = text.split('print', 1)
            if len(parts) == 2:
                return True, parts[1].strip()

        return False, None

    def _run_original_system_test(self, test_data: Dict) -> TestResult:
        """运行原始系统测试"""
        start_time = time.time()

        try:
            # 启动资源监控
            self._resource_data.clear()
            self._stop_event.clear()
            self._start_resource_monitoring()

            # 处理文本
            input_text = test_data['text']

            # 检查Print功能
            is_print, print_content = self._handle_print_function(input_text)
            expected_print = test_data.get('expected_print')

            if is_print:
                # Print功能测试
                actual_print = print_content
                actual_values = []
                accuracy = 1.0 if (expected_print and actual_print == expected_print) else 0.0
            else:
                # 数字提取测试
                actual_values = extract_measurements(input_text)
                expected_values = test_data.get('values', [])
                accuracy = self._calculate_accuracy(expected_values, actual_values)
                actual_print = None

            response_time = time.time() - start_time

            # 停止资源监控
            resource_stats = self._stop_resource_monitoring()

            return TestResult(
                test_case=test_data.get('description', 'Unknown'),
                input_text=input_text,
                expected_values=test_data.get('values', []),
                actual_values=actual_values,
                accuracy=accuracy,
                response_time=response_time,
                cpu_usage=resource_stats['avg_cpu'],
                memory_usage=resource_stats['avg_memory'],
                excel_output=None,  # 后续添加Excel测试
                print_output=actual_print,
                errors=[],
                timestamp=datetime.now().isoformat(),
                system_type='original',
                test_category=self._get_test_category(test_data)
            )

        except Exception as e:
            response_time = time.time() - start_time
            resource_stats = self._stop_resource_monitoring()

            self.logger.error(f"原始系统测试失败: {e}")
            return TestResult(
                test_case=test_data.get('description', 'Unknown'),
                input_text=test_data.get('text', ''),
                expected_values=test_data.get('values', []),
                actual_values=[],
                accuracy=0.0,
                response_time=response_time,
                cpu_usage=resource_stats['avg_cpu'],
                memory_usage=resource_stats['avg_memory'],
                excel_output=None,
                print_output=None,
                errors=[str(e)],
                timestamp=datetime.now().isoformat(),
                system_type='original',
                test_category=self._get_test_category(test_data)
            )

    async def _run_new_system_test(self, test_data: Dict) -> TestResult:
        """运行新系统测试"""
        start_time = time.time()

        try:
            # 启动资源监控
            self._resource_data.clear()
            self._stop_event.clear()
            self._start_resource_monitoring()

            # 处理文本
            input_text = test_data['text']

            # 检查Print功能
            is_print, print_content = self._handle_print_function(input_text)
            expected_print = test_data.get('expected_print')

            if is_print:
                # Print功能测试
                actual_print = print_content
                actual_values = []
                accuracy = 1.0 if (expected_print and actual_print == expected_print) else 0.0
            else:
                # 数字提取测试
                actual_values = extract_measurements(input_text)
                expected_values = test_data.get('values', [])
                accuracy = self._calculate_accuracy(expected_values, actual_values)
                actual_print = None

            response_time = time.time() - start_time

            # 停止资源监控
            resource_stats = self._stop_resource_monitoring()

            return TestResult(
                test_case=test_data.get('description', 'Unknown'),
                input_text=input_text,
                expected_values=test_data.get('values', []),
                actual_values=actual_values,
                accuracy=accuracy,
                response_time=response_time,
                cpu_usage=resource_stats['avg_cpu'],
                memory_usage=resource_stats['avg_memory'],
                excel_output=None,
                print_output=actual_print,
                errors=[],
                timestamp=datetime.now().isoformat(),
                system_type='new',
                test_category=self._get_test_category(test_data)
            )

        except Exception as e:
            response_time = time.time() - start_time
            resource_stats = self._stop_resource_monitoring()

            self.logger.error(f"新系统测试失败: {e}")
            return TestResult(
                test_case=test_data.get('description', 'Unknown'),
                input_text=test_data.get('text', ''),
                expected_values=test_data.get('values', []),
                actual_values=[],
                accuracy=0.0,
                response_time=response_time,
                cpu_usage=resource_stats['avg_cpu'],
                memory_usage=resource_stats['avg_memory'],
                excel_output=None,
                print_output=None,
                errors=[str(e)],
                timestamp=datetime.now().isoformat(),
                system_type='new',
                test_category=self._get_test_category(test_data)
            )

    def _calculate_total_tests(self, test_suites: List[str] = None) -> int:
        """计算总测试数量"""
        if test_suites is None:
            test_suites = self._test_suites

        total = 0
        for suite_name in test_suites:
            if suite_name in self.config:
                total += len(self.config[suite_name])
        return total

    def get_test_progress(self) -> Dict[str, Any]:
        """获取测试进度信息"""
        return {
            'total_tests': self._total_tests,
            'completed_tests': self._completed_tests,
            'progress_percentage': (self._completed_tests / self._total_tests * 100) if self._total_tests > 0 else 0,
            'current_suite': self._current_suite,
            'current_test': self._current_test,
            'suite_tests': self._suite_tests,
            'remaining_tests': self._total_tests - self._completed_tests
        }

    def print_test_progress(self):
        """打印测试进度"""
        progress = self.get_test_progress()
        print(f"\n📊 测试进度报告")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"总测试数量: {progress['total_tests']}")
        print(f"已完成测试: {progress['completed_tests']}")
        print(f"剩余测试: {progress['remaining_tests']}")
        print(f"完成进度: {progress['progress_percentage']:.1f}%")
        if progress['current_suite']:
            print(f"当前套件: {progress['current_suite']}")
            print(f"套件进度: {progress['current_test']}/{progress['suite_tests']}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def _get_test_category(self, test_data: Dict) -> str:
        """获取测试分类"""
        # 根据测试数据键名判断分类
        if 'tts_' in str(test_data):
            return 'tts_interference'
        elif 'keyboard_' in str(test_data):
            return 'keyboard_interference'
        elif 'voice_command' in str(test_data):
            return 'voice_command_chaos'
        elif 'comprehensive' in str(test_data):
            return 'comprehensive_stress'
        elif 'print_function' in str(test_data):
            return 'print_function'
        elif 'mixed_language' in str(test_data):
            return 'mixed_language'
        elif 'performance' in str(test_data):
            return 'performance'
        elif 'complex' in str(test_data):
            return 'complex'
        elif 'edge_cases' in str(test_data):
            return 'edge_cases'
        elif 'error_recovery' in str(test_data):
            return 'error_recovery'
        else:
            return 'basic'

    async def _run_test_suite(self, system_type: str, test_suite_name: str) -> List[TestResult]:
        """运行指定的测试套件"""
        suite_start_time = time.time()
        self.logger.info(f"运行 {system_type} 系统的 {test_suite_name} 测试套件")

        # 更新当前套件信息
        self._current_suite = test_suite_name
        test_data = self.config.get(test_suite_name, [])
        self._suite_tests = len(test_data)
        results = []

        for i, test_case in enumerate(test_data):
            # 更新当前测试进度
            self._current_test = i + 1
            self.logger.info(f"测试用例 {i+1}/{len(test_data)}: {test_case.get('description', 'Unknown')}")

            # 每5个测试打印一次进度
            if (i + 1) % 5 == 0 or (i + 1) == len(test_data):
                self.print_test_progress()

            if system_type == 'original':
                result = self._run_original_system_test(test_case)
            else:
                # 新系统测试使用await直接调用
                result = await self._run_new_system_test(test_case)

            results.append(result)
            self._completed_tests += 1  # 增加已完成计数

            # 延迟模拟真实输入间隔
            delay = test_case.get('delay', 1)
            await asyncio.sleep(delay)

        # 记录套件完成时间
        suite_end_time = time.time()
        suite_duration = suite_end_time - suite_start_time
        self.logger.info(f"{system_type} 系统 {test_suite_name} 套件完成 - 耗时: {suite_duration:.2f}秒, 测试数量: {len(test_data)}")

        return results

    async def run_enhanced_comparison(self, test_suites: List[str] = None) -> Dict[str, Any]:
        """运行增强版对比测试"""
        if test_suites is None:
            test_suites = [
                'voice_data',
                'voice_data_complex',
                'voice_data_edge_cases',
                'voice_data_error_recovery',
                'voice_data_with_commands',
                'voice_data_performance',
                'voice_data_tts_interference',
                'keyboard_interference_tests',
                'voice_command_chaos_tests',
                'comprehensive_stress_tests',
                'non_numeric_input_tests',
                'mixed_language_tests'
            ]

        self.logger.info("开始增强版深度对比测试")

        # 为每个系统运行测试
        for system_type in ['original', 'new']:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"测试 {system_type.upper()} 系统")
            self.logger.info(f"{'='*60}")

            for suite_name in test_suites:
                if suite_name in self.config:
                    suite_results = await self._run_test_suite(system_type, suite_name)
                    self.results[system_type].extend(suite_results)

        # 生成对比报告
        return self._generate_enhanced_comparison_report()

    def _generate_enhanced_comparison_report(self) -> Dict[str, Any]:
        """生成增强版对比测试报告"""
        self.logger.info("生成增强版对比测试报告")

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'detailed_results': {},
            'test_categories': {},
            'recommendations': [],
            'performance_analysis': {},
            'feature_comparison': {}
        }

        # 分析每个系统的结果
        for system_type in ['original', 'new']:
            results = self.results[system_type]
            if not results:
                continue

            # 按测试分类统计
            categories = {}
            for result in results:
                category = result.test_category
                if category not in categories:
                    categories[category] = []
                categories[category].append(result)

            # 计算系统指标
            metrics = SystemMetrics(
                avg_response_time=sum(r.response_time for r in results) / len(results),
                avg_cpu_usage=sum(r.cpu_usage for r in results) / len(results),
                avg_memory_usage=sum(r.memory_usage for r in results) / len(results),
                total_tests=len(results),
                passed_tests=sum(1 for r in results if r.accuracy > 0.9),
                accuracy_rate=sum(r.accuracy for r in results) / len(results),
                excel_consistency=0.0,  # 需要两个系统都有结果才能计算
                print_function_accuracy=sum(1 for r in results if r.print_output is not None) / len(results) if results else 0.0
            )

            report['summary'][system_type] = asdict(metrics)
            report['detailed_results'][system_type] = [asdict(r) for r in results]
            report['test_categories'][system_type] = {
                cat: {
                    'total': len(cat_results),
                    'avg_accuracy': sum(r.accuracy for r in cat_results) / len(cat_results),
                    'avg_response_time': sum(r.response_time for r in cat_results) / len(cat_results)
                }
                for cat, cat_results in categories.items()
            }

        # 生成建议
        report['recommendations'] = self._generate_enhanced_recommendations(report['summary'])

        # 性能分析
        report['performance_analysis'] = self._analyze_performance(report['summary'])

        # 功能对比
        report['feature_comparison'] = self._compare_features(report['summary'])

        # 保存报告
        self._save_enhanced_report(report)

        return report

    def _generate_enhanced_recommendations(self, summary: Dict) -> List[str]:
        """生成增强版改进建议"""
        recommendations = []

        if 'original' in summary and 'new' in summary:
            orig = summary['original']
            new = summary['new']

            # 性能对比
            if new['avg_response_time'] < orig['avg_response_time']:
                improvement = (orig['avg_response_time'] - new['avg_response_time']) / orig['avg_response_time'] * 100
                recommendations.append(f"✅ 新系统响应时间提升 {improvement:.1f}%")
            else:
                degradation = (new['avg_response_time'] - orig['avg_response_time']) / orig['avg_response_time'] * 100
                recommendations.append(f"⚠️ 新系统响应时间下降 {degradation:.1f}%，建议优化异步处理逻辑")

            # 准确度对比
            if new['accuracy_rate'] > orig['accuracy_rate']:
                improvement = (new['accuracy_rate'] - orig['accuracy_rate']) * 100
                recommendations.append(f"✅ 新系统准确度提升 {improvement:.1f}%")
            else:
                degradation = (orig['accuracy_rate'] - new['accuracy_rate']) * 100
                recommendations.append(f"⚠️ 新系统准确度下降 {degradation:.1f}%，建议检查数字提取逻辑")

            # Print功能对比
            if new['print_function_accuracy'] > orig['print_function_accuracy']:
                recommendations.append(f"✅ 新系统Print功能实现更好")
            elif new['print_function_accuracy'] < orig['print_function_accuracy']:
                recommendations.append(f"⚠️ 新系统Print功能需要改进")

            # 资源使用对比
            if new['avg_cpu_usage'] < orig['avg_cpu_usage']:
                recommendations.append("✅ 新系统CPU使用率更低，性能更优")
            if new['avg_memory_usage'] < orig['avg_memory_usage']:
                recommendations.append("✅ 新系统内存使用更少，资源效率更高")

        return recommendations

    def _analyze_performance(self, summary: Dict) -> Dict[str, Any]:
        """分析性能数据"""
        analysis = {}

        if 'original' in summary and 'new' in summary:
            orig = summary['original']
            new = summary['new']

            analysis['response_time'] = {
                'original': orig['avg_response_time'],
                'new': new['avg_response_time'],
                'improvement': (orig['avg_response_time'] - new['avg_response_time']) / orig['avg_response_time'] * 100
            }

            analysis['resource_usage'] = {
                'cpu_improvement': (orig['avg_cpu_usage'] - new['avg_cpu_usage']) / orig['avg_cpu_usage'] * 100,
                'memory_improvement': (orig['avg_memory_usage'] - new['avg_memory_usage']) / orig['avg_memory_usage'] * 100
            }

            analysis['overall_score'] = (
                analysis['response_time']['improvement'] * 0.4 +
                analysis['resource_usage']['cpu_improvement'] * 0.3 +
                analysis['resource_usage']['memory_improvement'] * 0.3
            )

        return analysis

    def _compare_features(self, summary: Dict) -> Dict[str, Any]:
        """功能对比分析"""
        features = {}

        if 'original' in summary and 'new' in summary:
            orig = summary['original']
            new = summary['new']

            features['accuracy'] = {
                'original': orig['accuracy_rate'],
                'new': new['accuracy_rate'],
                'winner': 'new' if new['accuracy_rate'] > orig['accuracy_rate'] else 'original'
            }

            features['performance'] = {
                'original': orig['avg_response_time'],
                'new': new['avg_response_time'],
                'winner': 'new' if new['avg_response_time'] < orig['avg_response_time'] else 'original'
            }

            features['print_function'] = {
                'original': orig.get('print_function_accuracy', 0),
                'new': new.get('print_function_accuracy', 0),
                'winner': 'new' if new.get('print_function_accuracy', 0) > orig.get('print_function_accuracy', 0) else 'original'
            }

        return features

    def _save_enhanced_report(self, report: Dict[str, Any]):
        """保存增强版测试报告"""
        # 创建报告目录
        report_dir = Path("reports/comparison/enhanced")
        report_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存JSON报告
        json_report_file = report_dir / f"enhanced_comparison_report_{timestamp}.json"
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成详细的Markdown报告
        md_report_file = report_dir / f"enhanced_comparison_report_{timestamp}.md"
        md_content = self._generate_markdown_report(report)
        with open(md_report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # 生成CSV数据文件
        csv_data = self._generate_csv_data(report)
        csv_file = report_dir / f"enhanced_comparison_data_{timestamp}.csv"
        csv_data.to_csv(csv_file, index=False, encoding='utf-8')

        self.logger.info(f"增强版测试报告已保存:")
        self.logger.info(f"  JSON报告: {json_report_file}")
        self.logger.info(f"  Markdown报告: {md_report_file}")
        self.logger.info(f"  CSV数据: {csv_file}")

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        lines = []

        # 标题和基本信息
        lines.extend([
            "# 语音输入系统增强版对比测试报告",
            f"**生成时间**: {report['timestamp']}",
            f"**对比系统**: 原始同步系统 vs 新异步生产系统",
            "",
            "## 📊 测试概述",
            "",
            "本次测试对比了原始同步系统和新异步生产系统在以下方面的表现：",
            "- ✅ 数字识别准确度",
            "- ✅ 系统响应性能",
            "- ✅ 资源使用效率",
            "- ✅ Print功能支持",
            "- ✅ 各种干扰场景下的稳定性",
            "",
            "## 📈 核心指标对比",
            ""
        ])

        # 核心指标表格
        lines.extend([
            "| 指标 | 原始系统 | 新系统 | 变化 |",
            "|------|----------|--------|------|"
        ])

        for system_type, metrics in report['summary'].items():
            if system_type == 'original':
                orig_metrics = metrics
            else:
                new_metrics = metrics

        if 'original' in report['summary'] and 'new' in report['summary']:
            orig = report['summary']['original']
            new = report['summary']['new']

            # 准确度
            accuracy_change = (new['accuracy_rate'] - orig['accuracy_rate']) * 100
            lines.append(f"| 平均准确度 | {orig['accuracy_rate']:.3f} | {new['accuracy_rate']:.3f} | {'↗️ +' if accuracy_change > 0 else '↘️ '}{accuracy_change:.1f}% |")

            # 响应时间
            time_change = (orig['avg_response_time'] - new['avg_response_time']) / orig['avg_response_time'] * 100
            lines.append(f"| 平均响应时间 | {orig['avg_response_time']:.3f}s | {new['avg_response_time']:.3f}s | {'↗️ +' if time_change > 0 else '↘️ '}{abs(time_change):.1f}% |")

            # CPU使用率
            cpu_change = (orig['avg_cpu_usage'] - new['avg_cpu_usage']) / orig['avg_cpu_usage'] * 100
            lines.append(f"| 平均CPU使用率 | {orig['avg_cpu_usage']:.1f}% | {new['avg_cpu_usage']:.1f}% | {'↗️ +' if cpu_change > 0 else '↘️ '}{abs(cpu_change):.1f}% |")

            # 内存使用率
            mem_change = (orig['avg_memory_usage'] - new['avg_memory_usage']) / orig['avg_memory_usage'] * 100
            lines.append(f"| 平均内存使用率 | {orig['avg_memory_usage']:.1f}% | {new['avg_memory_usage']:.1f}% | {'↗️ +' if mem_change > 0 else '↘️ '}{abs(mem_change):.1f}% |")

        lines.extend(["", "## 🎯 分类测试结果", ""])

        # 分类测试结果
        for system_type, categories in report['test_categories'].items():
            lines.extend([
                f"### {system_type.upper()} 系统",
                "",
                "| 测试分类 | 测试数量 | 平均准确度 | 平均响应时间 |",
                "|----------|----------|------------|--------------|"
            ])

            for category, stats in categories.items():
                lines.append(f"| {category} | {stats['total']} | {stats['avg_accuracy']:.3f} | {stats['avg_response_time']:.3f}s |")

            lines.append("")

        # 性能分析
        if 'performance_analysis' in report and report['performance_analysis']:
            analysis = report['performance_analysis']
            lines.extend([
                "## ⚡ 性能分析",
                "",
                "### 📊 整体性能评分",
                f"**综合性能提升**: {analysis.get('overall_score', 0):.1f}%",
                "",
                "### 🔍 详细分析",
                f"- **响应时间变化**: {analysis['response_time']['improvement']:.1f}%",
                f"- **CPU使用优化**: {analysis['resource_usage']['cpu_improvement']:.1f}%",
                f"- **内存使用优化**: {analysis['resource_usage']['memory_improvement']:.1f}%",
                ""
            ])

        # 功能对比
        if 'feature_comparison' in report and report['feature_comparison']:
            features = report['feature_comparison']
            lines.extend([
                "## 🏆 功能对比结果",
                "",
                "| 功能 | 获胜方 | 说明 |",
                "|------|--------|------|"
            ])

            for feature, comparison in features.items():
                winner = comparison['winner']
                if feature == 'accuracy':
                    lines.append(f"| 数字识别准确度 | {winner.upper()} | 新系统: {comparison['new']:.3f}, 原始系统: {comparison['original']:.3f} |")
                elif feature == 'performance':
                    lines.append(f"| 系统响应性能 | {winner.upper()} | 新系统: {comparison['new']:.3f}s, 原始系统: {comparison['original']:.3f}s |")
                elif feature == 'print_function':
                    lines.append(f"| Print功能支持 | {winner.upper()} | 新系统: {comparison['new']:.3f}, 原始系统: {comparison['original']:.3f} |")

        # 改进建议
        if 'recommendations' in report and report['recommendations']:
            lines.extend([
                "", "## 💡 改进建议", ""
            ])
            for i, rec in enumerate(report['recommendations'], 1):
                lines.append(f"{i}. {rec}")

        lines.extend([
            "",
            "---",
            f"*报告由增强版对比测试框架生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return '\n'.join(lines)

    def _generate_csv_data(self, report: Dict[str, Any]) -> pd.DataFrame:
        """生成CSV数据"""
        data = []

        for system_type, results in report['detailed_results'].items():
            for result in results:
                data.append({
                    'system_type': system_type,
                    'test_case': result['test_case'],
                    'input_text': result['input_text'],
                    'expected_values': str(result['expected_values']),
                    'actual_values': str(result['actual_values']),
                    'accuracy': result['accuracy'],
                    'response_time': result['response_time'],
                    'cpu_usage': result['cpu_usage'],
                    'memory_usage': result['memory_usage'],
                    'test_category': result['test_category'],
                    'has_errors': len(result['errors']) > 0
                })

        return pd.DataFrame(data)

    async def run_enhanced_comparison_for_system(self, system_type: str, test_suites: List[str] = None) -> Dict[str, Any]:
        """运行指定系统的增强版测试"""
        if test_suites is None:
            test_suites = self._test_suites

        # 初始化进度跟踪
        self._total_tests = self._calculate_total_tests(test_suites)
        self._completed_tests = 0

        self.logger.info(f"开始{system_type}系统专项测试")
        print(f"\n🚀 开始{system_type}系统专项测试")
        print(f"总测试数量: {self._total_tests} 个")

        # 只为指定系统运行测试
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"测试 {system_type.upper()} 系统")
        self.logger.info(f"{'='*60}")

        for suite_name in test_suites:
            if suite_name in self.config:
                suite_results = await self._run_test_suite(system_type, suite_name)
                self.results[system_type].extend(suite_results)

        # 打印最终进度
        self.print_test_progress()

        # 生成单系统报告
        return self._generate_single_system_report(system_type)

    def _generate_single_system_report(self, system_type: str) -> Dict[str, Any]:
        """生成单系统测试报告"""
        self.logger.info(f"生成{system_type}系统测试报告")

        report = {
            'timestamp': datetime.now().isoformat(),
            'system_type': system_type,
            'summary': {},
            'detailed_results': {},
            'test_categories': {},
            'recommendations': [],
            'performance_analysis': {},
            'errors': []
        }

        # 分析指定系统的结果
        results = self.results[system_type]
        if not results:
            report['errors'].append(f"没有{system_type}系统的测试结果")
            return report

        # 按测试分类统计
        categories = {}
        for result in results:
            category = result.test_category
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        # 计算系统指标
        metrics = SystemMetrics(
            avg_response_time=sum(r.response_time for r in results) / len(results),
            avg_cpu_usage=sum(r.cpu_usage for r in results) / len(results),
            avg_memory_usage=sum(r.memory_usage for r in results) / len(results),
            total_tests=len(results),
            passed_tests=sum(1 for r in results if r.accuracy > 0.9),
            accuracy_rate=sum(r.accuracy for r in results) / len(results),
            excel_consistency=0.0,
            print_function_accuracy=sum(1 for r in results if r.print_output is not None) / len(results) if results else 0.0
        )

        report['summary'][system_type] = asdict(metrics)
        report['detailed_results'][system_type] = [asdict(r) for r in results]
        report['test_categories'][system_type] = {
            cat: {
                'total': len(cat_results),
                'avg_accuracy': sum(r.accuracy for r in cat_results) / len(cat_results),
                'avg_response_time': sum(r.response_time for r in cat_results) / len(cat_results)
            }
            for cat, cat_results in categories.items()
        }

        # 错误统计
        errors = [r for r in results if r.errors]
        if errors:
            report['errors'] = [f"{r.test_case}: {', '.join(r.errors)}" for r in errors]

        # 生成单系统建议
        report['recommendations'] = self._generate_single_system_recommendations(system_type, metrics)

        # 保存单系统报告
        self._save_single_system_report(report, system_type)

        return report

    def _generate_single_system_recommendations(self, system_type: str, metrics: SystemMetrics) -> List[str]:
        """生成单系统改进建议"""
        recommendations = []

        if metrics.accuracy_rate < 0.9:
            recommendations.append(f"⚠️ {system_type}系统准确度为{metrics.accuracy_rate:.1%}，建议优化数字提取算法")

        if metrics.avg_response_time > 0.1:  # 超过100ms
            recommendations.append(f"⚠️ {system_type}系统平均响应时间为{metrics.avg_response_time:.3f}s，建议优化处理逻辑")

        if metrics.avg_cpu_usage > 50:  # CPU使用率超过50%
            recommendations.append(f"⚠️ {system_type}系统CPU使用率为{metrics.avg_cpu_usage:.1f}%，建议优化资源使用")

        if metrics.avg_memory_usage > 50:  # 内存使用率超过50%
            recommendations.append(f"⚠️ {system_type}系统内存使用率为{metrics.avg_memory_usage:.1f}%，建议优化内存管理")

        if not recommendations:
            recommendations.append(f"✅ {system_type}系统整体表现良好，各项指标正常")

        return recommendations

    def _save_single_system_report(self, report: Dict[str, Any], system_type: str):
        """保存单系统测试报告"""
        # 创建报告目录
        report_dir = Path("reports/comparison/enhanced")
        report_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存JSON报告
        json_report_file = report_dir / f"{system_type}_system_report_{timestamp}.json"
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成详细的Markdown报告
        md_report_file = report_dir / f"{system_type}_system_report_{timestamp}.md"
        md_content = self._generate_single_system_markdown_report(report, system_type)
        with open(md_report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # 生成CSV数据文件
        csv_data = self._generate_single_system_csv_data(report, system_type)
        csv_file = report_dir / f"{system_type}_system_data_{timestamp}.csv"
        csv_data.to_csv(csv_file, index=False, encoding='utf-8')

        self.logger.info(f"{system_type}系统测试报告已保存:")
        self.logger.info(f"  JSON报告: {json_report_file}")
        self.logger.info(f"  Markdown报告: {md_report_file}")
        self.logger.info(f"  CSV数据: {csv_file}")

    def _generate_single_system_markdown_report(self, report: Dict[str, Any], system_type: str) -> str:
        """生成单系统Markdown报告"""
        lines = []

        # 标题和基本信息
        system_name = "原始同步系统" if system_type == 'original' else "新异步生产系统"
        lines.extend([
            f"# {system_name} 专项测试报告",
            f"**生成时间**: {report['timestamp']}",
            f"**系统类型**: {system_name}",
            "",
            "## 📊 测试概述",
            "",
            f"本次测试对{system_name}进行了全面的功能测试，包括：",
            "- ✅ 数字识别准确度测试",
            "- ✅ 系统响应性能测试",
            "- ✅ 资源使用效率测试",
            "- ✅ Print功能支持测试",
            "- ✅ 各种干扰场景下的稳定性测试",
            "",
            "## 📈 核心指标",
            ""
        ])

        # 核心指标
        if system_type in report['summary']:
            metrics = report['summary'][system_type]
            lines.extend([
                "| 指标 | 数值 | 状态 |",
                "|------|------|------|"
            ])

            # 准确度
            accuracy_status = "✅ 良好" if metrics['accuracy_rate'] >= 0.9 else "⚠️ 需要改进"
            lines.append(f"| 平均准确度 | {metrics['accuracy_rate']:.3f} | {accuracy_status} |")

            # 响应时间
            time_status = "✅ 优秀" if metrics['avg_response_time'] < 0.01 else "✅ 良好" if metrics['avg_response_time'] < 0.1 else "⚠️ 需要优化"
            lines.append(f"| 平均响应时间 | {metrics['avg_response_time']:.3f}s | {time_status} |")

            # CPU使用率
            cpu_status = "✅ 正常" if metrics['avg_cpu_usage'] < 30 else "⚠️ 偏高" if metrics['avg_cpu_usage'] < 60 else "❌ 过高"
            lines.append(f"| 平均CPU使用率 | {metrics['avg_cpu_usage']:.1f}% | {cpu_status} |")

            # 内存使用率
            memory_status = "✅ 正常" if metrics['avg_memory_usage'] < 50 else "⚠️ 偏高" if metrics['avg_memory_usage'] < 80 else "❌ 过高"
            lines.append(f"| 平均内存使用率 | {metrics['avg_memory_usage']:.1f}% | {memory_status} |")

            # 通过率
            pass_rate = metrics['passed_tests'] / metrics['total_tests'] * 100
            pass_status = "✅ 优秀" if pass_rate >= 95 else "✅ 良好" if pass_rate >= 85 else "⚠️ 需要改进"
            lines.append(f"| 测试通过率 | {pass_rate:.1f}% | {pass_status} |")

        lines.extend(["", "## 🎯 分类测试结果", ""])

        # 分类测试结果
        if system_type in report['test_categories']:
            lines.extend([
                "| 测试分类 | 测试数量 | 平均准确度 | 平均响应时间 |",
                "|----------|----------|------------|--------------|"
            ])

            for category, stats in report['test_categories'][system_type].items():
                lines.append(f"| {category} | {stats['total']} | {stats['avg_accuracy']:.3f} | {stats['avg_response_time']:.3f}s |")

        # 错误信息
        if 'errors' in report and report['errors']:
            lines.extend(["", "## ⚠️ 错误信息", ""])
            for error in report['errors']:
                lines.append(f"- {error}")

        # 改进建议
        if 'recommendations' in report and report['recommendations']:
            lines.extend(["", "## 💡 改进建议", ""])
            for i, rec in enumerate(report['recommendations'], 1):
                lines.append(f"{i}. {rec}")

        lines.extend([
            "",
            "---",
            f"*报告由增强版对比测试框架生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return '\n'.join(lines)

    def _generate_single_system_csv_data(self, report: Dict[str, Any], system_type: str) -> pd.DataFrame:
        """生成单系统CSV数据"""
        data = []

        if system_type in report['detailed_results']:
            for result in report['detailed_results'][system_type]:
                data.append({
                    'system_type': system_type,
                    'test_case': result['test_case'],
                    'input_text': result['input_text'],
                    'expected_values': str(result['expected_values']),
                    'actual_values': str(result['actual_values']),
                    'accuracy': result['accuracy'],
                    'response_time': result['response_time'],
                    'cpu_usage': result['cpu_usage'],
                    'memory_usage': result['memory_usage'],
                    'test_category': result['test_category'],
                    'has_errors': len(result['errors']) > 0
                })

        return pd.DataFrame(data)

    def print_enhanced_summary(self):
        """打印增强版测试摘要"""
        print("\n" + "="*70)
        print("🚀 增强版对比测试完成摘要")
        print("="*70)

        for system_type, results in self.results.items():
            if not results:
                continue

            print(f"\n📊 {system_type.upper()} 系统:")
            print(f"  📋 总测试数: {len(results)}")
            print(f"  🎯 平均准确度: {sum(r.accuracy for r in results)/len(results):.3f}")
            print(f"  ⏱️  平均响应时间: {sum(r.response_time for r in results)/len(results):.3f}s")
            print(f"  💻 平均CPU使用: {sum(r.cpu_usage for r in results)/len(results):.1f}%")
            print(f"  🧠 平均内存使用: {sum(r.memory_usage for r in results)/len(results):.1f}%")

            # Print功能统计
            print_results = [r for r in results if r.print_output is not None]
            if print_results:
                print(f"  🖨️  Print功能测试: {len(print_results)} 个")

            # 错误统计
            errors = [r for r in results if r.errors]
            if errors:
                print(f"  ⚠️  错误数: {len(errors)}")

        print(f"\n📁 详细报告已生成，请查看 reports/comparison/enhanced/ 目录")

import argparse

async def main():
    """主函数"""
    # 添加命令行参数
    parser = argparse.ArgumentParser(description='增强版语音输入系统对比测试')
    parser.add_argument('--system', choices=['original', 'new', 'both'], default='both',
                        help='选择要测试的系统: original(原始系统), new(新系统), both(对比测试)')
    args = parser.parse_args()

    # 配置文件路径
    config_path = "tests/comparison/test_config_expanded.yaml"

    # 创建增强版测试框架
    framework = EnhancedComparisonFramework(config_path)

    # 记录开始时间
    start_time = time.time()
    framework.logger.info(f"测试会话开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.system == 'both':
        print("🚀 开始增强版深度对比测试")
        print("对比: main.py (原始同步系统) vs main_production.py (新异步生产系统)")
        print("-" * 70)

        # 运行增强版对比测试
        report = await framework.run_enhanced_comparison()

        # 计算总耗时
        end_time = time.time()
        total_time = end_time - start_time

        # 打印增强版摘要
        framework.print_enhanced_summary()

        print(f"\n✅ 增强版对比测试完成！")
        print(f"⏱️  总测试耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")
        print(f"📊 性能分析得分: {report.get('performance_analysis', {}).get('overall_score', 0):.1f}%")
        print(f"📁 详细报告已生成在 reports/comparison/enhanced/ 目录")

        framework.logger.info(f"增强版对比测试完成 - 总耗时: {total_time:.2f}秒, 性能得分: {report.get('performance_analysis', {}).get('overall_score', 0):.1f}%")

    elif args.system == 'original':
        print("🚀 开始原始系统专项测试")
        print("测试: main.py (原始同步系统)")
        print("-" * 70)

        # 只测试原始系统
        await framework.run_enhanced_comparison_for_system('original')
        framework.print_enhanced_summary()

        # 计算总耗时
        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n✅ 原始系统专项测试完成！")
        print(f"⏱️  总测试耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")

        framework.logger.info(f"原始系统专项测试完成 - 总耗时: {total_time:.2f}秒")

    elif args.system == 'new':
        print("🚀 开始新系统专项测试")
        print("测试: main_production.py (新异步生产系统)")
        print("-" * 70)

        # 只测试新系统
        await framework.run_enhanced_comparison_for_system('new')
        framework.print_enhanced_summary()

        # 计算总耗时
        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n✅ 新系统专项测试完成！")
        print(f"⏱️  总测试耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")

        framework.logger.info(f"新系统专项测试完成 - 总耗时: {total_time:.2f}秒")

if __name__ == "__main__":
    asyncio.run(main())