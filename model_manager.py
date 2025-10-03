from typing import Optional, Dict, Any
import threading
import time
import logging
from config_loader import config  # 导入配置系统

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelManager:
    """
    模型管理器单例类，确保Vosk模型只被加载一次
    管理模型的加载、卸载和缓存
    """
    # 单例实例
    _instance: Optional['ModelManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化模型管理器"""
        # 存储已加载的模型
        self._models: Dict[str, Dict[str, Any]] = {}
        # 模型加载状态锁
        self._model_locks: Dict[str, threading.Lock] = {}
        # 加载时间记录
        self._load_times: Dict[str, float] = {}
        # 全局加载标志
        self._is_global_loading = False
        self._global_loading_lock = threading.Lock()
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        """
        加载指定路径的Vosk模型，如果已加载则直接返回
        
        Args:
            model_path: 模型路径
        
        Returns:
            包含model和recognizer的字典
        """
        # 检查模型是否已加载
        if model_path in self._models:
            logger.info(f"✅ 模型 '{model_path}' 已加载，直接使用缓存实例")
            return self._models[model_path]
        
        # 为该模型路径创建锁（如果不存在）
        if model_path not in self._model_locks:
            self._model_locks[model_path] = threading.Lock()
        
        # 获取模型锁
        with self._model_locks[model_path]:
            # 双重检查锁定模式，避免竞态条件
            if model_path in self._models:
                return self._models[model_path]
            
            # 设置全局加载状态
            with self._global_loading_lock:
                self._is_global_loading = True
            
            logger.info(f"📦 开始加载模型: {model_path}")
            start_time = time.time()
            
            try:
                # 动态导入Vosk，避免启动时就加载
                from vosk import Model, KaldiRecognizer
                
                # 创建模型和识别器
                model = Model(model_path)
                # 从配置系统获取采样率
                sample_rate = config.get("audio.sample_rate", 16000)
                recognizer = KaldiRecognizer(model, sample_rate)
                recognizer.SetWords(False)
                
                # 存储模型和识别器
                self._models[model_path] = {"model": model, "recognizer": recognizer}
                
                # 记录加载时间
                load_time = time.time() - start_time
                self._load_times[model_path] = load_time
                
                logger.info(f"✅ 模型加载完成: {model_path} (耗时: {load_time:.2f}秒)")
                
                return self._models[model_path]
            except Exception as e:
                logger.error(f"❌ 模型加载失败: {e}")
                raise
            finally:
                # 重置全局加载状态
                with self._global_loading_lock:
                    self._is_global_loading = False
    
    def get_model(self, model_path: str) -> Optional[Dict[str, Any]]:
        """
        获取已加载的模型，如果未加载则返回None
        
        Args:
            model_path: 模型路径
        
        Returns:
            包含model和recognizer的字典，或None
        """
        return self._models.get(model_path)
    
    def unload_model(self, model_path: str) -> bool:
        """
        卸载指定路径的模型
        
        Args:
            model_path: 模型路径
        
        Returns:
            是否成功卸载
        """
        if model_path not in self._models:
            logger.warning(f"⚠️ 模型 '{model_path}' 未加载，无需卸载")
            return False
        
        with self._model_locks[model_path]:
            if model_path in self._models:
                logger.info(f"🧹 开始卸载模型: {model_path}")
                del self._models[model_path]
                if model_path in self._load_times:
                    del self._load_times[model_path]
                logger.info(f"✅ 模型卸载完成: {model_path}")
                return True
        return False
    
    def unload_all_models(self) -> None:
        """卸载所有已加载的模型"""
        model_paths = list(self._models.keys())
        for model_path in model_paths:
            self.unload_model(model_path)
        logger.info("✅ 所有模型已卸载")
    
    def is_model_loaded(self, model_path: str) -> bool:
        """
        检查模型是否已加载
        
        Args:
            model_path: 模型路径
        
        Returns:
            是否已加载
        """
        return model_path in self._models
    
    def get_loaded_models(self) -> list[str]:
        """
        获取所有已加载的模型路径
        
        Returns:
            模型路径列表
        """
        return list(self._models.keys())
    
    def get_load_time(self, model_path: str) -> float:
        """
        获取模型加载时间
        
        Args:
            model_path: 模型路径
        
        Returns:
            加载时间（秒）
        """
        return self._load_times.get(model_path, 0.0)
    
    def is_global_loading(self) -> bool:
        """
        检查是否有模型正在全局加载中
        
        Returns:
            是否正在加载
        """
        with self._global_loading_lock:
            return self._is_global_loading

# 创建全局模型管理器实例
global_model_manager = ModelManager()