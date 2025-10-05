# Flask模型加载网络API

## 📖 概述

本模块提供一个基于Flask的本地网络API服务，用于集中管理和加载语音识别模型。通过这个API，多个应用程序实例可以共享同一个模型实例，避免重复加载模型导致的资源浪费。

## 🚀 主要功能

- **模型集中管理**: 集中加载和卸载语音识别模型
- **多客户端共享**: 多个应用程序可以共享同一个模型实例
- **RESTful API**: 提供标准的HTTP接口，易于集成
- **状态监控**: 实时监控已加载模型的状态和使用情况
- **健康检查**: 提供API服务健康状态检查

## 🛠️ 技术架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  客户端应用1    ├───▶ │  Flask模型API   │◀───┤  客户端应用2    │
│                 │     │                 │     │                 │
└─────────────────┘     │  ┌───────────┐  │     └─────────────────┘
                        │  │           │  │     ┌─────────────────┐
                        │  │  模型池   │  │     │                 │
                        │  │           │  │     │  客户端应用3    │
                        │  └───────────┘  │◀───┤                 │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## 📁 文件结构

```
model_server/
├── flask_model_api.py  # Flask API服务器实现
├── model_api_client.py # 客户端SDK实现
└── README.md           # 本说明文件
```

## ⚙️ 安装与配置

### 安装依赖

```bash
# 在项目根目录下运行
uv add flask requests
```

### 配置说明

API服务支持以下配置（在`flask_model_api.py`中）：

- **默认模型路径**: `model/cn`
- **模型目录**: `model`
- **服务器地址**: `0.0.0.0` (允许所有网络接口访问)
- **服务器端口**: `5000`

## 📋 使用指南

### 启动API服务器

```bash
# 在项目根目录下运行
python model_server/flask_model_api.py
```

启动后，服务器将在`http://localhost:5000/api`提供以下端点：

- `GET /api/health` - 健康检查
- `GET /api/models` - 列出所有已加载的模型
- `GET /api/models/status/<path>` - 获取特定模型状态
- `POST /api/models/load` - 加载模型
- `POST /api/models/unload` - 卸载模型

### 使用客户端SDK

```python
from model_server.model_api_client import ModelAPIClient

# 创建客户端实例
client = ModelAPIClient()

# 检查API健康状态
health_status = client.check_health()
print(f"API状态: {health_status}")

# 加载模型
load_result = client.load_model("model/cn")
print(f"模型加载结果: {load_result}")

# 列出已加载的模型
models = client.list_models()
print(f"已加载模型: {models}")

# 卸载模型
unload_result = client.unload_model("model/cn")
print(f"模型卸载结果: {unload_result}")
```

### 直接使用HTTP请求

```bash
# 健康检查
curl http://localhost:5000/api/health

# 加载模型
curl -X POST -H "Content-Type: application/json" \
  -d '{"model_path": "model/cn"}' \
  http://localhost:5000/api/models/load

# 列出模型
curl http://localhost:5000/api/models

# 卸载模型
curl -X POST -H "Content-Type: application/json" \
  -d '{"model_path": "model/cn"}' \
  http://localhost:5000/api/models/unload
```

## 🔄 与现有系统集成

将模型API集成到现有系统的示例：

```python
class VoiceInputSystem:
    def __init__(self):
        self.model_api_client = ModelAPIClient()
        self.current_model = None
        
    def initialize(self, model_path: str = "model/cn"):
        # 检查API健康状态
        health_check = self.model_api_client.check_health()
        if not health_check.get("success", False):
            print("警告: 模型API服务不可用，将使用本地加载模式作为备选")
            # 使用本地加载模式的代码
            return False
        
        # 通过API加载模型
        load_result = self.model_api_client.load_model(model_path)
        if load_result.get("success", False):
            self.current_model = model_path
            return True
        else:
            return False
        
    def shutdown(self):
        if self.current_model:
            self.model_api_client.unload_model(self.current_model)
            self.current_model = None
```

## 🧪 测试

1. 首先启动API服务器：`python model_server/flask_model_api.py`
2. 然后运行客户端示例：`python model_server/model_api_client.py`

## 🚧 生产环境注意事项

在生产环境中部署时：

1. 使用Gunicorn或uWSGI等WSGI服务器替代Flask内置服务器
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "model_server.flask_model_api:app"
   ```

2. 考虑添加认证和授权机制

3. 配置日志轮转和监控

4. 使用HTTPS加密通信

## 🔮 未来改进方向

- 添加模型预热功能
- 实现模型版本管理
- 添加性能监控和统计
- 支持模型自动切换和故障转移
- 增加批量操作API

## 📅 版本历史

- **1.0.0**: 初始版本，提供基本的模型加载、卸载和管理功能

---

*Last Updated: October 2025*