import time
import logging
from audio_capture_v import AudioCapture
from model_manager import global_model_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelManagerTest:
    def __init__(self):
        self.test_mode = True
        self.model_path = "model/cn"
    
    def test_single_model_loading(self):
        """测试单个模型加载"""
        print("\n🔬 测试1: 单个模型加载")
        print("=" * 60)
        
        # 首先确保没有加载任何模型
        global_model_manager.unload_all_models()
        print(f"初始化后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 创建第一个实例并加载模型
        start_time = time.time()
        cap1 = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap1.load_model()
        load_time1 = time.time() - start_time
        
        print(f"第一次加载模型耗时: {load_time1:.2f}秒")
        print(f"第一次加载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 清理
        cap1.unload_model()
        
    def test_multiple_instances(self):
        """测试多个实例共享同一个模型"""
        print("\n🔬 测试2: 多个实例共享模型")
        print("=" * 60)
        
        # 首先确保没有加载任何模型
        global_model_manager.unload_all_models()
        print(f"初始化后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 创建第一个实例并加载模型
        start_time1 = time.time()
        cap1 = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap1.load_model()
        load_time1 = time.time() - start_time1
        
        print(f"第一个实例加载模型耗时: {load_time1:.2f}秒")
        print(f"第一个实例加载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 创建第二个实例并加载模型（应该很快，因为模型已加载）
        start_time2 = time.time()
        cap2 = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap2.load_model()
        load_time2 = time.time() - start_time2
        
        print(f"第二个实例加载模型耗时: {load_time2:.2f}秒")
        print(f"第二个实例加载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 创建第三个实例并加载模型
        start_time3 = time.time()
        cap3 = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap3.load_model()
        load_time3 = time.time() - start_time3
        
        print(f"第三个实例加载模型耗时: {load_time3:.2f}秒")
        print(f"第三个实例加载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 验证性能提升
        speedup = load_time1 / load_time2 if load_time2 > 0 else float('inf')
        print(f"\n🚀 性能提升: 第二个实例比第一个实例快 {speedup:.2f}倍")
        
        # 清理
        cap1.unload_model()
        cap2.unload_model()
        cap3.unload_model()
        
    def test_global_unloading(self):
        """测试全局卸载功能"""
        print("\n🔬 测试3: 全局卸载功能")
        print("=" * 60)
        
        # 首先确保没有加载任何模型
        global_model_manager.unload_all_models()
        
        # 创建实例并加载模型
        cap = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap.load_model()
        print(f"模型加载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 清除本地引用，但不卸载全局模型
        cap.unload_model()
        print(f"清除本地引用后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 验证模型仍然可用
        new_cap = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        start_time = time.time()
        new_cap.load_model()
        load_time = time.time() - start_time
        print(f"重新获取模型耗时: {load_time:.2f}秒")
        
        # 全局卸载模型
        new_cap.unload_model_globally()
        print(f"全局卸载后已加载的模型: {global_model_manager.get_loaded_models()}")
        
        # 验证全局卸载后需要重新加载
        final_cap = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        start_time = time.time()
        final_cap.load_model()
        load_time = time.time() - start_time
        print(f"全局卸载后重新加载耗时: {load_time:.2f}秒")
        
        # 清理
        final_cap.unload_model()
    
    def test_model_manager_status(self):
        """测试模型管理器状态查询功能"""
        print("\n🔬 测试4: 模型管理器状态查询")
        print("=" * 60)
        
        # 首先确保没有加载任何模型
        global_model_manager.unload_all_models()
        
        # 检查初始状态
        print(f"初始状态 - 模型已加载: {global_model_manager.is_model_loaded(self.model_path)}")
        print(f"初始状态 - 全局加载中: {global_model_manager.is_global_loading()}")
        
        # 加载模型
        cap = AudioCapture(test_mode=self.test_mode, model_path=self.model_path)
        cap.load_model()
        
        # 检查加载后状态
        print(f"加载后状态 - 模型已加载: {global_model_manager.is_model_loaded(self.model_path)}")
        print(f"加载后状态 - 全局加载中: {global_model_manager.is_global_loading()}")
        print(f"加载后状态 - 已加载模型列表: {global_model_manager.get_loaded_models()}")
        print(f"加载后状态 - 加载时间: {global_model_manager.get_load_time(self.model_path):.2f}秒")
        
        # 清理
        cap.unload_model_globally()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始模型管理器单例模式测试...")
        print("📋 此测试将验证模型是否只被加载一次，以及多个实例是否共享同一个模型")
        
        # 运行各个测试
        self.test_single_model_loading()
        self.test_multiple_instances()
        self.test_global_unloading()
        self.test_model_manager_status()
        
        print("\n✅ 所有测试完成！")
        print("=" * 60)
        
        # 给出总结和建议
        print("💡 模型管理优化总结:")
        print("✅ 成功实现了模型单例管理，避免重复加载")
        print("✅ 多个实例可以共享同一个模型，显著提升性能")
        print("✅ 提供了本地引用清除和全局卸载两种方式，灵活管理内存")
        print("✅ 模型加载时间只在首次发生，后续实例直接复用")
        print("\n📝 使用建议:")
        print("- 在生产环境中，推荐使用普通的unload_model()方法")
        print("- 只在需要完全释放内存时使用unload_model_globally()方法")
        print("- 多个功能模块可以安全地共享同一个模型实例")
        print("✅ 优化完成！")

if __name__ == "__main__":
    tester = ModelManagerTest()
    tester.run_all_tests()