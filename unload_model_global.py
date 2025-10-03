#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全局模型卸载脚本
用于在测试完成后完全释放Vosk模型占用的内存资源
"""
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def unload_vosk_model_globally(model_path: str = None):
    """
    全局卸载Vosk模型
    
    Args:
        model_path: 要卸载的Vosk模型路径，默认为None（卸载所有模型）
        
    Returns:
        bool: 是否成功卸载
    """
    try:
        # 动态导入，避免脚本开始就加载模块
        from model_manager import global_model_manager
        
        # 获取当前已加载的模型
        loaded_models = global_model_manager.get_loaded_models()
        
        if not loaded_models:
            print("⚠️ 当前没有已加载的模型，无需卸载")
            return True
        
        print(f"\n🧹 当前已加载的模型: {loaded_models}")
        
        if model_path:
            # 卸载指定模型
            if model_path not in loaded_models:
                print(f"⚠️ 模型 '{model_path}' 未加载，无法卸载")
                return False
            
            print(f"📤 开始全局卸载模型: {model_path}")
            success = global_model_manager.unload_model(model_path)
            if success:
                print(f"✅ 模型 '{model_path}' 已成功全局卸载")
            else:
                print(f"❌ 模型 '{model_path}' 卸载失败")
            return success
        else:
            # 卸载所有模型
            print("📤 开始全局卸载所有已加载的模型...")
            global_model_manager.unload_all_models()
            print("✅ 所有模型已成功全局卸载")
            return True
    except Exception as e:
        logger.error(f"❌ 模型卸载过程出错: {e}")
        print(f"❌ 模型卸载过程出错: {str(e)}")
        return False


if __name__ == "__main__":
    # 从命令行参数或环境变量获取模型路径
    import sys
    model_path = sys.argv[1] if len(sys.argv) > 1 else os.getenv("VOSK_MODEL_PATH")
    
    print("=== Vosk模型全局卸载工具 ===")
    success = unload_vosk_model_globally(model_path)
    
    if success:
        print("\n💡 注意事项:")
        print("   - 模型已从内存中完全释放")
        print("   - 后续使用模型将需要重新从磁盘加载（耗时较长）")
        print("   - 如仅需清除单个实例的模型引用，无需使用此脚本")
        sys.exit(0)
    else:
        print("\n❓ 可能的解决方法:")
        print("   - 检查模型路径是否正确")
        print("   - 确认模型确实已加载")
        print("   - 尝试不带参数运行以卸载所有模型: python unload_model_global.py")
        sys.exit(1)