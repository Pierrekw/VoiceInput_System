#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全局模型预加载脚本
用于在测试前预加载Vosk模型，避免重复加载导致的长时间等待
"""
import time
import os
import logging

# 导入配置系统
from config_loader import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def preload_vosk_model(model_path: str = None):
    """
    预加载Vosk模型
    
    Args:
        model_path: Vosk模型路径，默认使用配置文件中的值
        
    Returns:
        bool: 是否成功预加载
    """
    try:
        # 动态导入，避免脚本开始就加载模块
        from model_manager import global_model_manager
        
        # 如果未提供模型路径，从配置系统获取
        if model_path is None:
            model_path = config.get_model_path()
            logger.info(f"使用配置文件中的默认模型路径: {model_path}")
        
        print(f"\n📦 开始预加载Vosk模型: {model_path}")
        start_time = time.time()
        
        # 使用全局模型管理器加载模型
        model_data = global_model_manager.load_model(model_path)
        
        load_time = time.time() - start_time
        print(f"✅ 模型预加载成功！耗时: {load_time:.2f}秒")
        print(f"🔍 当前已加载模型: {global_model_manager.get_loaded_models()}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 模型预加载失败: {e}")
        print(f"❌ 模型预加载失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 从命令行参数或环境变量获取模型路径，如果都没有则使用配置文件中的值
    import sys
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = os.getenv("VOSK_MODEL_PATH")  # 允许通过环境变量覆盖配置
        
    print("=== Vosk模型全局预加载工具 ===")
    success = preload_vosk_model(model_path)
    
    if success:
        print("\n💡 使用提示:")
        print("   - 模型已在全局缓存，后续测试实例将直接复用")
        print("   - 测试完成后，可运行unload_model_global.py完全释放内存")
        print("   - 如需保留模型在内存中供其他程序使用，可直接关闭此窗口")
        sys.exit(0)
    else:
        print("\n❓ 可能的解决方法:")
        print("   - 检查模型路径是否正确")
        print("   - 确保模型文件完整无损坏")
        print("   - 尝试使用正确的模型路径参数运行: python preload_model.py [模型路径]")
        print(f"   - 或修改config.yaml中的model.default_path配置项")
        sys.exit(1)