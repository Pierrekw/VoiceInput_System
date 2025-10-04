#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全局模型卸载脚本
用于在测试完成后完全释放Vosk模型占用的内存资源
"""
import os
import logging

# 导入配置系统
from config_loader import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def unload_vosk_model_globally(model_path: str | None = None):
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
    # 获取命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='全局卸载Vosk模型')
    parser.add_argument('--model_path', type=str, default=None, help='要卸载的模型路径，默认卸载所有模型')
    parser.add_argument('--all', action='store_true', help='卸载所有模型')
    args = parser.parse_args()

    # 如果指定了--all或者没有指定model_path，则卸载所有模型
    if args.all or not args.model_path:
        unload_vosk_model_globally()
    else:
        # 否则只卸载指定的模型
        unload_vosk_model_globally(args.model_path)
    
    # 提示用户关于配置文件的信息
    print("\n💡 提示:")
    print(f"   - 您可以在config.yaml中的'model.default_path'配置默认模型路径")
    print(f"   - 系统全局卸载控制可通过'system.global_unload'配置")