#!/usr/bin/env python3
"""
Flask模型加载网络API
提供本地部署的RESTful API用于加载、卸载和管理语音识别模型
"""

import os
import sys
import logging
import time
from threading import Lock
from typing import Dict, Any, Optional, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_api')

# 创建Flask应用
app = Flask(__name__)

# 模型管理器类
class ModelManager:
    """模型管理器，负责加载、卸载和管理语音识别模型"""
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._config = {
            "default_model_path": "model/cn",
            "models_directory": "model"
        }

    def load_model(self, model_path: str) -> Tuple[bool, str]:
        """
        加载语音识别模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        with self._lock:
            # 检查模型路径是否存在
            if not os.path.exists(model_path):
                return False, f"模型路径不存在: {model_path}"
            
            # 检查模型是否已经加载
            if model_path in self._models:
                return True, f"模型已加载: {model_path}"
            
            try:
                start_time = time.time()
                
                # 导入Vosk并加载模型
                try:
                    import vosk
                    model = vosk.Model(model_path)
                    recognizer = vosk.KaldiRecognizer(model, 16000)
                except ImportError:
                    return False, "未找到Vosk库，请安装"
                except Exception as e:
                    return False, f"模型加载失败: {str(e)}"
                
                load_time = time.time() - start_time
                
                # 存储模型信息
                self._models[model_path] = {
                    "model": model,
                    "recognizer": recognizer,
                    "loaded_at": time.time(),
                    "load_time": load_time,
                    "usage_count": 0
                }
                
                logger.info(f"模型加载成功: {model_path} (耗时: {load_time:.2f}秒)")
                return True, f"模型加载成功: {model_path}"
            except Exception as e:
                logger.error(f"模型加载异常: {str(e)}")
                return False, f"模型加载异常: {str(e)}"

    def unload_model(self, model_path: str) -> Tuple[bool, str]:
        """
        卸载语音识别模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        with self._lock:
            if model_path not in self._models:
                return False, f"模型未加载: {model_path}"
            
            try:
                # 释放模型资源
                del self._models[model_path]
                logger.info(f"模型已卸载: {model_path}")
                return True, f"模型已卸载: {model_path}"
            except Exception as e:
                logger.error(f"模型卸载异常: {str(e)}")
                return False, f"模型卸载异常: {str(e)}"

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有已加载的模型
        
        Returns:
            Dict[str, Dict[str, Any]]: 模型信息字典
        """
        with self._lock:
            # 返回不包含实际模型对象的信息
            result = {}
            for path, info in self._models.items():
                result[path] = {
                    "loaded_at": info["loaded_at"],
                    "load_time": info["load_time"],
                    "usage_count": info["usage_count"]
                }
            return result

    def get_model_status(self, model_path: str) -> Optional[Dict[str, Any]]:
        """
        获取特定模型的状态
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 模型状态信息
        """
        with self._lock:
            if model_path not in self._models:
                return None
            
            info = self._models[model_path]
            return {
                "loaded": True,
                "loaded_at": info["loaded_at"],
                "load_time": info["load_time"],
                "usage_count": info["usage_count"]
            }

# 初始化模型管理器
global_model_manager = ModelManager()

# API端点定义
@app.route('/api/models/load', methods=['POST'])
def api_load_model():
    """
    加载模型API端点
    POST /api/models/load
    Body: {"model_path": "path/to/model"}
    """
    try:
        data = request.get_json()
        if not data or 'model_path' not in data:
            return jsonify({
                "success": False,
                "message": "请求缺少model_path参数"
            }), 400
        
        model_path = data['model_path']
        
        # 确保路径是绝对路径或相对于项目根目录
        if not os.path.isabs(model_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(project_root, model_path)
        
        success, message = global_model_manager.load_model(model_path)
        
        return jsonify({
            "success": success,
            "message": message,
            "model_path": model_path
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"加载模型API异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/models/unload', methods=['POST'])
def api_unload_model():
    """
    卸载模型API端点
    POST /api/models/unload
    Body: {"model_path": "path/to/model"}
    """
    try:
        data = request.get_json()
        if not data or 'model_path' not in data:
            return jsonify({
                "success": False,
                "message": "请求缺少model_path参数"
            }), 400
        
        model_path = data['model_path']
        
        # 确保路径是绝对路径或相对于项目根目录
        if not os.path.isabs(model_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(project_root, model_path)
        
        success, message = global_model_manager.unload_model(model_path)
        
        return jsonify({
            "success": success,
            "message": message,
            "model_path": model_path
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"卸载模型API异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/models', methods=['GET'])
def api_list_models():
    """
    列出所有已加载模型的API端点
    GET /api/models
    """
    try:
        models = global_model_manager.list_models()
        return jsonify({
            "success": True,
            "models": models,
            "count": len(models)
        }), 200
    except Exception as e:
        logger.error(f"列出模型API异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/models/status/<path:model_path>', methods=['GET'])
def api_model_status(model_path):
    """
    获取特定模型状态的API端点
    GET /api/models/status/<model_path>
    """
    try:
        # 确保路径是绝对路径或相对于项目根目录
        if not os.path.isabs(model_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(project_root, model_path)
        
        status = global_model_manager.get_model_status(model_path)
        if status:
            return jsonify({
                "success": True,
                "status": status,
                "model_path": model_path
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": f"模型未加载: {model_path}",
                "model_path": model_path
            }), 404
    except Exception as e:
        logger.error(f"模型状态API异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """
    健康检查API端点
    GET /api/health
    """
    try:
        models = global_model_manager.list_models()
        return jsonify({
            "success": True,
            "status": "running",
            "loaded_models_count": len(models),
            "version": "1.0.0"
        }), 200
    except Exception as e:
        logger.error(f"健康检查API异常: {str(e)}")
        return jsonify({
            "success": False,
            "status": "error",
            "message": str(e)
        }), 500

# 错误处理
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """处理HTTP异常"""
    return jsonify({
        "success": False,
        "error": e.name,
        "code": e.code,
        "message": e.description
    }), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    """处理未捕获的异常"""
    logger.error(f"未捕获的异常: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

# 启动服务器
if __name__ == '__main__':
    # 创建model_server目录（如果不存在）
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # 启动Flask服务器
    print("=== Flask模型加载API服务器 ==")
    print("服务端点:")
    print("- GET    /api/health             - 健康检查")
    print("- GET    /api/models             - 列出所有已加载的模型")
    print("- GET    /api/models/status/<path> - 获取特定模型状态")
    print("- POST   /api/models/load        - 加载模型")
    print("- POST   /api/models/unload      - 卸载模型")
    print("
启动服务器...")
    
    # 在生产环境中，应该使用Gunicorn或uWSGI等WSGI服务器
    app.run(host='0.0.0.0', port=5000, debug=False)