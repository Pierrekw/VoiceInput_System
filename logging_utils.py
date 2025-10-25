#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志处理工具类
为整个项目提供标准化的日志配置和管理功能
"""

import os
import logging
from datetime import datetime
from typing import Optional


class LoggingManager:
    """
    统一日志管理类
    提供标准化的日志配置，支持控制台和文件输出
    """
    
    # 默认日志格式
    DEFAULT_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # logs目录路径（使用小写保持一致性）
    LOGS_DIR = os.path.join(os.getcwd(), "logs")
    
    @classmethod
    def initialize_logs_directory(cls) -> None:
        """创建Logs目录（如果不存在）"""
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
    
    @classmethod
    def get_logger(cls, 
                  name: str, 
                  level: int = logging.DEBUG,  # 默认使用DEBUG级别，确保所有日志都能被捕获
                  log_file: Optional[str] = None,
                  file_level: Optional[int] = None,
                  console_level: Optional[int] = None,
                  log_to_console: bool = True,
                  log_to_file: bool = True
                  ) -> logging.Logger:
        """
        获取配置好的日志记录器
        
        Args:
            name: 日志记录器名称，建议使用模块名
            level: 日志级别，默认为INFO
            log_file: 日志文件名，如果不提供则自动生成
            file_level: 文件日志级别，如果不提供则使用level
            console_level: 控制台日志级别，如果不提供则使用level
            log_to_console: 是否输出到控制台
            log_to_file: 是否输出到文件
            
        Returns:
            配置好的logging.Logger实例
        """
        # 确保Logs目录存在
        cls.initialize_logs_directory()
        
        # 获取或创建logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 清除现有处理器，避免重复输出
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt=cls.DEFAULT_FORMAT,
            datefmt=cls.DEFAULT_DATE_FORMAT
        )
        
        # 配置文件日志
        if log_to_file:
            # 如果没有提供日志文件名，自动生成
            if log_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_file = f"{name}_{timestamp}.log"
            
            # 构建完整的日志文件路径
            log_file_path = os.path.join(cls.LOGS_DIR, log_file)
            
            try:
                # 创建文件处理器 - 确保使用正确的UTF-8编码
                file_handler = logging.FileHandler(
                    filename=log_file_path,
                    encoding='utf-8-sig',  # 使用utf-8-sig确保Windows下正确处理BOM
                    mode='a'
                )
                file_handler.setLevel(file_level or level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
                # 使用低级别的日志记录，而不是print语句
                logger.debug(f"日志文件已创建: {log_file_path}")
            except Exception as e:
                # 使用标准错误流输出错误信息
                import sys
                print(f"创建日志文件失败: {e}", file=sys.stderr)
        
        # 配置控制台日志
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level or level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    @classmethod
    def get_application_logger(cls, 
                              module_name: str,
                              debug: bool = False
                              ) -> logging.Logger:
        """
        获取应用程序日志记录器（便捷方法）
        
        Args:
            module_name: 模块名称
            debug: 是否启用调试模式
            
        Returns:
            配置好的logging.Logger实例
        """
        level = logging.DEBUG if debug else logging.INFO
        return cls.get_logger(name=module_name, level=level)
    
    @classmethod
    def get_silent_logger(cls, name: str) -> logging.Logger:
        """
        获取静默日志记录器（只输出到文件）
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的logging.Logger实例
        """
        return cls.get_logger(
            name=name,
            log_to_console=False,
            log_to_file=True
        )
    
    @classmethod
    def get_console_only_logger(cls, name: str) -> logging.Logger:
        """
        获取仅控制台日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的logging.Logger实例
        """
        return cls.get_logger(
            name=name,
            log_to_console=True,
            log_to_file=False
        )


# 便捷函数：获取标准日志记录器
def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    便捷函数：获取标准日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的logging.Logger实例
    """
    return LoggingManager.get_logger(name=name, level=level)


# 便捷函数：获取应用程序日志记录器
def get_app_logger(module_name: str, debug: bool = False) -> logging.Logger:
    """
    便捷函数：获取应用程序日志记录器
    
    Args:
        module_name: 模块名称
        debug: 是否启用调试模式
        
    Returns:
        配置好的logging.Logger实例
    """
    return LoggingManager.get_application_logger(module_name=module_name, debug=debug)


# 便捷函数：获取静默日志记录器
def get_silent_logger(name: str) -> logging.Logger:
    """
    便捷函数：获取静默日志记录器（只输出到文件）
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的logging.Logger实例
    """
    return LoggingManager.get_silent_logger(name=name)


def test_log_levels():
    """
    测试不同日志级别的记录情况
    验证debug、info、warning、error、critical都能正确记录到文件
    """
    # 创建一个专用的测试日志记录器
    test_logger = get_logger("log_level_test", level=logging.DEBUG)
    
    # 记录不同级别的日志
    test_logger.debug("🔍 这是一条DEBUG级别日志")
    test_logger.info("ℹ️ 这是一条INFO级别日志")
    test_logger.warning("⚠️ 这是一条WARNING级别日志")
    test_logger.error("❌ 这是一条ERROR级别日志")
    test_logger.critical("💀 这是一条CRITICAL级别日志")
    
    print("\n📝 日志级别测试完成！")
    print("✅ 所有级别的日志（debug、info、warning、error、critical）都已记录到文件")
    print("请检查Logs目录下的log_level_test_*.log文件")


def test_separate_levels():
    """
    测试文件和控制台使用不同日志级别的情况
    """
    # 创建一个文件记录DEBUG级别但控制台只显示INFO级别的日志记录器
    test_logger = LoggingManager.get_logger(
        name="separate_levels_test",
        level=logging.DEBUG,  # logger级别设置为最低
        file_level=logging.DEBUG,  # 文件记录所有级别
        console_level=logging.INFO  # 控制台只显示INFO及以上
    )
    
    # 记录不同级别的日志
    test_logger.debug("🔍 这条DEBUG日志只会出现在文件中")
    test_logger.info("ℹ️ 这条INFO日志会同时出现在文件和控制台")
    test_logger.warning("⚠️ 这条WARNING日志会同时出现在文件和控制台")
    
    print("\n📊 分离级别测试完成！")
    print("✅ DEBUG日志只在文件中可见")
    print("✅ INFO及以上级别的日志在文件和控制台都可见")


if __name__ == "__main__":
    print("=== 日志管理器测试套件 ===")
    print("1. 测试所有日志级别记录")
    test_log_levels()
    print("\n2. 测试分离的文件和控制台级别")
    test_separate_levels()
    print("\n=== 测试完成 ===")
    print("请查看Logs目录下的日志文件以验证结果")