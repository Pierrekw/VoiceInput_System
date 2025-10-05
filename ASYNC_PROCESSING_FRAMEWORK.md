# 异步处理框架设计与实现方案

## 1. 概述

本方案详细介绍了语音输入系统的异步处理框架设计与实现，重点解决以下核心问题：

- **异步任务生命周期管理**：确保异步任务能够正确创建、执行、取消和清理
- **资源泄漏防止**：避免"Task was destroyed but it is pending!"错误
- **系统稳定性**：提供健壮的异常处理和资源回收机制
- **高效的事件驱动架构**：实现松耦合、高可扩展的系统设计

## 2. 系统架构

### 2.1 总体架构

异步处理框架采用事件驱动、组件化的架构设计，主要包含以下层次：

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                  │
│  ┌───────────────┐    ┌───────────────────────────────┐ │
│  │  系统入口     │    │  控制中心 (Controller)         │ │
│  └───────────────┘    └───────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    业务逻辑层 (Business)                 │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────┐  │
│  │  语音识别     │    │  文本处理     │    │  TTS    │  │
│  └───────────────┘    └───────────────┘    └─────────┘  │
├─────────────────────────────────────────────────────────┤
│                    数据层 (Data)                         │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────┐  │
│  │  音频流处理   │    │  数据存储     │    │  配置   │  │
│  └───────────────┘    └───────────────┘    └─────────┘  │
├─────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)           │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────┐  │
│  │  事件总线     │    │  任务管理     │    │  日志   │  │
│  └───────────────┘    └───────────────┘    └─────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心组件关系

![组件关系图]()

- **事件总线**：连接所有组件，实现松耦合通信
- **任务管理器**：负责异步任务的创建、跟踪和清理
- **资源管理器**：管理系统资源的分配和释放
- **音频流控制器**：处理音频数据的采集和流处理
- **错误处理器**：统一处理系统中的异常情况

## 3. 异步任务管理机制

### 3.1 任务创建与跟踪

```python
class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_concurrent_tasks=10, task_timeout=60):
        # 任务集合，用于跟踪所有活动任务
        self.tasks = set()
        # 最大并发任务数限制
        self.max_concurrent_tasks = max_concurrent_tasks
        # 任务超时时间（秒）
        self.task_timeout = task_timeout
        # 任务ID计数器
        self.task_counter = 0
        # 任务映射表（任务ID -> 任务对象）
        self.task_map = {}
        # 锁，用于线程安全操作
        self._lock = asyncio.Lock()
    
    async def create_task(self, coro, task_name="Task", timeout=None):
        """创建并跟踪一个异步任务"""
        # 获取锁确保线程安全
        async with self._lock:
            # 检查并发任务数限制
            if len(self.tasks) >= self.max_concurrent_tasks:
                # 等待一些任务完成或超时
                await self._wait_for_task_slot()
            
            # 生成任务ID
            self.task_counter += 1
            task_id = f"{task_name}-{self.task_counter}"
            
            # 包装协程，添加超时和异常处理
            wrapped_coro = self._wrap_coroutine(coro, task_id, timeout)
            
            # 创建任务
            task = asyncio.create_task(wrapped_coro, name=task_id)
            
            # 添加到任务集合
            self.tasks.add(task)
            self.task_map[task_id] = task
            
            # 添加完成回调，任务完成后从集合中移除
            task.add_done_callback(self._task_done_callback)
            
            return task_id
    
    async def _wrap_coroutine(self, coro, task_id, timeout=None):
        """包装协程，添加超时和异常处理"""
        try:
            # 使用提供的超时或默认超时
            timeout_val = timeout if timeout is not None else self.task_timeout
            
            # 添加超时机制
            if timeout_val > 0:
                return await asyncio.wait_for(coro, timeout=timeout_val)
            else:
                return await coro
        except asyncio.TimeoutError:
            logging.warning(f"⏱️ 任务超时: {task_id}")
        except asyncio.CancelledError:
            logging.info(f"🚫 任务被取消: {task_id}")
            raise  # 重新抛出CancelledError，让任务状态正确反映为已取消
        except Exception as e:
            logging.error(f"❌ 任务执行异常: {task_id}, 错误: {e}")
        finally:
            # 确保任务资源被清理
            pass
    
    def _task_done_callback(self, task):
        """任务完成回调"""
        # 从任务集合中移除已完成的任务
        if task in self.tasks:
            self.tasks.remove(task)
            
            # 从任务映射表中移除
            for task_id, t in list(self.task_map.items()):
                if t == task:
                    del self.task_map[task_id]
                    break
        
        # 检查任务是否有异常
        try:
            task.result()  # 这会重新抛出任务中的异常
        except asyncio.CancelledError:
            logging.debug(f"🔄 任务已取消: {task.get_name()}")
        except Exception as e:
            logging.error(f"❌ 任务内部异常未捕获: {task.get_name()}, 错误: {e}")
    
    async def _wait_for_task_slot(self):
        """等待可用的任务槽位"""
        logging.warning(f"⚠️ 达到最大并发任务数: {self.max_concurrent_tasks}")
        
        # 等待最短时间的任务完成或超时
        if self.tasks:
            # 等待任意一个任务完成
            done, pending = await asyncio.wait(
                self.tasks, 
                return_when=asyncio.FIRST_COMPLETED, 
                timeout=1.0  # 1秒后超时，避免无限等待
            )
            
            if not done:
                # 如果没有任务完成，取消最老的任务
                oldest_task = min(self.tasks, key=lambda t: t.get_name())
                logging.warning(f"🔄 取消最老的任务: {oldest_task.get_name()}")
                oldest_task.cancel()
                try:
                    await oldest_task
                except asyncio.CancelledError:
                    pass
    
    async def cancel_task(self, task_id):
        """取消指定的任务"""
        async with self._lock:
            if task_id in self.task_map:
                task = self.task_map[task_id]
                if not task.done():
                    logging.info(f"🚫 取消任务: {task_id}")
                    task.cancel()
                    try:
                        # 等待任务被取消
                        await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
                    except asyncio.CancelledError:
                        pass
                    except asyncio.TimeoutError:
                        logging.warning(f"⚠️ 任务取消超时: {task_id}")
                return True
            return False
    
    async def cancel_all_tasks(self):
        """取消所有任务"""
        async with self._lock:
            tasks_to_cancel = list(self.tasks)
            
            if not tasks_to_cancel:
                return []
            
            logging.info(f"🚫 取消所有任务 ({len(tasks_to_cancel)}个)")
            
            # 取消所有任务
            for task in tasks_to_cancel:
                if not task.done():
                    task.cancel()
            
            # 等待所有任务被取消
            results = []
            for task in tasks_to_cancel:
                try:
                    result = await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
                    results.append((task.get_name(), True, result))
                except asyncio.CancelledError:
                    results.append((task.get_name(), True, None))
                except asyncio.TimeoutError:
                    results.append((task.get_name(), False, "Timeout"))
                except Exception as e:
                    results.append((task.get_name(), False, str(e)))
            
            # 清空任务集合
            self.tasks.clear()
            self.task_map.clear()
            
            return results
    
    def get_task_count(self):
        """获取当前活动任务数"""
        return len(self.tasks)
    
    def get_active_tasks(self):
        """获取所有活动任务的信息"""
        return [{
            'id': task.get_name(),
            'done': task.done(),
            'cancelled': task.cancelled()
        } for task in self.tasks]
```

### 3.2 异步任务的取消与清理机制

为了解决"Task was destroyed but it is pending!"错误，框架实现了完善的任务取消和清理机制：

1. **任务跟踪**：所有创建的任务都被添加到集中管理的任务集合中
2. **超时机制**：每个任务都有超时设置，避免任务无限期运行
3. **优雅取消**：通过`task.cancel()`和`await task`组合实现任务的优雅取消
4. **资源回收**：任务完成后自动清理相关资源
5. **系统关闭流程**：在系统关闭时确保所有任务都被正确取消和清理

以下是系统关闭时的任务清理流程：

```python
async def graceful_shutdown(self):
    """优雅关闭系统"""
    logging.info("🛑 开始优雅关闭系统...")
    
    try:
        # 1. 停止接受新任务
        self.running = False
        
        # 2. 取消所有任务
        cancel_results = await self.task_manager.cancel_all_tasks()
        
        # 3. 记录任务取消结果
        success_count = sum(1 for _, success, _ in cancel_results if success)
        fail_count = sum(1 for _, success, _ in cancel_results if not success)
        
        logging.info(f"✅ 任务取消结果: 成功={success_count}, 失败={fail_count}")
        
        # 4. 清理资源
        await self._cleanup_resources()
        
        # 5. 等待一段时间确保所有资源都被释放
        await asyncio.sleep(0.1)
        
        logging.info("✅ 系统已优雅关闭")
        return True
    except Exception as e:
        logging.error(f"❌ 优雅关闭失败: {e}")
        return False
```

### 3.3 防止资源泄漏的最佳实践

1. **总是跟踪任务**：确保每个创建的任务都被添加到任务管理器中
2. **使用asyncio.shield**：保护关键任务不被意外取消
3. **避免长时间阻塞**：不要在异步代码中使用阻塞式IO操作
4. **正确处理异常**：特别是CancelledError异常
5. **限制并发任务数**：防止系统资源耗尽
6. **使用上下文管理器**：自动管理资源的分配和释放

## 4. 事件驱动架构实现

### 4.1 事件总线设计

```python
class EventBus:
    """异步事件总线"""
    
    def __init__(self):
        # 事件订阅者映射表
        self.subscribers = {}
        # 锁，用于线程安全操作
        self._lock = asyncio.Lock()
    
    async def subscribe(self, event_type, subscriber):
        """订阅事件"""
        async with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            
            if subscriber not in self.subscribers[event_type]:
                self.subscribers[event_type].append(subscriber)
                logging.debug(f"✅ 订阅事件: {event_type}, 订阅者: {subscriber.__class__.__name__}")
    
    async def unsubscribe(self, event_type, subscriber):
        """取消订阅事件"""
        async with self._lock:
            if event_type in self.subscribers and subscriber in self.subscribers[event_type]:
                self.subscribers[event_type].remove(subscriber)
                logging.debug(f"✅ 取消订阅事件: {event_type}, 订阅者: {subscriber.__class__.__name__}")
                
                # 如果没有订阅者了，移除事件类型
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
    
    async def publish(self, event_type, data=None):
        """发布事件"""
        # 创建事件对象
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.datetime.now()
        }
        
        # 获取订阅者列表的副本，避免在迭代过程中修改列表
        async with self._lock:
            if event_type not in self.subscribers:
                return []
            
            # 创建订阅者列表的副本
            subscribers = self.subscribers[event_type].copy()
        
        # 异步通知所有订阅者
        tasks = []
        for subscriber in subscribers:
            # 为每个订阅者创建一个任务
            task = asyncio.create_task(self._notify_subscriber(subscriber, event))
            tasks.append(task)
        
        # 等待所有通知任务完成
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    subscriber = subscribers[i]
                    logging.error(f"❌ 通知订阅者失败: {subscriber.__class__.__name__}, 错误: {result}")
            
            return results
        
        return []
    
    async def _notify_subscriber(self, subscriber, event):
        """通知单个订阅者"""
        try:
            # 检查subscriber是否为可调用对象
            if callable(subscriber):
                return await subscriber(event)
            # 检查subscriber是否有handle_event方法
            elif hasattr(subscriber, 'handle_event') and callable(subscriber.handle_event):
                return await subscriber.handle_event(event)
            else:
                logging.error(f"❌ 无效的订阅者: {subscriber}, 不是可调用对象或没有handle_event方法")
                return None
        except Exception as e:
            logging.error(f"❌ 处理事件失败: {event['type']}, 订阅者: {subscriber.__class__.__name__}, 错误: {e}")
            raise
    
    def get_subscriber_count(self, event_type=None):
        """获取订阅者数量"""
        if event_type:
            return len(self.subscribers.get(event_type, []))
        else:
            return sum(len(subscribers) for subscribers in self.subscribers.values())
```

### 4.2 事件类型定义

```python
class EventType:
    """事件类型定义"""
    # 音频相关事件
    AUDIO_DATA_AVAILABLE = "AUDIO_DATA_AVAILABLE"  # 音频数据可用
    AUDIO_STREAM_STARTED = "AUDIO_STREAM_STARTED"  # 音频流开始
    AUDIO_STREAM_STOPPED = "AUDIO_STREAM_STOPPED"  # 音频流停止
    
    # 识别相关事件
    RECOGNITION_STARTED = "RECOGNITION_STARTED"    # 识别开始
    RECOGNITION_COMPLETE = "RECOGNITION_COMPLETE"  # 识别完成
    RECOGNITION_FAILED = "RECOGNITION_FAILED"      # 识别失败
    
    # 文本处理相关事件
    TEXT_PROCESSED = "TEXT_PROCESSED"              # 文本处理完成
    MEASUREMENT_EXTRACTED = "MEASUREMENT_EXTRACTED"  # 数值提取完成
    
    # TTS相关事件
    TTS_SPEAK_STARTED = "TTS_SPEAK_STARTED"        # TTS开始播报
    TTS_SPEAK_COMPLETE = "TTS_SPEAK_COMPLETE"      # TTS播报完成
    TTS_SPEAK_FAILED = "TTS_SPEAK_FAILED"          # TTS播报失败
    
    # 数据存储相关事件
    DATA_EXPORT_STARTED = "DATA_EXPORT_STARTED"    # 数据导出开始
    DATA_EXPORT_COMPLETE = "DATA_EXPORT_COMPLETE"  # 数据导出完成
    DATA_EXPORT_FAILED = "DATA_EXPORT_FAILED"      # 数据导出失败
    
    # 系统相关事件
    SYSTEM_STARTED = "SYSTEM_STARTED"              # 系统启动
    SYSTEM_STOPPED = "SYSTEM_STOPPED"              # 系统停止
    ERROR_OCCURRED = "ERROR_OCCURRED"              # 发生错误
    WARNING_OCCURRED = "WARNING_OCCURRED"          # 发生警告
    
    # 配置相关事件
    CONFIG_CHANGED = "CONFIG_CHANGED"              # 配置变更
    
    # 调试相关事件
    DEBUG_INFO = "DEBUG_INFO"                      # 调试信息
```

## 5. 音频流处理实现

### 5.1 异步音频流控制器

```python
class AsyncAudioStreamController:
    """异步音频流控制器"""
    
    def __init__(self, config=None):
        # 配置
        self.config = config or {}
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.channels = self.config.get('channels', 1)
        self.format = self.config.get('format', 16)
        self.chunk_size = self.config.get('chunk_size', 4096)
        
        # 音频流状态
        self.running = False
        self.audio_stream = None
        self.audio_source = None
        
        # 回调函数
        self.callbacks = {}
        
        # 任务引用
        self.stream_task = None
        
        # 缓冲区
        self.buffer = asyncio.Queue(maxsize=10)
    
    async def start(self):
        """启动音频流"""
        if self.running:
            logging.warning("⚠️ 音频流已经在运行中")
            return False
        
        try:
            logging.info(f"▶️ 启动音频流: 采样率={self.sample_rate}, 通道={self.channels}, 块大小={self.chunk_size}")
            
            # 初始化音频源
            await self._initialize_audio_source()
            
            # 创建音频流任务
            self.running = True
            self.stream_task = asyncio.create_task(self._audio_stream_task())
            
            # 发布音频流启动事件
            await self._notify_callbacks(EventType.AUDIO_STREAM_STARTED, {
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'format': self.format,
                'chunk_size': self.chunk_size
            })
            
            logging.info("✅ 音频流启动成功")
            return True
        except Exception as e:
            logging.error(f"❌ 音频流启动失败: {e}")
            self.running = False
            await self._cleanup_audio_source()
            return False
    
    async def stop(self):
        """停止音频流"""
        if not self.running:
            logging.warning("⚠️ 音频流已经停止")
            return False
        
        try:
            logging.info("⏹️ 停止音频流...")
            
            # 停止运行标志
            self.running = False
            
            # 取消音频流任务
            if self.stream_task and not self.stream_task.done():
                self.stream_task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(self.stream_task), timeout=2.0)
                except asyncio.CancelledError:
                    pass
                except asyncio.TimeoutError:
                    logging.warning("⚠️ 音频流任务取消超时")
            
            # 清理音频源
            await self._cleanup_audio_source()
            
            # 清空缓冲区
            while not self.buffer.empty():
                try:
                    self.buffer.get_nowait()
                    self.buffer.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # 发布音频流停止事件
            await self._notify_callbacks(EventType.AUDIO_STREAM_STOPPED)
            
            logging.info("✅ 音频流停止成功")
            return True
        except Exception as e:
            logging.error(f"❌ 音频流停止失败: {e}")
            return False
    
    async def _initialize_audio_source(self):
        """初始化音频源"""
        # 这里应该根据实际情况初始化音频源
        # 例如使用PyAudio、sounddevice等库
        # 以下是一个示例实现
        try:
            # 模拟音频源初始化
            logging.info("🎤 初始化音频源...")
            # self.audio_source = ...  # 实际的音频源初始化代码
        except Exception as e:
            logging.error(f"❌ 音频源初始化失败: {e}")
            raise
    
    async def _cleanup_audio_source(self):
        """清理音频源"""
        try:
            if self.audio_source:
                # 模拟音频源清理
                logging.info("🎤 清理音频源...")
                # self.audio_source.close()  # 实际的音频源清理代码
                self.audio_source = None
        except Exception as e:
            logging.error(f"❌ 音频源清理失败: {e}")
    
    async def _audio_stream_task(self):
        """音频流处理任务"""
        try:
            logging.info("🔄 进入音频流处理循环")
            
            while self.running:
                try:
                    # 模拟获取音频数据
                    # 在实际实现中，这里应该从音频源读取数据
                    audio_data = self._get_audio_data()
                    
                    if audio_data:
                        # 将音频数据放入缓冲区
                        try:
                            await asyncio.wait_for(
                                self.buffer.put(audio_data), 
                                timeout=0.1
                            )
                            
                            # 发布音频数据可用事件
                            await self._notify_callbacks(EventType.AUDIO_DATA_AVAILABLE, audio_data)
                        except asyncio.TimeoutError:
                            # 缓冲区已满，丢弃数据
                            logging.warning("⚠️ 音频缓冲区已满，丢弃数据")
                            # 可以选择清空缓冲区
                            # while not self.buffer.empty():
                            #     self.buffer.get_nowait()
                            #     self.buffer.task_done()
                except Exception as e:
                    logging.error(f"❌ 音频数据获取失败: {e}")
                    # 短暂暂停后继续
                    await asyncio.sleep(0.01)
                
                # 短暂暂停，避免CPU占用过高
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            logging.info("🚫 音频流任务被取消")
            raise
        except Exception as e:
            logging.error(f"❌ 音频流任务异常: {e}")
            # 发布错误事件
            await self._notify_callbacks(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '音频流处理'
            })
    
    def _get_audio_data(self):
        """获取音频数据（模拟实现）"""
        # 在实际实现中，这里应该从音频源读取数据
        # 例如使用PyAudio的stream.read()方法
        return b""  # 返回实际的音频数据
    
    def register_callback(self, event_type, callback):
        """注册回调函数"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        if callback not in self.callbacks[event_type]:
            self.callbacks[event_type].append(callback)
            logging.debug(f"✅ 注册回调: {event_type}, 回调: {callback.__name__}")
    
    def unregister_callback(self, event_type, callback):
        """取消注册回调函数"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
            logging.debug(f"✅ 取消注册回调: {event_type}, 回调: {callback.__name__}")
    
    async def _notify_callbacks(self, event_type, data=None):
        """通知所有注册的回调函数"""
        if event_type in self.callbacks:
            # 为每个回调创建一个任务
            tasks = []
            for callback in self.callbacks[event_type]:
                if callable(callback):
                    # 检查是否是协程函数
                    if asyncio.iscoroutinefunction(callback):
                        task = asyncio.create_task(callback(data))
                        tasks.append(task)
                    else:
                        # 对于同步回调，使用线程池执行
                        loop = asyncio.get_event_loop()
                        task = loop.run_in_executor(
                            None, 
                            lambda: self._safe_execute_callback(callback, data)
                        )
                        tasks.append(task)
            
            # 等待所有回调任务完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _safe_execute_callback(self, callback, data):
        """安全执行同步回调函数"""
        try:
            callback(data)
        except Exception as e:
            logging.error(f"❌ 回调执行失败: {callback.__name__}, 错误: {e}")
    
    async def get_audio_data(self, timeout=None):
        """从缓冲区获取音频数据"""
        try:
            if timeout is not None:
                return await asyncio.wait_for(self.buffer.get(), timeout=timeout)
            else:
                return await self.buffer.get()
        except asyncio.TimeoutError:
            logging.warning("⚠️ 获取音频数据超时")
            return None
    
    def is_running(self):
        """检查音频流是否正在运行"""
        return self.running
    
    def get_buffer_size(self):
        """获取缓冲区中的数据量"""
        return self.buffer.qsize()
```

## 6. 异步TTS管理器实现

```python
class AsyncTTSManager:
    """异步TTS管理器"""
    
    def __init__(self, config=None):
        # 配置
        self.config = config or {}
        self.voice = self.config.get('voice', 'zh-CN')
        self.speed = self.config.get('speed', 1.0)
        self.volume = self.config.get('volume', 1.0)
        
        # TTS引擎
        self.tts_engine = None
        self.audio_player = None
        
        # 状态
        self.initialized = False
        self.speaking = False
        
        # 音频队列
        self.audio_queue = asyncio.Queue(maxsize=5)
        
        # 播放任务
        self.playback_task = None
        
        # 语音反馈关键词，用于检测系统自身的TTS输出
        self.tts_feedback_keywords = ["成功提取", "识别到", "已记录", "数值是", "结果是"]
    
    async def initialize(self):
        """初始化TTS管理器"""
        if self.initialized:
            logging.warning("⚠️ TTS管理器已经初始化")
            return True
        
        try:
            logging.info(f"🔊 初始化TTS管理器: 语音={self.voice}, 语速={self.speed}, 音量={self.volume}")
            
            # 初始化TTS引擎
            await self._initialize_tts_engine()
            
            # 初始化音频播放器
            await self._initialize_audio_player()
            
            # 创建播放任务
            self.playback_task = asyncio.create_task(self._playback_task())
            
            self.initialized = True
            logging.info("✅ TTS管理器初始化成功")
            return True
        except Exception as e:
            logging.error(f"❌ TTS管理器初始化失败: {e}")
            await self.cleanup()
            return False
    
    async def _initialize_tts_engine(self):
        """初始化TTS引擎"""
        # 这里应该根据实际情况初始化TTS引擎
        # 例如使用piper-tts、pyttsx3等库
        # 以下是一个示例实现
        try:
            logging.info("🔊 初始化TTS引擎...")
            # self.tts_engine = ...  # 实际的TTS引擎初始化代码
        except Exception as e:
            logging.error(f"❌ TTS引擎初始化失败: {e}")
            raise
    
    async def _initialize_audio_player(self):
        """初始化音频播放器"""
        # 这里应该根据实际情况初始化音频播放器
        # 例如使用PyAudio、sounddevice等库
        # 以下是一个示例实现
        try:
            logging.info("🔊 初始化音频播放器...")
            # self.audio_player = ...  # 实际的音频播放器初始化代码
        except Exception as e:
            logging.error(f"❌ 音频播放器初始化失败: {e}")
            raise
    
    async def speak(self, text):
        """异步播放文本"""
        if not self.initialized:
            logging.error("❌ TTS管理器未初始化")
            return False
        
        try:
            logging.debug(f"🔊 准备播报: {text}")
            
            # 检查是否为系统自身的TTS反馈（避免循环）
            if self._is_tts_feedback(text):
                logging.warning(f"⚠️ 检测到TTS反馈文本，跳过播报: {text}")
                return False
            
            # 生成音频数据
            audio_data = await self._generate_speech(text)
            
            if not audio_data:
                logging.error("❌ 生成语音数据失败")
                return False
            
            # 将音频数据放入队列
            try:
                await asyncio.wait_for(self.audio_queue.put(audio_data), timeout=1.0)
            except asyncio.TimeoutError:
                logging.error("❌ 音频队列已满，无法添加新的语音数据")
                return False
            
            # 发布TTS开始播报事件
            await self._publish_event(EventType.TTS_SPEAK_STARTED, {
                'text': text
            })
            
            return True
        except Exception as e:
            logging.error(f"❌ TTS播报失败: {e}")
            # 发布TTS播报失败事件
            await self._publish_event(EventType.TTS_SPEAK_FAILED, {
                'text': text,
                'error': str(e)
            })
            return False
    
    def _is_tts_feedback(self, text):
        """检查文本是否为系统自身的TTS反馈"""
        # 检查是否包含任何TTS反馈关键词
        return any(keyword in text for keyword in self.tts_feedback_keywords)
    
    async def _generate_speech(self, text):
        """生成语音数据"""
        # 在实际实现中，这里应该使用TTS引擎将文本转换为音频数据
        # 以下是一个示例实现
        try:
            logging.debug(f"🔊 生成语音数据: {text}")
            # audio_data = self.tts_engine.synthesize(text, voice=self.voice, speed=self.speed)
            return b""  # 返回实际的音频数据
        except Exception as e:
            logging.error(f"❌ 生成语音数据失败: {e}")
            raise
    
    async def _playback_task(self):
        """音频播放任务"""
        try:
            logging.info("🔄 进入TTS播放循环")
            
            while self.initialized:
                try:
                    # 从队列获取音频数据
                    audio_data = await self.audio_queue.get()
                    
                    if audio_data:
                        # 播放音频数据
                        await self._play_audio(audio_data)
                        
                    # 标记任务完成
                    self.audio_queue.task_done()
                except Exception as e:
                    logging.error(f"❌ 音频播放失败: {e}")
                    # 确保任务标记为完成
                    if not self.audio_queue.empty():
                        self.audio_queue.task_done()
        except asyncio.CancelledError:
            logging.info("🚫 TTS播放任务被取消")
            raise
        except Exception as e:
            logging.error(f"❌ TTS播放任务异常: {e}")
    
    async def _play_audio(self, audio_data):
        """播放音频数据"""
        # 在实际实现中，这里应该使用音频播放器播放音频数据
        # 以下是一个示例实现
        try:
            self.speaking = True
            logging.debug("🔊 开始播放音频...")
            # await self.audio_player.play(audio_data)  # 实际的音频播放代码
            
            # 模拟播放延迟
            await asyncio.sleep(0.5)  # 根据实际音频长度调整
            
            logging.debug("🔊 音频播放完成")
            
            # 发布TTS播报完成事件
            await self._publish_event(EventType.TTS_SPEAK_COMPLETE)
        except Exception as e:
            logging.error(f"❌ 音频播放失败: {e}")
            # 发布TTS播报失败事件
            await self._publish_event(EventType.TTS_SPEAK_FAILED, {
                'error': str(e)
            })
        finally:
            self.speaking = False
    
    async def cleanup(self):
        """清理资源"""
        try:
            logging.info("🔊 清理TTS资源...")
            
            # 停止播放任务
            if self.playback_task and not self.playback_task.done():
                self.playback_task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(self.playback_task), timeout=2.0)
                except asyncio.CancelledError:
                    pass
                except asyncio.TimeoutError:
                    logging.warning("⚠️ TTS播放任务取消超时")
            
            # 清理音频播放器
            if self.audio_player:
                logging.info("🔊 清理音频播放器...")
                # await self.audio_player.cleanup()  # 实际的音频播放器清理代码
                self.audio_player = None
            
            # 清理TTS引擎
            if self.tts_engine:
                logging.info("🔊 清理TTS引擎...")
                # await self.tts_engine.shutdown()  # 实际的TTS引擎清理代码
                self.tts_engine = None
            
            # 清空音频队列
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            self.initialized = False
            self.speaking = False
            
            logging.info("✅ TTS资源清理完成")
        except Exception as e:
            logging.error(f"❌ TTS资源清理失败: {e}")
    
    async def _publish_event(self, event_type, data=None):
        """发布事件"""
        # 在实际实现中，这里应该使用事件总线发布事件
        # 以下是一个示例实现
        logging.debug(f"📡 发布TTS事件: {event_type}, 数据: {data}")
        # await event_bus.publish(event_type, data)  # 实际的事件发布代码
    
    def is_speaking(self):
        """检查是否正在播放音频"""
        return self.speaking
    
    def is_initialized(self):
        """检查TTS管理器是否已初始化"""
        return self.initialized
    
    def get_queue_size(self):
        """获取音频队列中的任务数"""
        return self.audio_queue.qsize()
```

## 7. 系统集成示例

### 7.1 主系统类实现

```python
class AsyncVoiceInputSystem:
    """异步语音输入系统主类"""
    
    def __init__(self):
        # 系统状态
        self.running = False
        
        # 事件循环
        self.loop = asyncio.get_event_loop()
        
        # 核心组件
        self.config = None
        self.event_bus = None
        self.task_manager = None
        self.audio_stream_controller = None
        self.voice_recognizer = None
        self.text_processor = None
        self.tts_manager = None
        self.data_exporter = None
        self.error_handler = None
        
        # 初始化系统
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化系统组件"""
        logging.info("🚀 初始化异步语音输入系统...")
        
        try:
            # 加载配置
            self.config = self._load_config()
            
            # 创建事件总线
            self.event_bus = EventBus()
            
            # 创建任务管理器
            self.task_manager = AsyncTaskManager(
                max_concurrent_tasks=self.config.get('async_specific.max_concurrent_tasks', 10),
                task_timeout=self.config.get('async_specific.task_timeout', 60)
            )
            
            # 创建错误处理器
            self.error_handler = ErrorHandler(self.event_bus)
            
            # 创建音频流控制器
            self.audio_stream_controller = AsyncAudioStreamController({
                'sample_rate': self.config.get('audio.sample_rate', 16000),
                'channels': self.config.get('audio.channels', 1),
                'chunk_size': self.config.get('audio.chunk_size', 4096)
            })
            
            # 注册音频数据回调
            self.audio_stream_controller.register_callback(
                EventType.AUDIO_DATA_AVAILABLE, 
                self._handle_audio_data_available
            )
            
            # 创建语音识别器
            self.voice_recognizer = AsyncVoiceRecognizer({
                'model_path': self.config.get('recognition.model_path', 'models'),
                'language': self.config.get('recognition.language', 'zh-CN')
            })
            
            # 创建文本处理器
            self.text_processor = TextProcessor({
                'error_correction': self.config.get('error_correction.enabled', True)
            })
            
            # 创建TTS管理器
            if self.config.get('tts.enabled', True):
                self.tts_manager = AsyncTTSManager({
                    'voice': self.config.get('tts.voice', 'zh-CN'),
                    'speed': self.config.get('tts.speed', 1.0),
                    'volume': self.config.get('tts.volume', 1.0)
                })
            
            # 创建数据导出器
            if self.config.get('excel.auto_export', True):
                self.data_exporter = DataExporter({
                    'file_path': self.config.get('excel.file_path', 'voice_data.xlsx'),
                    'sheet_name': self.config.get('excel.sheet_name', 'Data')
                })
            
            # 注册事件处理器
            self._register_event_handlers()
            
            logging.info("✅ 系统组件初始化完成")
        except Exception as e:
            logging.error(f"❌ 系统组件初始化失败: {e}")
            raise
    
    def _load_config(self):
        """加载配置"""
        # 这里应该从配置文件加载配置
        # 以下是一个示例实现
        return {
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'chunk_size': 4096
            },
            'recognition': {
                'model_path': 'models',
                'language': 'zh-CN'
            },
            'tts': {
                'enabled': True,
                'voice': 'zh-CN',
                'speed': 1.0,
                'volume': 1.0
            },
            'excel': {
                'auto_export': True,
                'file_path': 'voice_data.xlsx',
                'sheet_name': 'Data'
            },
            'error_correction': {
                'enabled': True
            },
            'async_specific': {
                'max_concurrent_tasks': 10,
                'task_timeout': 60
            }
        }
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        # 注册识别完成事件处理器
        self.event_bus.subscribe(EventType.RECOGNITION_COMPLETE, self._handle_recognition_complete)
        
        # 注册文本处理完成事件处理器
        self.event_bus.subscribe(EventType.TEXT_PROCESSED, self._handle_text_processed)
        
        # 注册数值提取完成事件处理器
        self.event_bus.subscribe(EventType.MEASUREMENT_EXTRACTED, self._handle_measurement_extracted)
        
        # 注册错误事件处理器
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._handle_error)
    
    def start(self):
        """启动系统"""
        try:
            if self.running:
                logging.warning("⚠️ 系统已经在运行中")
                return False
            
            logging.info("▶️ 启动异步语音输入系统...")
            
            # 异步初始化并启动系统
            self.loop.run_until_complete(self._start_async())
            
            # 运行事件循环
            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                logging.info("🛑 用户中断")
            except Exception as e:
                logging.error(f"❌ 事件循环异常: {e}")
            finally:
                # 优雅关闭系统
                self.loop.run_until_complete(self._stop_async())
                
                # 关闭事件循环
                self.loop.close()
            
            return True
        except Exception as e:
            logging.error(f"❌ 系统启动失败: {e}")
            return False
    
    async def _start_async(self):
        """异步启动系统"""
        try:
            # 初始化TTS管理器
            if self.tts_manager:
                await self.tts_manager.initialize()
            
            # 启动音频流控制器
            if not await self.audio_stream_controller.start():
                raise Exception("音频流控制器启动失败")
            
            # 标记系统为运行状态
            self.running = True
            
            # 发布系统启动事件
            await self.event_bus.publish(EventType.SYSTEM_STARTED)
            
            logging.info("✅ 异步语音输入系统启动成功")
        except Exception as e:
            logging.error(f"❌ 异步启动系统失败: {e}")
            await self._stop_async()
            raise
    
    async def _stop_async(self):
        """异步停止系统"""
        try:
            if not self.running:
                logging.warning("⚠️ 系统已经停止")
                return False
            
            logging.info("⏹️ 停止异步语音输入系统...")
            
            # 标记系统为非运行状态
            self.running = False
            
            # 停止音频流控制器
            if self.audio_stream_controller:
                await self.audio_stream_controller.stop()
            
            # 取消所有任务
            if self.task_manager:
                await self.task_manager.cancel_all_tasks()
            
            # 清理TTS管理器
            if self.tts_manager:
                await self.tts_manager.cleanup()
            
            # 清理数据导出器
            if self.data_exporter:
                await self.data_exporter.cleanup()
            
            # 发布系统停止事件
            await self.event_bus.publish(EventType.SYSTEM_STOPPED)
            
            logging.info("✅ 异步语音输入系统停止成功")
            return True
        except Exception as e:
            logging.error(f"❌ 异步停止系统失败: {e}")
            return False
    
    async def _handle_audio_data_available(self, audio_data):
        """处理音频数据可用事件"""
        try:
            # 创建识别任务
            await self.task_manager.create_task(
                self._process_audio_data_async(audio_data),
                task_name="AudioRecognition"
            )
        except Exception as e:
            logging.error(f"❌ 处理音频数据失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '音频数据处理'
            })
    
    async def _process_audio_data_async(self, audio_data):
        """异步处理音频数据"""
        try:
            # 异步识别语音
            text = await self.voice_recognizer.recognize_async(audio_data)
            
            # 发布识别完成事件
            await self.event_bus.publish(EventType.RECOGNITION_COMPLETE, text)
        except Exception as e:
            logging.error(f"❌ 语音识别失败: {e}")
            await self.event_bus.publish(EventType.RECOGNITION_FAILED, {
                'error': str(e)
            })
    
    async def _handle_recognition_complete(self, text):
        """处理识别完成事件"""
        try:
            # 处理文本
            processed_text = self.text_processor.process_text(text)
            
            # 发布文本处理完成事件
            await self.event_bus.publish(EventType.TEXT_PROCESSED, processed_text)
        except Exception as e:
            logging.error(f"❌ 处理识别结果失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '识别结果处理'
            })
    
    async def _handle_text_processed(self, processed_text):
        """处理文本处理完成事件"""
        try:
            # 提取数值
            measurements = self.text_processor.extract_measurements(processed_text)
            
            # 发布数值提取完成事件
            await self.event_bus.publish(EventType.MEASUREMENT_EXTRACTED, {
                'measurements': measurements,
                'original_text': processed_text
            })
        except Exception as e:
            logging.error(f"❌ 提取数值失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '数值提取'
            })
    
    async def _handle_measurement_extracted(self, data):
        """处理数值提取完成事件"""
        try:
            measurements = data['measurements']
            original_text = data['original_text']
            
            # 导出数据到Excel
            if self.data_exporter:
                await self.task_manager.create_task(
                    self.data_exporter.append_with_text_async(original_text),
                    task_name="DataExport"
                )
            
            # TTS播报结果
            if self.tts_manager:
                await self.task_manager.create_task(
                    self.tts_manager.speak(f"成功提取数值: {measurements}"),
                    task_name="TTSAnnouncement"
                )
        except Exception as e:
            logging.error(f"❌ 处理提取结果失败: {e}")
            await self.event_bus.publish(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'context': '提取结果处理'
            })
    
    async def _handle_error(self, error_data):
        """处理错误事件"""
        error = error_data.get('error', 'Unknown error')
        context = error_data.get('context', 'Unknown context')
        logging.error(f"❌ 系统错误 ({context}): {error}")
        
        # 这里可以添加错误处理逻辑
        # 例如重试操作、降级服务、发送通知等
```

### 7.2 主程序入口

```python
# 主程序入口
if __name__ == "__main__":
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('voice_input_system.log', encoding='utf-8')
        ]
    )
    
    # 捕获未处理的异常
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_uncaught_exception
    
    # 创建并启动系统
    try:
        system = AsyncVoiceInputSystem()
        sys.exit(0 if system.start() else 1)
    except Exception as e:
        logging.critical(f"系统启动失败: {e}")
        sys.exit(1)
```

## 8. 最佳实践与建议

### 8.1 异步编程最佳实践

1. **使用asyncio.run()**：对于简单应用，使用`asyncio.run()`来运行主协程
2. **避免阻塞操作**：不要在异步代码中使用阻塞式IO操作
3. **使用await**：始终使用`await`来等待协程完成
4. **使用async with**：对于需要异步上下文管理的资源，使用`async with`
5. **使用async for**：对于异步迭代器，使用`async for`
6. **避免长时间运行的同步函数**：如果必须使用，考虑使用`loop.run_in_executor()`

### 8.2 任务管理最佳实践

1. **跟踪所有任务**：确保每个创建的任务都被跟踪
2. **设置合理的超时**：为长时间运行的任务设置超时
3. **优雅取消任务**：使用`task.cancel()`和`await task`组合来取消任务
4. **处理CancelledError**：在协程中正确处理`CancelledError`异常
5. **使用shield保护关键任务**：使用`asyncio.shield()`保护不应该被取消的关键任务

### 8.3 防止资源泄漏的建议

1. **使用上下文管理器**：为资源创建上下文管理器，确保资源被正确释放
2. **实现优雅关闭**：为每个组件实现`cleanup()`或`shutdown()`方法
3. **避免循环引用**：注意避免对象之间的循环引用，这可能导致资源泄漏
4. **定期检查资源使用情况**：监控内存和文件句柄等资源的使用情况
5. **使用弱引用**：对于可能导致循环引用的情况，考虑使用弱引用

### 8.4 调试和故障排除

1. **启用详细日志**：在开发和调试阶段，启用详细日志
2. **使用aiomonitor**：使用`aiomonitor`来监控和调试运行中的异步应用
3. **检查未完成的任务**：在系统关闭前检查是否有未完成的任务
4. **使用asyncio debug模式**：通过设置`PYTHONASYNCIODEBUG=1`环境变量启用asyncio调试模式
5. **使用faulthandler**：启用`faulthandler`模块来获取更详细的崩溃信息

## 9. 常见问题与解决方案

### 9.1 Task was destroyed but it is pending!

**问题描述**：当系统关闭时，出现"Task was destroyed but it is pending!"错误。

**原因分析**：这通常是因为在事件循环关闭时，仍有未完成的异步任务。

**解决方案**：
1. 实现完善的任务跟踪机制，确保所有任务都被取消和清理
2. 在系统关闭时，显式取消所有任务并等待它们完成
3. 使用`asyncio.gather(*tasks, return_exceptions=True)`来等待所有任务完成
4. 为任务设置合理的超时，避免任务无限期运行

### 9.2 音频流中断

**问题描述**：音频流在运行一段时间后中断。

**原因分析**：可能是音频设备问题、缓冲区溢出或资源泄漏。

**解决方案**：
1. 实现音频流健康检查机制
2. 为音频缓冲区设置合理的大小和超时
3. 定期清理音频缓冲区，避免溢出
4. 实现音频流自动重连机制

### 9.3 TTS播报与语音识别循环

**问题描述**：TTS播报的内容被麦克风重新捕获，导致无限循环。

**原因分析**：系统没有区分用户语音和TTS播报的语音。

**解决方案**：
1. 实现TTS反馈检测机制，跳过包含特定关键词的文本
2. 使用音频播放时的静音检测
3. 在TTS播报时临时暂停语音识别
4. 为TTS播报添加特殊标记，在识别时过滤掉

### 9.4 高CPU占用率

**问题描述**：系统运行时CPU占用率过高。

**原因分析**：可能是因为异步循环中没有适当的暂停，或者任务过于密集。

**解决方案**：
1. 在异步循环中添加`await asyncio.sleep(0.001)`等短暂暂停
2. 限制并发任务数
3. 优化任务处理逻辑，减少不必要的计算
4. 使用性能分析工具识别性能瓶颈

## 10. 总结

本方案提供了一个完整的异步处理框架设计与实现，重点解决了以下问题：

1. **异步任务生命周期管理**：通过任务管理器实现了任务的创建、跟踪、取消和清理
2. **资源泄漏防止**：通过完善的清理机制，避免了"Task was destroyed but it is pending!"错误
3. **系统稳定性**：通过事件驱动架构和统一的错误处理机制，提高了系统的稳定性
4. **高效的事件驱动架构**：通过事件总线实现了组件间的松耦合通信

通过采用本方案，您可以构建一个高效、稳定、可扩展的异步语音输入系统，同时避免常见的异步编程陷阱和资源泄漏问题。