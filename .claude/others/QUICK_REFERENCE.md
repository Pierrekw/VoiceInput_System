# Voice Input System - Quick Reference

## 🚀 快速开始
```bash
# 激活虚拟环境
source .venv/scripts/activate

# 运行测试
.venv/scripts/python -m pytest -v

# 启动系统
.venv/scripts/python main.py
```

## 🎯 关键特性状态
| 特性 | 状态 | 测试覆盖 |
|------|------|----------|
| 实时语音识别 | ✅ 正常工作 | ✅ 已测试 |
| 暂停/恢复功能 | ✅ 正常工作 | ✅ 已测试 |
| Excel自动导出 | ✅ 正常工作 | ✅ 已测试 |
| 语音命令 | ✅ 正常工作 | ✅ 已测试 |
| 键盘控制 | ✅ 正常工作 | ✅ 已测试 |
| 中文数字转换 | ✅ 正常工作 | ✅ 已测试 |
| 错误处理 | ✅ 正常工作 | ✅ 已测试 |

## 🎮 控制参考
| 输入 | 操作 | 所需状态 |
|------|------|----------|
| 空格键 | 开始/暂停/继续 | 任意 |
| ESC | 停止并退出 | 任意 |
| "开始录音" | 语音开始 | 空闲 |
| "暂停录音" | 语音暂停 | 录音中 |
| "继续录音" | 语音继续 | 已暂停 |
| "停止录音" | 语音停止 | 任意 |

## 📊 测试命令
```bash
# 运行所有测试
.venv/scripts/python -m pytest -v

# 运行特定测试文件
.venv/scripts/python -m pytest test_main_integration.py -v

# 运行并生成覆盖率报告（如果已安装）
.venv/scripts/python -m pytest --cov=. --cov-report=html
```

## 🔧 常见问题与解决方案

### PyAudio 未找到
```bash
# 在虚拟环境中安装
.venv/scripts/python -m pip install pyaudio
```

### Vosk 模型缺失
```bash
# 下载模型到 model/ 目录
# model/cn - 中文标准模型
# model/cns - 中文小模型
# model/us - 英文标准模型
# model/uss - 英文小模型
```

### Excel 导出错误
- 检查文件权限
- 确保Excel文件未在其他程序中打开
- 验证pandas和openpyxl安装

## 📁 文件位置
- **主脚本**: `main.py`
- **音频模块**: `audio_capture_v.py`
- **Excel模块**: `excel_exporter.py`
- **测试文件**: `test_*.py`
- **输出Excel**: `measurement_data.xlsx`
- **日志文件**: `voice_input.log`

## 🧪 测试状态
- **总测试数**: 18
- **通过**: 18
- **失败**: 0
- **覆盖率**: 全面覆盖核心功能

## ⚡ 性能提示
- 使用较小的Vosk模型（cns/uss）以加快加载速度
- 调整timeout_seconds以适应较长会话
- 监控长时间录音时的内存使用情况
- 定期清理大型数据集的Excel文件

## 🔍 调试
- 查看 `voice_input.log` 获取详细日志
- 启用调试模式: `logging.basicConfig(level=logging.DEBUG)`
- 测试单个组件: `audio_capture_v.py` 和 `excel_exporter.py`
- 验证PyAudio安装: `import pyaudio; print(pyaudio.get_portaudio_version_text())`

---
*开发过程中请将此文档放在手边以便快速参考*