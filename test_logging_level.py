#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证日志级别设置是否生效
"""

import logging
import logging_utils

# 创建多个不同模块的logger实例
logger1 = logging_utils.get_logger("module1", level=logging.DEBUG)  # 虽然logger级别是DEBUG，但控制台应该只显示INFO及以上
logger2 = logging_utils.get_logger("module2", level=logging.DEBUG)

print("测试日志级别设置：")
print("- 以下应该只显示INFO和ERROR级别日志，不显示DEBUG级别日志")
print("---------------------------------------------------")

# 记录不同级别的日志
logger1.debug("这条DEBUG日志不应该显示在控制台")
logger1.info("这条INFO日志应该显示在控制台")
logger1.error("这条ERROR日志应该显示在控制台")

logger2.debug("这条来自module2的DEBUG日志也不应该显示在控制台")
logger2.info("这条来自module2的INFO日志应该显示在控制台")

print("\n测试完成。如果只看到INFO和ERROR日志，说明控制台日志级别设置成功。")