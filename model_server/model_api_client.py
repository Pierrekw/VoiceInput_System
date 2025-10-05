#!/usr/bin/env python3
"""
Flask模型API客户端示例
演示如何调用本地部署的模型加载网络API
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_api_client')

class ModelAPIClient:
    """模型API客户端，提供调用Flask模型API的便捷方法"""
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        """
        初始化API客户端
        
        Args:
            base_url: API服务器基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求的通用方法
        
        Args:
            method: HTTP方法（GET, POST等）
            endpoint: API端点
            **kwargs: 传递给requests的额外参数
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.debug(f"发送请求: {method} {url}, 参数: {kwargs}")
            response = self.session.request(method, url, **kwargs)
            
            # 检查响应状态
            if response.status_code >= 400:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error_code": response.status_code,
                    "error_message": response.text
                }
            
            # 尝试解析JSON响应
            try:
                data = response.json()
                logger.debug(f"请求成功: {data}")
                return data
            except json.JSONDecodeError:
                logger.error(f"无效的JSON响应: {response.text}")
                return {
                    "success": False,
                    "error_message": "无效的JSON响应",
                    "raw_response": response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {str(e)}")
            return {
                "success": False,
                "error_message": f"请求异常: {str(e)}"
            }

    def check_health(self) -> Dict[str, Any]:
        """
        检查API服务器健康状态
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        return self._make_request("GET", "health")

    def load_model(self, model_path: str) -> Dict[str, Any]:
        """
        加载语音识别模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict[str, Any]: 加载结果
        """
        data = {
            "model_path": model_path
        }
        return self._make_request("POST", "models/load", json=data)

    def unload_model(self, model_path: str) -> Dict[str, Any]:
        """
        卸载语音识别模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict[str, Any]: 卸载结果
        """
        data = {
            "model_path": model_path
        }
        return self._make_request("POST", "models/unload", json=data)

    def list_models(self) -> Dict[str, Any]:
        """
        列出所有已加载的模型
        
        Returns:
            Dict[str, Any]: 模型列表
        """
        return self._make_request("GET", "models")

    def get_model_status(self, model_path: str) -> Dict[str, Any]:
        """
        获取特定模型的状态
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict[str, Any]: 模型状态
        """
        # 处理路径中的特殊字符
        import urllib.parse
        encoded_path = urllib.parse.quote(model_path)
        return self._make_request("GET", f"models/status/{encoded_path}")

# 演示客户端使用方法
def demonstrate_api_client():
    """演示如何使用模型API客户端"""
    print("=== Flask模型API客户端演示 ===")
    
    # 创建客户端实例
    client = ModelAPIClient()
    
    # 检查API健康状态
    print("\n1. 检查API服务器健康状态:")
    health_result = client.check_health()
    print(f"   结果: {json.dumps(health_result, ensure_ascii=False, indent=2)}")
    
    if not health_result.get("success", False):
        print("   警告: API服务器未启动或不可用")
        print("   请先运行 flask_model_api.py 启动服务器")
        return
    
    # 列出当前已加载的模型
    print("\n2. 列出当前已加载的模型:")
    models_result = client.list_models()
    print(f"   结果: {json.dumps(models_result, ensure_ascii=False, indent=2)}")
    
    # 加载默认中文模型示例
    default_model_path = "model/cn"
    print(f"\n3. 尝试加载默认模型: {default_model_path}")
    load_result = client.load_model(default_model_path)
    print(f"   结果: {json.dumps(load_result, ensure_ascii=False, indent=2)}")
    
    # 再次列出已加载的模型
    print("\n4. 再次列出已加载的模型:")
    models_result = client.list_models()
    print(f"   结果: {json.dumps(models_result, ensure_ascii=False, indent=2)}")
    
    # 获取特定模型状态
    if load_result.get("success", False):
        model_path = load_result.get("model_path", default_model_path)
        print(f"\n5. 获取模型'{model_path}'的状态:")
        status_result = client.get_model_status(model_path)
        print(f"   结果: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
    
    # 卸载模型示例
    print(f"\n6. 卸载模型示例 (按Enter继续，输入'no'跳过):")
    user_input = input().strip().lower()
    if user_input != 'no':
        unload_result = client.unload_model(default_model_path)
        print(f"   结果: {json.dumps(unload_result, ensure_ascii=False, indent=2)}")
        
        # 最后列出模型
        print("\n7. 最终模型列表:")
        final_models_result = client.list_models()
        print(f"   结果: {json.dumps(final_models_result, ensure_ascii=False, indent=2)}")

# 集成到系统中的示例代码
def integrate_with_system_example():
    """\演示如何将模型API集成到现有系统中"""
    print("\n\n=== 将模型API集成到现有系统示例 ===")
    
    class VoiceInputSystem:
        def __init__(self):
            self.model_api_client = ModelAPIClient()
            self.current_model = None
            
        def initialize(self, model_path: str = "model/cn"):
            """初始化系统并加载模型"""
            print(f"初始化语音输入系统，加载模型: {model_path}")
            
            # 首先检查API健康状态
            health_check = self.model_api_client.check_health()
            if not health_check.get("success", False):
                print("警告: 模型API服务不可用，将使用本地加载模式作为备选")
                # 这里可以添加本地加载模式的代码
                return False
            
            # 通过API加载模型
            load_result = self.model_api_client.load_model(model_path)
            if load_result.get("success", False):
                self.current_model = model_path
                print(f"模型加载成功: {model_path}")
                return True
            else:
                print(f"模型加载失败: {load_result.get('message', '未知错误')}")
                return False
        
        def shutdown(self):
            """关闭系统并卸载模型"""
            print("关闭语音输入系统")
            if self.current_model:
                print(f"卸载模型: {self.current_model}")
                self.model_api_client.unload_model(self.current_model)
                self.current_model = None
            
    # 演示系统集成
    print("创建语音输入系统实例...")
    system = VoiceInputSystem()
    print("初始化系统...")
    system.initialize()
    print("执行系统操作...")
    print("系统关闭...")
    system.shutdown()

if __name__ == "__main__":
    # 演示API客户端基本功能
    demonstrate_api_client()
    
    # 演示如何集成到现有系统
    integrate_with_system_example()

    print("\n=== 演示完成 ===")
    print("提示:")
    print("1. 确保先启动模型API服务器: python model_server/flask_model_api.py")
    print("2. 客户端可以在不同的进程中运行")
    print("3. API支持多个客户端共享同一模型实例")