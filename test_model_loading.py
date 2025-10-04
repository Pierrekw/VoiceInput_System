#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模型加载日志是否只显示一次
"""
import logging
import os
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 清理之前可能加载的模型引用
try:
    # 尝试全局卸载模型以确保从头开始测试
    from unload_model_global import unload_vosk_model_globally
    unload_vosk_model_globally()
    logger.info("✅ 已全局卸载之前加载的模型")
except ImportError:
    logger.warning("⚠️ 无法导入全局卸载模块，继续测试")

# 确保重新启动测试环境
time.sleep(1)

logger.info("🚀 开始测试模型加载日志...")

# 导入并使用核心组件
try:
    from audio_capture_v import AudioCapture
    
    # 创建AudioCapture实例
    logger.info("🔄 创建AudioCapture实例...")
    capture = AudioCapture()
    
    # 加载模型
    logger.info("📦 调用load_model()方法...")
    start_time = time.time()
    success = capture.load_model()
    end_time = time.time()
    
    if success:
        logger.info(f"✅ 模型加载成功，耗时: {(end_time - start_time):.2f}秒")
        logger.info("请检查日志输出，'✅ 模型加载完成'应该只出现一次")
    else:
        logger.error("❌ 模型加载失败")
        
    # 清理资源
    capture.unload_model()
    logger.info("🧹 清理测试资源完成")
    
except Exception as e:
    logger.error(f"❌ 测试过程中出现错误: {e}")

logger.info("🏁 模型加载日志测试完成")