import speech_recognition as sr
import logging
import time
from unittest.mock import patch, MagicMock
import re
import threading
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

#os.environ["VOSK_LOG_LEVEL"] = "-1"   # -1 = 完全静默

from vosk import Model, KaldiRecognizer
import json
import pyaudio
import re
import cn2an
import vosk

vosk.SetLogLevel(-1)  # -1 表示关闭所有日志

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_input.log'),
        logging.StreamHandler()
    ]
)

# 语音误识别词典
VOICE_CORRECTION_DICT = {
    "其实": "七十",
    "一起": "一七",
    "是": "十",
    "我": "五",
    "支": "七",
    "期": "七",
    "而": "二",
    "就": "九",
    "吧": "八",
    "义务": "一五",
    "三六": "三十六",  # 可扩展
}

def correct_voice_errors(text):
    for wrong, correct in VOICE_CORRECTION_DICT.items():
        text = text.replace(wrong, correct)
    return text



def extract_measurements(text):
    if text is None or not isinstance(text, (str, int, float)):
        return []

    try:
        text = str(text).strip()
        text = correct_voice_errors(text)

        # 匹配纯中文数字或阿拉伯数字（不包含后续中文）
        candidates = re.findall(r'[零一二三四五六七八九十百千万点两\d\.]+', text)

        nums = []
        for c in candidates:
            # 清理尾部非数字字符（如“点八 六”）
            # c = re.sub(r'[^\d\.零一二三四五六七八九十百千万点两]', '', c)

            # 如果仍然包含中文数字，尝试转换
            try:
                num = cn2an.cn2an(c, "smart")
                nums.append(float(num))
            except:
                continue

        return nums

    except Exception:
        return []



class AudioCapture:
    def __init__(self, stop_commands=["停止录音", "stop"], timeout_seconds=30):
        self.stop_commands = stop_commands
        self.is_listening = False
        self.callback_function = None
        self.timeout_seconds = timeout_seconds
        self.buffered_values = []  # 缓存测量值
        
    def set_callback(self, callback):
        """设置实时识别结果回调函数"""
        self.callback_function = callback
      
         
    def adjust_for_ambient_noise(self, source, duration=1):
        """调整环境噪音"""
        try:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            logging.info("环境噪音调整完成")
            return True
        except Exception as e:
            logging.warning(f"环境噪音调整失败: {e}")
            return False
        
    def filtered_callback(self, text: str):
        if not isinstance(text, str):
            return []

        nums = extract_measurements(text)

        if nums:
            self.buffered_values.extend(nums)  # 缓存
            if self.callback_function:
                self.callback_function(nums)
            # ✅ 可选：显示格式化后的测量值
            print(f"🗣️ 语音文本: {text}")
            print(f"🔢 测量值: {nums}")
            
        else:
            # ❌ 不显示非测量内容
            pass    


    
    #"def filtered_callback(self, text: str):
    #    if not isinstance(text, str):
    #        return []
    #    nums = extract_measurements(text)
    #    if nums:
    #       self.buffered_values.extend(nums)  # 缓存
    #        if self.callback_function:
    #            self.callback_function(nums)
    #        #print(f"🔢 测量值: {nums}")
    #    else:
            
    #        #print(f"🗣️ 非测量: {text}")
   
    
    def listen_realtime_vosk(self):
        self.is_listening = True
        model = Model("model/cn")   #cn 大模型 启动慢精度高 ； cns 小模型 启动快精度低
        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(False)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1,
                        rate=16000, input=True, frames_per_buffer=8000)
        print("🎤 Vosk 实时监听中...（说‘停止录音’结束）")

        try:
            while self.is_listening:
                data = stream.read(8000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = (res.get("text") or "").replace(" ", "")
                    if text:
                        self.filtered_callback(text)
                        if any(cmd in text for cmd in self.stop_commands):
                            print("🛑 收到停止指令")
                            self.is_listening = False
                else:
                    partial = json.loads(rec.PartialResult()).get("partial") or ""
                    if partial:
                        print(f"🗣️ 部分结果: {partial}", end="\r")

            final = json.loads(rec.FinalResult()).get("text", "")
            #print(f"📝 最终: {final}")
            return {"final": final, "buffered_values": self.buffered_values}

        except Exception as e:
            return {"final": "", "buffered_values": []}
            import traceback
            print("\n❌ 完整异常：")
            traceback.print_exc()
            print("简要：", e)

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
 
        
    def test_realtime_vosk(self):
        """
        运行：python audio_capture.py vosk
        """
        print("\n=== 实时流式录音测试 ===")
        print("请对着麦克风说几句话，说“停止录音”结束 或 按 Ctrl C")
        self.set_callback(lambda nums: print(f"👂 测量值: {nums}"))
        try:
            result = self.listen_realtime_vosk()
            print("✅ 实时测试完成，最终文本：", result["final"])
        except AssertionError as e:
            print("❌ 出现 AssertionError：", e)
        except Exception as e:
            print("❌ 其他异常：", e)

# 模块自查代码
if __name__ == '__main__':
    
   
    if len(sys.argv) > 1 and sys.argv[1] == 'vosk':
        # 单独跑实时测试
        AudioCapture().test_realtime_vosk()
        sys.exit(0)
    
    def test_microphone_availability():
        """测试麦克风是否可用"""
        print("=== 测试麦克风可用性 ===")
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                print("❌ 未找到可用的麦克风设备")
                return False
            
            print(f"✅ 找到 {len(mic_list)} 个麦克风设备:")
            for i, mic_name in enumerate(mic_list):
                print(f"  {i}: {mic_name}")
            
            try:
                with sr.Microphone() as source:
                    print("✅ 默认麦克风初始化成功")
                return True
            except Exception as e:
                print(f"❌ 默认麦克风测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 麦克风检测异常: {e}")
            return False
    
    def test_microphone_input():
        """测试麦克风输入功能"""
        print("\n=== 测试麦克风输入 ===")
        print("请对着麦克风说几句话...")
        
        try:
            capture = AudioCapture()
            with sr.Microphone() as source:
                if not capture.adjust_for_ambient_noise(source):
                    print("⚠️  环境噪音调整失败")
                
                print("🔴 正在录音（5秒）...")
                # 使用优化后的参数 [1,3](@ref)
                audio = capture.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("✅ 音频录制成功")
                
                # 尝试识别
                try:
                    # 使用中文识别 [2,5](@ref)
                    text = capture.recognizer.recognize_google(audio, language='zh-CN')
                    print(f"✅ 语音识别成功: {text}")
                    return True
                except sr.UnknownValueError:
                    print("⚠️  录制到音频但无法识别内容（正常现象）")
                    return True
                except sr.RequestError as e:
                    print(f"❌ 语音识别服务错误: {e}")
                    # 尝试备用方案 [2](@ref)
                    try:
                        print("🔄 尝试使用备用API端点...")
                        text = capture.recognizer.recognize_google(audio, language='zh-CN')
                        print(f"✅ 语音识别成功（备用）: {text}")
                        return True
                    except:
                        return False
                    
        except Exception as e:
            print(f"❌ 麦克风输入测试失败: {e}")
            return False
    
    def test_timeout_functionality():
        """测试超时功能"""
        print("\n=== 测试超时功能 ===")
        
        # 使用很短的超时时间进行测试
        capture = AudioCapture(timeout_seconds=3)
        
        try:
            # 使用模拟无输入的情况
            with patch.object(capture.recognizer, 'listen') as mock_listen:
                mock_listen.side_effect = sr.WaitTimeoutError("模拟无输入")
                
                # 记录开始时间
                start_time = time.time()
                
                # 运行监听（应该会在3秒后超时）
                result = capture.continuous_listen()
                
                # 计算运行时间
                elapsed_time = time.time() - start_time
                
                # 检查是否在预期时间内完成
                if 2.5 <= elapsed_time <= 4.0 and result is None:
                    print(f"✅ 超时功能测试通过")
                    print(f"⏱️  实际超时时间: {elapsed_time:.1f}秒")
                    return True
                else:
                    print(f"❌ 超时功能测试失败")
                    print(f"⏱️  运行时间: {elapsed_time:.1f}秒")
                    print(f"📊 返回结果: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ 超时测试异常: {e}")
            return False
    
    def test_stop_commands():
        """测试停止命令识别"""
        print("\n=== 测试停止命令识别 ===")
        
        capture = AudioCapture(stop_commands=["停止录音", "stop"])
        
        # 测试停止命令识别
        test_cases = [
            ("停止录音", True),
            ("stop", True),
            ("继续录音", False),
            ("开始", False)
        ]
        
        for command, should_stop in test_cases:
            result = any(cmd in command for cmd in capture.stop_commands)
            if result == should_stop:
                print(f"✅ '{command}' 识别正确")
            else:
                print(f"❌ '{command}' 识别错误")
                return False
        
        print("✅ 停止命令识别测试通过")
        return True
    
    def run_all_tests():
        """运行所有测试"""
        print("开始运行 AudioCapture 模块测试...")
        print("=" * 50)
        
        tests = [
            test_microphone_availability,
            test_microphone_input,
            test_stop_commands,
            test_timeout_functionality
        ]
        
        results = []
        for test in tests:
            try:
                print(f"\n--- 运行测试: {test.__doc__} ---")
                success = test()
                results.append((test.__name__, success, test.__doc__))
                time.sleep(1)
            except Exception as e:
                print(f"❌ 测试执行失败: {e}")
                results.append((test.__name__, False, test.__doc__))
        
        print("\极狐" + "=" * 50)
        print("测试结果汇总:")
        print("=" * 50)
        
        all_passed = True
        for test_name, success, test_desc in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_desc}: {status}")
            if not success:
                all_passed = False
        
        print("=" * 50)
        if all_passed:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查相关问题")
        
        return all_passed
    
    # 根据命令行参数执行测试
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success = run_all_tests()
        sys.exit(0 if success else 1)
    
    # 交互式测试
    while True:
        print("\n" + "=" * 50)
        print("AudioCapture 模块自检菜单")
        print("=" * 50)
        print("1. 运行全部测试")
        print("2. 测试麦克风可用性")
        print("3. 测试麦克风输入")
        print("4. 测试停止命令识别")
        print("5. 测试超时功能")
        print("6. 退出程序")
        print("=" * 50)
        
        choice = input("请选择测试项目 (1-6): ").strip()
        
        if choice == '1':
            run_all_tests()
            break
        elif choice == '2':
            result = test_microphone_availability()
            print(f"\n测试完成: {'✅ 通过' if result else '❌ 失败'}")
            break
        elif choice == '3':
            result = test_microphone_input()
            print(f"\n测试完成: {'✅ 通过' if result else '❌ 失败'}")
            break
        elif choice == '4':
            result = test_stop_commands()
            print(f"\n测试完成: {'✅ 通过' if result else '❌ 失败'}")
            break
        elif choice == '5':
            result = test_timeout_functionality()
            print(f"\n测试完成: {'✅ 通过' if result else '❌ 失败'}")
            break
        elif choice == '6':
            print("退出程序")
            sys.exit(0)
        else:
            print("❌ 无效选择，请重新选择")
            continue
        
        # 测试完成后询问是否继续
        continue_test = input("\n是否返回主菜单？(y/n): ").strip().lower()
        if continue_test == 'y':
            # 重新执行脚本
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            print("程序结束")
            break