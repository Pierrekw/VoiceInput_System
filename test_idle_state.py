#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统在idle状态后的行为是否正常
"""
import os
import sys
import logging
from main import VoiceInputSystem

# 设置日志级别为DEBUG以便查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # 确保以测试模式运行
    os.environ["VOICE_INPUT_TEST_MODE"] = "true"
    
    # 配置较短的超时时间以便快速测试
    logger.info("🚀 启动测试：验证系统在idle状态后的行为")
    logger.info("📝 系统将在倒计时结束后自动开始录音")
    logger.info("💡 观察是否会出现系统状态设置为idle后直接结束的问题")
    
    try:
        # 创建系统实例，设置较短的超时时间
        system = VoiceInputSystem(timeout_seconds=30, test_mode=True)
        
        # 启动实时语音识别
        system.start_realtime_vosk()
        
        logger.info("✅ 测试完成：系统成功运行到结束")
    except KeyboardInterrupt:
        logger.info("👋 用户中断测试")
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清除环境变量
        if "VOICE_INPUT_TEST_MODE" in os.environ:
            del os.environ["VOICE_INPUT_TEST_MODE"]
        
        logger.info("✨ 测试脚本已结束")