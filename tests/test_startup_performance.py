#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动性能测试脚本
用于对比原版与优化版FunASR语音识别系统的启动性能
"""

import time
import os
import sys
import subprocess
import statistics
import traceback
from typing import Dict, List, Tuple, Optional
import json
import psutil
import threading
import tempfile
from datetime import datetime

class StartupPerformanceTester:
    """启动性能测试器"""

    def __init__(self):
        self.results = {
            'original': [],
            'optimized': []
        }
        self.test_reports = {}

    def measure_startup_time(self, script_path: str, version_name: str,
                           iterations: int = 5) -> Dict:
        """
        测量启动时间

        Args:
            script_path: 测试脚本路径
            version_name: 版本名称
            iterations: 测试迭代次数

        Returns:
            测试结果字典
        """
        print(f"\n🔍 测试 {version_name} 版本启动性能...")
        print(f"   测试脚本: {script_path}")
        print(f"   测试次数: {iterations}")

        startup_times = []
        memory_usages = []
        success_count = 0

        for i in range(iterations):
            print(f"   第 {i+1}/{iterations} 次测试...")

            try:
                # 记录开始时间和内存
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                # 创建测试脚本
                test_script = self._create_test_script(script_path, version_name)

                # 运行测试（带超时）
                result = subprocess.run(
                    [sys.executable, test_script],
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60秒超时
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )

                # 记录结束时间和内存
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                startup_time = end_time - start_time
                memory_usage = end_memory - start_memory

                if result.returncode == 0:
                    startup_times.append(startup_time)
                    memory_usages.append(memory_usage)
                    success_count += 1
                    print(f"      ✅ 启动成功 - 耗时: {startup_time:.2f}秒, 内存: {memory_usage:.1f}MB")
                else:
                    print(f"      ❌ 启动失败 - 返回码: {result.returncode}")
                    print(f"      错误输出: {result.stderr[:200]}...")

                # 清理临时文件
                try:
                    os.remove(test_script)
                except:
                    pass

            except subprocess.TimeoutExpired:
                print(f"      ⏰ 启动超时 (>60秒)")
            except Exception as e:
                print(f"      ❌ 测试异常: {e}")

            # 短暂休息，避免资源竞争
            time.sleep(2)

        # 计算统计结果
        if startup_times:
            stats = {
                'success_count': success_count,
                'total_tests': iterations,
                'startup_times': {
                    'mean': statistics.mean(startup_times),
                    'median': statistics.median(startup_times),
                    'min': min(startup_times),
                    'max': max(startup_times),
                    'stdev': statistics.stdev(startup_times) if len(startup_times) > 1 else 0,
                    'all_times': startup_times
                },
                'memory_usage': {
                    'mean': statistics.mean(memory_usages),
                    'min': min(memory_usages),
                    'max': max(memory_usages)
                }
            }
        else:
            stats = {
                'success_count': 0,
                'total_tests': iterations,
                'error': '所有测试都失败了'
            }

        return stats

    def _create_test_script(self, target_script: str, version_name: str) -> str:
        """创建测试脚本"""
        test_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的启动性能测试脚本
测试目标: {target_script}
版本: {version_name}
"""

import sys
import os
import time
import traceback

def test_startup():
    """测试启动过程"""
    try:
        # 添加当前目录到Python路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # 记录初始化开始时间
        init_start = time.time()

        # 导入并初始化FunASR识别器
        if "{version_name}" == "optimized":
            from funasr_voice_combined_optimized import FunASRVoiceRecognizer
        else:
            from funasr_voice_combined import FunASRVoiceRecognizer

        import_start = time.time()
        import_time = import_start - init_start

        # 创建识别器实例
        recognizer = FunASRVoiceRecognizer(
            model_path="./model/fun",
            device="cpu",
            silent_mode=True  # 使用配置文件中的VAD设置
        )

        instance_start = time.time()
        instance_time = instance_start - import_start

        # 初始化系统（但不开始识别）
        init_success = recognizer.initialize()

        init_end = time.time()
        init_time = init_end - instance_start

        total_time = init_end - init_start

        # 输出计时结果
        print(f"TIMING:import_time={{import_time:.3f}}")
        print(f"TIMING:instance_time={{instance_time:.3f}}")
        print(f"TIMING:init_time={{init_time:.3f}}")
        print(f"TIMING:total_time={{total_time:.3f}}")
        print(f"RESULT:init_success={{init_success}}")

        # 立即清理资源
        try:
            recognizer.unload_model()
        except:
            pass

        return True

    except Exception as e:
        print(f"ERROR:{{str(e)}}")
        print(f"TRACEBACK:{{traceback.format_exc()}}")
        return False

if __name__ == "__main__":
    success = test_startup()
    if success:
        print("SUCCESS:Startup test completed successfully")
        sys.exit(0)
    else:
        print("FAILED:Startup test failed")
        sys.exit(1)
'''

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,
                                       encoding='utf-8') as f:
            f.write(test_content)
            return f.name

    def run_comprehensive_test(self, iterations: int = 5):
        """运行完整的对比测试"""
        print("🚀 开始启动性能对比测试")
        print("=" * 60)

        # 测试原版
        original_stats = self.measure_startup_time(
            "funasr_voice_combined.py",
            "original",
            iterations
        )
        self.results['original'] = original_stats

        # 检查优化版是否存在
        optimized_path = "funasr_voice_combined_optimized.py"
        if not os.path.exists(optimized_path):
            print(f"\n⚠️ 优化版文件不存在: {optimized_path}")
            print("   请先创建优化版本，或使用 create_optimized_version.py 脚本")
            return

        # 测试优化版
        optimized_stats = self.measure_startup_time(
            optimized_path,
            "optimized",
            iterations
        )
        self.results['optimized'] = optimized_stats

        # 生成对比报告
        self._generate_comparison_report()

    def _generate_comparison_report(self):
        """生成对比报告"""
        print("\n" + "=" * 60)
        print("📊 启动性能对比报告")
        print("=" * 60)

        orig = self.results['original']
        opt = self.results['optimized']

        # 基本统计
        print(f"\n📈 基本统计:")
        print(f"原版测试:")
        print(f"   成功次数: {orig.get('success_count', 0)}/{orig.get('total_tests', 0)}")
        if 'startup_times' in orig:
            print(f"   平均启动时间: {orig['startup_times']['mean']:.3f}秒")
            print(f"   最快启动时间: {orig['startup_times']['min']:.3f}秒")
            print(f"   最慢启动时间: {orig['startup_times']['max']:.3f}秒")
            print(f"   标准差: {orig['startup_times']['stdev']:.3f}秒")

        print(f"\n优化版测试:")
        print(f"   成功次数: {opt.get('success_count', 0)}/{opt.get('total_tests', 0)}")
        if 'startup_times' in opt:
            print(f"   平均启动时间: {opt['startup_times']['mean']:.3f}秒")
            print(f"   最快启动时间: {opt['startup_times']['min']:.3f}秒")
            print(f"   最慢启动时间: {opt['startup_times']['max']:.3f}秒")
            print(f"   标准差: {opt['startup_times']['stdev']:.3f}秒")

        # 性能对比
        if 'startup_times' in orig and 'startup_times' in opt:
            orig_time = orig['startup_times']['mean']
            opt_time = opt['startup_times']['mean']
            improvement = ((orig_time - opt_time) / orig_time) * 100

            print(f"\n🚀 性能提升:")
            print(f"   原版平均时间: {orig_time:.3f}秒")
            print(f"   优化版平均时间: {opt_time:.3f}秒")
            print(f"   性能提升: {improvement:+.1f}%")

            if improvement > 0:
                print(f"   ✅ 优化有效！启动速度提升 {improvement:.1f}%")
            elif improvement < -5:
                print(f"   ⚠️ 优化导致性能下降 {abs(improvement):.1f}%")
            else:
                print(f"   ➖ 性能基本相当 (差异 < 5%)")

        # 内存使用对比
        if 'memory_usage' in orig and 'memory_usage' in opt:
            print(f"\n💾 内存使用:")
            print(f"   原版平均内存: {orig['memory_usage']['mean']:.1f}MB")
            print(f"   优化版平均内存: {opt['memory_usage']['mean']:.1f}MB")

            mem_diff = opt['memory_usage']['mean'] - orig['memory_usage']['mean']
            if abs(mem_diff) < 10:
                print(f"   ✅ 内存使用基本相当")
            elif mem_diff > 0:
                print(f"   ⚠️ 优化版内存使用增加 {mem_diff:.1f}MB")
            else:
                print(f"   ✅ 优化版内存使用减少 {abs(mem_diff):.1f}MB")

        # 保存详细报告
        self._save_detailed_report()

    def _save_detailed_report(self):
        """保存详细报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"startup_performance_report_{timestamp}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'test_results': self.results,
                    'system_info': {
                        'python_version': sys.version,
                        'platform': sys.platform,
                        'processor': os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown'),
                        'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024  # GB
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\n📄 详细报告已保存: {report_file}")

        except Exception as e:
            print(f"\n❌ 保存报告失败: {e}")

    def test_functionality(self, version_name: str):
        """测试功能完整性"""
        print(f"\n🔍 测试 {version_name} 版本功能完整性...")

        try:
            if version_name == "optimized":
                from funasr_voice_combined_optimized import FunASRVoiceRecognizer
            else:
                from funasr_voice_combined import FunASRVoiceRecognizer

            # 创建识别器
            recognizer = FunASRVoiceRecognizer(
                model_path="./model/fun",
                device="cpu",
                silent_mode=True
            )

            # 测试初始化
            init_success = recognizer.initialize()
            print(f"   ✅ 初始化: {'成功' if init_success else '失败'}")

            # 测试VAD配置
            vad_type = getattr(recognizer, '_vad_type', 'unknown')
            print(f"   ✅ VAD类型: {vad_type}")

            # 测试回调设置
            callback_set = False
            try:
                recognizer.set_callbacks(
                    on_partial_result=lambda x: None,
                    on_final_result=lambda x: None,
                    on_vad_event=lambda t, d: None
                )
                callback_set = True
                print(f"   ✅ 回调设置: 成功")
            except Exception as e:
                print(f"   ❌ 回调设置: 失败 - {e}")

            # 测试环境设置
            env_setup = False
            try:
                env_setup = recognizer.setup_environment()
                print(f"   ✅ 环境设置: {'成功' if env_setup else '失败'}")
            except Exception as e:
                print(f"   ❌ 环境设置: 失败 - {e}")

            # 清理
            try:
                recognizer.unload_model()
                print(f"   ✅ 资源清理: 成功")
            except Exception as e:
                print(f"   ❌ 资源清理: 失败 - {e}")

            all_tests_passed = init_success and callback_set and env_setup
            print(f"\n   📋 功能测试结果: {'✅ 全部通过' if all_tests_passed else '❌ 存在问题'}")

            return all_tests_passed

        except Exception as e:
            print(f"   ❌ 功能测试异常: {e}")
            return False

def main():
    """主函数"""
    print("🚀 FunASR启动性能测试工具")
    print("=" * 60)

    # 检查当前目录
    if not os.path.exists("funasr_voice_combined.py"):
        print("❌ 未找到 funasr_voice_combined.py 文件")
        print("   请确保在正确的项目目录中运行此脚本")
        return

    # 创建测试器
    tester = StartupPerformanceTester()

    # 运行功能测试
    print("\n🔍 功能完整性检查...")
    original_func = tester.test_functionality("original")

    # 如果优化版存在，也测试其功能
    optimized_func = False
    if os.path.exists("funasr_voice_combined_optimized.py"):
        optimized_func = tester.test_functionality("optimized")
    else:
        print("⚠️ 优化版文件不存在，跳过功能测试")

    # 运行性能测试
    if original_func:
        print("\n🚀 开始性能测试...")
        tester.run_comprehensive_test(iterations=3)  # 3次测试足够
    else:
        print("❌ 原版功能测试失败，跳过性能测试")

    print("\n👋 测试完成！")

if __name__ == "__main__":
    main()