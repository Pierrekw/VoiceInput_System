# 语音输入系统测试文档

## 概述

本测试套件包含了语音输入系统的完整测试功能，整合了所有原有的测试文件，提供了一套统一、高效的测试方法。测试套件包括单元测试、集成测试、系统测试和模拟测试，可以全面验证系统的各项功能。

## 测试文件结构

测试套件的主要文件是`integrated_test.py`，它整合了所有测试功能，替代了原来的多个测试文件：

- `auto_integration_test.py`
- `full_integration_test.py`
- `integration_test.py`
- `main_function_test.py`
- `quick_system_test.py`
- `simple_integration_test.py`
- `system_test_mock.py`
- `test_main_full_system.py`
- `test_main_integration.py`
- `test_simple_import.py`
- `voice_integration_main.py`

## 测试功能分类

整合后的测试文件包含以下几类测试功能：

### 1. 模块导入测试

- `test_simple_import()` - 验证核心模块能否正确导入

### 2. 单元测试

- `test_text_to_numbers_conversion()` - 测试文本转数字功能
- `test_state_machine()` - 测试系统状态机功能
- `test_voice_commands()` - 测试语音命令处理功能
- `test_main_initialization()` - 测试主程序初始化
- `test_callback_integration()` - 测试回调函数集成

### 3. 集成测试

- `test_voice_recognition_pipeline()` - 全面集成测试语音识别管道
- `test_main_function_flow()` - 测试主函数流程和Mode 1功能

### 4. 系统测试

- `run_quick_system_test()` - 快速系统测试，模拟语音输入和键盘控制
- `run_auto_integration_test()` - 自动集成测试（非交互式）

## 配置文件

`pytest.ini`文件包含了测试的配置信息：

- 设置Python路径，确保可以正确导入模块
- 配置测试文件发现模式
- 配置测试报告格式和详细程度
- 过滤不需要的警告
- 配置日志输出

## 使用方法

### 使用pytest运行测试

1. 安装pytest（如果尚未安装）：
   ```
   pip install pytest
   ```

2. 在项目根目录运行所有测试：
   ```
   pytest
   ```

3. 运行特定的测试函数：
   ```
   pytest tests/integrated_test.py::test_text_to_numbers_conversion -v
   ```

4. 运行特定类别的测试：
   ```
   pytest tests/integrated_test.py::test_voice_recognition_pipeline -v
   ```

### 作为独立脚本运行

您也可以直接运行`integrated_test.py`作为独立脚本，使用交互式命令行界面选择要运行的测试：

```
python tests/integrated_test.py
```

运行后，您将看到一个菜单，可以选择运行不同类型的测试：

```
🚀 语音输入系统 - 集成测试套件
============================================================
可用测试选项:
1. 综合集成测试
2. 主函数流程测试
3. 快速系统测试
4. 自动集成测试
q. 退出
============================================================
```

输入相应的数字选择要运行的测试，或输入`q`退出。

## 测试功能详解

### 模块导入测试

验证系统所需的核心模块能否正确导入，包括`audio_capture_v`、`excel_exporter`和`main`等。

### 文本转数字转换测试

测试系统能否正确地将中文文本中的数字（包括整数、小数、中文数字等）转换为数值。支持各种格式的数字识别，包括纯中文数字、混合中英文数字、特殊格式如"零点八"、"两千克"等。

### 状态机测试

测试系统的状态管理机制，验证系统能否在不同状态之间正确转换。

### 语音命令测试

测试系统能否正确识别和处理语音命令，如"开始录音"、"暂停录音"等。

### 主程序初始化测试

测试`main.py`中的`VoiceInputSystem`类能否正确初始化，验证系统组件是否被正确创建和配置。

### 回调函数集成测试

测试回调函数机制是否正常工作，确保数据能够正确传递和处理。

### 综合集成测试

全面测试语音识别系统的完整流程，包括系统初始化、音频设备检查、模型加载、语音命令处理、实时识别、数字提取和Excel导出等功能。

### 主函数流程测试

模拟主程序的完整运行流程，测试Mode 1语音识别功能和系统的主要操作流程。

### 快速系统测试

通过模拟语音输入会话和键盘控制，快速测试系统的核心功能，包括数据处理、暂停/恢复操作和Excel自动保存等。

### 自动集成测试

非交互式的自动测试，无需用户输入即可运行一系列基本测试，验证系统的基本功能是否正常。

## 常见问题及解决方案

### 1. 模块导入失败

如果遇到模块导入失败的问题，请确保：
- 您在项目根目录下运行测试
- 所有依赖项已安装（可通过`pip install -r requirements.txt`安装）
- `pytest.ini`文件中的`pythonpath = .`配置正确

### 2. 测试警告

为了避免不必要的测试警告，`pytest.ini`文件中已经配置了忽略常见警告的设置。如果遇到新的警告，可以在配置文件中添加相应的过滤规则。

### 3. 音频设备问题

测试过程中可能会遇到音频设备相关的问题，请确保：
- 您的计算机有可用的麦克风设备
- 麦克风权限已正确设置
- PyAudio库已正确安装

## 更新日志

### v1.0 (整合版本)
- 整合所有原有测试文件为一个统一的`integrated_test.py`
- 优化测试结构和组织方式
- 添加统一的配置文件和详细的使用文档
- 修复了pytest警告问题
- 改进了测试报告和日志输出