#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型预加载和测试后卸载示例脚本
演示如何使用全局模型管理器进行模型预加载、测试和卸载操作
"""
import time
from audio_capture_v import AudioCapture
from model_manager import global_model_manager

# 模型路径（根据AudioCapture类的默认设置）
MODEL_PATH = "model/cn"


def preload_model_demo():
    """演示模型预加载过程"""
    print("\n===== 模型预加载演示 =====")
    
    # 方法1：直接使用全局模型管理器预加载
    print("\n方法1: 通过全局模型管理器直接预加载")
    start_time = time.time()
    try:
        # 预加载模型
        model_data = global_model_manager.load_model(MODEL_PATH)
        load_time = time.time() - start_time
        print(f"✅ 模型预加载成功！耗时: {load_time:.2f}秒")
        print(f"当前已加载模型: {global_model_manager.get_loaded_models()}")
    except Exception as e:
        print(f"❌ 模型预加载失败: {e}")
    
    # 方法2：通过AudioCapture实例加载（会自动使用全局管理器）
    print("\n方法2: 通过AudioCapture实例加载模型")
    start_time = time.time()
    audio_capture = AudioCapture(model_path=MODEL_PATH, test_mode=True)
    success = audio_capture.load_model()
    load_time = time.time() - start_time
    if success:
        print(f"✅ 模型加载成功！耗时: {load_time:.2f}秒")
        # 注意：第二次加载应该非常快，因为模型已在全局缓存
    else:
        print("❌ 模型加载失败")
    
    return audio_capture


def run_tests_demo(audio_capture):
    """演示使用已加载的模型进行测试"""
    print("\n===== 测试过程演示 =====")
    
    # 这里可以放置实际测试代码
    # 例如：运行性能测试、识别测试等
    print("执行测试操作...")
    print(f"✅ 测试完成！模型状态: {global_model_manager.is_model_loaded(MODEL_PATH)}")


def unload_model_demo(audio_capture):
    """演示测试后卸载模型的两种方式"""
    print("\n===== 模型卸载演示 =====")
    
    # 方式1：仅清除本地引用（保留全局模型，适用于需要在其他地方继续使用模型的情况）
    print("\n方式1: 仅清除本地引用（保留全局模型）")
    audio_capture.unload_model()
    print(f"本地模型引用已清除，全局模型状态: {global_model_manager.is_model_loaded(MODEL_PATH)}")
    
    # 创建新实例验证模型仍然可用
    new_capture = AudioCapture(model_path=MODEL_PATH, test_mode=True)
    start_time = time.time()
    success = new_capture.load_model()
    load_time = time.time() - start_time
    if success:
        print(f"✅ 新实例成功复用全局模型！耗时: {load_time:.2f}秒")
    
    # 方式2：全局卸载模型（适用于测试完全结束，需要释放内存的情况）
    print("\n方式2: 全局卸载模型")
    new_capture.unload_model_globally()
    print(f"全局模型状态: {global_model_manager.is_model_loaded(MODEL_PATH)}")
    
    # 验证全局卸载后的状态
    another_capture = AudioCapture(model_path=MODEL_PATH, test_mode=True)
    print("\n验证全局卸载后重新加载的情况:")
    # 此时如果调用load_model，将会重新从磁盘加载模型


def batch_test_demo():
    """演示批量测试场景下的模型管理"""
    print("\n===== 批量测试场景演示 =====")
    
    # 1. 预加载模型（一次加载，多次使用）
    print("1. 预加载模型...")
    global_model_manager.load_model(MODEL_PATH)
    
    # 2. 执行多个测试
    test_cases = 5
    print(f"2. 执行{test_cases}个测试用例...")
    
    for i in range(test_cases):
        print(f"  测试用例 {i+1}/{test_cases}")
        # 创建测试实例，但不需要重新加载模型
        capture = AudioCapture(model_path=MODEL_PATH, test_mode=True)
        capture.load_model()  # 这会快速获取全局模型
        # 执行测试...
        time.sleep(0.5)  # 模拟测试操作
        capture.unload_model()  # 仅清除本地引用
    
    # 3. 所有测试完成后全局卸载模型
    print("3. 所有测试完成，全局卸载模型...")
    global_model_manager.unload_model(MODEL_PATH)
    print("✅ 批量测试完成！")


def main():
    """主函数"""
    print("===== 模型预加载与卸载完整演示 =====")
    
    # 1. 演示基本的预加载和卸载流程
    audio_capture = preload_model_demo()
    run_tests_demo(audio_capture)
    unload_model_demo(audio_capture)
    
    # 2. 演示批量测试场景
    batch_test_demo()
    
    print("\n===== 演示完成 =====")
    print("\n💡 使用建议：")
    print("   - 测试前预加载模型：提高测试效率，避免重复加载耗时")
    print("   - 测试中仅清除本地引用：允许其他测试实例复用模型")
    print("   - 所有测试完成后全局卸载：释放内存资源")


if __name__ == "__main__":
    main()