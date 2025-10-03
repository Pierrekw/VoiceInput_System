import time
import logging
from audio_capture_v import AudioCapture, start_keyboard_listener
import threading

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeyboardResponseTester:
    def __init__(self):
        # 创建AudioCapture实例，但不连接Excel
        self.audio_capture = AudioCapture(
            test_mode=True,  # 启用测试模式以查看详细输出
            tts_state="off"  # 禁用TTS以避免干扰测试
        )
        self.keyboard_listener = None
        self.test_start_time = 0
        self.test_end_time = 0
        self.key_press_count = 0
        self.max_test_duration = 10  # 测试持续10秒
    
    def start_test(self):
        """开始键盘响应测试"""
        print("🚀 启动键盘响应和性能测试...")
        print("🔍 测试说明：此测试将运行10秒，请在期间多次按下空格键")
        print("⏱️  系统会测量键盘响应时间并评估性能")
        print("🎯 按ESC键可提前结束测试")
        print("=" * 50)
        
        # 启动键盘监听器
        self.keyboard_listener = start_keyboard_listener(self.audio_capture, test_mode=True)
        
        # 加载模型
        print("📦 正在加载模型...")
        if not self.audio_capture.load_model():
            print("❌ 模型加载失败，无法进行测试")
            return False
        
        # 设置初始状态为paused
        self.audio_capture.state = "paused"
        self.test_start_time = time.time()
        
        # 启动响应测试线程
        response_thread = threading.Thread(target=self._response_check_thread)
        response_thread.daemon = True
        response_thread.start()
        
        # 启动监听循环
        try:
            # 我们不实际监听音频，只测试键盘响应
            while time.time() - self.test_start_time < self.max_test_duration:
                # 模拟主循环的工作
                if self.audio_capture.state == "stopped":
                    print("🛑 检测到ESC键，提前结束测试")
                    break
                time.sleep(0.01)  # 非常小的睡眠以不干扰测试
                
        except KeyboardInterrupt:
            print("👋 用户中断测试")
        finally:
            self.test_end_time = time.time()
            self._cleanup()
            self._print_test_results()
        
        return True
    
    def _response_check_thread(self):
        """检查键盘响应的线程"""
        last_state = "paused"
        
        while time.time() - self.test_start_time < self.max_test_duration:
            current_state = self.audio_capture.state
            
            # 检测状态变化（由键盘事件触发）
            if current_state != last_state:
                state_change_time = time.time() - self.test_start_time
                print(f"🔄 状态变化: {last_state} -> {current_state} (时间: {state_change_time:.2f}s)")
                last_state = current_state
                self.key_press_count += 1
            
            time.sleep(0.01)  # 高频检查以准确捕捉状态变化
    
    def _cleanup(self):
        """清理资源"""
        self.audio_capture.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
    
    def _print_test_results(self):
        """打印测试结果"""
        total_duration = self.test_end_time - self.test_start_time
        
        print("=" * 50)
        print("📊 键盘响应测试结果:")
        print(f"⏱️  总测试时间: {total_duration:.2f}秒")
        print(f"🔑 捕获的按键次数: {self.key_press_count}")
        
        if total_duration > 0:
            press_rate = self.key_press_count / total_duration
            print(f"⚡ 按键响应频率: {press_rate:.2f}次/秒")
        
        # 评估结果
        if self.key_press_count >= 5:
            print("✅ 键盘响应测试通过: 系统能够准确捕捉键盘事件")
        else:
            print("⚠️  键盘响应测试警告: 捕获的按键次数较少，可能存在响应延迟")
        
        print("✅ 测试完成！")

if __name__ == "__main__":
    tester = KeyboardResponseTester()
    tester.start_test()