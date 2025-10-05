# 测试套件

本目录包含事件驱动语音输入系统的完整测试套件。

## 📁 测试文件说明

### 核心测试文件

| 文件名 | 描述 | 依赖要求 |
|--------|------|---------|
| `test_basic.py` | 基础功能测试 | 无依赖 |
| `test_event_system.py` | 事件系统测试 | 无依赖 |
| `test_async_audio.py` | 异步音频组件测试 | 无依赖（使用模拟组件） |
| `test_full_async_audio.py` | 完整异步音频测试 | PyAudio |
| `test_integration.py` | 集成测试 | 事件系统 |

### 运行工具

| 文件名 | 描述 |
|--------|------|
| `run_tests.py` | 统一测试运行器 |

## 🚀 运行测试

### 使用统一测试运行器（推荐）
```bash
# 使用虚拟环境Python
.venv\Scripts\python.exe tests\run_tests.py
```

### 运行单个测试
```bash
# 基础功能测试
.venv\Scripts\python.exe tests\test_basic.py

# 事件系统测试
.venv\Scripts\python.exe tests\test_event_system.py

# 异步音频测试
.venv\Scripts\python.exe tests\test_async_audio.py

# 完整异步音频测试（需要PyAudio）
.venv\Scripts\python.exe tests\test_full_async_audio.py

# 集成测试
.venv\Scripts\python.exe tests\test_integration.py
```

### 使用虚拟环境
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行所有测试
python tests\run_tests.py
```

## 📊 测试覆盖范围

### ✅ 基础功能测试 (`test_basic.py`)
- 事件模块导入测试
- 事件处理器创建测试
- 系统协调器导入测试
- 接口模块导入测试
- 依赖注入容器导入测试

### ✅ 事件系统测试 (`test_event_system.py`)
- 事件类型测试
- 事件处理器测试
- 统计信息测试
- 错误处理测试

### ✅ 异步音频组件测试 (`test_async_audio.py`)
- 模拟音频流测试
- 模拟识别器测试
- 模拟TTS播放器测试
- 无外部依赖

### ✅ 完整异步音频测试 (`test_full_async_audio.py`)
- 真实PyAudio集成测试
- 异步音频组件创建测试
- 模拟组件功能测试
- 支持真实硬件测试

### ✅ 集成测试 (`test_integration.py`)
- 系统协调器测试
- 事件创建和传播测试
- 错误处理测试
- 组件集成测试

## 🔧 环境要求

### Python版本
- Python 3.8+

### 依赖包
- **核心功能**: 无额外依赖
- **完整音频测试**: PyAudio 0.2.14+

### 虚拟环境
项目使用 `venv` 虚拟环境管理依赖。

## 📈 预期输出

```
事件驱动语音输入系统 - 测试套件
==================================================
使用虚拟环境运行: .venv\Scripts\python.exe run_tests.py
==================================================

基础功能测试
==================================================
开始运行基础功能测试...
基础功能测试通过!

事件系统测试
==================================================
开始运行事件系统测试...
所有事件系统测试通过!

异步音频组件测试
==================================================
开始运行异步音频组件测试...
所有异步音频组件测试通过!

完整异步音频测试
==================================================
开始运行完整异步音频测试...
PyAudio可用: True
真实异步音频模块: True
所有完整异步音频测试通过!

集成测试
==================================================
开始运行集成测试...
所有集成测试通过!

==================================================
测试结果总结
==================================================
  test_basic              ✅ 通过
  test_event_system       ✅ 通过
  test_async_audio         ✅ 通过
  test_full_async_audio    ✅ 通过
  test_integration         ✅ 通过

总计: 5/5 测试套件通过

🎉 所有测试通过! 系统核心功能正常。

建议运行演示程序验证完整功能:
  .venv\Scripts\python.exe -m examples.event_driven_demo
```

## 🐛 故障排除

### 常见问题

1. **ModuleNotFoundError**
   - 确保在项目根目录下运行
   - 使用虚拟环境Python: `.venv\Scripts\python.exe`

2. **UnicodeEncodeError**
   - Windows环境下的编码问题
   - 测试文件已修复编码问题

3. **PyAudio导入错误**
   - 确保在虚拟环境中安装了PyAudio
   - 使用 `.venv\Scripts\python.exe` 运行

4. **异步测试失败**
   - 异步测试已修复事件循环问题
   - 大部分测试使用模拟组件，无依赖问题

## 📝 开发指南

### 添加新测试
1. 在相应测试文件中添加测试方法
2. 使用 `test_` 前缀命名
3. 使用 `self.assert*` 方法断言
4. 添加适当的文档字符串

### 测试原则
- 优先使用模拟组件避免依赖
- 异步测试使用 `unittest.IsolatedAsyncioTestCase`
- 同步测试使用 `unittest.TestCase`
- 保持测试独立性，避免相互依赖

---
*测试套件版本: 1.0*
*最后更新: 2025-10-05*