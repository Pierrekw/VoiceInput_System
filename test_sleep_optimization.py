import time
import logging
import psutil
import os
from audio_capture_v import AudioCapture, start_keyboard_listener
import threading

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SleepOptimizationTester:
    def __init__(self):
        # 要测试的睡眠时间（秒）
        self.sleep_times = [0.5, 0.1, 0.05, 0.01]
        self.current_process = psutil.Process(os.getpid())
        self.results = []
    
    def modify_sleep_time(self, sleep_time):
        """临时修改audio_capture_v.py中的睡眠时间"""
        file_path = "f:/04_AI/01_Workplace/Voice_Input/audio_capture_v.py"
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            # 查找并修改睡眠时间行
            for i, line in enumerate(content):
                if 'time.sleep(' in line and '# 折中的睡眠时间' in line:
                    # 保存原始行用于恢复
                    original_line = line
                    # 修改睡眠时间
                    content[i] = f"        time.sleep({sleep_time})  # 测试用睡眠时间\n"
                    break
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
            
            return original_line
        except Exception as e:
            logger.error(f"修改睡眠时间失败: {e}")
            return None
    
    def restore_sleep_time(self, original_line):
        """恢复原始睡眠时间"""
        if not original_line:
            return
        
        file_path = "f:/04_AI/01_Workplace/Voice_Input/audio_capture_v.py"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            for i, line in enumerate(content):
                if 'time.sleep(' in line and '# 测试用睡眠时间' in line:
                    content[i] = original_line
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
        except Exception as e:
            logger.error(f"恢复睡眠时间失败: {e}")
    
    def test_sleep_time(self, sleep_time):
        """测试特定睡眠时间下的性能"""
        print(f"\n🔍 开始测试睡眠时间: {sleep_time}秒")
        print("=" * 50)
        
        # 记录开始时间
        test_start_time = time.time()
        test_duration = 8  # 每个测试持续8秒
        
        # 创建AudioCapture实例
        audio_capture = AudioCapture(
            test_mode=True,
            tts_state="off"
        )
        
        # 启动键盘监听器
        keyboard_listener = start_keyboard_listener(audio_capture, test_mode=True)
        
        # 加载模型
        if not audio_capture.load_model():
            print(f"❌ 模型加载失败，跳过{sleep_time}秒测试")
            if keyboard_listener:
                keyboard_listener.stop()
            return
        
        # 设置初始状态为paused
        audio_capture.state = "paused"
        
        # 用于记录键盘响应次数
        key_press_count = 0
        last_state = "paused"
        
        # 记录CPU使用率
        cpu_usages = []
        
        print(f"⏱️  测试将持续{test_duration}秒，请在期间多次按下空格键...")
        
        # 测试循环
        while time.time() - test_start_time < test_duration:
            # 检查状态变化
            current_state = audio_capture.state
            if current_state != last_state:
                key_press_count += 1
                last_state = current_state
            
            # 记录CPU使用率
            cpu_usage = self.current_process.cpu_percent(interval=0.01)
            cpu_usages.append(cpu_usage)
            
            # 检测ESC键提前退出
            if audio_capture.state == "stopped":
                print("🛑 检测到ESC键，提前结束测试")
                break
            
            time.sleep(0.01)  # 非常小的睡眠以不干扰测试
        
        # 计算实际测试时间
        actual_duration = time.time() - test_start_time
        
        # 计算平均响应频率
        if actual_duration > 0:
            response_rate = key_press_count / actual_duration
        else:
            response_rate = 0
        
        # 计算平均CPU使用率
        avg_cpu_usage = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
        
        # 清理资源
        audio_capture.stop()
        if keyboard_listener:
            keyboard_listener.stop()
        
        # 记录结果
        result = {
            "sleep_time": sleep_time,
            "key_press_count": key_press_count,
            "test_duration": actual_duration,
            "response_rate": response_rate,
            "avg_cpu_usage": avg_cpu_usage
        }
        
        # 打印测试结果
        print(f"\n📊 {sleep_time}秒测试结果:")
        print(f"🔑 捕获的按键次数: {key_press_count}")
        print(f"⏱️  实际测试时间: {actual_duration:.2f}秒")
        print(f"⚡ 响应频率: {response_rate:.2f}次/秒")
        print(f"💻 平均CPU使用率: {avg_cpu_usage:.2f}%")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 启动睡眠时间优化测试...")
        print("📋 测试将对比不同睡眠时间下的系统性能和稳定性")
        print("🎯 按ESC键可提前结束当前测试轮次")
        print("=" * 50)
        
        original_line = None
        
        try:
            # 按顺序测试不同的睡眠时间
            for sleep_time in self.sleep_times:
                # 保存原始行并修改睡眠时间
                original_line = self.modify_sleep_time(sleep_time)
                
                # 测试当前睡眠时间
                self.test_sleep_time(sleep_time)
                
                # 等待一段时间再进行下一个测试
                time.sleep(2)
        finally:
            # 确保恢复原始睡眠时间
            self.restore_sleep_time(original_line)
        
        # 打印综合比较结果
        self.print_comparison_results()
    
    def print_comparison_results(self):
        """打印所有测试结果的对比"""
        print("\n" + "=" * 70)
        print("📊 睡眠时间优化测试综合对比")
        print("=" * 70)
        print(f"{'睡眠时间(秒)':<15}{'响应频率(次/秒)':<20}{'平均CPU使用率(%)':<20}{'推荐指数'}")
        print("=" * 70)
        
        # 按响应频率排序结果
        sorted_results = sorted(self.results, key=lambda x: x["response_rate"], reverse=True)
        
        for result in sorted_results:
            sleep_time = result["sleep_time"]
            response_rate = result["response_rate"]
            cpu_usage = result["avg_cpu_usage"]
            
            # 计算推荐指数 (响应频率高且CPU使用率低的为最佳)
            # 简单评分公式: 响应频率 * (1 - CPU使用率/100)
            if cpu_usage < 100:  # 避免除以0
                score = response_rate * (1 - min(cpu_usage, 99)/100)
            else:
                score = 0
            
            # 根据评分显示推荐指数
            if score > 10:  # 优秀
                recommendation = "⭐⭐⭐⭐⭐"
            elif score > 5:  # 良好
                recommendation = "⭐⭐⭐⭐"
            elif score > 2:  # 一般
                recommendation = "⭐⭐⭐"
            else:  # 不推荐
                recommendation = "⭐⭐"
            
            print(f"{sleep_time:<15}{response_rate:<20.2f}{cpu_usage:<20.2f}{recommendation}")
        
        print("=" * 70)
        
        # 分析结果并给出建议
        best_result = max(self.results, key=lambda x: 
            x["response_rate"] * (1 - min(x["avg_cpu_usage"], 99)/100) 
            if x["avg_cpu_usage"] < 100 else 0)
        
        print("💡 优化建议:")
        print(f"✅ 最佳睡眠时间设置: {best_result['sleep_time']}秒")
        print(f"   响应频率: {best_result['response_rate']:.2f}次/秒")
        print(f"   CPU使用率: {best_result['avg_cpu_usage']:.2f}%")
        
        # 基于测试结果提供具体建议
        if best_result['sleep_time'] == 0.01:
            print("   系统可以支持极低的睡眠时间，获得最佳响应性能。")
        elif best_result['sleep_time'] == 0.05:
            print("   0.05秒是性能和资源消耗的良好平衡。")
        elif best_result['sleep_time'] == 0.1:
            print("   当前设置(0.1秒)是一个稳定的选择。")
        else:
            print("   建议降低睡眠时间以提高系统响应性。")
        
        print("✅ 测试完成！")

if __name__ == "__main__":
    tester = SleepOptimizationTester()
    tester.run_all_tests()